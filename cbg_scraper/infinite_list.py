import re
import json
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlencode, urlparse, parse_qs
import requests

BASE = "https://my.cbg.163.com/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def _get(url: str, expect_json: bool = True, headers: Optional[Dict] = None, timeout: int = 20):
    h = {
        "User-Agent": UA,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
    }
    if expect_json:
        h["Accept"] = "application/json,text/javascript,*/*;q=0.1"
    else:
        h["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    if headers:
        h.update(headers)
    r = requests.get(url, headers=h, timeout=timeout)
    r.raise_for_status()
    return r.json() if expect_json else r.text

def extract_api_from_html(html: str) -> Tuple[Optional[str], Dict[str, str]]:
    """
    从首页HTML的内联脚本中尽力提取滚动接口及初始参数（容错）。
    返回：(api_base_url, params_dict)；若失败，返回 (None, {})
    """
    # 直链接口（含 https://my.cbg.163.com/cgi/...）
    m = re.search(r"https://my\.cbg\.163\.com(/cgi/[A-Za-z0-9_/\-\.\?=&%]+)", html)
    if m:
        path = m.group(1)
        parsed = urlparse(path)
        qs = parse_qs(parsed.query or "")
        params = {k: (v[0] if isinstance(v, list) and v else v) for k, v in qs.items()}
        return urljoin(BASE, parsed.path), params

    # 相对路径接口 /cgi/...
    m2 = re.search(r"(/cgi/[A-Za-z0-9_/\-\.\?=&%]+)", html)
    if m2:
        path = m2.group(1)
        parsed = urlparse(path)
        qs = parse_qs(parsed.query or "")
        params = {k: (v[0] if isinstance(v, list) and v else v) for k, v in qs.items()}
        return urljoin(BASE, parsed.path), params

    # 可能存在初始化对象里的一些关键参数，如 reco_request_id、scene、cursor
    params: Dict[str, str] = {}
    for key in ["reco_request_id", "exposed_scene_id", "scene", "cursor", "page", "offset", "tag", "tfid", "tcid"]:
        mm = re.search(rf'["\']{key}["\']\s*:\s*["\']([^"\']+)["\']', html)
        if mm:
            params[key] = mm.group(1)

    # 如果什么都没有，返回None
    return None, params

def crawl_infinite(api_base: str, params: Dict[str, str], pages: int = 10, delay: float = 0.8) -> List[Dict]:
    """
    通用无限滚动抓取：
    - api_base: 像 https://my.cbg.163.com/cgi/mweb/equip/reco 这样的基路径（不含查询）
    - params: 初始查询参数（包含可能的 scene/reco_request_id/cursor 等）
    - pages: 迭代请求次数（近似“10屏”）
    - 需要根据响应结构更新下一轮的 cursor/last_id 等键
    """
    rows: List[Dict] = []
    cursor_keys = ["cursor", "last_id", "lastSn", "last_sn", "next", "next_cursor", "page"]
    for i in range(1, pages + 1):
        url = api_base + "?" + urlencode(params)
        try:
            data = _get(url, expect_json=True)
        except Exception as e:
            print(f"[warn] api request failed page={i}: {e} url={url}")
            break

        # 根据常见结构抽取列表
        items = None
        for path in [["data", "list"], ["result", "list"], ["list"], ["items"], ["data"]]:
            cur = data
            ok = True
            for k in path:
                if isinstance(cur, dict) and k in cur:
                    cur = cur[k]
                else:
                    ok = False
                    break
            if ok and isinstance(cur, list):
                items = cur
                break
        if items is None and isinstance(data, list):
            items = data
        if not items:
            print(f"[info] empty items at page={i}")
            break

        # 规范化字段
        for it in items:
            title = (it.get("title") or it.get("name") or "").strip() if isinstance(it, dict) else ""
            price = str(it.get("price") or it.get("amount") or it.get("price_desc") or "").strip() if isinstance(it, dict) else ""
            server = (it.get("server") or it.get("area") or it.get("region") or "").strip() if isinstance(it, dict) else ""
            link = ""
            if isinstance(it, dict):
                for lk in ["link", "url", "href", "equip_url", "detail_url"]:
                    if it.get(lk):
                        link = it[lk]
                        break
            if link and not link.startswith("http"):
                link = urljoin(BASE, link)
            rows.append({
                "game": "梦幻西游手游",
                "title": title,
                "price": price,
                "server": server,
                "seller": "",
                "publish_time": (it.get("publish_time") or it.get("time") or it.get("desc") or "" ) if isinstance(it, dict) else "",
                "link": link,
                "category": "listing",
            })

        # 更新下一页指针
        next_cursor = None
        # 常见位置：data.next_cursor / data.cursor / result.next / next / last_id
        for k in ["next_cursor", "cursor", "next", "last_id", "lastSn", "last_sn"]:
            # 逐层查找
            for container in [data, data.get("data") if isinstance(data, dict) else None, data.get("result") if isinstance(data, dict) else None]:
                if isinstance(container, dict) and k in container and container[k]:
                    next_cursor = container[k]
                    break
            if next_cursor:
                break
        if next_cursor:
            for ck in cursor_keys:
                if ck in params:
                    params[ck] = next_cursor
                    break
            else:
                params["cursor"] = next_cursor
        else:
            # 若没有游标则尝试简单page自增
            if "page" in params:
                try:
                    params["page"] = int(params.get("page", 1)) + 1
                except Exception:
                    params["page"] = str(int(params.get("page", "1")) + 1)
            else:
                params["page"] = params.get("page", 1)
                try:
                    params["page"] = int(params["page"]) + 1
                except Exception:
                    params["page"] = "2"

        print(f"[info] api page={i} total_rows={len(rows)} next_cursor={next_cursor}")
        time.sleep(delay)
    return rows