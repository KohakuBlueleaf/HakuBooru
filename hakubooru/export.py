import os
import re
from concurrent.futures import ThreadPoolExecutor

import webdataset as wds
from tqdm import tqdm

from hakubooru.dataset.db import db, Post
from hakubooru.caption import BaseCaptioner, KohakuCaptioner
from hakubooru.logging import logger


file_id_regex = re.compile(r"data-(\d+)\.tar")


class BaseSaver:
    def __init__(self, output_dir: str, caption_ext: str = "txt"):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.output_dir = output_dir
        self.caption_ext = caption_ext

    def __call__(self, img_id: int, img_data: bytes, img_ext: str, caption: str):
        raise NotImplementedError


class WdsSaver(BaseSaver):
    def __init__(
        self, output_dir: str, filename: str = "data.tar", caption_ext: str = "txt"
    ):
        super().__init__(output_dir, caption_ext)
        self.writer = wds.TarWriter(os.path.join(output_dir, filename))

    def __call__(
        self,
        img_id: int,
        img_data: bytes,
        img_ext: str,
        caption: str,
    ):
        sample = {
            "__key__": f"{img_id}",
            img_ext: img_data,
        }
        if caption is not None:
            sample[self.caption_ext] = caption
        self.writer.write(sample)


class FileSaver(BaseSaver):
    def __init__(self, output_dir: str, caption_ext: str = "txt"):
        super().__init__(output_dir, caption_ext)

    def __call__(self, img_id: int, img_data: bytes, img_ext: str, caption: str):
        with open(os.path.join(self.output_dir, f"{img_id}.{img_ext}"), "wb") as f:
            f.write(img_data)
        if caption is not None:
            with open(
                os.path.join(self.output_dir, f"{img_id}.{self.caption_ext}"), "w"
            ) as f:
                f.write(caption)


class Exporter:
    def __init__(
        self,
        dataset_dir: str,
        saver: BaseSaver = FileSaver("./out"),
        captioner: BaseCaptioner | None = KohakuCaptioner(),
    ):
        # ThreadPool will speed up database query and saver
        self.pool = ThreadPoolExecutor(16)
        self.dataset_dir = dataset_dir

        self.saver = saver
        self.captioner = captioner

        self.do_caption = captioner is not None

    def process_data(self, args):
        fail = success = False
        data_id, data, post = args
        try:
            ext, content = list(data.items())[-1]
            if self.do_caption:
                caption = self.captioner.caption(post, content)
            else:
                caption = None

            self.saver(
                data_id,
                content,
                ext,
                caption,
            )
        except Exception as e:
            logger.warning(
                f"Error occured when doing captioning and saving {data_id}: {e}"
            )
            fail = True
        if not fail:
            success = True
        return data_id, success, fail

    def _export(self, tar_files, post_dict):
        success = fail = 0
        # Concat main and sub dataset together
        dataset = wds.WebDataset(tar_files)
        data_cache = {}

        for data in iter(dataset):
            data_id = int(data["__key__"])
            if data_id in post_dict:
                data_cache[data_id] = data
                if len(data_cache) == len(post_dict):
                    break

        args = [
            (data_id, data, post_dict[data_id]) for data_id, data in data_cache.items()
        ]

        for data_id, s, f in self.pool.map(self.process_data, args):
            success += s
            fail += f
            if s:
                del post_dict[data_id]
        return success, fail

    def export_posts(self, choosed_posts: list[Post]):
        dataset_dir = self.dataset_dir

        # Read all tar files we have
        existed_tar = {
            int(file_id_regex.match(f).group(1)): [
                os.path.join(dataset_dir, f).replace("\\", "/")
            ]
            for f in os.listdir(dataset_dir)
            if f.endswith(".tar")
        }
        assert len(existed_tar), "Dataset is empty"

        # Group posts by bucket
        id_map = {}
        for post in choosed_posts:
            bucket_id = post.id % 1000
            if bucket_id not in id_map:
                id_map[bucket_id] = {}
            id_map[bucket_id][post.id] = post
        id_map = {k: id_map[k] for k in sorted(id_map)}

        # Export
        bucket_not_found = set()
        success = 0
        fail = 0
        for bucket_id, post_dict in tqdm(
            id_map.items(), desc="reading buckets", smoothing=0.1
        ):
            if bucket_id not in existed_tar and bucket_id + 1000 not in existed_tar:
                bucket_not_found.add(bucket_id)
                continue

            # Concat main and sub dataset together
            s, f = self._export(
                existed_tar.get(bucket_id, []) + existed_tar.get(bucket_id + 1000, []),
                post_dict,
            )
            success += s
            fail += f

        remains = {}
        for _, post_dict in id_map.items():
            remains.update(post_dict)

        # Check addon dataset if needed
        if remains and 2000 in existed_tar:
            s, f = self._export(existed_tar[2000], post_dict)
            success += s
            fail += f

        post_not_found = len(remains)

        if bucket_not_found:
            logger.warning(
                f"{len(bucket_not_found)} posts are not exported"
                "because the bucket doesn't exist"
            )

        if post_not_found:
            logger.warning(
                f"{post_not_found} posts are not found in the dataset\n"
                "Some of them are gif or mp4 or corrupted files so small number is normal\n"
                "Lot of not found can be caused by missing/outdating dataset files or corrupted dataset files"
            )

        if fail:
            logger.warning(
                f"{fail} images failed to captioning and save\n"
                "please check your settings on captioner and saver."
            )

        logger.info(f"Successfully exported {success} images")
