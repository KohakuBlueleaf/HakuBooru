from .db import load_db, Post, PostTagRelation, Tag


if __name__ == "__main__":
    load_db("./data/danbooru2023.db")
    print(Tag.get(Tag.name == "agnes_digital_(umamusume)"))
