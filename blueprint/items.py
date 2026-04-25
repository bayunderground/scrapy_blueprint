from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class QuoteItem:
    text: Optional[str] = None
    author_name: Optional[str] = None
    exhibitor_category: List[str] = field(default_factory=list)

    author_born_date: Optional[str] = None
    author_born_location: Optional[str] = None
    author_born_description: Optional[str] = None

    tags: List[str] = field(default_factory=list)
    scraped_from: Optional[str] = None

    # structured error/debug info
    extra: Dict = field(default_factory=dict)