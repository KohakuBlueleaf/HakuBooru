from numpy import base_repr
from peewee import ModelSelect

from .db import *


def get_post_by_tags(tag: Tag | list[Tag]) -> ModelSelect:
    if isinstance(tag, Tag):
        id_str = f"${base_repr(tag.id, 36)}#"
        return (
            Post.select()
            .join(PostFTS, on=(Post.id == PostFTS.rowid))
            .where(PostFTS.tag_list.contains(id_str))
        )
    else:
        id_str = " OR ".join(f'"${base_repr(t.id, 36)}#"' for t in tag)
        return (
            Post.select()
            .join(PostFTS, on=(Post.id == PostFTS.rowid))
            .where(PostFTS.tag_list.match(id_str))
        )


def get_tag_by_name(name: str):
    return Tag.get(Tag.name == name)


def get_tags_by_popularity(n: int):
    return Tag.select().where(Tag.popularity >= n)
