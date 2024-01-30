import logging

from hakubooru.dataset import load_db, Post
from hakubooru.dataset.utils import (
    get_post_by_tags,
    get_tag_by_name,
)
from hakubooru.caption import KohakuCaptioner
from hakubooru.export import Exporter, FileSaver
from hakubooru.logging import logger


if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    logger.info("Loading danbooru2023.db")
    load_db("./data/danbooru2023.db")

    logger.info("Build exporter")
    exporter = Exporter(
        "./images",
        saver=FileSaver("./out/umamusume"),
        captioner=KohakuCaptioner(),
    )

    logger.info("Querying posts")
    # Querying posts for:
    # * whose tag_list have any of the following tags:
    #   * rice_shower_(umamusume)
    #   * agnes_digital_(umamusume)
    #   * mr._c.b._(umamusume)
    # * whose rating < 2 (general/sensitive only)
    # * whose score > 20
    choosed_post = list(
        get_post_by_tags(
            [
                get_tag_by_name(tag)
                for tag in [
                    "rice_shower_(umamusume)",
                    "agnes_digital_(umamusume)",
                    "mr._c.b._(umamusume)",
                ]
            ]
        )
        .where(Post.rating < 2)
        .where(Post.score > 20)
    )
    logger.info(f"Found {len(choosed_post)} posts")

    logger.info("Exporting images")
    exporter.export_posts(choosed_post)
