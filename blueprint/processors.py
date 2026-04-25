import logging
from typing import Optional, List

from w3lib.html import remove_tags
from dateutil.parser import parse as date_parse


logger = logging.getLogger(__name__)


def clean_text(value: str) -> str:
    if not value:
        return ""

    value = remove_tags(value)
    value = value.strip()
    value = value.strip('“” ')

    if len(value) > 1 and value[0] == value[-1]:
        value = value.strip('"\'')
    return value


def clean_list(values: List[str]) -> List[str]:
    return [v.strip() for v in values if v and v.strip()]


def parse_date_safe(value: str) -> Optional[str]:
    try:
        dt = date_parse(value)
        return dt.strftime("%Y-%m-%d")
    except Exception as e:
        logger.debug(f"Date parse failed: {value} ({e})")
        return None


def identity(value):
    return value