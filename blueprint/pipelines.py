import logging
import pprint

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class BlueprintPipeline:
    def process_item(self, item, spider):
        return item


class ManualReviewPipeline:

    items: list

    def open_spider(self, spider):
        self.items = []

    def close_spider(self, spider):
        if not env('DEV', 0):
            return True

        some_not_parsed = any(
            [i['extra'] for i in self.items if 'extra' in i]
        )

        if not some_not_parsed:
            return True

        not_parsed = [i for i in self.items if 'extra' in i and i['extra']]
        extras = [i['extra'] for i in not_parsed]
        pprint.pp(extras)

        logging.getLogger().setLevel(logging.INFO)  #in scrapy shell
        import ipdb;ipdb.set_trace()

    def process_item(self, item, spider):
        if env('DEV', 0):
            self.items.append(item)
        else:
            if 'extra' in item and not item['extra']:
                del item['extra']
        return item





import psycopg
from itemadapter import ItemAdapter


class PostgresPipeline:

    def __init__(self, dsn):
        self.dsn = dsn
        self.conn = None

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
        return cls(dsn)

    def open_spider(self, spider):
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



    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()

    def process_item(self, item, spider):
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



class NormalizeItemPipeline:
    """
    Final cleanup + attach loader errors
    """

    def process_item(self, item, spider):
        # attach loader errors if present
        errors = getattr(item, "_loader_context", {}).get("errors")
        if errors:
            item.extra["errors"] = errors

        # normalize empty lists
        if not item.tags:
            item.tags = []

        if not item.exhibitor_category:
            item.exhibitor_category = []

        return item