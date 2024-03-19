"""
Dataset exporter for DanTagGen
"""

import logging
from concurrent.futures import *
from json import dumps

from tqdm import tqdm

from hakubooru.caption import *
from hakubooru.tag_generator import *
from hakubooru.dataset import load_db, Post
from hakubooru.logging import logger
from hakubooru.metainfo import fav_count_percentile_full


def make_caption(
    post: Post,
    tag_word_sep: str = " ",
) -> str:
    height = post.image_height
    width = post.image_width
    fav = post.fav_count
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
        "fav": fav,
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
    return dumps(data, ensure_ascii=False)


if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    logger.info("Loading danbooru2023.db")
    load_db("./data/danbooru2023.db")

    logger.info("Build exporter")

    logger.info("Querying posts")
    choosed_post: list[Post] = (
        list(
            Post.select().where(
                Post.fav_count > fav_count_percentile_full["general"][75],
                Post.rating == 0,
            )
        )
        + list(
            Post.select().where(
                Post.fav_count > fav_count_percentile_full["sensitive"][75],
                Post.rating == 1,
            )
        )
        + list(
            Post.select().where(
                Post.fav_count > fav_count_percentile_full["questionable"][75],
                Post.rating == 2,
            )
        )
        + list(
            Post.select().where(
                Post.fav_count > fav_count_percentile_full["sensitive"][75],
                Post.rating == 3,
            )
        )
    )
    logger.info(f"Found {len(choosed_post)} posts")

    captions = list(
        make_caption(x)
        for x in tqdm(
            choosed_post, "make captions", total=len(choosed_post), smoothing=0.01
        )
    )
    with open("./out/captions.jsonl", "w") as f:
        f.write("\n".join(captions) + "\n")
