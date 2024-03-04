from peewee import ModelSelect

from .db import *


def get_post_by_tags(tag: Tag | list[Tag]) -> list[Post]:
    if isinstance(tag, Tag):
        posts = tag.posts
    else:
        posts = set()
        for t in tag:
            for post in t.posts:
                posts.add(post)
        posts = list(posts)
    return posts


def select_post_by_tags(tag: Tag | list[Tag]) -> ModelSelect:
    if isinstance(tag, Tag):
        ids = [tag.id]
    else:
        ids = [tag.id for tag in tag]
    return Post.select().join(PostTagRelation).join(Tag).where(Tag.id << ids)


def get_tag_by_name(name: str):
    return Tag.get(Tag.name == name)


def get_tags_by_popularity(n: int):
    return Tag.select().where(Tag.popularity >= n)
