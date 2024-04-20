from setuptools import setup, find_packages


setup(
    name="hakubooru",
    packages=find_packages(),
    version="0.0.2",
    license="Apache 2.0",
    url="https://github.com/KohakuBlueleaf/HakuBooru",
    description="Text-image dataset maker for anime-style images",
    author="Shih-Ying Yeh(KohakuBlueLeaf)",
    author_email="apolloyeh0123@gmail.com",
    zip_safe=False,
    install_requires=[
        "peewee",
        "python-dateutil",
        "webdataset",
    ],
)
