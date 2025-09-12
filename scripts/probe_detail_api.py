import os
import re
import json
from urllib.parse import urlparse
import requests

BASE = "https://my.cbg.163.com"

CANDIDATES = [
    "/cgi/api/mweb/equip/detail",
    "/cgi/mweb/equip/detail",
    "/cgi/api/equip/detail",
]

def parse_server_sn(url: str):
    # e.g. https://my.cbg.163.com/cgi/mweb/equip/271/202507310201716-271-LVRAVMES380K?... 
    m = re.search(r"/equip/(\\d+)/(\\d+-\\d+-[A-Z0-9]+)", url)
    if not m:
        return None, None
    return m.group(1), m.group(2)

def build_headers():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    cookie = os.getenv("CBG_COOKIE", "")
    h = {
        "User-Agent": ua,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": BASE + "/",
    }
    if cookie:
        h["Cookie"] = cookie
    return h

def try_probe(urls):
    headers = build_headers()
    ok = []
    for full_url in urls:
        try:
            r = requests.get(full_url, headers=headers, timeout=15)
            ct = r.headers.get("Content-Type", "")
            if r.status_code == 200 and ("json" in ct or r.text.strip().startswith("{")):
                data = r.json()
                ok.append((full_url, data))
        except Exception:
            pass
    return ok

def main():
    # sample detail urls (from user)
    urls = [
        "https://my.cbg.163.com/cgi/mweb/equip/271/202507310201716-271-LVRAVMES380K",
        "https://my.cbg.163.com/cgi/mweb/equip/94/202509070101716-94-JYRBC8LSXO1IW",
        "https://my.cbg.163.com/cgi/mweb/equip/47/202504290701716-47-UYEZGMCLKZBXP",
    ]
    # strip query for parsing server/sn
    urls = [u.split("?")[0] for u in urls]
    targets = []
    for u in urls:
        server, sn = parse_server_sn(u)
        if not server or not sn:
            continue
        # assemble candidate query urls
        for path in CANDIDATES:
            targets.append(f"{BASE}{path}?server_id={server}&sn={sn}")
        # also try json param on the html path (some sites support)
        targets.append(f"{BASE}/cgi/mweb/equip/{server}/{sn}?format=json")
        targets.append(f"{BASE}/cgi/mweb/equip/{server}/{sn}&format=json")

    results = try_probe(targets)
    out = {
        "tried": targets,
        "found": [(u, list(d.keys()) if isinstance(d, dict) else type(d).__name__) for u, d in results],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()