from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlencode
from .config import ScrapeConfig
from .utils import sleep_s

BASE = "https://my.cbg.163.com/"

# 说明：CBG不同游戏的频道与参数可能差异较大。
# 这里先以占位的“mweb/equip/{game}?page=x”结构试跑，若返回结构与选择器不匹配，将在运行后按实际页面调整。
def build_list_url(game: str, page: int) -> str:
    # 先以首页流做占位分页（若站点不支持该参数，后续切换到真实分页/接口）
    query = {"page": page}
    return urljoin(BASE, f"?{urlencode(query)}")

def fetch_page(url: str, ua: str) -> str:
    headers = {
        "User-Agent": ua,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text

def parse_list(html: str, game: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    items: List[Dict] = []

    # 锚定页面容器：page-index-cnt -> goods-list.list-block.bg-content
    root = soup.select_one("div.page-index-cnt") or soup
    goods = root.select_one(".goods-list.list-block.bg-content") or root

    # 灰底列表内的卡片链接（移动端常见 .item-link）
    cards = goods.select(".gray a.item-link, .gray .item-link, .list-block a.item-link, a[href*='/cgi/mweb/equip/']")
    if not cards:
        # 回退选择
        cards = goods.select("a.item-link, a[href*='/cgi/mweb/equip/']")

    for card in cards:
        href = card.get("href") or ""
        if href and not href.startswith("http"):
            href = urljoin(BASE, href)

        def txt(sel: str) -> str:
            el = card.select_one(sel)
            return el.get_text(strip=True) if el else ""

        title = txt(".title, .name, .item-title, .equip-name, .row .col-80")
        price = txt(".price, .money, .number, .item-after, .red")
        server = txt(".server, .area, .region, .item-subtitle, .tag-area")
        publish_time = txt(".time, .pub-time, .item-text, .desc")

        items.append({
            "game": game,
            "title": title,
            "price": price,
            "server": server,
            "seller": "",
            "publish_time": publish_time,
            "link": href,
            "category": "listing",
        })
    return items

def scrape_game(config: ScrapeConfig) -> List[Dict]:
    all_rows: List[Dict] = []
    for p in range(1, config.pages + 1):
        url = build_list_url(config.game, p)
        try:
            html = fetch_page(url, config.user_agent)
            rows = parse_list(html, config.game)
            all_rows.extend(rows)
            # 简要进度输出
            print(f"[info] page={p} url={url} rows={len(rows)} total={len(all_rows)}")
        except Exception as e:
            print(f"[warn] page {p} failed: {e}")
        sleep_s(config.delay_seconds)
    return all_rows