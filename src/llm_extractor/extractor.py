import base64
import json
import concurrent.futures
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from . import extractor_types
from .config import get_config
from .prompts import get_prompt, get_system_prompt
from llm_extractor.logging_config import get_logger


logger = get_logger(__name__)


def pil_img_to_base64(img) -> str:
    """
    Convert a PIL image (or first image in a list) to a base64-encoded JPEG string.
    Args:
        img: PIL Image object, list of PIL Images, or image-like object
    Returns:
        Base64-encoded string of the image
    """
    from io import BytesIO
    from PIL import Image as PILImage

    # If a list of images is provided, use the first one
    if isinstance(img, list):
        if not img:
            raise ValueError("Empty image list provided")
        img = img[0]

    # If it's not a PIL image, attempt to open from bytes-like object
    if not hasattr(img, "save"):
        try:
            img = PILImage.open(BytesIO(img))
        except Exception as e:
            logger.error(f"Unable to open image from provided data: {e}")
            raise

    # Ensure RGB mode for JPEG compatibility
    if getattr(img, "mode", None) != "RGB":
        img = img.convert("RGB")

    buffered = BytesIO()
    img.save(buffered, format="JPEG", quality=85)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def extract_object(
    doc: extractor_types.Document,
    object_to_extract: extractor_types.ExtractableObjectTypes,
    config: extractor_types.ExtractionConfig,
) -> extractor_types.ExtractionResult:
    """
    Extract specified objects from the document using the provided configuration.
    Args:
        doc: Document object containing the data to extract from
        object_to_extract: The object (e.g., table, string, etc) to extract
        config: Configuration for the extraction process
    Returns:
        Extracted data as an ExtractionResult object
    """

    SYSTEM_PROMPT = get_system_prompt()
    PROMPT = get_prompt(object_to_extract)

    model_kwargs = dict()
    model_kwargs["response_format"] = {"type": "json_object"}

    model = ChatOpenAI(
        openai_api_key=get_config("OPENAI_API_KEY"),
        openai_api_base=get_config("OPENAI_API_BASE"),
        model_name=config.model_name,
        temperature=config.temperature,
        model_kwargs=model_kwargs,
    )

    if extractor_types.FileInputMode.TEXT in config.file_input_modes:
        PROMPT = PROMPT.replace("{{text}}", f"\n\n{doc.text}")

    # Add Attachments
    attachments = []
    if extractor_types.FileInputMode.IMAGE in config.file_input_modes:
        if doc.image is not None:
            try:
                attachments.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{pil_img_to_base64(doc.image)}"
                        },
                    }
                )
            except Exception as e:
                logger.warning(f"Skipping image attachment due to error: {e}")
        else:
            logger.debug("No image data available; skipping image attachment")

    if extractor_types.FileInputMode.FILE in config.file_input_modes:
        attachments.append(
            {
                "type": "file",
                "file": {
                    "filename": "document.pdf",
                    "file_data": f"data:application/pdf;base64,{base64.b64encode(doc.binary).decode()}",
                },
            }
        )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=attachments + [{"type": "text", "text": PROMPT}]),
    ]

    logger.debug(
        f"Extracting {object_to_extract.name} {type(object_to_extract)}. Config: {config}"
    )

    # Invoke model
    try:
        response = model.invoke(messages)
    except Exception as e:
        logger.error(f"Model invocation failed: {e}")
        return extractor_types.ExtractionResult(
            extracted_data=None,
            response_raw=None,
            success=False,
            message=f"Model invocation failed: {e}",
        )

    # Parse JSON content
    content = getattr(response, "content", "")
    if not isinstance(content, str):
        content = str(content)

    # Strip potential markdown code fences
    content_str = content.replace("```json", "").replace("```", "").strip()

    try:
        response_json = json.loads(content_str)
        return extractor_types.ExtractionResult(
            extracted_data=response_json,
            response_raw=response,
            success=True,
            message="Extraction successful",
        )
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from model response: {e}")
        preview = content_str[:200].replace("\n", " ")
        return extractor_types.ExtractionResult(
            extracted_data=None,
            response_raw=response,
            success=False,
            message=f"Response was not valid JSON: {e}. Content preview: {preview}",
        )


def extract_objects(
    doc: extractor_types.Document,
    objects_to_extract: extractor_types.ObjectsToExtract,
) -> extractor_types.ExtractionResults:
    """
    Extract multiple objects from the document concurrently.
    Args:
        doc: Document object containing the data to extract from
        objects_to_extract: ObjectsToExtract object containing the list of objects and config
    Returns:
        ExtractionResults object containing the results of the extractions
    """

    # NOTE: use objects_to_extract.config.parallel_requests to set max_workers
    max_workers = max(1, int(objects_to_extract.config.parallel_requests or 1))

    results = dict()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_name = {
            executor.submit(
                extract_object, doc, obj, objects_to_extract.config
            ): obj.name
            for obj in objects_to_extract.objects
        }

        for future in concurrent.futures.as_completed(future_to_name):
            obj_name = future_to_name[future]
            try:
                result = future.result()
                results[obj_name] = result
            except Exception as e:
                logger.error(f"Error extracting {obj_name}: {e}")
                results[obj_name] = extractor_types.ExtractionResult(
                    extracted_data=None,
                    response_raw=None,
                    success=False,
                    message=str(e),
                )

    overall_success = all(result.success for result in results.values())

    return extractor_types.ExtractionResults(
        results=results,
        success=overall_success,
        message=None if overall_success else "Some extractions failed",
    )
