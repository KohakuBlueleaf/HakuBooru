import os
import re
from tarfile import TarFile
from typing import Iterable, Any

import webdataset as wds
from tqdm import tqdm
from peewee import chunked

from hakubooru.dataset import Post
from hakubooru.logging import logger


file_id_regex = re.compile(r"data-(\d+)\.tar")


class BaseSource:
    def __init__(self):
        self.not_found = []

    def add_not_found(self, post: Post):
        self.not_found.append(post)

    def read(self, choosed_posts: list[Post]) -> Iterable[tuple[int, bytes, str, Post]]:
        """
        yield (data_id, data, ext, post)
        """
        raise NotImplementedError


class WdsSource(BaseSource):
    def __init__(self, dataset_dirs: str | list[str]):
        super().__init__()
        if isinstance(dataset_dirs, str):
            dataset_dirs = [dataset_dirs]
        self.dataset_dirs = dataset_dirs
        self.not_found = []

        # Read all tar files we have
        self.existed_tar = {
            int(file_id_regex.match(f).group(1)): [
                os.path.join(dataset_dir, f).replace("\\", "/")
            ]
            for dataset_dir in dataset_dirs
            for f in os.listdir(dataset_dir)
            if f.endswith(".tar")
        }
        self.updates_tar = {}
        for dataset_dir in dataset_dirs:
            if os.path.isdir(os.path.join(dataset_dir, "updates")):
                for dir in os.listdir(os.path.join(dataset_dir, "updates")):
                    updates_dir = os.path.join(dataset_dir, "updates", dir)
                    for file in os.listdir(updates_dir):
                        updates_file = os.path.join(updates_dir, file).replace("\\", "/")
                        if file.endswith(".tar"):
                            self.updates_tar[updates_file] = updates_file
        assert len(self.existed_tar), "Dataset is empty"

    def _read(self, tar_files: list[str], post_dict: dict[str, Any]):
        dataset = wds.WebDataset(tar_files)

        for data in iter(dataset):
            data_id = int(data["__key__"].rsplit("/", 1)[-1])
            if data_id in post_dict:
                ext, content = list(data.items())[-1]
                yield data_id, content, ext, post_dict[data_id]
                post_dict.pop(data_id)

    def read(self, choosed_posts: list[Post]):
        existed_tar = self.existed_tar

        # Group posts by bucket
        id_map = {}
        for post in choosed_posts:
            bucket_id = post.id % 1000
            if bucket_id not in id_map:
                id_map[bucket_id] = {}
            id_map[bucket_id][post.id] = post
        id_map = {k: id_map[k] for k in sorted(id_map)}

        bucket_not_found = set()
        for base_bucket_id, post_dict in tqdm(
            id_map.items(), desc="reading buckets", smoothing=0.1
        ):
            all_bucket_id = [
                base_bucket_id + offset for offset in range(0, 10000, 1000)
            ]
            if all(bucket_id not in existed_tar for bucket_id in all_bucket_id):
                bucket_not_found.add(base_bucket_id)
                continue

            all_files = sum(
                [existed_tar.get(bucket_id, []) for bucket_id in all_bucket_id], []
            )
            yield from list(
                self._read(
                    all_files,
                    post_dict,
                )
            )

        remains = {}
        for _, post_dict in id_map.items():
            remains.update(post_dict)

        # Check updates folder if neede
        if remains and self.updates_tar:
            yield from list(self._read(list(self.updates_tar.values()), remains))

        for post in remains.values():
            self.add_not_found(post)

        if bucket_not_found:
            logger.warning(
                f"{len(bucket_not_found)} buckets are not used "
                "because the bucket doesn't exist"
            )


class TarSource(WdsSource):
    def _read(self, tar_files: list[str], post_dict: dict[str, Any]):
        tarfiles = [TarFile.open(f) for f in tar_files]

        for tarfile in tarfiles:
            for file in tarfile.getmembers():
                data_id, ext = os.path.splitext(file.name)
                data_id = int(data_id.rsplit("/", 1)[-1])
                ext = ext.lstrip(".")
                if data_id in post_dict:
                    content = tarfile.extractfile(file).read()
                    yield data_id, content, ext, post_dict[data_id]
                    post_dict.pop(data_id)


class FakeSource(BaseSource):
    def __init__(self, dataset_dir: str):
        super().__init__()

    def read(self, choosed_posts: list[Post]):
        for post in tqdm(choosed_posts, desc="reading posts"):
            yield (post.id, b"", "", post)
