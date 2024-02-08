import logging

from hakubooru.caption import KohakuCaptioner
from hakubooru.dataset import load_db, Post
from hakubooru.dataset.utils import (
    get_post_by_tags,
    get_tag_by_name,
)
from hakubooru.export import Exporter, FileSaver
from hakubooru.logging import logger
from hakubooru.source import TarSource, WdsSource


if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    logger.info("Loading danbooru2023.db")
    load_db("./data/danbooru2023.db")

    logger.info("Build exporter")
    exporter = Exporter(
        source=TarSource("./images"),
        saver=FileSaver("./out/example"),
        captioner=KohakuCaptioner(),
    )

    logger.info("Querying posts")
    # Querying posts for:
    # * whose tag_list have any of the following tags:
    #   * rice_shower_(umamusume)
    #   * mejiro_mcqueen_(umamusume)
    #   * daiwa_scarlet_(umamusume)
    #   * amiya_(arknights)
    #   * texas_(arknights)
    #   * skadi_(arknights)
    # * whose rating < 3 (avoid explicit images)
    # * whose score > 10 (better preference)
    choosed_post = list(
        get_post_by_tags(
            [
                get_tag_by_name(tag)
                for tag in [
                    "rice_shower_(umamusume)",
                    "mejiro_mcqueen_(umamusume)",
                    "daiwa_scarlet_(umamusume)",
                    "amiya_(arknights)",
                    "texas_(arknights)",
                    "skadi_(arknights)",
                ]
            ]
        ).where(Post.rating < 2, Post.score > 10)
    )
    logger.info(f"Found {len(choosed_post)} posts")

    logger.info("Exporting images")
    exporter.export_posts(choosed_post)
