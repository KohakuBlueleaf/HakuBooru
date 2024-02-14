from hakubooru.metainfo import (
    meta_keywords_black_list,
    special_tags,
)
from hakubooru.tag_generator import (
    rating_tag,
    quality_tag,
    year_tag,
)
from hakubooru.dataset.db import (
    Post,
    Tag,
)


def tag_str_list(tag_list: list[Tag], tag_word_sep: str) -> list[str]:
    return [
        tag.name.replace("_", tag_word_sep) if len(tag.name) > 3 else tag.name
        for tag in tag_list
        if tag.name.strip()
    ]


def meta_tags_filter(tag: Tag) -> bool:
    if tag.type != "meta":
        return True

    # NOTE: we only filter out meta tags with these keywords
    # Which is definitely not related to the content of image
    if any(keyword in tag.name for keyword in meta_keywords_black_list):
        return False

    return True


def extract_special_tags(tag_list: list[Tag]) -> tuple[list[str], list[str]]:
    special = []
    general = []
    for tag in tag_list:
        if tag.name in special_tags:
            special.append(tag)
        else:
            general.append(tag)
    return special, general


def make_caption(
    post: Post,
    tag_word_sep: str = " ",
    tag_seperator: str = ", ",
    keep_seperator: str = "|||",
    processor=[year_tag, rating_tag, quality_tag],
) -> str:
    special_tag_list, general_tag_list = extract_special_tags(post.tag_list_general)
    special_tag_list = tag_str_list(special_tag_list, tag_word_sep)
    general_tag_list = tag_str_list(general_tag_list, tag_word_sep)
    character_tag_list = tag_str_list(post.tag_list_character, tag_word_sep)
    copyright_tag_list = tag_str_list(post.tag_list_copyright, tag_word_sep)
    artists_tag_list = tag_str_list(post.tag_list_artist, tag_word_sep)
    meta_tag_list = tag_str_list(
        [tag for tag in post.tag_list_meta if meta_tags_filter(tag)], tag_word_sep
    )

    keep_tags = (
        special_tag_list + character_tag_list + copyright_tag_list + artists_tag_list
    )
    general_tags = general_tag_list + meta_tag_list

    for processor_func in processor:
        keep_tags, general_tags = processor_func(post, keep_tags, general_tags)

    keep_tag_string = tag_seperator.join(keep_tags)
    general_tag_string = tag_seperator.join(general_tags)

    return keep_tag_string + tag_seperator + keep_seperator + general_tag_string


def make_caption_from_id(
    post_id: int,
    tag_word_sep: str = " ",
    tag_seperator: str = ", ",
    keep_seperator: str = "|||",
    processor=[year_tag, rating_tag, quality_tag],
) -> str:
    post = Post.get_by_id(post_id)
    if post is None:
        raise Exception(f"Post with id {post_id} not found")
    return make_caption(post, tag_word_sep, tag_seperator, keep_seperator, processor)


class BaseCaptioner:
    def caption(self, post: Post, img: bytes) -> str:
        raise NotImplementedError


class KohakuCaptioner(BaseCaptioner):
    def __init__(
        self,
        tag_word_sep=" ",
        tag_seperator=", ",
        keep_seperator="|||",
        processors=[year_tag, rating_tag, quality_tag],
    ):
        self.processors = processors
        self.tag_word_sep = tag_word_sep
        self.tag_seperator = tag_seperator
        self.keep_seperator = keep_seperator

    def caption(self, post: Post, img: bytes) -> str:
        return make_caption(
            post,
            self.tag_word_sep,
            self.tag_seperator,
            self.keep_seperator,
            self.processors,
        )


if __name__ == "__main__":
    print(make_caption_from_id(5982731))
