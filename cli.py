"""Command line interface for pdf2md."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import List, Tuple

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

from . import __version__
from .converter import ConversionResult, PDFConverter


def collect_pdf_files(target: Path, recursive: bool = False) -> List[Path]:
    """Collect all PDF files from a file path or directory."""
    if target.is_file():
        if target.suffix.lower() == ".pdf":
            return [target]
        return []

    pattern = "**/*.[pP][dD][fF]" if recursive else "*.[pP][dD][fF]"
    files = sorted([f for f in target.glob(pattern) if f.is_file() and not f.name.startswith(".")])
    return files


def parse_args(args: List[str] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="pdf2md",
        description="Convert single PDF files or directories of PDFs into clean, formatted Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  pdf2md document.pdf
  pdf2md document.pdf -o output.md
  pdf2md ./documents/ -o ./markdown_notes/
  pdf2md ./library/ -r -o ./output/ --extract-images
        """,
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Path to a PDF file or a directory containing PDFs",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file (.md) or target directory (default: same folder as input)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively scan subdirectories for PDF files",
    )
    parser.add_argument(
        "--extract-images",
        action="store_true",
        help="Extract embedded images into an image folder and link them in Markdown",
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=None,
        help="Directory to save extracted images (default: <filename>_images)",
    )
    parser.add_argument(
        "--no-page-breaks",
        action="store_true",
        help="Disable inserting horizontal rules (---) between pages",
    )
    parser.add_argument(
        "-f",
        "--overwrite",
        action="store_true",
        help="Overwrite existing Markdown files without warning",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print detailed information during conversion",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser.parse_args(args)


def main(cli_args: List[str] = None) -> int:
    """Main CLI entrypoint."""
    args = parse_args(cli_args)
    input_path: Path = args.input.resolve()

    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        return 1

    pdf_files = collect_pdf_files(input_path, recursive=args.recursive)

    if not pdf_files:
        if input_path.is_file():
            print(f"Error: '{input_path.name}' is not a PDF file.", file=sys.stderr)
        else:
            search_desc = "recursively " if args.recursive else ""
            print(f"No PDF files found {search_desc}in '{input_path}'.", file=sys.stderr)
        return 1

    total_files = len(pdf_files)
    print(f"Found {total_files} PDF file{'s' if total_files != 1 else ''} to process.")

    try:
        converter = PDFConverter()
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    output_base: Path | None = args.output.resolve() if args.output else None
    if output_base and total_files > 1:
        output_base.mkdir(parents=True, exist_ok=True)

    results: List[ConversionResult] = []
    start_all = time.time()

    use_pbar = tqdm is not None and sys.stdout.isatty() and total_files > 1
    pbar = tqdm(total=total_files, desc="Converting", unit="file") if use_pbar else None

    for i, pdf_file in enumerate(pdf_files, start=1):
        # Resolve destination path
        if output_base is None:
            dest_file = pdf_file.with_suffix(".md")
        elif input_path.is_dir():
            # If recursive, preserve relative hierarchy
            if args.recursive:
                rel_path = pdf_file.relative_to(input_path)
                dest_file = output_base / rel_path.with_suffix(".md")
            else:
                dest_file = output_base / f"{pdf_file.stem}.md"
        else:
            # Single file input
            if output_base.suffix.lower() == ".md":
                dest_file = output_base
            else:
                dest_file = output_base / f"{pdf_file.stem}.md"

        if not use_pbar:
            rel_display = pdf_file.name if total_files == 1 else f"[{i}/{total_files}] {pdf_file.name}"
            if args.verbose:
                print(f"Processing {rel_display} -> {dest_file.name} ...")

        res = converter.convert_file(
            pdf_path=pdf_file,
            output_path=dest_file,
            extract_images=args.extract_images,
            image_dir=args.image_dir,
            page_chunks=not args.no_page_breaks,
            overwrite=args.overwrite,
        )
        results.append(res)

        if use_pbar:
            pbar.update(1)
            pbar.set_postfix_str(pdf_file.name[:25])
        elif not args.verbose and total_files > 1:
            status = "OK" if res.success else ("SKIPPED" if "already exists" in (res.error_message or "") else "ERR")
            print(f"[{i}/{total_files}] {pdf_file.name} -> {status}")

    if pbar:
        pbar.close()

    total_time = time.time() - start_all
    successes = [r for r in results if r.success]
    skipped = [r for r in results if not r.success and "already exists" in (r.error_message or "")]
    errors = [r for r in results if not r.success and "already exists" not in (r.error_message or "")]

    print("\n" + "=" * 55)
    print(f"Conversion Summary: {len(successes)} succeeded, {len(skipped)} skipped, {len(errors)} failed ({total_time:.2f}s)")
    print("=" * 55)

    if skipped and not args.overwrite:
        print(f"\n{len(skipped)} file(s) skipped because .md already exists (use --overwrite to force):")
        for r in skipped[:5]:
            print(f"  - {r.input_path.name}")
        if len(skipped) > 5:
            print(f"  ... and {len(skipped) - 5} more")

    if errors:
        print(f"\n{len(errors)} error(s) occurred:")
        for r in errors:
            print(f"  - {r.input_path.name}: {r.error_message}")
        return 1

    if successes and total_files == 1:
        res = successes[0]
        img_info = f", {res.images_extracted} images extracted" if res.images_extracted else ""
        print(f"Generated: {res.output_path} ({res.page_count} pages{img_info})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
