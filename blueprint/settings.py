# Scrapy settings for blueprint project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os
from dotenv import load_dotenv
load_dotenv()


# =============================================================================
# CORE PROJECT SETTINGS
# =============================================================================
BOT_NAME = "blueprint"

SPIDER_MODULES = ["blueprint.spiders"]
NEWSPIDER_MODULE = "blueprint.spiders"

ADDONS = {}

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"


# =============================================================================
# REQUEST IDENTITY / HEADERS
# =============================================================================
# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "blueprint (+http://www.yourdomain.com)"

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}


# =============================================================================
# CONCURRENCY & THROTTLING
# =============================================================================
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

# Concurrency tuning
CONCURRENT_REQUESTS = 16


# =============================================================================
# COOKIES / ROBOTS
# =============================================================================
# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Respect robots.txt (optional)
ROBOTSTXT_OBEY = False


# =============================================================================
# TELNET / EXTENSIONS
# =============================================================================
# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}


# =============================================================================
# MIDDLEWARES
# =============================================================================
# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
#    "blueprint.middlewares.BlueprintSpiderMiddleware": 543,
}

DUPEFILTER_DEBUG = False


# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 543,
#    "blueprint.middlewares.BlueprintDownloaderMiddleware": 543,
    "blueprint.middlewares.PlaywrightStealthMiddleware": 543,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}
RETRY_ENABLED = False
REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 5


# =============================================================================
# PIPELINES
# =============================================================================
# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
#    "blueprint.pipelines.BlueprintPipeline": 300,
    "blueprint.pipelines.ManualReviewPipeline": 100,
    "blueprint.pipelines.PostgresPipeline": 300,
}


FEEDS = {
    # "items.jsonl": {
    #     "format": "jsonlines",
    #     "encoding": "utf8",
    #     "overwrite": True,
    # },
    'result.csv': {
        'format': 'csv',
    }
}

PGHOST = os.getenv("PGHOST")
PGDATABASE = os.getenv("PGDATABASE")
PGUSER = os.getenv("PGUSER")
PGPASSWORD = os.getenv("PGPASSWORD")
PGSSLMODE = os.getenv("PGSSLMODE", "require")
PGCHANNELBINDING = os.getenv("PGCHANNELBINDING", "require")


# =============================================================================
# AUTOTHROTTLE
# =============================================================================
# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True

# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5

# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60

# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False


# =============================================================================
# HTTP CACHE
# =============================================================================
# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"


# =============================================================================
# TWISTED / ASYNCIO
# =============================================================================
# Enable asyncio reactor (required)
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"


# =============================================================================
# PLAYWRIGHT INTEGRATION
# =============================================================================
# Playwright handler
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Optional: keep normal handler for non-JS requests
# "http": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler"

# Browser config
PLAYWRIGHT_BROWSER_TYPE = "chromium"

# --- stealth / anti-bot ---
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "args": [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
    ],
}

PLAYWRIGHT_CONTEXTS = {
    "default": {
        "user_agent": None,  # we’ll override dynamically
        "java_script_enabled": True,
        "ignore_https_errors": True,
        "viewport": {"width": 1280, "height": 800},
        # Persistent session (cookies!)
        "user_data_dir": "/tmp/playwright_session",

    }
}

PLAYWRIGHT_MAX_CONTEXTS = 4
PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 4
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30_000

# Abort unnecessary resources
PLAYWRIGHT_ABORT_REQUEST = lambda req: req.resource_type in ["image", "font", "media"]

# --- retry ---
RETRY_ENABLED = False  # we implement our own smarter retry
DOWNLOAD_TIMEOUT = 30


