import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mecadoi",
    version="1.0.0",
    author="EMBO Press",
    author_email="thomas.eidens@embo.org",
    description="Depositing peer reviews from a MECA archive to CrossRef",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/source-data/mecadoi",
    project_urls={
        "Bug Tracker": "https://github.com/source-data/mecadoi/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)
