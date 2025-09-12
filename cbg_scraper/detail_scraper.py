import re
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
import os
import requests
from bs4 import BeautifulSoup

BASE = "https://my.cbg.163.com/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def fetch_html(url: str) -> str:
    cookie = os.getenv("CBG_COOKIE", "")
    h = {
        "User-Agent": UA,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
        "Cookie": cookie,
    }
    r = requests.get(url, headers=h, timeout=25)
    r.raise_for_status()
    return r.text

def parse_detail(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    data: Dict[str, Any] = {}

    # 顶部关键摘要（移动端页面常见结构）
    head = soup.select_one(".request-status-ctrl") or soup

    # 标题/昵称（左上角头像旁/标题区域）
    title = head.select_one(".name, .title, .item-title, .detail-title, .user-name, .equip-name")
    # 价格（红色金额/立即购买按钮附近）
    price = head.select_one(".price, .money, .red, .detail-price, .buy-price, .price-num")
    # 区服（标题下方/摘要条）
    server = head.select_one(".server, .area, .region, .summary .server, .loc, .zone")
    # 等级
    level_el = head.select_one(".level, .lv, .grade")
    if not level_el:
        level_el = soup.find(string=re.compile(r"\b\d+\s*级\b"))

    data["title"] = title.get_text(strip=True) if title else ""
    data["price"] = price.get_text(strip=True) if price else ""
    data["server"] = server.get_text(strip=True) if server else ""
    data["level"] = (level_el.strip() if isinstance(level_el, str) else level_el.get_text(strip=True)) if level_el else ""

    # 商品编号（“编号：xxxxxx”）
    sn = ""
    sn_el = soup.find(string=re.compile(r"编号[:：]\s*\d+"))
    if sn_el:
        m = re.search(r"编号[:：]\s*(\d+)", sn_el)
        if m:
            sn = m.group(1)
    if not sn:
        # 备选：页面变量里可能有 sn/ware_id
        script_text = " ".join(s.get_text(" ") for s in soup.find_all("script"))
        m2 = re.search(r'"(?:sn|ware_id)"\s*:\s*"(\d+)"', script_text)
        if m2:
            sn = m2.group(1)
    data["sn"] = sn

    # 剩余时间
    remain = head.select_one(".countdown, .remain-time, .time-left, .left-time")
    if not remain:
        remain = soup.find(string=re.compile(r"剩余时间"))
    data["remain_time"] = (remain.strip() if isinstance(remain, str) else remain.get_text(strip=True)) if remain else ""

    # 预览标签：outer-content/pdetailPreview 内的标签、按钮文本
    preview = head.select_one(".outer-content .list-block.border.pdetailPreview") or soup.select_one(".pdetailPreview, .preview, .tag-list")
    if preview:
        tags = [t.get_text(strip=True) for t in preview.select(".tag, .label, .badge, .btn, .chip, .col, .pill") if t.get_text(strip=True)]
        data["preview_tags"] = " | ".join(tags)

    # 主内容摘要（评估报告等tab标题与表格）
    main = head.select_one(".main-content") or soup.select_one(".main-content, .detail-tabs, .tabs")
    if main:
        assess_titles = [x.get_text(strip=True) for x in main.select(".eva-title, .panel-title, .card-title, .tab-title, .section-title") if x.get_text(strip=True)]
        if assess_titles:
            data["assess_titles"] = " | ".join(assess_titles)

        kvs: List[str] = []
        for row in main.select("table tr"):
            cols = [c.get_text(strip=True) for c in row.select("th,td")]
            if len(cols) >= 2:
                kvs.append(f"{cols[0]}={cols[1]}")
        # 备选：列表样式的 key:value
        for li in main.select("li"):
            txt = li.get_text(" ", strip=True)
            m = re.match(r"(.{1,12})[:：]\s*(.+)", txt)
            if m:
                kvs.append(f"{m.group(1)}={m.group(2)}")
        if kvs:
            data["main_table"] = " | ".join(kvs)

        chips = [c.get_text(strip=True) for c in main.select(".tag, .label, .badge, .chip, .pill") if c.get_text(strip=True)]
        if chips:
            data["main_tags"] = " | ".join(chips)

    # 卖家信息
    seller = soup.find(string=re.compile(r"卖家[:：]")) or soup.select_one(".seller, .shop, .owner, .user, .merchant")
    data["seller"] = (seller.strip() if isinstance(seller, str) else seller.get_text(strip=True)) if seller else ""

    # 兜底：若价格/标题为空，尝试全局正则提取
    if not data.get("price"):
        m = re.search(r"￥\s*([\d,\.]+)", soup.get_text(" ", strip=True))
        if m:
            data["price"] = m.group(0)
    if not data.get("title"):
        # 从 <title> 标签兜底
        t = soup.title.get_text(strip=True) if soup.title else ""
        data["title"] = t

    return data