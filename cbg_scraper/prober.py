import os
import re
import json
from typing import Dict, List
import requests
from bs4 import BeautifulSoup
from .utils import ensure_dir, ts

BASE = "https://my.cbg.163.com/"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def fetch_home_html() -> str:
    headers = {
        "User-Agent": UA,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }
    resp = requests.get(BASE, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text

def probe_home(debug_dir: str = "output/debug") -> Dict:
    ensure_dir(debug_dir)
    html = fetch_home_html()
    # 保存首屏HTML
    html_path = os.path.join(debug_dir, f"home_{ts()}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    soup = BeautifulSoup(html, "lxml")
    # 1) 可能的接口URL片段
    candidates = set()
    for m in re.finditer(r"/cgi/[^\"]+", html):
        s = m.group(0)
        if any(k in s for k in ["equip", "list", "reco", "search", "mweb"]):
            candidates.add(s)

    # 2) 首屏详情链接
    links: List[str] = []
    for a in soup.select("a[href*='/cgi/mweb/equip/']"):
        href = a.get("href") or ""
        if href and not href.startswith("http"):
            href = requests.compat.urljoin(BASE, href)
        links.append(href)

    data = {
        "debug_html": html_path,
        "candidates": sorted(candidates),
        "detail_links": links,
    }
    # 保存探测结果
    json_path = os.path.join(debug_dir, f"probe_{ts()}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data