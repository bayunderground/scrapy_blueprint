import scrapy
from scrapy_playwright.page import PageMethod


class ExampleSpider(scrapy.Spider):
    name = "example"

    async def start(self):
        yield scrapy.Request(
            url="https://example.com",
            meta={
                "playwright": True,
                "playwright_context": "default",

                # Actions on page
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state",
                               "networkidle"),
                    # Example click (if exists)
                    # PageMethod("click", "button.load-more"),
                    # PageMethod("wait_for_selector", ".item"),
                ],
            },
        )
        """
        #If you want manual cookies:
        meta={
            "playwright": True,
            "playwright_context": "default",
            "playwright_context_kwargs": {
                "storage_state": "cookies.json"
            }
        }
        #Advanced interaction (clicking, typing)
        PageMethod("fill", "#search", "laptop"),
        PageMethod("click", "button[type=submit]"),
        PageMethod("wait_for_selector", ".results"),
        """



    def parse(self, response, **kwargs):
        # Extract something
        title = response.css("title::text").get()

        yield {
            "title": title,
            "url": response.url,
        }

        # Example: follow links (normal Scrapy requests)
        return  #STUB
        for href in response.css("a::attr(href)").getall():
            yield scrapy.Request(
                response.urljoin(href),
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_context": "default",
                },
            )