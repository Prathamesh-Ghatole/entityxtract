from pathlib import Path
import polars as pl
import time

from entityxtract.extractor_types import Document
from entityxtract.logging_config import setup_logging, get_logger
from entityxtract.extractor import extract_objects
from entityxtract import extractor_types as et
from utils_io import save_results_to_csv

# Initialize logging for the script
setup_logging()
logger = get_logger(__name__)

SAMPLE_PDF_PATH = Path(__file__).parent / "data" / "attention-is-all-you-need.pdf"
MODEL = "google/gemini-2.5-flash"
TEMPERATURE = 0.3

TABLE_AUTHORS = et.TableToExtract(
    name="Authors",
    example_table=pl.DataFrame(
        [
            {
                "Name": "Foo Bar",
                "Organization": "University of Nowhere",
                "Email": "foo.bar@unowhere.edu",
            },
            {
                "Name": "Jane Doe",
                "Organization": "Institute of Something",
                "Email": "",
            },
            {
                "Name": "John Smith",
                "Organization": "",
                "Email": "john.smith@example.com",
            },
        ]
    ),
    instructions="""
    Extract all the authors from the document with their Name, Organization, and Email.
    Typically found on the first page of the document.
    """,
    required=True,
)

TABLE_BENCHMARKS = et.TableToExtract(
    name="Benchmarks",
    example_table=pl.DataFrame(
        [
            {
                "Model": "ModelA [12]",
                "BLEU_EN_DE": 31.2,
                "BLEU_EN_FR": None,
                "Training_Cost_EN_DE": "5.4 · 10¹⁸",
                "Training_Cost_EN_FR": "",
            },
            {
                "Model": "ModelB + Enhancement [45]",
                "BLEU_EN_DE": 28.9,
                "BLEU_EN_FR": 42.5,
                "Training_Cost_EN_DE": "1.7 · 10¹⁹",
                "Training_Cost_EN_FR": "3.2 · 10²⁰",
            },
            {
                "Model": "BaselineSystem",
                "BLEU_EN_DE": None,
                "BLEU_EN_FR": 35.8,
                "Training_Cost_EN_DE": "",
                "Training_Cost_EN_FR": "8.1 · 10¹⁹",
            },
        ]
    ),
    instructions="""
    Extract benchmark results comparing different neural machine translation models.
    The table includes BLEU scores for English-to-German (EN-DE) and English-to-French (EN-FR) translation tasks,
    along with their training costs measured in FLOPs.
    Not all models have complete data - some may only have results for one language pair.
    Typically found in tables showing model performance comparisons.
    """,
    required=True,
)


def main():
    logger.info(f"Loading document from {SAMPLE_PDF_PATH}")

    start_time = time.time()
    doc = Document(SAMPLE_PDF_PATH)

    logger.info(f"Loaded document text: {len(doc.text)} characters")
    logger.info(f"Loaded document text preview: \n{doc.text[:500]}...\n")
    logger.info(f"Loaded document image data: {doc.image}")

    config_file_input = et.ExtractionConfig(
        model_name=MODEL,
        temperature=TEMPERATURE,
        file_input_modes=[
            et.FileInputMode.FILE,
        ],
        parallel_requests=4,
        calculate_costs=True,
    )

    objects_to_extract = et.ObjectsToExtract(
        objects=[
            TABLE_AUTHORS,
            TABLE_BENCHMARKS,
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

    time_taken = round(time.time() - start_time, 2)

    logger.info(
        f"Extracted {len(result.results)} tables in ${result.total_cost} using {result.total_input_tokens} input tokens and {result.total_output_tokens} output tokens in {time_taken} seconds"
    )


if __name__ == "__main__":
    main()
