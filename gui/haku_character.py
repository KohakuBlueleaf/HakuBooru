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

def haku_character(names,required,max,ratings,db_path,image_path,output_path,id_range_min,id_range_max):
    log_stream = StringIO()
    stream_handler = logging.StreamHandler(log_stream)
    logger.addHandler(stream_handler)

    logger.setLevel(logging.INFO)
    logger.info("Loading danbooru2023.db")
    load_db(db_path)

    logger.info("Querying posts")

    required_tags = [
        get_tag_by_name(tag) for tag in required
    ]

    for name in names:
        target_characters = [
            get_tag_by_name(tag)
            for tag in [
                "{name}".format(name=name),
            ]
        ]

        choosed_post_characters = select_post_by_tags(target_characters)
        choosed_post_required = select_post_by_required_tags(required_tags)
        choosed_post = choosed_post_required.where(Post.id << choosed_post_characters).where(Post.id > id_range_min, Post.id < id_range_max)
        choosed_post = list(choosed_post)

        if len(choosed_post) < max:
            rp = max/len(choosed_post)
            rp = round(rp)

            logger.info(f"Found {len(choosed_post_characters)} posts for characters")
            logger.info(f"Found {len(choosed_post_required)} posts for required tags")
            logger.info(f"Found {len(choosed_post)} posts")

            logger.info("Build exporter")
            clean_name = re.sub(r'[^\w\s]', '', name)
            exporter = Exporter(
                source=TarSource(image_path),
                saver=FileSaver("{output_path}/{clean_name}/{rp}_data".format(output_path=output_path,clean_name=clean_name,rp=rp)),
                captioner=KohakuCaptioner(),
                process_batch_size=250,
                process_threads=4,
            )

            exporter.export_posts(choosed_post)
            continue

        x = 100

        while True:
            choosed_post = choosed_post_required.where(Post.id << choosed_post_characters).where(Post.id > id_range_min, Post.id < id_range_max).where(Post.score >= x).where(reduce(operator.or_, (Post.rating == r for r in ratings)))
            choosed_post = list(choosed_post)

            if len(choosed_post) >= max:
                break

            if x < 0:
                break

            x -= 10

        if len(choosed_post) >= max:
            choosed_post = random.sample(choosed_post, max)

        logger.info(f"Found {len(choosed_post_characters)} posts for characters")
        logger.info(f"Found {len(choosed_post_required)} posts for required tags")
        logger.info(f"Found {len(choosed_post)} posts")

        logger.info("Build exporter")
        clean_name = re.sub(r'[^\w\s]', '', name)
        exporter = Exporter(
            source=TarSource(image_path),
            saver=FileSaver("{output_path}/{clean_name}/1_data".format(output_path=output_path,clean_name=clean_name)),
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
    names = ["kamisato_ayaka"]
    required = ["solo","highres","genshin_impact"]
    max = 200
    ratings = [0,1,2]
    db_path = "./HakuBooru/data/danbooru2023.db"
    image_path = "./HakuBooru/images"
    output_path = "./train_data"
    id_range_min = 5000000
    id_range_max = 8000000
    print(haku_character(names, required, max, ratings, db_path, image_path, output_path, id_range_min, id_range_max))
