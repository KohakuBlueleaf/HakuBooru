import logging
import os
from io import StringIO
from typing import Optional

from hakubooru.dataset import load_db, Tag
from hakubooru.logging import logger


def generate_tag_files(
    db_path: str = "./data/danbooru2023.db", output_dir: Optional[str] = None
):
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    try:
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info(f"Loading {db_path}")
        load_db(db_path)

        logger.info("Querying tags")
        artists_tags = Tag.select().where(Tag.type == Tag.type.enum_map["artist"])
        character_tags = Tag.select().where(Tag.type == Tag.type.enum_map["character"])
        copyright_tags = Tag.select().where(Tag.type == Tag.type.enum_map["copyright"])
        meta_tags = Tag.select().where(Tag.type == Tag.type.enum_map["meta"])

        output_dir = output_dir or "."
        logger.info(f"Writing tags to files: {output_dir}")

        def write_file(filename, tags):
            os.makedirs(output_dir, exist_ok=True)
            with open(f"{output_dir.rstrip('/')}/{filename}", "w") as f:
                for tag in tags:
                    f.write(tag.name.replace("_", " ") + "\n")

        write_file("artist.txt", artists_tags)
        logger.info(f"artist: {len(artists_tags)}")
        write_file("characters.txt", character_tags)
        logger.info(f"characters: {len(character_tags)}")
        write_file("copyrights.txt", copyright_tags)
        logger.info(f"copyrights: {len(copyright_tags)}")
        write_file("meta.txt", meta_tags)
        logger.info(f"meta: {len(meta_tags)}")

        return log_stream.getvalue()

    except Exception as e:
        logging.error(f"{str(e)}")
        return f"{str(e)}"


if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    generate_tag_files()
