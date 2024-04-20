import logging

from hakubooru.dataset import load_db, Tag
from hakubooru.logging import logger


if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    logger.info("Loading danbooru2023.db")
    load_db("./data/danbooru2023.db")

    logger.info("Querying tags")
    artists_tags = Tag.select().where(Tag.type == Tag.type.enum_map["artist"])
    character_tags = Tag.select().where(Tag.type == Tag.type.enum_map["character"])
    copyright_tags = Tag.select().where(Tag.type == Tag.type.enum_map["copyright"])
    meta_tags = Tag.select().where(Tag.type == Tag.type.enum_map["meta"])
    logger.info(f"Found {len(artists_tags)} artists")
    logger.info(f"Found {len(character_tags)} characters")
    logger.info(f"Found {len(copyright_tags)} copyrights")
    logger.info(f"Found {len(meta_tags)} meta")

    logger.info("Writing tags to files")

    with open("artists-tags.txt", "w") as f:
        for tag in artists_tags:
            f.write(tag.name.replace("_", " ") + "\n")

    with open("character-tags.txt", "w") as f:
        for tag in character_tags:
            f.write(tag.name.replace("_", " ") + "\n")

    with open("copyright-tags.txt", "w") as f:
        for tag in copyright_tags:
            f.write(tag.name.replace("_", " ") + "\n")

    with open("meta-tags.txt", "w") as f:
        for tag in meta_tags:
            f.write(tag.name.replace("_", " ") + "\n")

    logger.info("Done")
