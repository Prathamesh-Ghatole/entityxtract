from pydantic import BaseModel, ConfigDict
import polars as pl
from typing import Union, List
from pathlib import Path
from enum import Enum

from .pdf.extractor import pdf_to_text, pdf_to_image
from .config import get_config
from llm_extractor.logging_config import get_logger

logger = get_logger(__name__)

# allow arbitrary types in pydantic models
BaseModel.model_config = ConfigDict(arbitrary_types_allowed=True)


class ExtractionConfig(BaseModel):
    """
    Pydantic model to declare the configuration for the extraction process.
    """

    model_name: str = get_config("DEFAULT_MODEL")
    temperature: float = 0.0
    max_retries: int = 3
    parallel_requests: int = 1


class TableToExtract(BaseModel):
    """
    Pydantic model to declare a table to be extracted from a document.
    """

    name: str
    example_table: pl.DataFrame
    instructions: str
    required: bool


class ObjectsToExtract(BaseModel):
    """
    Pydantic model to declare a collection of objects to be extracted from a document.
    """

    objects: list[TableToExtract]
    config: ExtractionConfig


ExtractableObjects = Union[TableToExtract]


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
    _image_data: bytes = b""
    _file_path: Path = Path("")
    _file_type: DocType = None

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

        return self._text_data

    @property
    def image(self) -> bytes | List[bytes]:
        if self._image_data:
            return self._image_data

        if self._file_type == DocType.PDF:
            self._image_data = pdf_to_image(self._binary)

        return self._image_data
