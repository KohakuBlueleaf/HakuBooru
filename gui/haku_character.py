import logging
import random
import re
import operator
import os
from io import StringIO
from functools import reduce
from typing import List, Optional

from hakubooru.caption import KohakuCaptioner
from hakubooru.dataset import load_db, Post
from hakubooru.dataset.utils import (
    select_post_by_tags,
    select_post_by_required_tags,
    get_tag_by_name,
    select_post_by_excluded_tags,
)
from hakubooru.export import Exporter, FileSaver
from hakubooru.logging import logger
from hakubooru.source import TarSource


def haku_character(
    names: List[str],
    required: List[str],
    exclude: List[str],
    max_posts: int,
    ratings: List[int],
    score_threshold: int,
    db_path: str,
    image_path: str,
    output_path: str,
    id_range_min: int,
    id_range_max: int,
    add_character_category_path: bool,
    export_images: bool,
    process_threads: int,
    export_id_file: Optional[str] = None,
    id_list: Optional[List[int]] = None,
) -> str:
    """Main processing function for filtering and exporting posts."""
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)

    try:
        # Setup logging
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Initialize database
        logger.info(f"Loading {db_path}")
        load_db(db_path)

        # Add ID list Export
        if id_list or export_id_file:
            logger.info("Enter ID export mode")

            all_ids = []
            if id_list:
                all_ids.extend(id_list)
            if export_id_file:
                try:
                    with open(export_id_file, "r") as f:
                        all_ids.extend(int(line.strip()) for line in f if line.strip())
                except Exception as e:
                    logger.error(f"File load failed: {str(e)}")

            unique_ids = list(set(all_ids))
            posts = query_posts_by_ids(unique_ids)

            if export_images and posts:
                _export_posts(
                    posts=posts, output_path=output_path, image_path=image_path
                )

            return log_stream.getvalue()

        # Process tags
        required_tags = _get_valid_tags(required)
        exclude_tags = _get_valid_tags(exclude)
        target_tags = _get_valid_tags(names) if names else []

        # Build base query
        base_query = _build_base_query(
            required_tags=required_tags,
            exclude_tags=exclude_tags,
            id_min=id_range_min,
            id_max=id_range_max,
            ratings=ratings,
        )

        # Process posts
        if names:
            all_posts = []
            for tag in target_tags:
                character_posts = select_post_by_tags([tag])
                filtered_posts = _filter_posts(
                    base_query=base_query,
                    additional_query=character_posts,
                    score_threshold=score_threshold,
                    max_posts=max_posts,
                )
                logger.info(f"Found tag: {len(filtered_posts)} {tag}")
                if not filtered_posts:
                    continue

                # Prepare export
                if export_images:
                    _export_posts(
                        posts=filtered_posts,
                        tag=tag,
                        output_path=output_path,
                        image_path=image_path,
                        add_category=add_character_category_path,
                        process_threads=process_threads,
                    )
                all_posts.extend(filtered_posts)
        else:
            filtered_posts = _filter_posts(
                base_query=base_query,
                score_threshold=score_threshold,
                max_posts=max_posts,
            )
            logger.info(f"Found posts num: {len(filtered_posts)}")
            if export_images and filtered_posts:
                _export_posts(
                    posts=filtered_posts,
                    output_path=output_path,
                    image_path=image_path,
                    process_threads=process_threads,
                )

        return log_stream.getvalue()

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise
    finally:
        logger.removeHandler(handler)
        handler.close()


def _get_valid_tags(tag_names: List[str]) -> List[Optional[int]]:
    """Validate and return existing tag IDs."""
    valid_tags = []
    for name in tag_names:
        tag = get_tag_by_name(name.strip())
        if tag:
            valid_tags.append(tag)
        else:
            logger.warning(f"Tag not found: {name}")
    return valid_tags


def _build_base_query(
    required_tags: List[int],
    exclude_tags: List[int],
    id_min: int,
    id_max: int,
    ratings: List[int],
) -> Post:
    """Build base query with common filters."""
    query = Post.select()
    if required_tags:
        query = select_post_by_required_tags(required_tags)
    if exclude_tags:
        excluded_posts = select_post_by_excluded_tags(exclude_tags)
        query = query.where(Post.id << excluded_posts)
    return query.where(
        Post.id >= id_min,
        Post.id <= id_max,
        reduce(operator.or_, (Post.rating == r for r in ratings)),
    )


def _filter_posts(
    base_query: Post,
    additional_query: Optional[Post] = None,
    score_threshold: int = -1,
    max_posts: int = -1,
) -> List[Post]:
    """Apply score filtering and sampling."""
    query = base_query
    if additional_query:
        query = query.where(Post.id << additional_query)

    # Dynamic score adjustment
    if score_threshold == -1:
        if max_posts > 0:
            current_score = 100
            while current_score >= 0:
                filtered = query.where(Post.score >= current_score)
                if len(filtered) >= max_posts:
                    break
                current_score -= 10
        else:
            filtered = query
    else:
        filtered = query.where(Post.score >= score_threshold)

    filtered = list(filtered)

    # Apply max limit
    if max_posts > 0 and len(filtered) > max_posts:
        return random.sample(filtered, max_posts)
    return filtered


def query_posts_by_ids(post_ids: List[int]) -> List[Post]:
    """Query posts based on ID list."""
    valid_ids = [pid for pid in post_ids if isinstance(pid, int) and pid > 0]
    if not valid_ids:
        return []

    try:
        return list(Post.select().where(Post.id << valid_ids))
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        return []


def _export_posts(
    posts: List[Post],
    output_path: str,
    image_path: str,
    tag: Optional[str] = None,
    add_category: bool = False,
    process_threads: int = 4,
) -> None:
    """Handle post export with proper path handling."""
    if add_category and tag:
        clean_name = re.sub(r"[^\w\s]", "", tag.name)
        sub_path = f"{len(posts)}_{clean_name}"
        save_path = os.path.join(output_path, sub_path)
    else:
        save_path = output_path

    os.makedirs(save_path, exist_ok=True)
    txt_path = os.path.join(save_path, "ID_list.txt")
    with open(txt_path, "w") as f:
        f.write("\n".join(str(p.id) for p in posts))

    exporter = Exporter(
        source=TarSource(image_path),
        saver=FileSaver(save_path),
        captioner=KohakuCaptioner(),
        process_batch_size=max(1, len(posts) // process_threads // 2),
        process_threads=process_threads,
    )
    exporter.export_posts(posts)


if __name__ == "__main__":
    # Test code remains similar
    pass
