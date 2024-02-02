from .db import *


def get_post_by_tags(tag: Tag | list[Tag]) -> list[Post]:
    if isinstance(tag, Tag):
        return list(tag.posts)
    else:
        posts = {post.id: post for t in tag for post in t.posts}
        return list(posts.values())


def get_tag_by_name(name: str):
    return Tag.get(Tag.name == name)


def get_tags_by_popularity(n: int):
    return Tag.select().where(Tag.popularity >= n)
