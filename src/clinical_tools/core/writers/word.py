import logging
from pathlib import Path

import pandas as pd
from docx import Document


def pandas_to_word(
    doc: Document,
    df: pd.DataFrame,
    heading: str | None = None,
    summary: str | None = None,
) -> Document:
    """
    Generate a Word document from a pandas DataFrame.

    Args:
        doc (Document): The Word document object to populate.
        df (pd.DataFrame): The pandas DataFrame.
        heading (str, optional): A heading to add to the document. Defaults to None.
        summary (str, optional): A summary to add before the table. Defaults to None.

    Returns:
        Document: The populated Word document object.
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


def initiate_word_document() -> Document:
    """
    Create and return an empty Word document.

    Returns:
        Document: A new Word document object.
    """
    return Document()


def save_word_document(doc: Document, output_file: str | Path) -> None:
    """
    Save a Word document to a file.

    Args:
        doc (Document): The Word document object to save.
        output_file (str | Path): The path to save the Word file.

    Returns:
        None
    """
    doc.save(output_file)
    logging.info(f"Word document saved to {output_file}")
