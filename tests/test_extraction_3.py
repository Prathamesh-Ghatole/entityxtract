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

SAMPLE_PDF_PATH = Path(__file__).parent / "data" / "sample_3.pdf"
MODEL = "google/gemini-2.5-flash"

TABLE1 = et.TableToExtract(
    name="monthly_production_and_stock",
    example_table=pl.DataFrame(
        [
            {
                "production_day": "1-Sep-25",
                "opening_stock_g_bbls": "812,944",
                "opening_stock_n_bbls": "744,308",
                "production_g_bbls": "96,305",
                "production_n_bbls": "88,512",
                "closing_stock_g_bbls": "931,227",
                "closing_stock_n_bbls": "872,340",
                "export_g_bbls": None,
                "export_n_bbls": None,
            },
            {
                "production_day": "2-Sep-25",
                "opening_stock_g_bbls": "912,377",
                "opening_stock_n_bbls": "833,261",
                "production_g_bbls": "70,029",
                "production_n_bbls": "87,454",
                "closing_stock_g_bbls": "1,082,539",
                "closing_stock_n_bbls": "901,662",
                "export_g_bbls": None,
                "export_n_bbls": None,
            },
            {
                "production_day": "3-Sep-25",
                "opening_stock_g_bbls": "948,902",
                "opening_stock_n_bbls": "927,900",
                "production_g_bbls": "92,024",
                "production_n_bbls": "77,672",
                "closing_stock_g_bbls": "1,104,396",
                "closing_stock_n_bbls": "1,092,780",
                "export_g_bbls": None,
                "export_n_bbls": None,
            },
        ]
    ),
    instructions="Daily stock and production figures.",
    required=True,
)

TABLE2 = et.TableToExtract(
    name="daily_partner_report_production",
    example_table=pl.DataFrame(
        [
            {
                "metric": "oil",
                "daily_volume": "93,508",
                "mtd": "269,401",
                "ytd": "21,442,011",
                "cumulative_avg_mtd": "86,732",
                "cumulative_avg_ytd": "71,882",
            },
            {
                "metric": "gas",
                "daily_volume": "478,291",
                "mtd": "1,196,847",
                "ytd": "115,066,132",
                "cumulative_avg_mtd": "444,260",
                "cumulative_avg_ytd": "430,590",
            },
            {
                "metric": "water",
                "daily_volume": "64,902",
                "mtd": "148,220",
                "ytd": "13,038,411",
                "cumulative_avg_mtd": "57,411",
                "cumulative_avg_ytd": "42,121",
            },
        ]
    ),
    instructions="Daily oil, gas, and water production volumes.",
    required=True,
)

TABLE3 = et.TableToExtract(
    name="daily_partner_report_water_injection",
    example_table=pl.DataFrame(
        [
            {
                "metric": "total_water_injected",
                "daily_volume": "125,942",
                "mtd": "321,556",
                "ytd": "20,142,308",
                "cumulative_avg_mtd": "118,745",
                "cumulative_avg_ytd": "80,811",
            }
        ]
    ),
    instructions="Daily water injection summary.",
    required=True,
)

TABLE4 = et.TableToExtract(
    name="daily_partner_report_gas_volumes",
    example_table=pl.DataFrame(
        [
            {
                "metric": "gas_injection",
                "daily_volume": "514,120",
                "mtd": "1,384,228",
                "ytd": "89,277,665",
                "cumulative_avg_mtd": "419,991",
                "cumulative_avg_ytd": "393,402",
            },
            {
                "metric": "fuel_gas",
                "daily_volume": "19,804",
                "mtd": "85,276",
                "ytd": "5,244,320",
                "cumulative_avg_mtd": "22,091",
                "cumulative_avg_ytd": "19,132",
            },
            {
                "metric": "flare",
                "daily_volume": "2,986",
                "mtd": "8,223",
                "ytd": "1,678,842",
                "cumulative_avg_mtd": "2,502",
                "cumulative_avg_ytd": "7,010",
            },
        ]
    ),
    instructions="Gas injection, fuel gas usage, and flare volumes.",
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
