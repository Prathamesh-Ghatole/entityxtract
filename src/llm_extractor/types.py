from dataclasses import dataclass
import polars as pl


@dataclass
class TableToExtract:
    """
    Dataclass to declare a table to be extracted from a document.
    """

    table_name: str
    example_table: pl.DataFrame
    additional_instructions: str
    required: bool
