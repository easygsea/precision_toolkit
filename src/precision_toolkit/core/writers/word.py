"""Word writer."""

import logging
from pathlib import Path

import pandas as pd
from docx import Document
from docx.document import Document as DocumentType

logger = logging.getLogger(__name__)

# Module-level default document
_DEFAULT_DOCUMENT = Document()


def pandas_to_word(
    df: pd.DataFrame,
    doc: DocumentType = _DEFAULT_DOCUMENT,
    heading: str | None = None,
    summary: str | None = None,
) -> DocumentType:
    """Generate a Word document from a pandas DataFrame.

    Args:
        doc: The Word document object to populate.
        df: The pandas DataFrame.
        heading: A heading to add to the document. Defaults to None.
        summary: A summary to add before the table. Defaults to None.

    Returns:
        The populated Word document object.
    """
    if heading:
        doc.add_heading(heading, level=1)
    if summary:
        doc.add_paragraph(summary)

    headers = df.columns.tolist()
    table = doc.add_table(rows=len(df) + 1, cols=len(headers))

    for j, header in enumerate(headers):
        table.cell(0, j).text = header

    for i, row in enumerate(df.itertuples(index=False), start=1):
        for j, value in enumerate(row):
            table.cell(i, j).text = str(value)

    return doc


def initiate_word_document() -> DocumentType:
    """Create and return an empty Word document.

    Returns:
        A new Word document object.
    """
    return Document()


def save_word_document(
    output_file: str | Path, doc: DocumentType = _DEFAULT_DOCUMENT
) -> None:
    """Save a Word document to a file.

    Args:
        doc: The Word document object to save.
        output_file: The path to save the Word file.

    Raises:
        IOError: If file cannot be written
    """
    try:
        doc.save(str(output_file))
        logger.info(f"Word document saved to {output_file}")
    except OSError as e:
        logger.error(f"Failed to save Word document to {output_file}: {e}")
        raise
