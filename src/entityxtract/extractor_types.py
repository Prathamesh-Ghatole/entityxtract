import threading
import warnings

from pydantic import BaseModel, ConfigDict, Field
import polars as pl
from typing import Union, List, Any, Optional
from pathlib import Path
from enum import Enum
from PIL import Image as PILImage
from PIL.Image import Image as PILImageType
from io import BytesIO

from .pdf.extractor import pdf_to_text, pdf_to_image, trim_pdf_pages
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
    .. deprecated::
        `ObjectsToExtract` is deprecated and will be removed in a future release.
        Pass a plain ``list[ExtractableObjectTypes]`` and an ``ExtractionConfig``
        directly to :func:`extract_objects` instead.
    """

    objects: list[ExtractableObjectTypes]
    config: ExtractionConfig

    def __init__(self, **data):
        warnings.warn(
            "ObjectsToExtract is deprecated. Pass a plain list of extractable objects "
            "and an ExtractionConfig directly to extract_objects() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)


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

        3. With PDF page filtering:
            Document("path/to/file.pdf", page_range=(0, 3))
            Document(file_bytes=pdf_bytes, file_type="pdf", page_range=(0, 3))

    Thread-safety
    -------------
    A ``Document`` performs **all** PDFium / PIL work eagerly at construction
    time (text extraction, page-image rendering, any page-range trimming).
    After ``__init__`` returns, the instance holds only immutable bytes,
    strings and already-rendered PIL images — no further PDFium calls are
    made when you read ``.binary`` / ``.text`` / ``.image``. That makes a
    constructed ``Document`` safe to share across threads.

    Parallel construction (e.g. multiple web-request handlers each building
    their own ``Document``) is also safe: the underlying PDFium helpers
    serialize themselves via a module-level lock (see
    ``entityxtract.pdf.extractor._PDFIUM_LOCK``).

    If you want to skip the (potentially expensive) image render step —
    typical when using only ``FileInputMode.FILE`` or ``FileInputMode.TEXT``
    — construct the document with ``render_images=False``. Image access
    will then lazily render on first use (also thread-safely).
    """

    def __init__(
        self,
        file_path: Optional[Union[str, Path]] = None,
        *,
        file_bytes: Optional[bytes] = None,
        file_type: Optional[Union[str, DocType]] = None,
        page_range: Optional[tuple[int, int]] = None,
        render_images: bool = True,
    ):
        # Per-instance defaults (intentionally NOT class-level attributes, to
        # avoid accidentally sharing mutable state across instances / threads).
        self._binary: bytes = b""
        self._text_data: str = ""
        self._image_data: Optional[Union[PILImageType, List[PILImageType]]] = None
        self._file_path: Path = Path("")
        self._file_type: Optional[DocType] = None
        # Explicit "already computed" flags for `.text` / `.image`. We use
        # dedicated flags (instead of truthy-checking `_text_data` / `is not
        # None` on `_image_data`) so that:
        #   * genuinely empty results (e.g. a scan-only PDF with no embedded
        #     text, or a failed PIL decode) are cached and NOT re-attempted
        #     on every property access;
        #   * doc-type/content-type combinations that simply don't apply
        #     (e.g. `.image` on a TEXT doc, `.text` on an IMAGE doc) still
        #     hit the fast path instead of taking the lock forever.
        # Invariant: these flags only ever transition False -> True.
        self._text_materialized: bool = False
        self._image_materialized: bool = False
        # Guards the (rare) lazy fallback path in `.text` / `.image` when a
        # caller opts out of eager materialisation via render_images=False.
        # After eager load completes, these properties become simple getters
        # and this lock is not touched on the hot path.
        self._lazy_lock = threading.Lock()

        if page_range is not None:
            start, end = page_range
            if start < 0 or end < 0:
                msg = "page_range values must be non-negative."
                logger.error(msg)
                raise ValueError(msg)
            if start >= end:
                msg = f"page_range start ({start}) must be < end ({end})."
                logger.error(msg)
                raise ValueError(msg)

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
            self._apply_page_range(page_range)
            self._eager_materialize(render_images=render_images)
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

        self._apply_page_range(page_range)
        self._eager_materialize(render_images=render_images)

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

    def _apply_page_range(self, page_range: Optional[tuple[int, int]]) -> None:
        """Trim PDF bytes to the specified page range if applicable."""
        if page_range is None:
            return

        if self._file_type != DocType.PDF:
            logger.warning(
                f"page_range is only supported for PDF files; ignoring for {self._file_type}"
            )
            return

        self._binary = trim_pdf_pages(self._binary, *page_range)

    def _eager_materialize(self, render_images: bool) -> None:
        """Eagerly compute ``text`` and (optionally) ``image`` up-front.

        This is the heart of the thread-safety story: we do every PDFium /
        PIL call *here*, once, on the constructing thread (which holds the
        module-level PDFium lock internally via the helpers). Any subsequent
        access to ``.text`` or ``.image`` from other threads is then just a
        pure-Python attribute read against immutable / read-only objects.

        The ``_text_materialized`` / ``_image_materialized`` flags are set
        once the corresponding work has run (successfully *or* with a
        handled failure) — including for doc-type/content-type combinations
        that have no work to do (e.g. there is no ``.image`` for a TEXT
        document). This guarantees the fast path in the ``.text`` / ``.image``
        properties is always hit after ``__init__`` returns, regardless of
        the actual content or doc type.
        """
        try:
            if self._file_type == DocType.PDF:
                self._text_data = pdf_to_text(self._binary)
                self._text_materialized = True
                if render_images:
                    self._image_data = pdf_to_image(self._binary)
                    self._image_materialized = True
                # else: leave _image_materialized=False so a later `.image`
                # access lazily renders on demand under _lazy_lock.
            elif self._file_type == DocType.TEXT:
                try:
                    self._text_data = self._binary.decode("utf-8", errors="ignore")
                except Exception as e:
                    logger.error(f"Failed to decode text file: {e}")
                    self._text_data = ""
                self._text_materialized = True
                # TEXT documents have no image concept — mark `.image`
                # materialized so the fast path returns None without ever
                # taking the lock.
                self._image_materialized = True
            elif self._file_type == DocType.IMAGE:
                if render_images:
                    try:
                        self._image_data = PILImage.open(
                            BytesIO(self._binary)
                        ).convert("RGB")
                        # Force a full decode/load now so no lazy PIL work
                        # remains to happen later on a reader thread.
                        self._image_data.load()
                    except Exception as e:
                        logger.error(f"Failed to decode image file: {e}")
                        self._image_data = None
                    self._image_materialized = True
                # else: leave _image_materialized=False so a later `.image`
                # access lazily decodes on demand under _lazy_lock.
                #
                # IMAGE documents have no text concept — mark `.text`
                # materialized so the fast path returns "" without ever
                # taking the lock.
                self._text_materialized = True
        except Exception as e:
            # We deliberately don't swallow this — constructing a Document
            # whose content can't be materialised should fail loudly, so the
            # caller learns at construction time rather than on first use
            # inside a worker thread where it's harder to debug.
            logger.error(f"Failed to eagerly materialise Document content: {e}")
            raise

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
        # Fast path: after __init__'s eager materialisation this is just a
        # plain attribute read, safe from any number of reader threads.
        # We check the explicit flag (not truthiness of _text_data) so that
        # legitimately empty results — e.g. a scan-only PDF, an empty text
        # file, or `.text` on an IMAGE document — do NOT re-enter the lock
        # on every access.
        if self._text_materialized:
            return self._text_data

        # Slow/fallback path: should only be reachable in unusual scenarios
        # (e.g. an exception from `_eager_materialize` that the caller chose
        # to handle). Compute under a lock with double-checked locking so
        # the work runs at most once.
        with self._lazy_lock:
            if self._text_materialized:
                return self._text_data
            if self._file_type == DocType.PDF:
                self._text_data = pdf_to_text(self._binary)
            elif self._file_type == DocType.TEXT:
                try:
                    self._text_data = self._binary.decode("utf-8", errors="ignore")
                except Exception as e:
                    logger.error(f"Failed to decode text file: {e}")
                    self._text_data = ""
            self._text_materialized = True
            return self._text_data

    @property
    def image(self) -> Optional[Union[PILImageType, List[PILImageType]]]:
        # Fast path: already-rendered images from __init__ (or an explicit
        # "no image for this doc type" materialisation). Using the flag
        # rather than `_image_data is not None` means we don't re-try a
        # previously failed render on every access, and we don't lock on
        # `.image` reads against TEXT documents.
        if self._image_materialized:
            return self._image_data

        # Slow/fallback path: the caller opted out of eager image
        # materialisation via `render_images=False` and is now requesting
        # `.image`. Render once under a lock; subsequent readers hit the
        # fast path.
        with self._lazy_lock:
            if self._image_materialized:
                return self._image_data
            if self._file_type == DocType.PDF:
                self._image_data = pdf_to_image(self._binary)
            elif self._file_type == DocType.IMAGE:
                try:
                    self._image_data = PILImage.open(BytesIO(self._binary)).convert(
                        "RGB"
                    )
                    self._image_data.load()
                except Exception as e:
                    logger.error(f"Failed to decode image file: {e}")
                    self._image_data = None
            self._image_materialized = True
            return self._image_data

