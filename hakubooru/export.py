import os
import re
from threading import Lock
from concurrent.futures import ThreadPoolExecutor

import webdataset as wds
from tqdm import tqdm
from peewee import chunked

from hakubooru.caption import BaseCaptioner, KohakuCaptioner
from hakubooru.dataset.db import db, Post
from hakubooru.logging import logger
from hakubooru.source import BaseSource


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


class TextSaver(BaseSaver):
    def __init__(
        self, output_dir: str, caption_ext: str = "txt", one_file: bool = True
    ):
        super().__init__(output_dir, caption_ext)
        self.one_file = one_file
        if self.one_file:
            self.cache = []
            self.file_lock = Lock()
            self.file = open(
                os.path.join(self.output_dir, f"captions.{self.caption_ext}"), "w"
            )

    def __del__(self):
        if self.one_file:
            logger.info(f"Writing {len(self.cache)} captions")
            self.file.write("\n".join(self.cache) + "\n")
            self.file.close()

    def __call__(self, img_id: int, img_data: bytes, img_ext: str, caption: str):
        if self.one_file:
            self.cache.append(caption)
        else:
            with open(
                os.path.join(self.output_dir, f"{img_id}.{self.caption_ext}"), "w"
            ) as f:
                f.write(caption)


class DummyPoolExecutor:
    def map(self, func, args):
        for arg in args:
            yield func(arg)


class Exporter:
    def __init__(
        self,
        source: BaseSource,
        saver: BaseSaver = FileSaver("./out"),
        captioner: BaseCaptioner | None = KohakuCaptioner(),
        process_batch_size=1000,
        process_threads=16,
    ):
        # ThreadPool will speed up database query and saver
        if process_threads:
            self.pool = ThreadPoolExecutor(process_threads)
        else:
            self.pool = DummyPoolExecutor()

        self.source = source
        self.saver = saver
        self.captioner = captioner

        self.do_caption = captioner is not None
        self.batch_size = process_batch_size

    def process_data(self, args):
        fail = success = False
        data_id, content, ext, post = args
        try:
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

    def export_posts(self, choosed_posts: list[Post]):
        success = fail = 0
        for datas in chunked(self.source.read(choosed_posts), self.batch_size):
            for data_id, s, f in self.pool.map(self.process_data, datas):
                success += s
                fail += f

        post_not_found = self.source.not_found

        del self.saver
        del self.source

        if post_not_found:
            logger.warning(
                f"{len(post_not_found)} posts are not found in the dataset\n"
                "Some of them are gif or mp4 or corrupted files so small number is normal\n"
                "Lot of not found can be caused by missing/outdating dataset files or corrupted dataset files"
            )

        if fail:
            logger.warning(
                f"{fail} images failed to captioning and save\n"
                "please check your settings on captioner and saver."
            )

        logger.info(f"Successfully exported {success} images")
