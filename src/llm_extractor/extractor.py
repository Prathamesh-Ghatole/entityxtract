from . import extractor_types


def extract_object(
    doc: extractor_types.Document,
    objects_to_extract: extractor_types.ExtractableObjects,
    config: extractor_types.ExtractionConfig = extractor_types.ExtractionConfig(),
):
    """
    Extract specified objects from the document using the provided configuration.
    Args:
        doc: Document object containing the data to extract from
        objects_to_extract: The objects (e.g., tables) to extract
        config: Configuration for the extraction process
    Returns:
        Extracted data as a dictionary
    """
