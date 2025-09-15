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

    model_name: str = get_config("DEFAULT_MODEL")
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
    """

    _binary: bytes = b""
    _text_data: str = ""
    _image_data: Optional[Union[PILImageType, List[PILImageType]]] = None
    _file_path: Path = Path("")
    _file_type: Optional[DocType] = None

    def __init__(self, file_path: str | Path):
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

        # determine file type
        ext = self._file_path.suffix.lower().replace(".", "")
        for dtype in DocType:
            if ext in dtype.value:
                self._file_type = dtype
                break

        if not self._file_type:
            msg = f"Unsupported file type: {ext}"
            logger.error(msg)
            raise ValueError(msg)

        # load file into memory as bytes
        with open(file_path, "rb") as f:
            self._binary = f.read()

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
