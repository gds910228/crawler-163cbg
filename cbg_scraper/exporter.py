from typing import List, Dict
from .utils import ensure_dir, ts
import os

try:
    import pandas as pd
except ImportError:
    pd = None

COLUMNS = ["game", "title", "price", "server", "seller", "publish_time", "link", "category"]

def export_excel(rows: List[Dict], game: str, output_dir: str) -> str:
    ensure_dir(output_dir)
    filename = f"{game}_{ts()}.xlsx"
    path = os.path.join(output_dir, filename)
    # Normalize rows with fixed columns
    normalized = [{col: (row.get(col) if row.get(col) is not None else "") for col in COLUMNS} for row in rows]
    if pd is None:
        # Fallback: write CSV if pandas not installed
        csv_path = path.replace(".xlsx", ".csv")
        import csv
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(normalized)
        return csv_path
    else:
        df = pd.DataFrame(normalized, columns=COLUMNS)
        df.to_excel(path, index=False)
        return path