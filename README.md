# compliant-scraper

[![tests](https://github.com/Naiiodoll/Claude/actions/workflows/tests.yml/badge.svg)](https://github.com/Naiiodoll/Claude/actions/workflows/tests.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A polite, configurable web scraper in Python that treats websites the way you'd
want your own site to be treated. You describe **what** to scrape in a small
TOML file; the framework handles the *responsible* parts for you.

## Why "compliant"?

Web scraping is legal when done respectfully. This framework bakes the good
habits in by default:

| Behaviour | How it's handled |
| --- | --- |
| `robots.txt` | Checked before **every** request (`urllib.robotparser`) |
| `Crawl-delay` | Read and honoured, alongside a configurable minimum delay |
| Rate limiting | Per-host throttling (never hammers a site) |
| Honest `User-Agent` | Required in config, with contact info |
| Transient errors | Retried with exponential backoff + jitter |
| `Retry-After` | Respected on `429` / `503` responses |
| Off-site drift | Optional `allowed_domains` allow-list |

> ⚠️ **Legal note.** A scraper's legality depends on **what you scrape and how
> you use it**, not just on polite request behaviour. Before scraping any site,
> you should:
>
> 1. Read the site's **Terms of Service** and check whether automated access is
>    permitted.
> 2. Check `robots.txt` (this tool does this automatically) and obey it.
> 3. Don't scrape **personal data** (which may trigger GDPR/CCPA and similar
>    laws) or **copyrighted content** you don't have rights to use.
> 4. Keep request volume reasonable; don't overload the server.
> 5. Only use scraped data in ways you're entitled to (licensing, fair use, etc.).
>
> This project is a general-purpose tool. You are responsible for using it
> lawfully against a given target.

## Features

- Declarative TOML configuration — no code changes needed per site.
- CSS-selector based extraction (text and attributes, single or multiple).
- Automatic pagination with a hard page cap.
- Export to **JSON** or **CSV**.
- `--dry-run` to validate config and check robots.txt without scraping.
- Zero heavy dependencies: only `requests` + `beautifulsoup4`.

## Installation

```bash
# 1. clone the repo
git clone https://github.com/<your-name>/compliant-scraper.git
cd compliant-scraper

# 2. (recommended) create a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Validate config + check robots.txt, without scraping anything:
python -m scraper config.example.toml --dry-run

# Run the scraper and write JSON (default):
python -m scraper config.example.toml

# Choose output path and format:
python -m scraper config.example.toml -o output/quotes.csv -f csv
```

### Example

The bundled `config.example.toml` scrapes
[quotes.toscrape.com](https://quotes.toscrape.com/) — a public *scraping
sandbox* provided specifically for learning and practising scraping:

```bash
python -m scraper config.example.toml -o output/quotes.json
```

Expected output:

```json
[
  {
    "text": "“The world as we have created it is a process of our thinking...”",
    "author": "Albert Einstein",
    "tags": ["change", "deep-thoughts", "thinking", "world"]
  },
  ...
]
```

## Configuration

Copy `config.example.toml` and edit it for your target. Key options:

| Key | Type | Meaning |
| --- | --- | --- |
| `name` | string | Human-readable job name |
| `user_agent` | string | **Required.** Identify your bot with contact info |
| `start_urls` | list | One or more URLs to begin at |
| `allowed_domains` | list (optional) | Only crawl these hosts |
| `delay` | float | Min seconds between requests per host |
| `timeout` | float | Per-request timeout |
| `max_retries` | int | Retry count for transient failures |
| `backoff_base` | float | Exponential backoff base (seconds) |
| `item.selector` | string | CSS selector for one item |
| `item.fields` | list | Fields to extract per item |
| `pagination.selector` | string | CSS selector for the "next" link |
| `pagination.max_pages` | int | Hard cap on pages per start URL |

Each field supports:

- `attribute = "text"` (default) — text content, or an attribute like `"href"`.
- `multiple = true` — collect all matches as a list.

## Project layout

```
compliant-scraper/
├── scraper/
│   ├── __init__.py     # public API
│   ├── config.py       # TOML config loading & validation
│   ├── robots.py       # robots.txt + Crawl-delay handling
│   ├── fetcher.py      # throttled, retrying HTTP client
│   ├── parser.py       # BeautifulSoup field extraction
│   ├── pipeline.py     # fetch -> parse -> collect
│   ├── exporter.py     # JSON / CSV output
│   ├── cli.py          # command-line interface
│   └── __main__.py     # `python -m scraper` entry point
├── tests/              # pytest tests
├── config.example.toml # commented example configuration
├── requirements.txt
└── LICENSE
```

## Development

```bash
pip install -r requirements.txt pytest
pytest
```

## License

[MIT](LICENSE)
