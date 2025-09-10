from pathlib import Path
import polars as pl

from llm_extractor.extractor_types import Document
from llm_extractor.logging_config import setup_logging, get_logger
from llm_extractor.extractor import extract_objects
from llm_extractor import extractor_types as et
from utils_io import save_results_to_csv

# Initialize logging for the script
setup_logging()
logger = get_logger(__name__)

SAMPLE_PDF_PATH = Path(__file__).parent / "data" /"sample_1.pdf"
MODEL = "google/gemini-2.5-flash"

TABLE1 = et.TableToExtract(
    name="Summary of Events",
    example_table=pl.DataFrame(
        [
            {
                "Begin": "02:05",
                "End": "03:25",
                "Duration": "01:20",
                "Type": "Geotechnical operation",
                "Description": "LL-CC-CPT-142A performance - Recovery: 23.70 mbsf - Termination Criteria: Maximum total thrust limit exceeded",
            },
            {
                "Begin": "00:00",
                "End": "00:40",
                "Duration": "00:40",
                "Type": "Geotechnical operation",
                "Description": "Operators busy with shift-handovers & recovering the SBF to Moonpool",
            },
            {
                "Begin": "01:00",
                "End": "02:05",
                "Duration": "01:05",
                "Type": "Geotechnical operation",
                "Description": "LL-CC-CPT-142 performance - Recovery: 25.71 mbsf - Termination Criteria: Maximum total thrust limit exceeded - Decision to perform a Bump-over on request of the Client",
            },
            {
                "Begin": "00:40",
                "End": "01:00",
                "Duration": "00:20",
                "Type": "Geotechnical operation - transit between locations",
                "Description": "Vessel in transit to LL-CC-CPT-142 location",
            },
        ]
    ),
    instructions="Extract the employee data table with columns Name, Age, and Department.",
    required=True,
)

TABLE2 = et.TableToExtract(
    name="Weather and Sea",
    example_table=pl.DataFrame(
        [
            {
                "Weather and Sea State": "Sig. Wave Height",
                "Unit": "m",
                "06:00": "0.75 - 1.50",
                "12:00": "1.00 - 2.00",
                "18:00": "1.50 - 2.75",
                "24:00": "1.25 - 2.25",
                "Comments": "Slightly increasing swell during evening hours",
            },
            {
                "Weather and Sea State": "Air Temperature",
                "Unit": "°C",
                "06:00": "6.0",
                "12:00": "8.5",
                "18:00": "7.0",
                "24:00": "5.5",
                "Comments": "Mild daytime warming, cooler overnight",
            },
            {
                "Weather and Sea State": "Wind Direction",
                "Unit": "Degrees",
                "06:00": "SW",
                "12:00": "S",
                "18:00": "WSW",
                "24:00": "W",
                "Comments": "Winds veering from south to west through the day",
            },
            {
                "Weather and Sea State": "Wind Speed",
                "Unit": "Knots",
                "06:00": "5 - 12",
                "12:00": "10 - 18",
                "18:00": "12 - 22",
                "24:00": "8 - 15",
                "Comments": "Freshening winds in late afternoon",
            },
        ]
    ),
    instructions="N/A",
    required=True,
)


def main():
    logger.info(f"Loading document from {SAMPLE_PDF_PATH}")
    doc = Document(SAMPLE_PDF_PATH)

    logger.info(f"Loaded document text: {len(doc.text)} characters")
    logger.info(f"Loaded document text preview: \n{doc.text[:500]}...\n")
    logger.info(f"Loaded document image data: {doc.image}")

    config_file_input = et.ExtractionConfig(
        model_name=MODEL,
        temperature=0.0,
        file_input_modes=[
            et.FileInputMode.FILE,
        ],
        parallel_requests=2,
        calculate_costs=True,
    )

    objects_to_extract = et.ObjectsToExtract(
        objects=[
            TABLE1,
            TABLE2,
        ],
        config=config_file_input,
    )

    logger.info(f"\nUsing extraction config: {config_file_input}")

    result = extract_objects(doc, objects_to_extract)

    if result.success:
        logger.info(
            f"\n\nExtraction successful. Results keys:\n{list(result.results.keys())}"
        )
        output_dir = Path(__file__).parent / "logs" / "extracted_csv"
        save_results_to_csv(result.results, output_dir, logger, SAMPLE_PDF_PATH.stem)
        for name, res in result.results.items():
            logger.info(
                f"[{name}] success={res.success} message={res.message} input_tokens={res.input_tokens} output_tokens={res.output_tokens} costs={res.cost}"
            )
            logger.info(
                f"[{name}] extracted data:\n{pl.DataFrame(res.extracted_data)}\n\n"
            )
            logger.info(f"[{name}] raw response: {res.response_raw}\n\n")


if __name__ == "__main__":
    main()
