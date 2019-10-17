# setup.py

import sys, pathlib, json
from setuptools import setup, find_packages

# --- Get the text of README.md
HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

# --- Get the version number
reVersion = re.compile(r'^__version__\s*=\s*\"(.*)\"')
version = ''
with open('./parserUtils.py') as fh:
	for line in fh:
		result = reVersion.match(line)
		if result:
			version = result.group(1)
			break

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
	py_modules = ['parserUtils','TreeNode','RETokenizer','PLLParser'],
	classifiers = [
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		],
	python_requires = '>=3.6',
	)
