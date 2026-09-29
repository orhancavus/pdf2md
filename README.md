# pdf2md: PDF to Formatted Markdown CLI

Implemented by : Orhan Cavus (<https://github.com/orhancavus>)

A high-performance Python CLI tool that converts PDF documents or directories of PDFs into clean, formatted Markdown.

Powered by [`pymupdf4llm`](https://github.com/pymupdf/pymupdf4llm), it preserves document structure, converts complex tables into GitHub-flavored Markdown, formats lists and headers, and optionally extracts embedded images.

---

## Quick Start

### Option 1: Instant Run with `uv` (Recommended - No Manual Setup)

If you have [`uv`](https://github.com/astral-sh/uv) installed, you can run the script immediately. It will fetch dependencies automatically in an isolated temporary environment:

```bash
# Direct execution (uses PEP 723 metadata)
./pdf2md.py input.pdf

# Or explicitly via uv
uv run pdf2md.py input.pdf
```

### Option 2: Standard Python Virtual Environment

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install requirements
pip install -r tools/pdf2md/requirements.txt

# 3. Run the CLI
python3 pdf2md.py input.pdf
```

---

## Usage Examples

### 1. Convert a Single PDF

Generates `document.md` in the same directory:

```bash
./pdf2md.py document.pdf
```

Specify a custom output file or destination directory:

```bash
./pdf2md.py document.pdf -o ./output/custom_name.md
./pdf2md.py document.pdf -o ./output/
```

### 2. Convert an Entire Directory

Converts all `.pdf` files in the directory:

```bash
./pdf2md.py ./git/ -o ./git_markdown/
```

### 3. Recursive Conversion

Walks all subdirectories and preserves the folder hierarchy under the output path:

```bash
./pdf2md.py ./python/ -r -o ./python_markdown/
```

### 4. Extract Images

Extracts all embedded figures into an accompanying `<filename>_images` folder and links them directly inside the Markdown:

```bash
./pdf2md.py document.pdf --extract-images
```

---

## Options & Flags

| Flag | Long Flag | Description |
| :--- | :--- | :--- |
| `-o` | `--output` | Destination `.md` file path or target directory |
| `-r` | `--recursive` | Recursively scan subdirectories for `.pdf` files |
| | `--extract-images` | Extract embedded figures to an image folder and link them |
| | `--image-dir` | Custom folder path for extracted images |
| | `--no-page-breaks` | Disable inserting `---` horizontal rules between pages |
| `-f` | `--overwrite` | Overwrite existing `.md` files without skipping |
| `-v` | `--verbose` | Show per-file processing details |
| | `--version` | Show program version |

---

## Global Access (Optional)

To run `pdf2md` from any directory on your Mac, symlink the script to your `~/bin/` directory:

```bash
ln -s "$(pwd)/pdf2md.py" ~/bin/pdf2md
```

Then you can simply run:

```bash
pdf2md my_cheatsheet.pdf
```
