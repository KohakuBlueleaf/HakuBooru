import os
import sqlite3
import warnings

from peewee import *

warnings.warn(
    "Remember to update your db file to catch up latest changes!", DeprecationWarning
)


class MemoryConnection(sqlite3.Connection):
    def __init__(self, dbname, *args, **kwargs):
        load_conn = sqlite3.connect(dbname)
        super(MemoryConnection, self).__init__(":memory:", *args, **kwargs)
        load_conn.backup(self)
        load_conn.close()


class SqliteMemDatabase(SqliteDatabase):
    def __init__(self, database, *args, **kwargs) -> None:
        self.dbname = database
        super().__init__(database, *args, factory=MemoryConnection, **kwargs)

    def reload(self, dbname=None):
        if dbname is None:
            dbname = self.dbname
        load_conn = sqlite3.connect(dbname)
        try:
            load_conn.backup(self._state.conn)
        finally:
            load_conn.close()

    def save(self, dbname=None):
        if dbname is None:
            dbname = self.dbname
        save_conn = sqlite3.connect(dbname)
        try:
            self._state.conn.backup(save_conn)
        finally:
            save_conn.close()


db: SqliteDatabase = None
tag_cache_map = {}


def get_tag_by_id(tag_id):
    if tag_id not in tag_cache_map:
        tag_cache_map[tag_id] = Tag.get_by_id(tag_id)
    return tag_cache_map[tag_id]


class EnumField(IntegerField):
    def __init__(self, enum_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_list = enum_list
        self.enum_map = {value: index for index, value in enumerate(enum_list)}

    def db_value(self, value):
        if isinstance(value, str):
            return self.enum_map[value]
        assert isinstance(value, int)
        return value

    def python_value(self, value):
        if value is not None:
            return self.enum_list[value]


class BaseModel(Model):
    class Meta:
        database = db


class Tag(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField(unique=True)
    type = EnumField(["general", "artist", "character", "copyright", "meta"])
    popularity = IntegerField()
    _posts: ManyToManyField
    _posts_cache = None

    @property
    def posts(self):
        if self._posts_cache is None:
            self._posts_cache = list(self._posts)
        return self._posts_cache

    def __str__(self):
        return f"<Tag '{self.name}'>"

    def __repr__(self):
        return f"<Tag|#{self.id}|{self.name}|{self.type[:2]}>"


class Post(BaseModel):
    id = IntegerField(primary_key=True)
    created_at = CharField()
    uploader_id = IntegerField()
    source = CharField()
    md5 = CharField(null=True)
    parent_id = IntegerField(null=True)
    has_children = BooleanField()
    is_deleted = BooleanField()
    is_banned = BooleanField()
    pixiv_id = IntegerField(null=True)
    has_active_children = BooleanField()
    bit_flags = IntegerField()
    has_large = BooleanField()
    has_visible_children = BooleanField()

    image_width = IntegerField()
    image_height = IntegerField()
    file_size = IntegerField()
    file_ext = CharField()

    rating = EnumField(["general", "sensitive", "questionable", "explicit"])
    score = IntegerField()
    up_score = IntegerField()
    down_score = IntegerField()
    fav_count = IntegerField()

    file_url = CharField(null=True)
    large_file_url = CharField(null=True)
    preview_file_url = CharField(null=True)

    _tags: ManyToManyField = None  # set by tags.bind
    _tags_cache = None

    @property
    def tag_count(self):
        return len(self.tag_list) if self.tag_list else 0

    @property
    def tag_count_general(self):
        return len(self.tag_list_general) if self.tag_list else 0

    @property
    def tag_count_artist(self):
        return len(self.tag_list_artist) if self.tag_list else 0

    @property
    def tag_count_character(self):
        return len(self.tag_list_character) if self.tag_list else 0

    @property
    def tag_count_copyright(self):
        return len(self.tag_list_copyright) if self.tag_list else 0

    @property
    def tag_count_meta(self):
        return len(self.tag_list_meta) if self.tag_list else 0

    @property
    def tag_list(self):
        if self._tags_cache is None:
            self._tags_cache = list(self._tags)
        return self._tags_cache

    @property
    def tag_list_general(self):
        return [tag for tag in self.tag_list if tag.type == "general"]

    @property
    def tag_list_artist(self):
        return [tag for tag in self.tag_list if tag.type == "artist"]

    @property
    def tag_list_character(self):
        return [tag for tag in self.tag_list if tag.type == "character"]

    @property
    def tag_list_copyright(self):
        return [tag for tag in self.tag_list if tag.type == "copyright"]

    @property
    def tag_list_meta(self):
        return [tag for tag in self.tag_list if tag.type == "meta"]


# create table LocalPost Table that can contain "filepath", "latentpath"
class LocalPost(BaseModel):
    # Usage : LocalPost.create(filepath="path/to/file", latentpath="path/to/latent", post=post)
    id = IntegerField(primary_key=True)
    filepath = CharField(null=True)
    latentpath = CharField(null=True)
    post = ForeignKeyField(Post, backref="localpost")

    def __str__(self):
        return f"<LocalPost '{self.filepath}'>"

    def __repr__(self):
        return f"<LocalPost|#{self.id}|{self.filepath}|{self.latentpath}|{self.post}>"


class PostTagRelation(BaseModel):
    post = ForeignKeyField(Post, backref="post_tags")
    tag = ForeignKeyField(Tag, backref="tag_posts")


tags = ManyToManyField(Tag, backref="_posts", through_model=PostTagRelation)
tags.bind(Post, "_tags", set_attribute=True)


def load_db(db_file: str):
    global db
    file_exists = os.path.exists(db_file)
    db = SqliteDatabase(db_file)
    Post._meta.database = db
    Tag._meta.database = db
    PostTagRelation._meta.database = db
    LocalPost._meta.database = db
    db.connect()
    print("Database connected.")
    if not file_exists:
        db.create_tables([Post, Tag, PostTagRelation])
        db.create_tables([LocalPost])
        db.commit()
        print("Database initialized.")
    assert db is not None, "Database is not loaded"
    return db


def print_post_info(post):
    """
    Debugging function to print out a post's tags
    """
    print(f"Post id : {post.id}")
    print(
        "General Tags: ",
        post.tag_count_general,
        len(post.tag_list_general),
        post.tag_list_general,
    )
    print(
        "Artist Tags: ",
        post.tag_count_artist,
        len(post.tag_list_artist),
        post.tag_list_artist,
    )
    print(
        "Character Tags: ",
        post.tag_count_character,
        len(post.tag_list_character),
        post.tag_list_character,
    )
    print(
        "Copyright Tags: ",
        post.tag_count_copyright,
        len(post.tag_list_copyright),
        post.tag_list_copyright,
    )
    print(
        "Meta Tags: ", post.tag_count_meta, len(post.tag_list_meta), post.tag_list_meta
    )


if __name__ == "__main__":
    db_existed = os.path.exists("danbooru2023.db")
    db = load_db("danbooru2023.db")
    if db_existed:
        # run sanity check
        post = Post.get_by_id(1)
        print_post_info(post)
        tag = Tag.select().where(Tag.name == "kousaka_kirino").get()
        print(f"Tag {tag} has {len(tag.posts)} posts")
        # get last post
        post = Post.select().order_by(Post.id.desc()).limit(1).get()
        print_post_info(post)
