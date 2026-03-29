from pydantic import BaseModel, ConfigDict, Field
import polars as pl
from typing import Union, List, Any, Optional
from pathlib import Path
from enum import Enum
from PIL import Image as PILImage
from PIL.Image import Image as PILImageType
from io import BytesIO

from .pdf.extractor import pdf_to_text, pdf_to_image
from .config import get_config
from entityxtract.logging_config import get_logger

logger = get_logger(__name__)

# allow arbitrary types in pydantic models
BaseModel.model_config = ConfigDict(arbitrary_types_allowed=True)


class FileInputMode(Enum):
    FILE = "file"
    TEXT = "text"
    IMAGE = "image"


class ExtractionConfig(BaseModel):
    """
    Pydantic model to declare the configuration for the extraction process.
    """

    model_name: str = get_config("OPENAI_DEFAULT_MODEL")
    temperature: float = 0.0
    max_retries: int = 3
    parallel_requests: int = 1
    file_input_modes: List[FileInputMode] = Field(
        default_factory=lambda: [FileInputMode.FILE]
    )
    calculate_costs: bool = False


# === Extractable Objects === #


class TableToExtract(BaseModel):
    """
    Pydantic model to declare a table to be extracted from a document.
    """

    name: str
    example_table: pl.DataFrame
    instructions: str
    required: bool


class StringToExtract(BaseModel):
    """
    Pydantic model to declare a string to be extracted from a document.
    """

    name: str
    example_string: str
    instructions: str
    required: bool


# === End of Extractable Objects === #

ExtractableObjectTypes = Union[TableToExtract, StringToExtract]


class ExtractionResult(BaseModel):
    """
    Pydantic model to hold the results of the extraction process.
    """

    extracted_data: Any
    response_raw: Any
    success: bool
    message: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost: Optional[float] = None


class ExtractionResults(BaseModel):
    """
    Pydantic model to hold a collection of extraction results.
    """

    results: dict[str, ExtractionResult]
    success: bool
    message: str | None = None
    total_input_tokens: Optional[int] = None
    total_output_tokens: Optional[int] = None
    total_cost: Optional[float] = None


class ObjectsToExtract(BaseModel):
    """
    Pydantic model to declare a collection of objects to be extracted from a document.
    """

    objects: list[ExtractableObjectTypes]
    config: ExtractionConfig


class DocType(Enum):
    PDF = ["pdf"]
    IMAGE = ["png", "jpg", "jpeg", "bmp", "tiff", "gif"]
    TEXT = ["txt", "md", "csv", "tsv"]


class Document:
    """
    An object that holds a specific type of document and it's relevant data.

    Can be constructed in two ways:
        1. From a file path:
            Document("path/to/file.pdf")

        2. From raw bytes (file_type is required):
            Document(file_bytes=pdf_bytes, file_type="pdf")
            Document(file_bytes=pdf_bytes, file_type=DocType.PDF)
    """

    _binary: bytes = b""
    _text_data: str = ""
    _image_data: Optional[Union[PILImageType, List[PILImageType]]] = None
    _file_path: Path = Path("")
    _file_type: Optional[DocType] = None

    def __init__(
        self,
        file_path: Optional[Union[str, Path]] = None,
        *,
        file_bytes: Optional[bytes] = None,
        file_type: Optional[Union[str, DocType]] = None,
    ):
        # --- Validate that exactly one input source is provided ---
        if file_path is not None and file_bytes is not None:
            msg = "Provide either 'file_path' or 'file_bytes', not both."
            logger.error(msg)
            raise ValueError(msg)

        if file_path is None and file_bytes is None:
            msg = "Must provide either 'file_path' or 'file_bytes'."
            logger.error(msg)
            raise ValueError(msg)

        # --- Bytes mode ---
        if file_bytes is not None:
            if file_type is None:
                msg = "'file_type' is required when using 'file_bytes'."
                logger.error(msg)
                raise ValueError(msg)

            self._binary = file_bytes
            self._file_type = self._resolve_file_type(file_type)
            return

        # --- File path mode (existing behaviour) ---
        self._file_path = Path(file_path)

        # validate file
        if not self._file_path.exists():
            msg = f"File not found: {file_path}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        if not self._file_path.is_file():
            msg = f"Path is not a file: {file_path}"
            logger.error(msg)
            raise ValueError(msg)

        # determine file type from extension (or use explicit override)
        if file_type is not None:
            self._file_type = self._resolve_file_type(file_type)
        else:
            ext = self._file_path.suffix.lower().replace(".", "")
            for dtype in DocType:
                if ext in dtype.value:
                    self._file_type = dtype
                    break

        if not self._file_type:
            ext = self._file_path.suffix.lower().replace(".", "")
            msg = f"Unsupported file type: {ext}"
            logger.error(msg)
            raise ValueError(msg)

        # load file into memory as bytes
        with open(self._file_path, "rb") as f:
            self._binary = f.read()

    # --- Internal helpers ---

    @staticmethod
    def _resolve_file_type(file_type: Union[str, DocType]) -> DocType:
        """Resolve a string extension or DocType enum into a DocType."""
        if isinstance(file_type, DocType):
            return file_type

        ext = file_type.lower().replace(".", "")
        for dtype in DocType:
            if ext in dtype.value:
                return dtype

        msg = f"Unsupported file type: {ext}"
        logger.error(msg)
        raise ValueError(msg)

    @property
    def file_path(self) -> Path:
        return self._file_path

    @property
    def file_type(self) -> DocType:
        return self._file_type

    @property
    def binary(self) -> bytes:
        return self._binary

    @property
    def text(self) -> str:
        if self._text_data:
            return self._text_data

        if self._file_type == DocType.PDF:
            self._text_data = pdf_to_text(self._binary)
        elif self._file_type == DocType.TEXT:
            try:
                self._text_data = self._binary.decode("utf-8", errors="ignore")
            except Exception as e:
                logger.error(f"Failed to decode text file: {e}")
                self._text_data = ""

        return self._text_data

    @property
    def image(self) -> Optional[Union[PILImageType, List[PILImageType]]]:
        if self._image_data is not None:
            return self._image_data

        if self._file_type == DocType.PDF:
            self._image_data = pdf_to_image(self._binary)
        elif self._file_type == DocType.IMAGE:
            try:
                self._image_data = PILImage.open(BytesIO(self._binary)).convert("RGB")
            except Exception as e:
                logger.error(f"Failed to decode image file: {e}")
                self._image_data = None

        return self._image_data
