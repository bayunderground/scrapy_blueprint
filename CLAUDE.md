# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Scrapy-based web scraping framework (blueprint v2) with advanced anti-detection capabilities. It uses Playwright for JavaScript-rendered pages and includes PostgreSQL integration for data storage.

**Tech Stack**: Python 3.12, Scrapy 2.15.0, scrapy-playwright 0.0.46, playwright-stealth, PostgreSQL (psycopg 3.3.3)

## Running Spiders

### Basic Commands
```bash
# List all available spiders
scrapy list

# Run a specific spider
scrapy crawl <spider_name>

# Run in development mode (enables ipdb debugging on errors)
DEV=1 scrapy crawl <spider_name>

# Examples
scrapy crawl quotes
scrapy crawl example
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Playwright browser installation (required for scrapy-playwright)
playwright install chromium
```

Environment variables are loaded from `.env` file (PostgreSQL credentials). **Never commit the .env file.**

## Architecture

### Core Components

**BaseSpider** (`blueprint/base.py`):
- Parent class that all spiders should inherit from
- Provides automatic retry logic (3 attempts for 403, 429, 5xx errors)
- Handles user-agent rotation via fake-useragent
- Request builder with `self.request()` method (not `scrapy.Request()`)
- Playwright helpers: `pw_click()`, `pw_wait_selector()`, `pw_js()`, `pw_human_scroll()`
- Supports curl fixtures: create `<spider_name>_fixtures.curl` in spiders/ directory to load headers/cookies

**Items** (`blueprint/items.py`):
- Use Python dataclasses for item definitions
- Always include an `extra: Dict` field for errors and metadata

**Loaders** (`blueprint/loaders.py`):
- Use `SafeItemLoader` base class for all loaders
- Automatically catches and logs field extraction errors to `item.extra["errors"]`
- Define field processors as `<field>_in` and `<field>_out` attributes

**Pipelines** (`blueprint/pipelines.py`):
- `ManualReviewPipeline` (priority 100): In DEV mode, drops into ipdb debugger if any items have errors
- `PostgresPipeline` (priority 300): Stores items to PostgreSQL as JSONB

**Middlewares** (`blueprint/middlewares.py`):
- `PlaywrightStealthMiddleware`: Applies playwright-stealth to all playwright pages for anti-bot

**Processors** (`blueprint/processors.py`):
- `clean_text()`: Strips HTML tags, whitespace, quotes
- `clean_list()`: Cleans list of strings
- `parse_date_safe()`: Parses dates to YYYY-MM-DD format, returns None on failure

### Spider Implementation Pattern

```python
from blueprint.base import BaseSpider
from blueprint.loaders import SafeItemLoader  # or create custom loader
from blueprint.items import YourItem

class YourSpider(BaseSpider):
    name = "yourspider"
    start_urls = ["https://example.com"]

    async def start(self):
        # Use self.request() instead of scrapy.Request()
        yield self.request(
            url=self.start_urls[0],
            callback=self.parse,
            playwright=True,  # Enable playwright
            page_methods=[
                self.pw_wait_selector(".content"),
                self.pw_human_scroll(),
            ]
        )

    async def parse(self, response, **kwargs):
        # Call super to get automatic retry on errors
        result = await super().parse(response, **kwargs)
        if result:
            return result

        # Your extraction logic
        for item_sel in response.css(".item"):
            loader = SafeItemLoader(item=YourItem(), selector=item_sel)
            loader.add_css("field", ".selector::text")
            yield loader.load_item()
```

### Request Building

Always use `self.request()` from BaseSpider, not `scrapy.Request()`. This provides:
- Automatic user-agent rotation
- Consistent header management
- Playwright integration
- Error callback wiring

```python
# For playwright requests
yield self.request(
    url=url,
    callback=self.parse,
    playwright=True,
    page_methods=[
        self.pw_wait_selector(".content"),
    ]
)

# For normal requests
yield self.request(
    url=url,
    callback=self.parse,
    referer=response.url,
)
```

## Settings Configuration

Key settings in `blueprint/settings.py`:

- **Concurrency**: `CONCURRENT_REQUESTS = 16`, `CONCURRENT_REQUESTS_PER_DOMAIN = 1`
- **Delays**: `DOWNLOAD_DELAY = 1` (plus random jitter in BaseSpider)
- **Playwright**: Browser type is chromium, runs headless with stealth args
- **Retries**: Custom retry logic in BaseSpider (not Scrapy's built-in)
- **Output**: CSV export to `result.csv` via FEEDS setting
- **Database**: PostgreSQL credentials loaded from environment variables

## Development Workflow

1. Create spider in `blueprint/spiders/`
2. Define items in `blueprint/items.py` (use dataclasses)
3. Create custom loader in `blueprint/loaders.py` if needed (inherit from SafeItemLoader)
4. Test with `DEV=1 scrapy crawl <spider>` - will drop into ipdb if extraction errors occur
5. Check `result.csv` for output

## Curl Fixtures

To use browser-captured requests:
1. Copy curl command from browser DevTools
2. Save as `blueprint/spiders/<spider_name>_fixtures.curl`
3. BaseSpider will auto-load headers and cookies on initialization
4. Rejected headers: Connection, Upgrade-Insecure-Requests, Referer, Accept-Encoding, DNT

## Debugging

- Use `DEV=1` environment variable to enable ManualReviewPipeline debugging
- Check `tmp.log` for detailed logs
- Items with extraction errors will trigger ipdb in DEV mode
- Use `import ipdb; ipdb.set_trace()` for manual breakpoints

## Important Notes

- All spiders inherit from `BaseSpider`, not `scrapy.Spider`
- Use `async def start(self)` and `async def parse(self, response, **kwargs)` in spiders
- Call `await super().parse(response, **kwargs)` to get automatic retry handling
- Playwright is configured with persistent session in `/tmp/playwright_session`
- ROBOTSTXT_OBEY is False - respect website terms of service manually
- Images, fonts, and media are blocked in playwright requests for performance
