import os
import logging
import random
from pathlib import Path

import scrapy
from scrapy import Request
from scrapy.utils.curl import curl_to_request_kwargs

from scrapy_playwright.page import PageMethod

import coloredlogs
from fake_useragent import UserAgent

GOOGLEBOT_UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

class BaseSpider(scrapy.Spider):
    headers = {}
    base_cookies = {}

    MAX_RETRIES = 3
    RETRY_HTTP_CODES = {403, 429, 500, 502, 503, 504}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # logging
        for h in logging.getLogger().handlers[:]:
            if isinstance(h, logging.StreamHandler):
                logging.getLogger().removeHandler(h)
        coloredlogs.install(level=logging.INFO)

        self.ua = UserAgent()
        # self.ua = GOOGLEBOT_UA

        # load curl fixtures
        project_root = Path(__file__).resolve().parent
        fixture_path = project_root / f"{self.name}_fixtures.curl"

        if fixture_path.exists():
            with open(fixture_path) as f:
                curl = f.read().strip()

            rq = curl_to_request_kwargs(curl)
            self._set_from_fixtures(
                dict(rq.get("headers", {})),
                dict(rq.get("cookies", {})),
            )

    def _set_from_fixtures(self, headers: dict, cookies: dict):
        rejected = {
            "Connection",
            "Upgrade-Insecure-Requests",
            "Referer",
            "Accept-Encoding",
            "DNT",
        }

        for h in rejected:
            headers.pop(h, None)

        self.headers = headers
        self.base_cookies = cookies

    def start(self):
        for url in self.start_urls:
            yield self.request(
                url,
                callback=self.parse,
                cookies=self.base_cookies,
                meta={"retry_times": 0, "initial": True},
                playwright=True,
            )

    # ---------------------------
    # CORE REQUEST BUILDER
    # ---------------------------
    def request(
        self,
        url,
        callback,
        *,
        playwright=False,
        referer=None,
        headers=None,
        meta=None,
        page_methods=None,
        **kwargs,
    ):
        meta = meta or {}
        headers = headers or {}

        # random UA
        ua = self.ua.random

        merged_headers = {
            **self.headers,
            "User-Agent": ua,
            "Accept-Language": "en-US,en;q=0.9",
            **headers,
        }

        if referer:
            merged_headers["Referer"] = referer

        if playwright:
            meta["playwright"] = True
            meta["playwright_context"] = "default"

            if page_methods:
                meta["playwright_page_methods"] = page_methods


        # jitter delay (anti-bot)
        delay = random.uniform(0.5, 2.5)

        return Request(
            url=url,
            callback=callback,
            headers=merged_headers,
            meta=meta,
            errback=self.errback,
            dont_filter=True,
            **kwargs,
        )

    # ---------------------------
    # RETRY LOGIC
    # ---------------------------
    def errback(self, failure):
        request = failure.request
        return self._retry(request, reason=str(failure.value))

    def _retry(self, request, reason):
        retries = request.meta.get("retry_times", 0)

        if retries >= self.MAX_RETRIES:
            self.logger.warning(f"Gave up retrying {request.url} ({reason})")
            return

        self.logger.info(f"Retrying {request.url} ({retries+1}) due to {reason}")

        new_meta = dict(request.meta)
        new_meta["retry_times"] = retries + 1

        return request.replace(
            meta=new_meta,
            dont_filter=True,
        )

    # --- helpers for playwright actions ---
    def pw_click(self, selector, wait=1.0):
        return (
            PageMethod("click", selector, timeout=30000),
            PageMethod(
        "wait_for_timeout", int(wait * 1000)
            )
        )

    def pw_wait_selector(self, selector):
        return PageMethod("wait_for_selector", selector)

    def pw_js(self, script):
        return PageMethod("evaluate", script)

    def pw_human_scroll(self):
        return PageMethod(
            "evaluate",
            """async () => {
                await new Promise(resolve => {
                    let total = 0;
                    let distance = 100;
                    let timer = setInterval(() => {
                        window.scrollBy(0, distance);
                        total += distance;
                        if (total >= document.body.scrollHeight){
                            clearInterval(timer);
                            resolve();
                        }
                    }, 200);
                });
            }"""
        )



    async def parse(self, response, **kwargs):
        # retry on bad status
        if response.status in self.RETRY_HTTP_CODES:
            return self._retry(response.request, f"HTTP {response.status}")

        # retry on empty content (anti-bot soft block)
        if not response.text or len(response.text) < 200:
            return self._retry(response.request, "empty response")

        raise NotImplementedError()



    async def close_page(self, response):
        page = response.meta.get("playwright_page")
        if page:
            await page.close()