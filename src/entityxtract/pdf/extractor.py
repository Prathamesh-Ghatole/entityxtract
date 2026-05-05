"""
PDF extraction utilities for the dpr_parser module.
"""

import re
from pathlib import Path
from io import BytesIO
import pypdfium2 as pdfium
from PIL import Image
from typing import Dict, List, Union
from entityxtract.logging_config import get_logger

# Module logger (configured by setup_logging() at app entry)
logger = get_logger(__name__)

# Regexes used to scrub non-deterministic metadata from PDF output so that
# re-saving the same logical document produces byte-identical output (needed
# for reliable exact-match LLM-response caching on PDF attachments).
_PDF_CREATION_DATE_RE = re.compile(rb"/CreationDate\s*\(D:[^)]*\)")
_PDF_MOD_DATE_RE = re.compile(rb"/ModDate\s*\(D:[^)]*\)")
_PDF_ID_RE = re.compile(rb"/ID\s*\[\s*<[0-9A-Fa-f]+>\s*<[0-9A-Fa-f]+>\s*\]")


def _strip_pdf_nondeterministic_metadata(pdf_bytes: bytes) -> bytes:
    """Normalize volatile metadata fields so identical inputs → identical bytes.

    pypdfium2 (and most PDF writers) stamp a fresh /CreationDate, /ModDate and
    random /ID on every save(), which would otherwise change the base64 payload
    sent to the LLM on every run and defeat response caching.
    """
    pdf_bytes = _PDF_CREATION_DATE_RE.sub(b"/CreationDate(D:00000000000000)", pdf_bytes)
    pdf_bytes = _PDF_MOD_DATE_RE.sub(b"/ModDate(D:00000000000000)", pdf_bytes)
    pdf_bytes = _PDF_ID_RE.sub(
        b"/ID [<00000000000000000000000000000000><00000000000000000000000000000000>]",
        pdf_bytes,
    )
    return pdf_bytes



def trim_pdf_pages(file: bytes, start: int, end: int) -> bytes:
    """
    Trim a PDF to only include pages in range [start, end) (0-indexed).

    Args:
        file: Bytes of the source PDF
        start: Start page index (inclusive, 0-indexed)
        end: End page index (exclusive, 0-indexed)

    Returns:
        A new PDF as bytes containing only the selected pages
    """
    try:
        src = pdfium.PdfDocument(file, autoclose=True)
        try:
            page_count = len(src)

            if start < 0 or end <= start:
                raise ValueError(
                    f"Invalid page range [{start}, {end}). Expected 0 <= start < end."
                )
            if end > page_count:
                raise ValueError(
                    f"Page range [{start}, {end}) exceeds PDF page count ({page_count})."
                )

            dst = pdfium.PdfDocument.new()
            try:
                dst.import_pages(src, pages=list(range(start, end)))
                output = BytesIO()
                dst.save(output)
                trimmed = _strip_pdf_nondeterministic_metadata(output.getvalue())
                logger.debug(
                    f"Trimmed PDF from {page_count} pages to {end - start} pages: [{start}, {end})"
                )
                return trimmed
            finally:
                dst.close()
        finally:
            src.close()
    except Exception as e:
        logger.error(f"Error trimming PDF pages: {str(e)}")
        raise


def get_pdf_page_count(file: bytes | Path | str) -> int:
    """
    Get the number of pages in a PDF file.

    Args:
        file: Bytes, Path, or string path of the PDF file

    Returns:
        Number of pages in the PDF
    Raises:
        PDFProcessingError: If there's an error processing the PDF
    """
    if isinstance(file, Path) or isinstance(file, str):
        with open(file, "rb") as f:
            file = f.read()

    try:
        doc = pdfium.PdfDocument(file, autoclose=True)
        page_count = len(doc)
        doc.close()
        logger.debug(f"PDF has {page_count} pages")
        return page_count

    except Exception as e:
        logger.error(f"Error getting PDF page count: {str(e)}")
        raise e


def pdf_to_text(file: bytes | Path | str) -> str:
    """
    Extract text from a PDF file.

    Args:
        file: Bytes, Path, or string path of the PDF file

    Returns:
        Extracted text with page markers

    Raises:
        PDFProcessingError: If there's an error processing the PDF
    """
    if isinstance(file, Path) or isinstance(file, str):
        with open(file, "rb") as f:
            file = f.read()
    try:
        doc = pdfium.PdfDocument(file, autoclose=True)
        doc_parsed: Dict[int, str] = {}

        try:
            for page_number, page in enumerate(doc):
                text_page = page.get_textpage()
                content = text_page.get_text_bounded()
                text_page.close()
                page.close()
                doc_parsed[page_number] = content
                logger.debug(f"Extracted text from page {page_number + 1}")
        finally:
            doc.close()

        # Format the extracted text with page markers
        full_text = ""
        for page_n, text in doc_parsed.items():
            full_text += f"========== page {page_n + 1} start ==========\n\n"
            full_text += text
            full_text += "\n\n"
            full_text += f"========== page {page_n + 1} end ==========\n\n"

        logger.debug(f"Extracted text from {len(doc_parsed)} pages")
        return full_text

    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise e


def pdf_to_image(
    file: bytes, scale: int = 4, combine_pages: bool = True
) -> Union[Image.Image, List[Image.Image]]:
    """
    Convert a PDF file to a list of PIL images.

    Args:
        file: Bytes of the PDF file
        scale: Rendering scale factor (higher values = higher resolution)
        combine_pages: If True, combine all pages into a single image; if False, return a list of images

    Returns:
        Either a single PIL Image (if combine_pages=True) or a list of PIL Images (if combine_pages=False)

    Raises:
        PDFProcessingError: If there's an error processing the PDF
    """
    logger.debug(
        f"Converting PDF to image(s): (scale={scale}, combine={combine_pages})"
    )

    try:
        # Load the PDF document
        pdf = pdfium.PdfDocument(file, autoclose=True)

        # Render each page as an image
        images = []
        for i in range(len(pdf)):
            page_image = pdf[i].render(scale).to_pil()
            images.append(page_image)
            logger.debug(f"Rendered page {i + 1} as image")

        # Return list of images if not combining
        if not combine_pages:
            logger.info(f"Returning {len(images)} separate page images")
            return images

        # Combine all pages into a single image
        logger.debug("Combining all pages into a single image")
        combined_image = Image.new(
            "RGB", (images[0].width, images[0].height * len(images))
        )

        for i, image in enumerate(images):
            combined_image.paste(image, (0, i * image.height))

        logger.debug(f"Combined {len(images)} pages into a single image")
        return combined_image

    except Exception as e:
        logger.error(f"Error converting PDF to image: {str(e)}")
        raise e
