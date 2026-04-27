import logging
import pprint

from psycopg.types.json import Json

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import os
from dotenv import load_dotenv
load_dotenv()


class BlueprintPipeline:
    def process_item(self, item):
        return item


class ManualReviewPipeline:

    def __init__(self, crawler):
        self.crawler = crawler
        self.items = []

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def open_spider(self):
        self.items = []

    def process_item(self, item):
        return item

    def close_spider(self):
        if not os.getenv('DEV'):
            return

        # collect items WITH errors
        bad_items = [
            i for i in self.items
            if getattr(i, "extra", {}).get("errors")
        ]

        if not bad_items:
            return

        errors = [i.extra["errors"] for i in bad_items]

        pprint.pp(errors)

        logging.getLogger().setLevel(logging.INFO)

        import ipdb; ipdb.set_trace()


import psycopg
from itemadapter import ItemAdapter


class PostgresPipeline:

    def __init__(self, dsn, crawler):
        self.dsn = dsn
        self.crawler = crawler
        self.conn = None
        self.cur = None

    @classmethod
    def from_crawler(cls, crawler):
        dsn = (
            f"host={crawler.settings.get('PGHOST')} "
            f"dbname={crawler.settings.get('PGDATABASE')} "
            f"user={crawler.settings.get('PGUSER')} "
            f"password={crawler.settings.get('PGPASSWORD')} "
            f"sslmode={crawler.settings.get('PGSSLMODE', 'require')} "
            f"channel_binding={crawler.settings.get('PGCHANNELBINDING', 'require')}"
        )
        return cls(dsn, crawler)

    def open_spider(self):
        self.conn = psycopg.connect(self.dsn)
        self.conn.autocommit = True
        self.cur = self.conn.cursor()

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS quote_items (
            id SERIAL PRIMARY KEY,

            scraped_from TEXT UNIQUE NOT NULL,

            text TEXT,
            author_name TEXT,

            exhibitor_category TEXT[],
            author_born_date DATE,
            author_born_location TEXT,
            author_born_description TEXT,

            tags TEXT[],

            extra JSONB,

            created_at TIMESTAMP DEFAULT NOW()
        );
        """)

        return
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            data JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)

    def close_spider(self):
        self.cur.close()
        self.conn.close()


    def process_item(self, item):
        data = ItemAdapter(item).asdict()

        url = data.get("url")
        title = data.get("title")
        price = data.get("price")
        currency = data.get("currency")

        # everything else → extra
        extra = {
            k: v for k, v in data.items()
            if k not in {"url", "title", "price", "currency"}
        }

        if not item.scraped_from:
            raise ValueError("scraped_from is required")

        self.cur.execute(
            """
            INSERT INTO quote_items (
                scraped_from,
                text,
                author_name,
                exhibitor_category,
                author_born_date,
                author_born_location,
                author_born_description,
                tags,
                extra
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (scraped_from) DO UPDATE SET
                text = EXCLUDED.text,
                author_name = EXCLUDED.author_name,
                exhibitor_category = EXCLUDED.exhibitor_category,
                author_born_date = EXCLUDED.author_born_date,
                author_born_location = EXCLUDED.author_born_location,
                author_born_description = EXCLUDED.author_born_description,
                tags = EXCLUDED.tags,
                extra = EXCLUDED.extra
            """,
            (
                item.scraped_from,
                item.text,
                item.author_name,
                item.exhibitor_category,
                item.author_born_date,
                item.author_born_location,
                item.author_born_description,
                item.tags,
                Json(item.extra) if item.extra else None,
            )
        )

        return item

        self.cur.execute(
            "INSERT INTO items (data) VALUES (%s)",
            (Json(data),)
        )

