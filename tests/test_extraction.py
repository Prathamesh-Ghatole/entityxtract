from pathlib import Path

from llm_extractor.types import Document
from llm_extractor.logging_config import setup_logging, get_logger

# Initialize logging for the script
setup_logging()
logger = get_logger(__name__)

SAMPLE_PDF_PATH = Path(__file__).parent / "sample.pdf"


def main():
    logger.info(f"Loading document from {SAMPLE_PDF_PATH}")
    doc = Document(SAMPLE_PDF_PATH)

    logger.info(f"Loaded document text: {len(doc.text)} characters")
    logger.info(f"Loaded document text preview: \n{doc.text[:500]}...\n")
    logger.info(f"Loaded document image data: {doc.image}")


if __name__ == "__main__":
    main()
