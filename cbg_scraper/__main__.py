import argparse
from .config import ScrapeConfig
from .scraper import scrape_game
from .exporter import export_excel

def main():
    parser = argparse.ArgumentParser(description="CBG Mobile Pilot Scraper")
    parser.add_argument("--game", default="mhxy-mobile", help="game slug/id, default: mhxy-mobile")
    parser.add_argument("--pages", type=int, default=10, help="number of pages to scrape")
    parser.add_argument("--delay", type=float, default=1.0, help="delay seconds between pages")
    parser.add_argument("--out", default="output", help="output directory")
    args = parser.parse_args()

    cfg = ScrapeConfig(game=args.game, pages=args.pages, delay_seconds=args.delay, output_dir=args.out)
    rows = scrape_game(cfg)
    out_path = export_excel(rows, cfg.game, cfg.output_dir)
    print(f"Saved: {out_path} | rows: {len(rows)}")

if __name__ == "__main__":
    main()