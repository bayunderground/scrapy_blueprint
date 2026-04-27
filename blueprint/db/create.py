from dataclasses import fields
from .schema import python_type_to_sql


def generate_create_table_sql(item_cls):
    table = getattr(item_cls, "__table__", None)
    if not table:
        raise ValueError(f"{item_cls} missing __table__")

    columns = []

    for f in fields(item_cls):
        name = f.name
        py_type = f.type

        sql_type = f.metadata.get("db_type") or python_type_to_sql(f.type)

        col = f"{name} {sql_type}"

        # special rules
        if name == "id":
            col = "id SERIAL PRIMARY KEY"

        if name == "scraped_from":
            col += " NOT NULL"

        columns.append(col)

    columns.append("created_at TIMESTAMP DEFAULT NOW()")

    sql = f"""
    CREATE TABLE IF NOT EXISTS {table} (
        {", ".join(columns)}
    );
    """

    return sql