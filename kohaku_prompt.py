"""
Dataset exporter for DanTagGen
"""

import logging
import gc
from concurrent.futures import *
from json import dumps

from tqdm import tqdm

from hakubooru.caption import *
from hakubooru.tag_generator import *
from hakubooru.dataset import load_db, Post
from hakubooru.logging import logger
from hakubooru.metainfo import fav_count_percentile_full


def calc_quality_tag(score, rating):
    percentile = fav_count_percentile_full[rating]
    if score > percentile[90]:
        quality_tag = "masterpiece"
    elif score > percentile[75]:
        quality_tag = "best quality"
    elif score > percentile[60]:
        quality_tag = "great quality"
    elif score > percentile[45]:
        quality_tag = "good quality"
    elif score > percentile[30]:
        quality_tag = "normal quality"
    elif score > percentile[10]:
        quality_tag = "low quality"
    else:
        quality_tag = "worst quality"
    return quality_tag


def make_caption(
    post: Post,
    tag_word_sep: str = " ",
) -> str:
    height = post.image_height
    width = post.image_width
    special_tag_list, general_tag_list = extract_special_tags(post.tag_list_general)
    special_tag_list = tag_str_list(special_tag_list, tag_word_sep)
    general_tag_list = tag_str_list(general_tag_list, tag_word_sep)
    character_tag_list = tag_str_list(post.tag_list_character, tag_word_sep)
    copyright_tag_list = tag_str_list(post.tag_list_copyright, tag_word_sep)
    artists_tag_list = tag_str_list(post.tag_list_artist, tag_word_sep)
    meta_tag_list = tag_str_list(
        [tag for tag in post.tag_list_meta if meta_tags_filter(tag)], tag_word_sep
    )

    _, year_tags = year_tag(post, [], [])
    _, rating_tags = rating_tag(post, [], [])
    _, quality_tags = quality_tag(post, [], [])

    data = {
        "height": height,
        "width": width,
        "fav": post.fav_count,
        "quality": calc_quality_tag(getattr(post, "fav_count", -100), post.rating),
        "special": special_tag_list,
        "general": general_tag_list,
        "character": character_tag_list,
        "copyright": copyright_tag_list,
        "artist": artists_tag_list,
        "meta": meta_tag_list,
        "year": year_tags,
        "rating": rating_tags,
        "quality": quality_tags,
    }
    for tag in post.tag_list:
        del tag
    del post._tags_cache
    del post
    result = dumps(data, ensure_ascii=False)
    del data
    return result


if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    logger.info("Loading danbooru2023.db")
    load_db("./data/danbooru2023.db")

    logger.info("Build exporter")

    logger.info("Querying posts")
    choosed_post: list[Post] = list(Post.select())
    choosed_post = sorted(set(choosed_post), key=lambda x: x.id)
    logger.info(f"Found {len(choosed_post)} posts")

    captions = list(
        make_caption(x)
        for x in tqdm(
            choosed_post, "make captions", total=len(choosed_post), smoothing=0.01
        )
    )
    with open("./out/captions-full.jsonl", "w") as f:
        f.write("\n".join(captions) + "\n")
