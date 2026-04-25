import scrapy
from scrapy_playwright.page import PageMethod
from blueprint.base import BaseSpider
from blueprint.loaders import QuoteLoader, QuoteItem


class QuotesSpider(BaseSpider):
    name = "quotes"
    start_urls = ["https://quotes.toscrape.com/js/"]
    allowed_domains = ["quotes.toscrape.com"]

    async def start(self):
        yield scrapy.Request(
            url="https://quotes.toscrape.com/js/",
            meta={
                "playwright": True,
                "playwright_context": "default",

                # Wait until JS renders content
                "playwright_page_methods": [
                    #PageMethod("click", "li.next a"),
                    self.pw_human_scroll(),
                    self.pw_wait_selector(".quote"),
                ],
            },
        )

    async def parse(self, response, **kwargs):
        loader = QuoteLoader(
            item=QuoteItem(),
            response=response,
        )

        loader.add_css("text", ".quote::text")
        loader.add_css("author_name", ".author::text")
        loader.add_css("tags", ".tag::text")

        loader.add_value("scraped_from", response.url)

        item = loader.load_item()

        yield item


        next_page = response.css(".next a::attr(href)").get()
        if next_page:
            yield self.request(
                response.urljoin(next_page),
                callback=self.parse,
                playwright=True,
                page_methods=[
                    self.pw_wait_selector(".quote")
                ],
            )


        """
        #Infinite scroll (loop)
        page = response.meta["playwright_page"]
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
        html = await page.content()
        """

        """
        #Conditional logic
        if await page.locator(".captcha").count() > 0:
            # handle it
        """



