import logging
import pprint

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import os
from dotenv import load_dotenv
load_dotenv()


class BlueprintPipeline:
    def process_item(self, item, spider):
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
        if os.getenv('DEV'):
            self.items.append(item)
        else:
            # strip empty extra in prod
            if getattr(item, "extra", None) == {}:
                del item.extra
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

        return
        # ✅ create table if not exists
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            url TEXT UNIQUE,
            title TEXT,
            price NUMERIC,
            currency TEXT,
            extra JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)



    def close_spider(self):
        self.cur.close()
        self.conn.close()

    def process_item(self, item):
        data = ItemAdapter(item).asdict()

        # ⚠️ adjust to your schema
        self.cur.execute(
            """
            INSERT INTO items (data)
            VALUES (%s)
            """,
            (data,)
        )

        return item

        url = data.get("url")
        title = data.get("title")
        price = data.get("price")
        currency = data.get("currency")

        # everything else → extra
        extra = {
            k: v for k, v in data.items()
            if k not in {"url", "title", "price", "currency"}
        }

        self.cur.execute(
            """
            INSERT INTO items (url, title, price, currency, extra)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET
                title = EXCLUDED.title,
                price = EXCLUDED.price,
                currency = EXCLUDED.currency,
                extra = EXCLUDED.extra;
            """,
            (url, title, price, currency, extra)
        )

        return item


