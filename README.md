# [WIP]HakuBooru - text-image dataset maker for anime-style images

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

~~Thx ChatGPT4 for this introduction :p~~


## Usage[WIP]

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


The detail documents on the components are WIP, you can check the example.py to see some basic usage of it.
