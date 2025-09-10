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

SAMPLE_PDF_PATH = Path(__file__).parent / "data" / "sample_2.pdf"
MODEL = "google/gemini-2.5-flash"

TABLE1 = et.TableToExtract(
    name="daily_production_summary",
    example_table=pl.DataFrame(
        [
            {"product": "Condensate", "quantity_bbls_or_mmscf": 58342},
            {"product": "Gas", "quantity_bbls_or_mmscf": 415.8},
            {"product": "Water", "quantity_bbls_or_mmscf": 102115},
        ]
    ),
    instructions="Overall daily production of Condensate, Gas, and Water.",
    required=True,
)

TABLE2 = et.TableToExtract(
    name="producers_estimated_flow_rate",
    example_table=pl.DataFrame(
        [
            {
                "well_names": "P15C/A118/31",
                "reservoir": "B",
                "cond_bbls": 1250,
                "water_bbls": 5200,
                "gas_mmscf": 2.5,
                "time_open_hrs": 24.0,
                "chk_percent": 28,
                "bsw_percent": 75.4,
                "gor_scf_bbl": 1850,
                "bhfp_bar": "N/A",
                "bhft_celsius": "N/A",
                "whp_bar": 120,
                "wht_celsius": 88,
            },
            {
                "well_names": "P21D/A115/30",
                "reservoir": "A",
                "cond_bbls": 438,
                "water_bbls": 2157,
                "gas_mmscf": 0.7,
                "time_open_hrs": 24.0,
                "chk_percent": 44,
                "bsw_percent": 83.1,
                "gor_scf_bbl": 1494,
                "bhfp_bar": 239,
                "bhft_celsius": 85,
                "whp_bar": 103,
                "wht_celsius": 76,
            },
            {
                "well_names": "P31C/A126/53",
                "reservoir": "EF",
                "cond_bbls": 3249,
                "water_bbls": 12197,
                "gas_mmscf": 9.7,
                "time_open_hrs": 24.0,
                "chk_percent": 47,
                "bsw_percent": 79.0,
                "gor_scf_bbl": 2985,
                "bhfp_bar": 331,
                "bhft_celsius": 96,
                "whp_bar": 170,
                "wht_celsius": 91,
            },
            {
                "well_names": "P41D/A131/61",
                "reservoir": "AW",
                "cond_bbls": 10216,
                "water_bbls": 0,
                "gas_mmscf": 89.2,
                "time_open_hrs": 24.0,
                "chk_percent": 56,
                "bsw_percent": 0.0,
                "gor_scf_bbl": 8733,
                "bhfp_bar": "N/A",
                "bhft_celsius": "N/A",
                "whp_bar": 190,
                "wht_celsius": 6,
            },
        ]
    ),
    instructions="Table detailing the production metrics for each producer well. 'Cond' is condensate, 'bbis' is barrels, 'MMScf' is million standard cubic feet, 'bbls' is barrels, 'BHFP' is bottom hole flowing pressure, 'BHFT' is bottom hole flowing temperature, 'WHP' is wellhead pressure, 'WHT' is wellhead temperature, 'GOR' is gas-oil ratio, and 'BSW' is basic sediment and water.",
    required=True,
)

TABLE3 = et.TableToExtract(
    name="gas_injection_data",
    example_table=pl.DataFrame(
        [
            {
                "well_names": "G141B/A302/23",
                "reservoir": "D",
                "gas_mmscf": 0,
                "time_open_hrs": 0,
                "chk_percent": 5,
                "whp_bar": 219,
                "wht_celsius": 5,
                "bhfp_bar": "N/A",
                "bhft_celsius": "N/A",
            },
            {
                "well_names": "G141D/A303/59",
                "reservoir": "AW",
                "gas_mmscf": 118.5,
                "time_open_hrs": 24,
                "chk_percent": 48,
                "whp_bar": 266,
                "wht_celsius": 11,
                "bhfp_bar": 301,
                "bhft_celsius": 21,
            },
        ]
    ),
    instructions="Data for gas injection wells, including total gas injected. 'MMScf' is million standard cubic feet, 'WHP' is wellhead pressure, 'WHT' is wellhead temperature, 'BHFP' is bottom hole flowing pressure, and 'BHFT' is bottom hole flowing temperature.",
    required=True,
)

TABLE4 = et.TableToExtract(
    name="water_injection_data",
    example_table=pl.DataFrame(
        [
            {
                "well_names": "WI12B/A218/40",
                "reservoir": "EF",
                "water_bbls": 16229,
                "time_open_hrs": 22,
                "chk_percent": 6,
                "whp_bar": 176,
                "wht_celsius": 19,
                "bhfp_bar": "N/A",
                "bhft_celsius": "N/A",
            },
            {
                "well_names": "W115B/A213/34",
                "reservoir": "A",
                "water_bbls": 24899,
                "time_open_hrs": 23,
                "chk_percent": 6,
                "whp_bar": 239,
                "wht_celsius": 14,
                "bhfp_bar": "N/A",
                "bhft_celsius": "N/A",
            },
            {
                "well_names": "WI22A/A217/39",
                "reservoir": "EF",
                "water_bbls": 28367,
                "time_open_hrs": 23,
                "chk_percent": 9,
                "whp_bar": 242,
                "wht_celsius": 24,
                "bhfp_bar": "N/A",
                "bhft_celsius": "N/A",
            },
            {
                "well_names": "WI32B/A220/56",
                "reservoir": "EF",
                "water_bbls": 47525,
                "time_open_hrs": 22,
                "chk_percent": 4,
                "whp_bar": 221,
                "wht_celsius": 27,
                "bhfp_bar": "N/A",
                "bhft_celsius": "N/A",
            },
        ]
    ),
    instructions="Data for water injection wells, including total water injected. 'bbls' is barrels, 'WHP' is wellhead pressure, 'WHT' is wellhead temperature, 'BHFP' is bottom hole flowing pressure, and 'BHFT' is bottom hole flowing temperature.",
    required=True,
)

TABLE5 = et.TableToExtract(
    name="gas_utilization",
    example_table=pl.DataFrame(
        [
            {
                "category": "Gas Production",
                "mmscf": 427.54,
            },
            {
                "category": "Gas Export",
                "mmscf": 289.96,
            },
            {
                "category": "Gas Injection",
                "mmscf": 118.50,
            },
            {
                "category": "Fuel Gas",
                "mmscf": 17.52,
            },
            {
                "category": "Flared Gas",
                "mmscf": 1.56,
            },
            {
                "category": "Official Sales Gas",
                "mmscf": 291.03,
            },
        ]
    ),
    instructions="A breakdown of how produced gas is utilized, including production, export, injection, and other uses. 'MMScf' is million standard cubic feet.",
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
        parallel_requests=4,
        calculate_costs=True,
    )

    objects_to_extract = et.ObjectsToExtract(
        objects=[
            TABLE1,
            TABLE2,
            TABLE3,
            TABLE4,
            TABLE5,
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
            # logger.info(f"[{name}] raw response: {res.response_raw}\n\n")


if __name__ == "__main__":
    main()
