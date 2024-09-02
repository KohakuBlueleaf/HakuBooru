import logging
import random
import re
import operator

from io import StringIO
from functools import reduce
from hakubooru.caption import KohakuCaptioner
from hakubooru.dataset import load_db, Post
from hakubooru.dataset.utils import (
    select_post_by_tags,
    select_post_by_required_tags,
    get_tag_by_name,
)
from hakubooru.export import Exporter, FileSaver
from hakubooru.logging import logger
from hakubooru.source import TarSource


def haku_character(
    names,
    required,
    max,
    ratings,
    score,
    db_path,
    image_path,
    output_path,
    id_range_min,
    id_range_max,
    add_character_category_path,
    export_images,
):
    log_stream = StringIO()
    stream_handler = logging.StreamHandler(log_stream)
    logger.addHandler(stream_handler)

    logger.setLevel(logging.INFO)
    logger.info("Loading danbooru2023.db")
    load_db(db_path)

    logger.info("Querying posts")

    if required:
        required_tags = [get_tag_by_name(tag) for tag in required]
    else:
        required_tags = []

    rp = 1
    path = ""

    if names:
        for name in names:
            target_characters = [
                get_tag_by_name(tag)
                for tag in [
                    "{name}".format(name=name),
                ]
            ]

            choosed_post_characters = select_post_by_tags(target_characters)
            choosed_post_required = select_post_by_required_tags(required_tags)

            clean_name = re.sub(r"[^\w\s]", "", name)

            if max == -1:
                max = float("inf")

            if score != -1:
                if required_tags:
                    choosed_post = (
                        choosed_post_required.where(Post.id << choosed_post_characters)
                        .where(Post.id >= id_range_min, Post.id <= id_range_max)
                        .where(Post.score >= score)
                        .where(
                            reduce(operator.or_, (Post.rating == r for r in ratings))
                        )
                    )
                else:
                    choosed_post = (
                        choosed_post_characters.where(
                            Post.id >= id_range_min, Post.id <= id_range_max
                        )
                        .where(Post.score >= score)
                        .where(
                            reduce(operator.or_, (Post.rating == r for r in ratings))
                        )
                    )
                choosed_post = list(choosed_post)
            else:
                x = 100

                while True:
                    if required_tags:
                        choosed_post = (
                            choosed_post_required.where(
                                Post.id << choosed_post_characters
                            )
                            .where(Post.id >= id_range_min, Post.id <= id_range_max)
                            .where(Post.score >= x)
                            .where(
                                reduce(
                                    operator.or_, (Post.rating == r for r in ratings)
                                )
                            )
                        )
                    else:
                        choosed_post = (
                            choosed_post_characters.where(
                                Post.id >= id_range_min, Post.id <= id_range_max
                            )
                            .where(Post.score >= x)
                            .where(
                                reduce(
                                    operator.or_, (Post.rating == r for r in ratings)
                                )
                            )
                        )
                    choosed_post = list(choosed_post)

                    if len(choosed_post) >= max:
                        break

                    if x < 0:
                        break

                    x -= 10

            if len(choosed_post) < max and max != float("inf"):
                rp = max / len(choosed_post)
                rp = round(rp)

            if add_character_category_path:
                path = "{clean_name}/{rp}_data".format(clean_name=clean_name, rp=rp)

            if len(choosed_post) >= max and max != float("inf"):
                choosed_post = random.sample(choosed_post, max)

            logger.info(f"Found {len(choosed_post_characters)} posts for {name}")
            logger.info(f"Found {len(choosed_post_required)} posts for required tags")
            logger.info(f"Found {len(choosed_post)} posts")

            if export_images:
                logger.info("Build exporter")

                exporter = Exporter(
                    source=TarSource(image_path),
                    saver=FileSaver(
                        "{output_path}/{path}".format(
                            output_path=output_path, path=path
                        ),
                    ),
                    captioner=KohakuCaptioner(),
                    process_batch_size=250,
                    process_threads=4,
                )

                exporter.export_posts(choosed_post)
    else:
        choosed_post = list(
            Post.select()
            .where(Post.id >= id_range_min, Post.id <= id_range_max)
            .where(Post.score >= score)
            .where(reduce(operator.or_, (Post.rating == r for r in ratings)))
        )

        if max == -1:
            max = float("inf")

        if len(choosed_post) >= max and max != float("inf"):
            choosed_post = random.sample(choosed_post, max)

        logger.info(f"Found {len(choosed_post)} posts")

        if export_images:
            logger.info("Build exporter")

            exporter = Exporter(
                source=TarSource(image_path),
                saver=FileSaver(
                    "{output_path}/{path}".format(output_path=output_path, path=path),
                ),
                captioner=KohakuCaptioner(),
                process_batch_size=250,
                process_threads=4,
            )

            exporter.export_posts(choosed_post)

    logger.removeHandler(stream_handler)
    log_contents = log_stream.getvalue()
    log_stream.close()

    return log_contents


if __name__ == "__main__":
    # test
    names = []
    required = []
    max = 200
    ratings = [0, 1, 2]
    score = 10
    db_path = "./data/danbooru2023.db"
    image_path = "./images"
    output_path = "./train_data"
    id_range_min = 5000000
    id_range_max = 8000000
    add_character_category_path = True
    export_images = True
    print(
        haku_character(
            names,
            required,
            max,
            ratings,
            score,
            db_path,
            image_path,
            output_path,
            id_range_min,
            id_range_max,
            add_character_category_path,
            export_images,
        )
    )
