from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass(kw_only=True)
class BaseItem:
    extra: Dict = field(default_factory=dict)

    # default fallback
    __table__ = None


@dataclass
class QuoteItem(BaseItem):
    __table__ = "quote_items"
    __indexes__ = [
        # ("scraped_from", "UNIQUE"),
    ]
    __unique__ = ["text", "author_name"]

    text: Optional[str] = None
    author_name: Optional[str] = None

    exhibitor_category: List[str] = field(default_factory=list)

    author_born_date: Optional[str] = None
    author_born_location: Optional[str] = None
    author_born_description: Optional[str] = None

    tags: List[str] = field(default_factory=list)
    #Add per-field overrides
    # tags: List[str] = field(
    #     default_factory=list,
    #     metadata={"db_type": "TEXT[]"}
    # )

    scraped_from: str = None
    # scraped_from: Optional[str] = None


@dataclass
class RedditCommentItem:
    author: Optional[str] = None
    score: Optional[str] = None
    text: Optional[str] = None
    replies: List['RedditCommentItem'] = field(default_factory=list)


@dataclass
class RedditPostItem(BaseItem):
    __table__ = "reddit_posts"
    __unique__ = ["url"]

    title: Optional[str] = None
    url: Optional[str] = None
    post_text: Optional[str] = None
    author: Optional[str] = None
    score: Optional[str] = None
    num_comments: Optional[int] = None
    subreddit: Optional[str] = None
    comments: List[RedditCommentItem] = field(default_factory=list)
