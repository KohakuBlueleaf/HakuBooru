import logging
from random import choices

from pytorch_lightning import seed_everything

from hakubooru.dataset import load_db, Post
from hakubooru.caption import KohakuCaptioner
from hakubooru.export import Exporter, FileSaver
from hakubooru.logging import logger
from hakubooru.source import TarSource


if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    logger.info("Loading danbooru2023.db")
    load_db("./data/danbooru2023.db")

    logger.info("Build exporter")
    exporter = Exporter(
        source=TarSource("/segate10t/datasets/danbooru/webp-images"),
        saver=FileSaver("/mnt/mp44l/nn/datasets/danbooru/kxl-delta/1_3.6M"),
        captioner=KohakuCaptioner(),
        process_batch_size=100000,
        process_threads=2,
    )

    logger.info("Querying posts")
    # Querying posts for:
    # All the post after 5_000_000
    # 1/2 of the post before 5_000_000, after 3_000_000
    # 1/3 of the post before 3_000_000
    # Use seed_everything(1) to make the result reproducible
    seed_everything(1)
    choosed_post = (
        list(Post.select().where(Post.id >= 5_000_000))
        + choices(
            Post.select().where(Post.id < 5_000_000, Post.id >= 3_000_000), k=1_000_000
        )
        + choices(Post.select().where(Post.id < 3_000_000), k=1_000_000)
    )
    logger.info(f"Found {len(choosed_post)} posts")

    logger.info("Exporting images")
    exporter.export_posts(choosed_post)
