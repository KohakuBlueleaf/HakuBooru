import dateutil.parser

from hakubooru.dataset.db import (
    Post,
)
from hakubooru.metainfo import (
    rating_map,
    fav_count_percentile_full,
)


def year_tag(
    post: Post, keep_tags: list[str], general_tags: list[str]
) -> tuple[list[str], list[str]]:
    year = 0
    try:
        date = dateutil.parser.parse(post.created_at)
        year = date.year
    except:
        pass
    if 2005 <= year <= 2010:
        year_tag = "old"
    elif year <= 2014:
        year_tag = "early"
    elif year <= 2017:
        year_tag = "mid"
    elif year <= 2020:
        year_tag = "recent"
    elif year <= 2024:
        year_tag = "newest"
    else:
        return keep_tags, general_tags
    general_tags.append(year_tag)
    return keep_tags, general_tags


def rating_tag(
    post: Post, keep_tags: list[str], general_tags: list[str]
) -> tuple[list[str], list[str]]:
    if (tag := rating_map.get(post.rating, None)) is not None:
        general_tags += tag
    return keep_tags, general_tags


def quality_tag(
    post: Post,
    keep_tags: list[str],
    general_tags: list[str],
    percentile_map: dict[str, dict[int, int]] = fav_count_percentile_full,
) -> tuple[list[str], list[str]]:
    if post.id > 7000000:
        # Don't add quality tag for posts which are new.
        return keep_tags, general_tags
    rating = post.rating
    score = post.fav_count
    percentile = percentile_map[rating]

    if score > percentile[95]:
        quality_tag = "masterpiece"
    elif score > percentile[85]:
        quality_tag = "best quality"
    elif score > percentile[75]:
        quality_tag = "great quality"
    elif score > percentile[50]:
        quality_tag = "good quality"
    elif score > percentile[25]:
        quality_tag = "normal quality"
    elif score > percentile[10]:
        quality_tag = "low quality"
    else:
        quality_tag = "worst quality"

    general_tags.append(quality_tag)

    return keep_tags, general_tags
