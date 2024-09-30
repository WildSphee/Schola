import html
import os
import subprocess
import tempfile
from io import BytesIO
from typing import Dict, List, Tuple

import fitz
import pandas as pd
from docx import Document
from pptx import Presentation
from pypdf import PdfReader

from tools.form_recognizer import get_doc_analysis_client

# Azure Form Recognizer credentials (assumed to be set)
AZURE_FORM_RECOGNIZER_ENDPOINT = "YOUR_FORM_RECOGNIZER_ENDPOINT"
AZURE_FORM_RECOGNIZER_CREDENTIAL = "YOUR_FORM_RECOGNIZER_CREDENTIAL"


def read_docx(docx_file) -> str:
    """Reads a DOCX file and returns a string of the text content.

    Args:
        docx_file: A file-like object representing the DOCX file.

    Returns:
        str: A string containing all the text from the document.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp:
        docx_file.seek(0)
        data = docx_file.read()
        temp.write(data)
        temp_filename = temp.name
    # Use python-docx to read the temporary file
    doc = Document(temp_filename)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text


def read_pptx(pptx_file) -> str:
    """Reads a PPTX file and returns a string of the text content.

    Args:
        pptx_file: A file-like object representing the PPTX file.

    Returns:
        str: A string containing all the text from the presentation.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as temp:
        pptx_file.seek(0)
        contents = pptx_file.read()
        temp.write(contents)
        temp_filename = temp.name
    # Use python-pptx to read the temporary file
    presentation = Presentation(temp_filename)
    text = ""
    for slide in presentation.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text += shape.text + " "
    return text


def doc_to_pdf(file):
    """
    Converts a document file to PDF using LibreOffice and returns a file-like object representing the PDF.

    Args:
        file: A file-like object representing the document to convert.

    Returns:
        file-like object: A file-like object representing the converted PDF.
    """
    try:
        # Check if LibreOffice is installed
        subprocess.run(
            ["libreoffice", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError:
        raise Exception("Please install LibreOffice to convert documents to PDF.")

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_name = temp_file.name
        with open(temp_file_name, "wb") as buffer:
            file.seek(0)
            buffer.write(file.read())

    pdf_file_name = os.path.splitext(temp_file_name)[0] + ".pdf"

    # Convert document to PDF using LibreOffice
    command = [
        "libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        temp_file_name,
        "--outdir",
        os.path.dirname(temp_file_name),
    ]
    subprocess.run(command, check=True)

    # Read the converted PDF into a file-like object
    pdf_file = open(pdf_file_name, "rb")

    # Remove the temporary files
    os.remove(temp_file_name)
    os.remove(pdf_file_name)

    return pdf_file


def pdf_to_page_map_azure(file) -> List[Tuple[int, int, str]]:
    """
    Extracts text from a PDF file and returns a page map using Azure Form Recognizer.

    Args:
        file: A file-like object representing the PDF file.

    Returns:
        List[Tuple[int, int, str]]: A list of tuples containing page number, offset, and text content.
    """

    def _table_to_html(table) -> str:
        """
        Converts a table to HTML string.

        Args:
            table: The table to convert.

        Returns:
            str: HTML representation of the table.
        """
        table_html = "<table>"
        rows = [
            sorted(
                [cell for cell in table.cells if cell.row_index == i],
                key=lambda cell: cell.column_index,
            )
            for i in range(table.row_count)
        ]
        for row_cells in rows:
            table_html += "<tr>"
            for cell in row_cells:
                tag = (
                    "th"
                    if (cell.kind == "columnHeader" or cell.kind == "rowHeader")
                    else "td"
                )
                cell_spans = ""
                if cell.column_span > 1:
                    cell_spans += f" colSpan={cell.column_span}"
                if cell.row_span > 1:
                    cell_spans += f" rowSpan={cell.row_span}"
                table_html += f"<{tag}{cell_spans}>{html.escape(cell.content)}</{tag}>"
            table_html += "</tr>"
        table_html += "</table>"
        return table_html

    offset = 0
    page_map: List[Tuple[int, int, str]] = []

    # Initialize the Azure Form Recognizer client
    form_recognizer_client = get_doc_analysis_client()

    # Read file data into bytes
    file.seek(0)
    file_data = file.read()

    # Create a BytesIO object from the file data
    file_stream = BytesIO(file_data)

    poller = form_recognizer_client.begin_analyze_document(
        "prebuilt-layout", document=file_stream
    )
    form_recognizer_results = poller.result()

    for page_num, page in enumerate(form_recognizer_results.pages):
        tables_on_page = []
        if form_recognizer_results.tables is not None:
            for table in form_recognizer_results.tables:
                if table.bounding_regions is None:
                    continue
                if table.bounding_regions[0].page_number == page_num + 1:
                    tables_on_page.append(table)

        # Mark all positions of the table spans in the page
        page_offset = page.spans[0].offset
        page_length = page.spans[0].length
        table_chars = [-1] * page_length
        for table_id, table in enumerate(tables_on_page):
            for span in table.spans:
                # Replace all table spans with "table_id" in table_chars array
                for i in range(span.length):
                    idx = span.offset - page_offset + i
                    if 0 <= idx < page_length:
                        table_chars[idx] = table_id

        # Build page text by replacing characters in table spans with table HTML
        page_text = ""
        added_tables = set()
        for idx, table_id in enumerate(table_chars):
            if table_id == -1:
                page_text += form_recognizer_results.content[page_offset + idx]
            elif table_id not in added_tables:
                page_text += _table_to_html(tables_on_page[table_id])
                added_tables.add(table_id)
        page_text += " "
        page_map.append((page_num, offset, page_text))
        offset += len(page_text)

    return page_map


def pdf_to_page_map_pypdf(file) -> List[Tuple[int, int, str]]:
    """
    Extracts text from a PDF file and returns a page map using PyPDF.

    Args:
        file: A file-like object representing the PDF file.

    Returns:
        List[Tuple[int, int, str]]: A list of tuples containing page number, offset, and text content.
    """
    file.seek(0)
    reader = PdfReader(file)

    pages_text = []
    offset = 0
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text() if page.extract_text() is not None else ""
        pages_text.append((page_num, offset, text))
        offset += len(text)

    return pages_text


def pdf_to_page_map_pymupdf(file) -> List[Tuple[int, int, str]]:
    """
    Extracts text from a PDF file and returns a page map using PyMuPDF.

    Args:
        file: A file-like object representing the PDF file.

    Returns:
        List[Tuple[int, int, str]]: A list of tuples containing page number, offset, and text content.
    """
    file.seek(0)
    pdf_document = fitz.open(stream=file.read(), filetype="pdf")

    pages_text = []
    offset = 0
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        text = page.get_text("text")
        pages_text.append((page_num, offset, text))
        offset += len(text)

    pdf_document.close()

    return pages_text


def extract_csv(file, csv_header) -> List[Dict]:
    """
    Converts a CSV file into a list of dictionaries, each representing a row.

    Args:
        file: A file-like object representing the CSV file.
        csv_header (bool): Whether the CSV contains a header row.

    Returns:
        List[Dict]: A list of dictionaries representing the CSV data.
    """
    file.seek(0)
    csvdf = pd.read_csv(file, encoding="utf-8", header=0 if csv_header else None)
    record = csvdf.to_dict(orient="records")

    # Convert all integer keys to strings (e.g., 0 -> "k0")
    if not csv_header:
        record = [{f"k{k}": v for k, v in d.items()} for d in record]

    return record
