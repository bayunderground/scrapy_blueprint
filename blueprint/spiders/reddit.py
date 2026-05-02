import logging
from urllib.parse import urljoin

from blueprint.base import BaseSpider
from blueprint.loaders import RedditPostLoader
from blueprint.items import RedditPostItem, RedditCommentItem
from blueprint.processors import clean_text


class RedditSpider(BaseSpider):
    name = "reddit"
    start_urls = ["https://old.reddit.com/r/Python/top/"]

    # Configuration
    MAX_PAGES = 10
    ROOT_COMMENTS = 5
    REPLIES_PER_ROOT = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages_scraped = 0

    async def start(self):
        """Start requests - override BaseSpider's non-async start method."""
        for url in self.start_urls:
            yield self.request(
                url,
                callback=self.parse,
                cookies=self.base_cookies,
                meta={"retry_times": 0, "initial": True},
                playwright=False,  # Use plain HTTP with authenticated cookies
            )

    async def parse(self, response, **kwargs):
        """Parse listing page and extract post links."""
        self.pages_scraped += 1
        self.logger.info(f"Scraping page {self.pages_scraped}/{self.MAX_PAGES}")

        # Extract all post links
        for post_sel in response.css('.thing.link'):
            title_elem = post_sel.css('.title > a')
            post_url = title_elem.css('::attr(href)').get()

            if post_url:
                # Make absolute URL
                if post_url.startswith('/r/'):
                    post_url = urljoin(response.url, post_url)

                # Only scrape reddit post detail pages
                if 'old.reddit.com' in post_url and '/comments/' in post_url:
                    yield self.request(
                        url=post_url,
                        callback=self.parse_post,
                        playwright=False,
                    )

        # Follow pagination if we haven't reached max pages
        if self.pages_scraped < self.MAX_PAGES:
            next_link = response.css('a.nextprev[rel="nofollow next"]::attr(href)').get()
            if next_link:
                self.logger.info(f"Following next page: {next_link}")
                yield self.request(
                    url=next_link,
                    callback=self.parse,
                    playwright=False,
                )
            else:
                self.logger.info("No next link found, pagination ended")
        else:
            self.logger.info(f"Reached max pages ({self.MAX_PAGES}), stopping pagination")

    async def parse_post(self, response, **kwargs):
        """Parse post detail page and extract post data with comments."""
        # Check for retry conditions
        if response.status in self.RETRY_HTTP_CODES:
            self.logger.warning(f"Got HTTP {response.status} for post, retrying...")
            yield self._retry(response.request, f"HTTP {response.status}")
            return
        elif not response.text or len(response.text) < 200:
            self.logger.warning(f"Got empty response for post ({len(response.text)} bytes), retrying...")
            yield self._retry(response.request, "empty response")
            return

        self.logger.info(f"Parsing post: {response.url}")

        loader = RedditPostLoader(item=RedditPostItem(), response=response)

        # Extract post metadata
        loader.add_css('title', '.thing.link .title > a::text')
        loader.add_value('url', response.url)

        # Extract post text (self-post content)
        post_text_elements = response.css('.thing.link .usertext-body .md p::text').getall()
        if post_text_elements:
            loader.add_value('post_text', post_text_elements)

        # Extract author and score
        loader.add_css('author', '.thing.link .author::text')
        loader.add_css('score', '.thing.link .score.unvoted::text')

        # Extract number of comments
        comments_text = response.css('.thing.link .comments::text').get()
        if comments_text:
            try:
                # Extract number from text like "42 comments"
                num = ''.join(filter(str.isdigit, comments_text))
                if num:
                    loader.add_value('num_comments', int(num))
            except:
                pass

        # Extract subreddit
        loader.add_css('subreddit', '.thing.link .subreddit::text')

        # Extract root comments (direct children only)
        comments = []
        root_comment_selectors = response.css('.sitetable.nestedlisting > .thing.comment')[:self.ROOT_COMMENTS]

        for comment_sel in root_comment_selectors:
            comment_data = self._extract_comment(comment_sel, max_replies=self.REPLIES_PER_ROOT)
            if comment_data:
                comments.append(comment_data)

        loader.add_value('comments', comments)

        item = loader.load_item()
        self.logger.info(f"Extracted post with {len(comments)} root comments")
        yield item

    def _extract_comment(self, comment_sel, max_replies=None):
        """Extract a single comment with its replies."""
        # Extract comment metadata
        author = comment_sel.css('.author::text').get()
        score = comment_sel.css('.score.unvoted::text').get()

        # Extract comment text (all paragraphs)
        text_elements = comment_sel.css('.usertext-body .md > p::text, .usertext-body .md > p > *::text').getall()
        text = ' '.join([clean_text(t) for t in text_elements if t and clean_text(t)])

        if not text:
            # Try alternative selector for comment text
            text_elements = comment_sel.css('.usertext-body .md::text').getall()
            text = ' '.join([clean_text(t) for t in text_elements if t and clean_text(t)])

        # Extract replies
        replies = []
        if max_replies and max_replies > 0:
            # Get the child comments container
            child_container = comment_sel.css('.child')
            if child_container:
                # Get direct child comments only (not nested deeper)
                reply_selectors = child_container.css('> .sitetable > .thing.comment')[:max_replies]

                for reply_sel in reply_selectors:
                    reply_data = self._extract_comment(reply_sel, max_replies=0)
                    if reply_data:
                        replies.append(reply_data)

        return RedditCommentItem(
            author=author,
            score=score,
            text=text if text else None,
            replies=replies
        )
