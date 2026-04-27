import logging
import pprint

import psycopg
from psycopg.types.json import Json

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import os
from dotenv import load_dotenv
load_dotenv()

from blueprint.db.create import generate_create_table_sql



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



class PostgresPipeline:

    def __init__(self, dsn, crawler):
        self.dsn = dsn
        self.crawler = crawler
        self.conn = None
        self.cur = None
        self.created_tables = set()


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

    def ensure_table(self, item):
        item_cls = item.__class__
        table = getattr(item_cls, "__table__", None)

        if not table:
            raise ValueError(f"{item_cls.__name__} missing __table__")

        if table in self.created_tables:
            return

        sql = generate_create_table_sql(item_cls)
        self.cur.execute(sql)

        self.created_tables.add(table)


    def open_spider(self):
        self.conn = psycopg.connect(self.dsn)
        self.conn.autocommit = True
        self.cur = self.conn.cursor()


    def close_spider(self):
        self.cur.close()
        self.conn.close()


    def process_item(self, item):
        self.ensure_table(item)

        adapter = ItemAdapter(item)
        data = adapter.asdict()

        table = item.__class__.__table__

        # --- build query dynamically ---
        columns = []
        values = []

        for key, value in data.items():
            columns.append(key)

            if isinstance(value, dict):
                values.append(Json(value))
            else:
                values.append(value)

        col_names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(values))

        update_clause = ", ".join([
            f"{col} = EXCLUDED.{col}"
            for col in columns
            if col != "scraped_from"
        ])

        unique = getattr(item.__class__, "__unique__", ["scraped_from"])
        conflict_cols = ", ".join(unique)

        sql = f"""
        INSERT INTO {table} ({col_names})
        VALUES ({placeholders})
        ON CONFLICT ({conflict_cols}) DO UPDATE SET
        {update_clause}
        """

        self.cur.execute(sql, values)

        return item

        self.cur.execute(
            "INSERT INTO items (data) VALUES (%s)",
            (Json(data),)
        )

