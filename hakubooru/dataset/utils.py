from numpy import base_repr
from .db import *


def get_post_by_tag(tag: Tag):
    id_str = f"${base_repr(tag.id, 36)}#"
    return (
        Post.select()
        .join(PostFTS, on=(Post.id == PostFTS.rowid))
        .where(PostFTS.tag_list.contains(id_str))
    )


def get_tag_by_name(name: str):
    return Tag.get(Tag.name == name)


def get_tags_by_popularity(n: int):
    return Tag.select().where(Tag.popularity >= n)
