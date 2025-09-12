import os
import json
from pathlib import Path
from urllib.parse import urlparse
from cbg_scraper.detail_scraper import fetch_html

URLS = [
    "https://my.cbg.163.com/cgi/mweb/equip/271/202507310201716-271-LVRAVMES380K?view_loc=reco_home%7Ctag_key%3A%7B%22exposed_scene_id%22%3A%20%221757631007986-5c17696e%22,%20%22is_from_ad_reco%22%3A%200,%20%22tag%22%3A%20%22user%22%7D&reco_request_id=1757631008165I1W3u&tag=user&tfid=f_reco_home&tcid=c_reco_home&exposed_scene_id=1757631007986-5c17696e&refer_sn=01993AF8-CA48-A8F9-7E51-D806446C66F6",
    "https://my.cbg.163.com/cgi/mweb/equip/94/202509070101716-94-JYRBC8LSXO1IW?view_loc=reco_home%7Ctag_key%3A%7B%22exposed_scene_id%22%3A%20%221757631007986-5c17696e%22,%20%22is_from_ad_reco%22%3A%200,%20%22tag%22%3A%20%22user%22%7D&reco_request_id=1757631008165I1W3u&tag=user&tfid=f_reco_home&tcid=c_reco_home&exposed_scene_id=1757631007986-5c17696e&refer_sn=01993AF8-CA48-A8F9-7E51-D806446C66F6",
    "https://my.cbg.163.com/cgi/mweb/equip/47/202504290701716-47-UYEZGMCLKZBXP?view_loc=reco_home%7Ctag_key%3A%7B%22exposed_scene_id%22%3A%20%221757631007986-5c17696e%22,%20%22is_from_ad_reco%22%3A%200,%20%22tag%22%3A%20%22user%22%7D&reco_request_id=1757631008165I1W3u&tag=user&tfid=f_reco_home&tcid=c_reco_home&exposed_scene_id=1757631007986-5c17696e&refer_sn=01993AF8-CA48-A8F9-7E51-D806446C66F6",
]

def main():
    out_dir = Path("output/html")
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for i, u in enumerate(URLS, 1):
        html = fetch_html(u)
        fn = out_dir / f"detail_{i}.html"
        fn.write_text(html, encoding="utf-8")
        saved.append(str(fn))
    print(json.dumps({"saved": saved}, ensure_ascii=False))

if __name__ == "__main__":
    main()