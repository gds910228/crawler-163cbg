from dataclasses import dataclass

@dataclass
class ScrapeConfig:
    game: str = "mhxy-mobile"  # 梦幻西游手游（占位，可覆盖）
    pages: int = 10
    delay_seconds: float = 1.0
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    output_dir: str = "output"