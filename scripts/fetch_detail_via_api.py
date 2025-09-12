import os
import re
import json
import time
from typing import Dict, Any, List, Tuple
import requests
from pandas import DataFrame

BASE = "https://my.cbg.163.com"

API_PATHS = [
    "/cgi/api/mweb/equip/detail",
    "/cgi/mweb/equip/detail",
    "/cgi/api/equip/detail",
]

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def get_cookie() -> str:
    # 从环境变量读取 Cookie
    return os.getenv("CBG_COOKIE", "").strip()

def headers() -> Dict[str, str]:
    cookie = get_cookie()
    h = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": BASE + "/",
    }
    if cookie:
        h["Cookie"] = cookie
    return h

def parse_server_sn(url: str) -> Tuple[str, str]:
    # 支持形如 /equip/{server}/{sn}
    m = re.search(r"/equip/(\\d+)/(\\d+-\\d+-[A-Z0-9]+)", url)
    if not m:
        return "", ""
    return m.group(1), m.group(2)

def fetch_detail(server: str, sn: str) -> Tuple[str, Dict[str, Any]]:
    hdr = headers()
    last_err = None
    # 尝试常见 detail 接口
    for path in API_PATHS:
        detail_url = f"{BASE}{path}?server_id={server}&sn={sn}"
        try:
            r = requests.get(detail_url, headers=hdr, timeout=15)
            ct = r.headers.get("Content-Type", "")
            if r.status_code == 200 and ("json" in ct or r.text.strip().startswith("{")):
                try:
                    return detail_url, r.json()
                except Exception:
                    return detail_url, {"raw": r.text}
        except Exception as e:
            last_err = str(e)
    # 兜底：尝试 HTML 路径添加 ?format=json
    for suffix in ["?format=json", "&format=json"]:
        detail_url = f"{BASE}/cgi/mweb/equip/{server}/{sn}{suffix}"
        try:
            r = requests.get(detail_url, headers=hdr, timeout=15)
            ct = r.headers.get("Content-Type", "")
            if r.status_code == 200 and ("json" in ct or r.text.strip().startswith("{")):
                try:
                    return detail_url, r.json()
                except Exception:
                    return detail_url, {"raw": r.text}
        except Exception as e:
            last_err = str(e)
    return "", {"error": last_err or "no_detail_api_found"}

def pick(d: Dict[str, Any], keys: List[str]) -> str:
    for k in keys:
        v = d.get(k)
        if v not in (None, "", []):
            return str(v)
    return ""

def normalize_detail(data: Dict[str, Any], sn: str) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "game": "梦幻西游手游",
        "title": "",
        "price": "",
        "server": "",
        "level": "",
        "sn": sn,
        "remain_time": "",
        "seller": "",
        "preview_tags": "",
        "assess_titles": "",
        "main_table": "",
        "main_tags": "",
    }
    if not isinstance(data, dict):
        row["error"] = "invalid_detail_response"
        return row

    row["title"] = pick(data, ["title", "name", "equip_name", "role_name", "item_name"])
    row["price"] = pick(data, ["price", "amount", "deal_price", "sale_price", "price_yuan"])
    row["server"] = pick(data, ["server", "server_name", "area_name"])
    row["level"] = pick(data, ["level", "role_level", "equip_level"])
    row["remain_time"] = pick(data, ["remain_time", "left_time", "time_left", "expire_in"])
    row["seller"] = pick(data, ["seller", "seller_name", "shop_name"])

    # tags / assess（尽力映射）
    if "tags" in data:
        try:
            row["preview_tags"] = json.dumps(data.get("tags", []), ensure_ascii=False)
        except Exception:
            pass
    if isinstance(data.get("assess"), list):
        row["assess_titles"] = ",".join([str(a.get("title", "")) for a in data["assess"] if isinstance(a, dict)])

    if not any([row["title"], row["price"], row["server"]]):
        row["raw_keys"] = ",".join(list(data.keys())[:30])

    return row

def run(urls: List[str]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    debug: List[Dict[str, Any]] = []
    for u in urls:
        base = u.split("?")[0]
        server, sn = parse_server_sn(base)
        if not server or not sn:
            rows.append({"link": u, "error": "parse_server_sn_failed"})
            continue
        api_hit, data = fetch_detail(server, sn)
        row = normalize_detail(data, sn)
        row["link"] = u
        rows.append(row)
        debug.append({
            "link": u,
            "api": api_hit,
            "keys": list(data.keys()) if isinstance(data, dict) else type(data).__name__
        })
    return {"rows": rows, "debug": debug}

def save_excels(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    os.makedirs("output", exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    # 明细
    order = ["game", "title", "price", "server", "level", "sn", "remain_time", "seller",
             "preview_tags", "assess_titles", "main_table", "main_tags", "link", "error", "raw_keys"]
    allk = set().union(*[set(r.keys()) for r in rows]) if rows else set(order)
    cols = order + [k for k in sorted(allk) if k not in order]
    DataFrame([{k: r.get(k, "") for k in cols} for r in rows], columns=cols).to_excel(
        f"output/mhxy_detail_sample_{ts}.xlsx", index=False
    )
    # 列表（由详情兜底）
    list_cols = ["game", "title", "price", "server", "seller", "publish_time", "link", "category"]
    list_rows = [{
        "game": r.get("game", "梦幻西游手游"),
        "title": r.get("title", ""),
        "price": r.get("price", ""),
        "server": r.get("server", ""),
        "seller": r.get("seller", ""),
        "publish_time": r.get("remain_time", ""),
        "link": r.get("link", ""),
        "category": "listing",
    } for r in rows]
    DataFrame(list_rows, columns=list_cols).to_excel(
        f"output/mhxy_list_sample_{ts}.xlsx", index=False
    )
    return {"detail_rows": len(rows), "list_rows": len(list_rows)}

def main():
    urls = [
        "https://my.cbg.163.com/cgi/mweb/equip/271/202507310201716-271-LVRAVMES380K",
        "https://my.cbg.163.com/cgi/mweb/equip/94/202509070101716-94-JYRBC8LSXO1IW",
        "https://my.cbg.163.com/cgi/mweb/equip/47/202504290701716-47-UYEZGMCLKZBXP",
    ]
    result = run(urls)
    stats = save_excels(result["rows"])
    print(json.dumps({"stats": stats, "debug": result["debug"]}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()