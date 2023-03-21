# make_better

make_better is a Python package designed to improve the quality of your code by providing preconfigured linters and a
code formatter. The package is built to make it easy for Python developers to maintain high standards in their code by
running a single command.

## Features

- Preconfigured linters to check your code for potential issues without being too annoying.
- A preconfigured code formatter to ensure your code is formatted according to best practices.
- Easy to use: simply run a single command to check and format your code.
- Saves time by removing the routine of having to check and format code manually.

## Installation

You can install make_better via pip:

```bash
pip install make_better
```

## Usage

To check and format your code, simply navigate to the directory containing your Python files and run the following
command:

```bash
make_better --autoformat
```

This will run the preconfigured linters and code formatter on your code. Any potential issues will be flagged, and your
code will be formatted according to best practices.

## Why line-length 90

We use a line length of 90, so that people on laptops with a diagonal of 16 do not have problems during the review
