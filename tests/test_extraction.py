from pathlib import Path
import polars as pl

from llm_extractor.extractor_types import Document
from llm_extractor.logging_config import setup_logging, get_logger
from llm_extractor.extractor import extract_object
from llm_extractor import extractor_types as et

# Initialize logging for the script
setup_logging()
logger = get_logger(__name__)

SAMPLE_PDF_PATH = Path(__file__).parent / "sample.pdf"
MODEL = "google/gemini-2.5-flash"

TABLE_TO_EXTRACT = et.TableToExtract(
    name="Summary of Events",
    example_table=pl.DataFrame(
        [
            {
                "Begin": "00:00",
                "End": "00:40",
                "Duration": "00:40",
                "Type": "Geotechnical operation",
                "Description": "Operators busy with shift-handovers & recovering the SBF to Moonpool",
            },
            {
                "Begin": "00:40",
                "End": "01:00",
                "Duration": "00:20",
                "Type": "Geotechnical operation - transit between locations",
                "Description": "Vessel in transit to LL-CC-CPT-142 location",
            },
            {
                "Begin": "01:00",
                "End": "02:05",
                "Duration": "01:05",
                "Type": "Geotechnical operation",
                "Description": "LL-CC-CPT-142 performance - Recovery: 25.71 mbsf - Termination Criteria: Maximum total thrust limit exceeded - Decision to perform a Bump-over on request of the Client",
            },
            {
                "Begin": "02:05",
                "End": "03:25",
                "Duration": "01:20",
                "Type": "Geotechnical operation",
                "Description": "LL-CC-CPT-142A performance - Recovery: 23.70 mbsf - Termination Criteria: Maximum total thrust limit exceeded",
            },
        ]
    ),
    instructions="Extract the employee data table with columns Name, Age, and Department.",
    required=True,
)


def main():
    logger.info(f"Loading document from {SAMPLE_PDF_PATH}")
    doc = Document(SAMPLE_PDF_PATH)

    logger.info(f"Loaded document text: {len(doc.text)} characters")
    logger.info(f"Loaded document text preview: \n{doc.text[:500]}...\n")
    logger.info(f"Loaded document image data: {doc.image}")

    # config_img_text = et.ExtractionConfig(
    #     model_name=MODEL,
    #     temperature=0.0,
    #     file_input_modes=[
    #         et.FileInputMode.TEXT,
    #         et.FileInputMode.IMAGE,
    #         # et.FileInputMode.FILE,
    #     ],
    # )

    # logger.info(f"\nUsing extraction config: {config_img_text}")
    # result = extract_object(doc, TABLE_TO_EXTRACT, config_img_text)
    # if result.success:
    #     logger.info(
    #         f"\n\nExtraction successful. Extracted data:\n{result.extracted_data}"
    #     )
    #     logger.info(f"raw response: {result.response_raw}")

    config_file_input = et.ExtractionConfig(
        model_name=MODEL,
        temperature=0.0,
        file_input_modes=[
            et.FileInputMode.FILE,
        ],
    )

    logger.info(f"\nUsing extraction config: {config_file_input}")
    result = extract_object(doc, TABLE_TO_EXTRACT, config_file_input)
    if result.success:
        logger.info(
            f"\n\nExtraction successful. Extracted data:\n{result.extracted_data}"
        )
        logger.info(f"raw response: {result.response_raw}")


if __name__ == "__main__":
    main()
