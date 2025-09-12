import json, os
from cbg_scraper.detail_scraper import fetch_html, parse_detail
from cbg_scraper.exporter import export_excel

URLS = [
  "https://my.cbg.163.com/cgi/mweb/equip/271/202507310201716-271-LVRAVMES380K?view_loc=reco_home%7Ctag_key%3A%7B%22exposed_scene_id%22%3A%20%221757631007986-5c17696e%22,%20%22is_from_ad_reco%22%3A%200,%20%22tag%22%3A%20%22user%22%7D&reco_request_id=1757631008165I1W3u&tag=user&tfid=f_reco_home&tcid=c_reco_home&exposed_scene_id=1757631007986-5c17696e&refer_sn=01993AF8-CA48-A8F9-7E51-D806446C66F6",
  "https://my.cbg.163.com/cgi/mweb/equip/94/202509070101716-94-JYRBC8LSXO1IW?view_loc=reco_home%7Ctag_key%3A%7B%22exposed_scene_id%22%3A%20%221757631007986-5c17696e%22,%20%22is_from_ad_reco%22%3A%200,%20%22tag%22%3A%20%22user%22%7D&reco_request_id=1757631008165I1W3u&tag=user&tfid=f_reco_home&tcid=c_reco_home&exposed_scene_id=1757631007986-5c17696e&refer_sn=01993AF8-CA48-A8F9-7E51-D806446C66F6",
  "https://my.cbg.163.com/cgi/mweb/equip/47/202504290701716-47-UYEZGMCLKZBXP?view_loc=reco_home%7Ctag_key%3A%7B%22exposed_scene_id%22%3A%20%221757631007986-5c17696e%22,%20%22is_from_ad_reco%22%3A%200,%20%22tag%22%3A%20%22user%22%7D&reco_request_id=1757631008165I1W3u&tag=user&tfid=f_reco_home&tcid=c_reco_home&exposed_scene_id=1757631007986-5c17696e&refer_sn=01993AF8-CA48-A8F9-7E51-D806446C66F6"
]

def main():
  os.makedirs("output", exist_ok=True)
  rows = []
  for u in URLS:
    try:
      html = fetch_html(u)
      d = parse_detail(html)
      d["link"] = u
      d["game"] = "梦幻西游手游"
      rows.append(d)
    except Exception as e:
      rows.append({"link": u, "error": str(e)})
  # 打印摘要
  print(json.dumps({"count": len(rows)}, ensure_ascii=False))
  # 导出Excel（明细小样本）
  # 将动态字典转为统一列集合
  all_keys = set()
  for r in rows:
    all_keys.update(r.keys())
  # 关键列优先
  ordered = ["game", "title", "price", "server", "level", "sn", "remain_time", "preview_tags", "assess_titles", "main_table", "main_tags", "seller", "link", "error"]
  columns = ordered + [k for k in sorted(all_keys) if k not in ordered]
  norm_rows = [{k: (rows[i].get(k, "") if isinstance(rows[i], dict) else "") for k in columns} for i in range(len(rows))]
  from pandas import DataFrame
  df = DataFrame(norm_rows, columns=columns)
  path = os.path.join("output", "mhxy_detail_sample.xlsx")
  df.to_excel(path, index=False)
  print("Saved detail sample:", path, "rows:", len(rows))

if __name__ == "__main__":
  main()