import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="actionnetwork-activist-sync-DCdsa",
    version="0.0.1",
    author="MetroDCDSA",
    author_email="afittsDSA@protonmail.com",
    description="Syncs Activists to ActionNetwork",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/afitts/actionnetwork_activist_sync",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
