# [WIP]HakuBooru - text-image dataset maker for booru style image platform

**This repo is still WIP**

## Introduction

**Project Overview**

This project introduces a robust dataset exporter specifically designed for online image platforms, particularly those in the booru series.

We addresses a critical issue prevalent in dataset creation - the excessive use of crawlers. As user numbers swell, these crawlers often lead to unintentional "bot spam" or can even escalate to forms of DDoS attacks.

To mitigate these issues, our approach leverages pre-downloaded or previously dumped data to construct datasets, significantly reducing the impact on the original websites.

**Key Features**

The framework integrates several functionalities, streamlining the creation of custom datasets:

* **Metadata-Based Image Selection**
  * Simulates the "search by tag" functionality found in typical booru websites.
  * Offers options to filter explicit images or, conversely, to select only explicit content.
  * Excludes low-scoring images, among other customizable filters.
  * etc.
* **Image Captioning**
  * Utilizes metadata from xxxbooru-like platforms for generating quality and year tags.

You are also encouraged to develop and integrate your own components to enhance or replace existing stages of this framework. We warmly welcome contributions in the form of pull requests for new built-in processors as well!

The combination of these features not only preserves the integrity of source platforms but also offers users an efficient and customizable tool for dataset creation.

## Resources

* [danbooru2023-sqlite](https://huggingface.co/datasets/KBlueLeaf/danbooru2023-sqlite)
* [danbooru2023-webp-2Mpixel](https://huggingface.co/datasets/KBlueLeaf/danbooru2023-webp-2Mpixel)

## Setup

You can install this package through PyPi with pip utilities:

```bash
python -m pip install hakubooru
```

Or build from source:

```bash
git clone https://github.com/KohakuBlueleaf/HakuBooru
cd HakuBooru
python -m pip install -e .
```

## Components Overview

This project simplifies the workflow for exporting images from tar files into designated folders, consisting of four main components:

- **Post Chooser:** Selects relevant posts from a dataset.
  - Normally you only need peewee's api to query all the post you want.
- **Source:** Reading images from disk or web.
- **Captioner:** Generates captions for images based on the image itself or its metadata.
- **Saver:** Saves the targeted data (image bytes, caption text, and ID) on disk. Includes two built-in savers:
  - **File Saver:** Saves images and captions into separate files with a shared base name.
  - **WDS Saver:** Saves data into a tar file in webdataset format.
- **Exporter:** Manages the workflow by reading tar files, selecting posts identified by the Post Chooser, and processing them through the Captioner and Saver. Typically, customization of the Exporter's workflow is unnecessary unless integration of custom data sources or additional processing is desired.

## Usage Guide

To effectively utilize this project, follow these steps:

1. **Preparation:**

   - Download the metadata database from [Hugging Face - danbooru2023.db](https://huggingface.co/datasets/KBlueLeaf/danbooru2023-sqlite/blob/main/danbooru2023.db).
   - Download the image tar files from [Hugging Face - danbooru2023-webp-2Mpixel](https://huggingface.co/datasets/KBlueLeaf/danbooru2023-webp-2Mpixel).
   - Place the database file as `DB.db` and image tar files in `IMAGE_FOLDER/data-xxxx.tar`, where `DB` and `IMAGE_FOLDER` represent your chosen paths.
2. **Initialization:**

   - Load the database and set up logging.

```python
import logging
from hakubooru.dataset import load_db
from hakubooru.logging import logger

logger.setLevel(logging.INFO)
logger.info("Loading database")
load_db("DB")  # Replace "DB" with your database file path.
```

3. **Select Posts:**
   - Query posts based on specific tags, ratings, and scores to filter content.
   - In here we utilize the API provided by Peewee, refer to the [official documentations](https://docs.peewee-orm.com/en/latest/peewee/querying.html#selecting-multiple-records) for more information.

```python
from hakubooru.dataset import Post
from hakubooru.dataset.utils import get_post_by_tags, get_tag_by_name

logger.info("Querying posts")
choosed_post = list(
    get_post_by_tags([
        get_tag_by_name(tag) 
        for tag in [
            "rice_shower_(umamusume)", 
            "mejiro_mcqueen_(umamusume)"
        ]
    ]).where(Post.rating < 2, Post.score > 10)
)
logger.info(f"Found {len(choosed_post)} posts")
```

4. **Export Process:**
   - Configure the Exporter with your chosen `IMAGE_FOLDER`, `FileSaver` directory, and `KohakuCaptioner`, and initiate the export process.

```python
from hakubooru.export import Exporter, FileSaver
from hakubooru.caption import KohakuCaptioner
from hakubooru.source import TarSource


logger.info("Building exporter")
exporter = Exporter(
    source=TarSource("IMAGE_FOLDER"), 
    saver=FileSaver("./out/example"), 
    captioner=KohakuCaptioner()
)
logger.info("Exporting images")
exporter.export_posts(choosed_post)
```

## Acknowledgement

* GPT4: Refine this README.
