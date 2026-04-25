from itemloaders import ItemLoader
from itemloaders.processors import MapCompose, TakeFirst, Join

from .processors import clean_text, clean_list, parse_date_safe


class SafeItemLoader(ItemLoader):
    """
    Safe loader:
    - catches processor errors
    - stores them in context['errors']
    """

    default_output_processor = TakeFirst()

    def add_value(self, field_name, value, *processors, **kwargs):
        try:
            super().add_value(field_name, value, *processors, **kwargs)
        except Exception as e:
            self.context.setdefault("errors", []).append({
                "field": field_name,
                "value": value,
                "error": str(e),
            })

    def load_item(self):
        item = super().load_item()

        item.extra.update(self.context.get("errors", {}))

        return item


class QuoteLoader(SafeItemLoader):

    # --- TEXT ---
    text_in = MapCompose(clean_text)

    # --- AUTHOR ---
    author_name_in = MapCompose(clean_text)
    author_name_out = Join(" ")

    # --- CATEGORY ---
    exhibitor_category_in = MapCompose(clean_text)
    exhibitor_category_out = clean_list

    # --- DATE ---
    author_born_date_in = MapCompose(clean_text, parse_date_safe)

    # --- LOCATION ---
    author_born_location_in = MapCompose(clean_text)

    # --- DESCRIPTION ---
    author_born_description_in = MapCompose(clean_text)

    # --- TAGS ---
    tags_in = MapCompose(clean_text)
    tags_out = clean_list

    # --- META ---
    scraped_from_in = MapCompose(clean_text)