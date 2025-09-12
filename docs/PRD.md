# PRD - CBG Mobile Pilot Scraper

## 1. Introduction
### 1.1 Background & Goals
Client needs to scrape game listings from NetEase CangBaoGe (https://cbg.163.com), prioritizing mobile (手游). Pilot: scrape one mobile game to validate fields, structure, anti-bot feasibility, and delivery format (Excel).

### 1.2 Target User
- Client operator/analyst who needs market listing data quickly without manual collection.

### 1.3 Core Value Proposition
- Fast delivery of structured listing data in Excel for a chosen mobile game.

## 2. Functional Requirements
### 2.1 Feature List
- Select target mobile game (default: 梦幻西游手游).
- Fetch latest listings (first 10 pages).
- Extract fields: title, price, server, seller info (as available), item link, publish time, game name, category.
- Export to Excel (xlsx).
- Configurable page count and game.

### 2.2 User Stories
- As an operator, I want the latest N pages for a chosen mobile game so that I can analyze prices quickly.
- As an operator, I want Excel output so I can filter/sort in familiar tools.

### 2.3 Detailed Specs
- Input: game identifier (slug/ID), page_count (default 10).
- Output: Excel file `output/{game}_{timestamp}.xlsx`.
- Error handling: retry on transient errors; log skipped items.
- Rate limiting: polite delay to reduce anti-bot triggers.
- Resilience: continue on partial failures, summarize at end.

## 3. Non-Functional Requirements
- Performance: finish pilot (10 pages) within minutes on typical network.
- Usability: simple CLI invocation.
- Security: no credentials needed; no secrets logged.
- Reliability: deterministic export, consistent columns.

## 4. Scope & Constraints
### 4.1 In Scope (Pilot)
- One mobile game.
- Latest 10 pages.
- Excel export with base fields.

### 4.2 Out of Scope (Pilot)
- Full site crawling, deduping, complex filters, image download, captcha solving.

### 4.3 Assumptions & Dependencies
- Site accessible without login; no hard captcha on list pages.
- HTML structure stable during pilot window.

## 5. Initial UI/UX (CLI)
- `python -m cbg_scraper --game "mhxy-mobile" --pages 10 --out ./output`

## 6. Future Considerations
- Add more games, server-side scheduling, proxy pool, captcha bypass, data cleaning, incremental updates, DB storage.