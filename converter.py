"""Core conversion engine using pymupdf4llm."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import pymupdf as fitz  # PyMuPDF
    import pymupdf4llm
except ImportError:
    fitz = None
    pymupdf4llm = None


@dataclass
class ConversionResult:
    input_path: Path
    output_path: Optional[Path]
    page_count: int = 0
    duration: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    images_extracted: int = 0


class PDFConverter:
    """Handles single PDF and batch conversions to Markdown."""

    def __init__(self):
        if pymupdf4llm is None or fitz is None:
            raise ImportError(
                "Dependencies missing. Please install pymupdf4llm:\n"
                "  pip install -r requirements.txt\n"
                "or run using uv: uv run pdf2md.py <input>"
            )

    def convert_file(
        self,
        pdf_path: Path | str,
        output_path: Optional[Path | str] = None,
        extract_images: bool = False,
        image_dir: Optional[Path | str] = None,
        page_chunks: bool = True,
        overwrite: bool = False,
    ) -> ConversionResult:
        """Convert a single PDF file to a formatted Markdown file."""
        pdf_path = Path(pdf_path).resolve()
        start_time = time.time()

        if not pdf_path.exists():
            return ConversionResult(
                input_path=pdf_path,
                output_path=None,
                success=False,
                error_message=f"File not found: {pdf_path}",
            )

        if pdf_path.suffix.lower() != ".pdf":
            return ConversionResult(
                input_path=pdf_path,
                output_path=None,
                success=False,
                error_message=f"Not a PDF file: {pdf_path.name}",
            )

        # Determine target output path
        if output_path is None:
            out_file = pdf_path.with_suffix(".md")
        else:
            out_file = Path(output_path).resolve()
            if out_file.is_dir():
                out_file = out_file / f"{pdf_path.stem}.md"

        if out_file.exists() and not overwrite:
            return ConversionResult(
                input_path=pdf_path,
                output_path=out_file,
                success=False,
                error_message=f"Output file already exists (use --overwrite to force): {out_file.name}",
            )

        # Open and inspect the PDF
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            return ConversionResult(
                input_path=pdf_path,
                output_path=out_file,
                success=False,
                error_message=f"Failed to open PDF ({type(e).__name__}): {e}",
            )

        page_count = len(doc)
        if doc.is_encrypted:
            if not doc.authenticate(""):
                doc.close()
                return ConversionResult(
                    input_path=pdf_path,
                    output_path=out_file,
                    page_count=page_count,
                    success=False,
                    error_message="PDF is password-protected/encrypted.",
                )

        # Prepare images destination if requested
        img_path_str = None
        images_count = 0
        if extract_images:
            if image_dir is not None:
                img_dest = Path(image_dir).resolve()
            else:
                img_dest = out_file.parent / f"{out_file.stem}_images"
            img_dest.mkdir(parents=True, exist_ok=True)
            img_path_str = str(img_dest)

        # Convert to markdown using pymupdf4llm
        try:
            res = pymupdf4llm.to_markdown(
                doc,
                write_images=extract_images,
                image_path=img_path_str,
                page_chunks=page_chunks,
            )

            # If page_chunks was True, pymupdf4llm returns a list of page dicts
            if isinstance(res, list):
                chunks = []
                for idx, chunk in enumerate(res):
                    text = chunk.get("text", "")
                    if text.strip():
                        chunks.append(text)
                md_content = "\n\n---\n\n".join(chunks)
            else:
                md_content = str(res)

            # Clean up trailing spaces / consecutive blank lines
            md_content = md_content.strip() + "\n"

            # Create destination folder if not exists
            out_file.parent.mkdir(parents=True, exist_ok=True)

            with open(out_file, "w", encoding="utf-8") as f:
                f.write(md_content)

            # Count images if extracted
            if extract_images and img_path_str and os.path.isdir(img_path_str):
                images_count = len([f for f in os.listdir(img_path_str) if not f.startswith(".")])

            duration = time.time() - start_time
            doc.close()

            return ConversionResult(
                input_path=pdf_path,
                output_path=out_file,
                page_count=page_count,
                duration=duration,
                success=True,
                images_extracted=images_count,
            )

        except Exception as e:
            doc.close()
            return ConversionResult(
                input_path=pdf_path,
                output_path=out_file,
                page_count=page_count,
                duration=time.time() - start_time,
                success=False,
                error_message=f"Conversion error ({type(e).__name__}): {e}",
            )
