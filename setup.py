# pylint: disable = C0111
from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as f:
    # Remove GitHub dark mode images
    DESCRIPTION = "".join([line for line in f if "gh-dark-mode-only" not in line])

# Required dependencies
install = []

# Optional dependencies
extras = {}

# Development dependencies - not included in "all" install
extras["dev"] = [
    "black",
    "coverage",
    "coveralls",
    "httpx",
    "mkdocs-material",
    "mkdocs-redirects",
    "mkdocstrings[python]",
    "pre-commit",
    "pylint",
]

extras["google"] = ["google-auth", "google-api-python-client", "google-auth-oauthlib"]

extras["o365"] = ["O365"]

extras["s3"] = ["boto3"]


extras["all"] = (
    extras["google"]
    + extras["o365"]
    + extras["s3"]
)

setup(
    name="corpusflowai",
    version="0.3",
    author="check-ai",
    description="Python framework designed to streamline the process of gathering training data for Large Language Models. in a ongoing basis",
    long_description=DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/check-ai-labs/CorpusFlow",
    project_urls={
        "Documentation": "https://github.com/check-ai-labs/CorpusFlow",
        "Issue Tracker": "https://github.com/check-ai-labs/CorpusFlow/issues",
        "Source Code": "https://github.com/check-ai-labs/CorpusFlow",
    },
    license="Apache 2.0: http://www.apache.org/licenses/LICENSE-2.0",
    packages=find_packages(where="src/python"),
    package_dir={"": "src/python"},
    keywords="documents LLM traning notifications",
    python_requires=">=3.9",
    install_requires=install,
    extras_require=extras,
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development",
        "Topic :: Text Processing :: Indexing",
        "Topic :: Utilities",
    ],
)