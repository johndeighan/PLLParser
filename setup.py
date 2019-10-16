# setup.py

import sys, pathlib, json
from setuptools import setup, find_packages

# --- Get the text of README.md
HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

# --- Get the version number

version = ''
with open('./version.json') as fh:
	hJson = json.load(fh)
	version = hJson['version']

setup(
	name = "PLLParser",
	version = version,
	author = "John Deighan",
	author_email = "john.deighan@gmail.com",
	description = "Parse a Python-like language",
	long_description = README,
	long_description_content_type = "text/markdown",
	license="MIT",

	url = "https://github.com/johndeighan/PLLParser",
	packages = find_packages(),
	py_modules = ['myutils','TreeNode','RETokenizer','PLLParser'],
	classifiers = [
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		],
	python_requires = '>=3.6',
	)
