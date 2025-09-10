from pathlib import Path
import polars as pl


def save_results_to_csv(results, output_dir: Path, logger, source_name: str) -> None:
    """
    Save each extraction result's extracted_data to a CSV file.

    Parameters:
    - results: Mapping[str, Result] where each Result has 'extracted_data' (rows for a table).
    - output_dir: Base directory where CSVs should be written.
    - logger: Logger instance for info/error messages.
    - source_name: Prefix (source file stem) to include in CSV filenames.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"CSV output directory: {output_dir}")

    for name, res in results.items():
        try:
            df = pl.DataFrame(res.extracted_data)
            csv_path = output_dir / f"{source_name}_{name}.csv"
            df.write_csv(csv_path)
            logger.info(f"[{name}] CSV written to {csv_path}")
        except Exception as e:
            logger.error(f"[{name}] Failed to write CSV: {e}")
