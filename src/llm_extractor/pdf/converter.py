"""
Conversion utilities for PDF-related data.
"""

import base64
from io import BytesIO
from PIL import Image
from typing import Optional
from llm_extractor.logging_config import get_logger

logger = get_logger(__name__)


def image_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    """
    Convert a PIL Image to a base64-encoded string.

    Args:
        image: PIL Image to convert
        format: Image format to use (JPEG, PNG, etc.)

    Returns:
        Base64-encoded string representation of the image

    Raises:
        PDFProcessingError: If there's an error converting the image
    """
    try:
        logger.debug(f"Converting image to base64 (format={format})")
        buffered = BytesIO()
        image.save(buffered, format=format)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        logger.debug("Image successfully converted to base64")
        return img_str
    except Exception as e:
        error_msg = f"Error converting image to base64: {str(e)}"
        logger.error(error_msg)
        raise e


def resize_image(
    image: Image.Image,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
) -> Image.Image:
    """
    Resize an image while maintaining aspect ratio.

    Args:
        image: PIL Image to resize
        max_width: Maximum width (if None, determined by max_height)
        max_height: Maximum height (if None, determined by max_width)

    Returns:
        Resized PIL Image

    Raises:
        PDFProcessingError: If there's an error resizing the image
        ValueError: If both max_width and max_height are None
    """
    if max_width is None and max_height is None:
        raise ValueError("At least one of max_width or max_height must be specified")

    try:
        original_width, original_height = image.size

        # Calculate new dimensions while maintaining aspect ratio
        if max_width and max_height:
            # Scale based on the more restrictive dimension
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            ratio = min(width_ratio, height_ratio)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
        elif max_width:
            # Scale based on width
            ratio = max_width / original_width
            new_width = max_width
            new_height = int(original_height * ratio)
        else:
            # Scale based on height
            ratio = max_height / original_height
            new_width = int(original_width * ratio)
            new_height = max_height

        logger.debug(
            f"Resizing image from {original_width}x{original_height} to {new_width}x{new_height}"
        )
        resized_image = image.resize((new_width, new_height), Image.LANCZOS)
        return resized_image

    except Exception as e:
        error_msg = f"Error resizing image: {str(e)}"
        logger.error(error_msg)
        raise e
