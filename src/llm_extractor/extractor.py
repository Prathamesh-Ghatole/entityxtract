import base64
import json
import time
import concurrent.futures
from typing import Any, Dict, Optional, Tuple

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

    from io import BytesIO as _BytesIO

    buffered = _BytesIO()
    img.save(buffered, format="JPEG", quality=85)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


# ---------------------------
# Internal helpers
# ---------------------------


def _build_model(config: extractor_types.ExtractionConfig) -> ChatOpenAI:
    model_kwargs = {"response_format": {"type": "json_object"}}
    return ChatOpenAI(
        openai_api_key=get_config("OPENAI_API_KEY"),
        openai_api_base=get_config("OPENAI_API_BASE"),
        model_name=config.model_name,
        temperature=config.temperature,
        model_kwargs=model_kwargs,
    )


def _build_messages(
    doc: extractor_types.Document,
    object_to_extract: extractor_types.ExtractableObjectTypes,
    config: extractor_types.ExtractionConfig,
):
    system_prompt = get_system_prompt()
    prompt = get_prompt(object_to_extract)

    if extractor_types.FileInputMode.TEXT in config.file_input_modes:
        prompt = prompt.replace("{{text}}", f"\n\n{doc.text}")

    # Add Attachments (keep existing structure as requested)
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
        SystemMessage(content=system_prompt),
        HumanMessage(content=attachments + [{"type": "text", "text": prompt}]),
    ]
    return messages


def _parse_token_usage(
    response: Any, response_dict: Optional[Dict[str, Any]]
) -> Tuple[Optional[int], Optional[int], Dict[str, Any], Any]:
    input_tokens = None
    output_tokens = None
    usage_meta = (
        response_dict.get("usage_metadata") if isinstance(response_dict, dict) else None
    ) or getattr(response, "usage_metadata", None)
    if isinstance(usage_meta, dict):
        input_tokens = usage_meta.get("input_tokens") or usage_meta.get("prompt_tokens")
        output_tokens = usage_meta.get("output_tokens") or usage_meta.get(
            "completion_tokens"
        )
    resp_meta = (
        (
            response_dict.get("response_metadata")
            if isinstance(response_dict, dict)
            else None
        )
        or getattr(response, "response_metadata", None)
        or {}
    )
    if (input_tokens is None or output_tokens is None) and isinstance(resp_meta, dict):
        tu = resp_meta.get("token_usage", {}) or {}
        input_tokens = input_tokens or tu.get("input_tokens") or tu.get("prompt_tokens")
        output_tokens = (
            output_tokens or tu.get("output_tokens") or tu.get("completion_tokens")
        )
    return input_tokens, output_tokens, resp_meta, usage_meta


def _clean_response_content(response: Any) -> str:
    content = getattr(response, "content", "")
    if not isinstance(content, str):
        content = str(content)
    # Strip potential markdown code fences
    return content.replace("```json", "").replace("```", "").strip()


def _fetch_generation_cost(
    config: extractor_types.ExtractionConfig, resp_meta: Dict[str, Any]
) -> Tuple[Optional[float], Optional[Dict[str, Any]]]:
    cost = None
    generation_stats = None
    try:
        generation_id = resp_meta.get("id") if isinstance(resp_meta, dict) else None
        if config.calculate_costs and generation_id:
            api_base = (
                get_config("OPENROUTER.API_BASE")
                or get_config("OPENAI_API_BASE")
                or "https://openrouter.ai/api/v1"
            )
            api_key = get_config("OPENROUTER.API_KEY") or get_config("OPENAI_API_KEY")
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            url = f"{api_base.rstrip('/')}/generation"
            logger.debug(
                f"Cost lookup: id={generation_id} base={api_base} auth={'yes' if api_key else 'no'}"
            )
            try:
                import requests as _requests

                # Retry a few times in case the generation record isn't immediately available
                delays = [0.5, 1.0, 2.0]
                last_status = None
                last_text = ""
                for attempt, delay in enumerate(delays, start=1):
                    resp = _requests.get(
                        url, params={"id": generation_id}, headers=headers, timeout=10
                    )
                    last_status = resp.status_code
                    last_text = resp.text[:200]
                    if resp.ok:
                        logger.info(f"Generation API output: {resp.text}")
                        generation_stats = resp.json()
                        try:
                            data = generation_stats.get("data", {})
                            cost = data.get("total_cost")
                            logger.debug(f"Cost lookup success: total_cost={cost}")
                        except Exception:
                            logger.warning(
                                "Generation stats JSON missing 'data.total_cost'."
                            )
                        break
                    # Retry on 404 as record may not be indexed yet
                    if resp.status_code == 404 and attempt < len(delays):
                        logger.debug(
                            f"Generation not found yet (404). Retry {attempt}/{len(delays) - 1} after {delay}s..."
                        )
                        time.sleep(delay)
                        continue
                    # Non-retryable or final attempt
                    logger.warning(
                        f"Generation stats request failed: {resp.status_code} {resp.text[:200]}"
                    )
                    break
                else:
                    logger.warning(
                        f"Generation stats request failed: {last_status} {last_text}"
                    )
            except ImportError as ie:
                logger.warning(
                    f"Requests library not installed; skipping generation stats fetch: {ie}"
                )
            except Exception as e:
                logger.warning(f"Error calling generation stats endpoint: {e}")
        elif config.calculate_costs and not generation_id:
            logger.debug(
                "calculate_costs enabled but no generation id found in response metadata."
            )
    except Exception as e:
        logger.warning(f"Failed to process generation stats: {e}")
    return cost, generation_stats


# ---------------------------
# Public API
# ---------------------------


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

    logger.debug(
        f"Extracting {object_to_extract.name} {type(object_to_extract)}. Config: {config}"
    )

    messages = _build_messages(doc, object_to_extract, config)
    model = _build_model(config)

    # Retry loop using config.max_retries
    max_retries = max(1, int(config.max_retries or 1))
    last_error_msg: Optional[str] = None
    last_input_tokens: Optional[int] = None
    last_output_tokens: Optional[int] = None
    last_response_raw_payload: Optional[Dict[str, Any]] = None
    last_cost: Optional[float] = None

    for attempt in range(1, max_retries + 1):
        try:
            response = model.invoke(messages)
            # Serialize response to dict for complete metadata (incl. generation id)
            try:
                response_dict = response.dict()
            except Exception:
                response_dict = None

            input_tokens, output_tokens, resp_meta, usage_meta = _parse_token_usage(
                response, response_dict
            )

            cost, generation_stats = _fetch_generation_cost(config, resp_meta)

            content_str = _clean_response_content(response)

            if isinstance(response_dict, dict):
                logger.debug(f"Raw chat response dict: {response_dict}")
                response_raw_payload = dict(response_dict)
            else:
                response_raw_payload = {
                    "content": getattr(response, "content", ""),
                    "response_metadata": resp_meta,
                    "usage_metadata": usage_meta,
                }
            if generation_stats is not None:
                response_raw_payload["generation_stats"] = generation_stats

            # Save last-attempt metadata in case of JSON parse failure
            last_input_tokens = input_tokens
            last_output_tokens = output_tokens
            last_response_raw_payload = response_raw_payload
            last_cost = cost

            response_json = json.loads(content_str)
            return extractor_types.ExtractionResult(
                extracted_data=response_json,
                response_raw=response_raw_payload,
                success=True,
                message="Extraction successful",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
            )

        except json.JSONDecodeError as e:
            # Content preview for debugging
            preview = ""
            try:
                preview = content_str[:200].replace("\n", " ")
            except Exception:
                pass
            last_error_msg = f"Response was not valid JSON: {e}. Content preview: {preview}"
            logger.error(
                f"Failed to parse JSON from model response on attempt {attempt}/{max_retries}: {e}"
            )

        except Exception as e:
            last_error_msg = f"Model invocation failed: {e}"
            logger.error(
                f"Model invocation failed on attempt {attempt}/{max_retries}: {e}"
            )

        # Backoff and retry if attempts remain
        if attempt < max_retries:
            sleep_s = min(2 ** (attempt - 1), 8)
            logger.debug(f"Retrying extraction in {sleep_s}s...")
            time.sleep(sleep_s)

    # All attempts failed
    return extractor_types.ExtractionResult(
        extracted_data=None,
        response_raw=last_response_raw_payload,
        success=False,
        message=last_error_msg or f"Failed after {max_retries} attempts",
        input_tokens=last_input_tokens,
        output_tokens=last_output_tokens,
        cost=last_cost,
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

    results: Dict[str, extractor_types.ExtractionResult] = {}
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
