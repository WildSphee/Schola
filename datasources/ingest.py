import itertools
import os
import pathlib
import re
import shutil
from typing import Dict, Iterator, List, Literal, Optional, Tuple

# Assuming these extraction functions are available
from tools.extraction import (
    doc_to_pdf,
    extract_csv,
    pdf_to_page_map_azure,
    pdf_to_page_map_pymupdf,
    pdf_to_page_map_pypdf,
    read_docx,
    read_pptx,
)

# Importing FAISSDS directly
from .faiss_ds import FAISSDS

# Configurations
DATASOURCE_PATH = "datasources"
PDF_PAGEMAP_EXTRACTION_METHOD: Literal["AzureFormRecognizer", "PyPDF", "PyMuPDF"] = (
    "AzureFormRecognizer"
)
slicable = [".pdf", ".docx", ".pptx", ".doc", ".docm"]
libreoffice_convertable = [".docx", ".pptx", ".doc", ".docm"]


# Assuming DatasourceConfig is a simple dictionary or a class you can define
class DatasourceConfig:
    def __init__(
        self,
        csv_header=True,
        csv_key="issue",
        csv_out_template="Issue:{issue}\n\nCause:{cause}\n\nSolution:{solution}",
        doc_max_section_length=1000,
        doc_section_overlap=100,
        doc_sentence_search_limit=100,
        doc_slice=True,
    ):
        self.csv_header = csv_header
        self.csv_key = csv_key
        self.csv_out_template = csv_out_template
        self.doc_max_section_length = doc_max_section_length
        self.doc_section_overlap = doc_section_overlap
        self.doc_sentence_search_limit = doc_sentence_search_limit
        self.doc_slice = doc_slice


def create_local_dir(datasource_name) -> str:
    """
    Creates a new directory with the provided datasource name under a predefined path.
    """
    new_dir = pathlib.Path(DATASOURCE_PATH) / datasource_name
    new_dir.mkdir(parents=True, exist_ok=True)
    return str(new_dir)


def save_local_copy(file, local_dir_path: str) -> str:
    """
    Saves a locally uploaded file to a specified path and returns the file object.
    Works with any type of files.
    """
    full_path = pathlib.Path(local_dir_path) / str(file.filename)
    if full_path.exists():
        print(f"A file with the name {file.filename} already exists at: {full_path}.")
    else:
        # write the file to path
        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # Reset the file's position to the beginning
        file.file.seek(0)
    return str(full_path)


def create_sections(
    page_map: List[Tuple[int, int, str]],
    doc_max_section_length: int,
    doc_sentence_search_limit: int,
    doc_section_overlap: int,
    file_url: str,
    filename: Optional[str],
) -> Iterator:
    """Extract content and text from a page_map, creates a generator.
    Args:
        page_map (List[Tuple[int, int, str]]): a list of pages to be read,
            e.g: [(0, 0, "John is a great person"),
                  (1, 22, "He is always punctual.")]
            Whereas the first int represents the page number, 2nd int represents
            the accummulated characters prior to the start of the text
        doc_max_section_length (int, optional): The maximum length of a section in
            tokens. Defaults to 1000.
        doc_sentence_search_limit (int, optional): The maximum number of
            sentences to search. Defaults to 100.
        doc_section_overlap (int, optional): The number of overlapping tokens
            between sections. Defaults to 100.
        file_url (str): the url to retrieve the copy of the file
        filename (Optional[str]): name of the uploaded file


    Returns:
        section (generator): a generator with text content for indexing.
    """

    def _split_text(page_map):
        SENTENCE_ENDINGS = [".", "!", "?"]
        WORDS_BREAKS = [",", ";", ":", " ", "(", ")", "[", "]", "{", "}", "\t", "\n"]

        def find_page(offset):
            mapsize = len(page_map)
            for i in range(mapsize - 1):
                if offset >= page_map[i][1] and offset < page_map[i + 1][1]:
                    return i
            return mapsize - 1

        all_text = "".join(p[2] for p in page_map)
        length = len(all_text)
        start = 0
        end = length
        while start + doc_section_overlap < length:
            last_word = -1
            end = start + doc_max_section_length

            if end > length:
                end = length
            else:
                # Try to find the end of the sentence
                while (
                    end < length
                    and (end - start - doc_max_section_length)
                    < doc_sentence_search_limit
                    and all_text[end] not in SENTENCE_ENDINGS
                ):
                    if all_text[end] in WORDS_BREAKS:
                        last_word = end
                    end += 1
                if (
                    end < length
                    and all_text[end] not in SENTENCE_ENDINGS
                    and last_word > 0
                ):
                    end = last_word  # Fall back to at least keeping a whole word
            if end < length:
                end += 1

            # Try to find the start of the sentence or at least a whole word boundary
            last_word = -1
            while (
                start > 0
                and start > end - doc_max_section_length - 2 * doc_sentence_search_limit
                and all_text[start] not in SENTENCE_ENDINGS
            ):
                if all_text[start] in WORDS_BREAKS:
                    last_word = start
                start -= 1
            if all_text[start] not in SENTENCE_ENDINGS and last_word > 0:
                start = last_word
            if start > 0:
                start += 1

            section_text = all_text[start:end]
            yield (section_text, find_page(start))

            last_table_start = section_text.rfind("<table")
            if (
                last_table_start > 2 * doc_sentence_search_limit
                and last_table_start > section_text.rfind("</table")
            ):
                start = min(end - doc_section_overlap, start + last_table_start)
            else:
                start = end - doc_section_overlap

        if start + doc_section_overlap < end:
            yield (all_text[start:end], find_page(start))

    # create session, enumerating the above function
    # page num + 1 as pdf file page numbers are 1 base
    for i, (section, pagenum) in enumerate(_split_text(page_map)):
        yield {
            "id": re.sub("[^0-9a-zA-Z_-]", "_", f"{filename}-{i}"),
            "search_key": section,
            "content": section,
            "file_url": f"{file_url}#page={pagenum + 1}",
        }


def create_section_non_slice(
    text: str, filename: Optional[str], file_url: str
) -> Iterator:
    """Create a generator from non-slicable documents or user preference
    Suitable for uploading the raw text of a file without the need to dissect
    or section it.

    Args:
        text(str): text to be uploaded as content
        file_url (str): the url to retrieve the copy of the file
        filename(Optional[str]): filename of the UploadFile
    Returns:
        section (Iterator): a generator with text content for indexing.
    """
    yield {
        "id": re.sub("[^0-9a-zA-Z_-]", "_", f"{filename}"),
        "search_key": text,
        "content": text,
        "file_url": file_url,
    }


def create_section_csv(
    json: List[Dict[str, str]],
    file_url: str,
    search_key: str,
    csv_out_template: str,
    filename: Optional[str],
) -> Iterator:
    """Create a generator out of each row of a json file
        The generator will then be passed to the datasource to be indexed

    Args:
        json (List[Dict[str, str]]): a json representation of a csv
            eg: [{"issue": "cannot start computer", "solution": "restart"},
                 {"issue": "black screen", "solution": "turn on computer"}]
        file_url (str): the url to retrieve the copy of the file
        search_key (str): the string value used to retrieve the content
        csv_out_template (str): the content to be retrieved
        filename (str): the filename of the UploadFile
    """
    for i, d in enumerate(json):
        yield {
            "id": re.sub("[^0-9a-zA-Z_-]", "_", f"{filename}-{i}"),
            "search_key": d[search_key],
            "content": csv_out_template.format(**d),
            "file_url": file_url,
        }


def create_upload_file(
    datasource: str, file_name: str, base_path: str = DATASOURCE_PATH
):
    """
    Create an UploadFile object from a specified file path.
    """

    # [Implement UploadFile or use an appropriate file-like object]
    # For the purpose of this example, assume UploadFile is a simple wrapper
    class UploadFile:
        def __init__(self, filename, file):
            self.filename = filename
            self.file = file

    ds_file_dir = pathlib.Path(base_path) / datasource / file_name
    file_like = open(ds_file_dir, mode="rb")
    return UploadFile(filename=file_name, file=file_like)


def main(
    files: List,
    existing_file_names: List[str],
    datasource_name: str,
    config: DatasourceConfig,
) -> str:
    """Upload files and create datasources from files."""
    # Append local files to the files list
    files += [
        create_upload_file(datasource=datasource_name, file_name=file_name)
        for file_name in existing_file_names
    ]

    # Ensure files are not empty
    if not files:
        raise Exception("No files uploaded or local files selected.")

    for file in files:
        if not isinstance(file.filename, str):
            raise Exception("Filename not found")
        file.filename = file.filename.replace(" ", "_").lstrip("_").rstrip("_")

    # Check for duplication in filenames
    file_names = [f.filename for f in files]
    if len(file_names) != len(set(file_names)):
        raise Exception("Duplicate filenames detected. Please use unique filenames.")

    # Process files and create sections
    section_generators: List[Iterator] = []

    for file in files:
        file_url = os.path.join(datasource_name, file.filename)
        file_type = os.path.splitext(file.filename)[1].lower()

        extraction_method = {
            "AzureFormRecognizer": pdf_to_page_map_azure,
            "PyPDF": pdf_to_page_map_pypdf,
            "PyMuPDF": pdf_to_page_map_pymupdf,
        }

        if file_type in slicable and config.doc_slice:
            # Convert to PDF if necessary
            if file_type in libreoffice_convertable:
                file = doc_to_pdf(file)
                file_type = ".pdf"

            # Extract page map
            page_map = extraction_method[PDF_PAGEMAP_EXTRACTION_METHOD](file)

            # Create sections
            sections = create_sections(
                filename=file.filename,
                page_map=page_map,
                doc_max_section_length=config.doc_max_section_length,
                doc_sentence_search_limit=config.doc_sentence_search_limit,
                doc_section_overlap=config.doc_section_overlap,
                file_url=file_url,
            )
        elif file_type == ".csv":
            # Extract CSV data
            json_data = extract_csv(file, config.csv_header)
            sections = create_section_csv(
                filename=file.filename,
                json_data=json_data,
                file_url=file_url,
                search_key=config.csv_key if config.csv_header else "k0",
                csv_out_template=config.csv_out_template,
            )
        else:
            # Handle non-slicable documents or when slicing is disabled
            if file_type == ".docx":
                text = read_docx(file)
            elif file_type == ".pptx":
                text = read_pptx(file)
            elif file_type in libreoffice_convertable:
                file = doc_to_pdf(file)
                page_map = extraction_method[PDF_PAGEMAP_EXTRACTION_METHOD](file)
                text = "".join([page[2] for page in page_map])
            elif file_type == ".pdf":
                page_map = extraction_method[PDF_PAGEMAP_EXTRACTION_METHOD](file)
                text = "".join([page[2] for page in page_map])
            elif file_type in [".txt", ".md"]:
                file.file.seek(0)
                text = file.file.read().decode("utf-8")
            else:
                raise Exception(f"Incompatible file type: {file_type}")

            sections = create_section_non_slice(
                text=text, filename=file.filename, file_url=file_url
            )

        section_generators.append(sections)

    # Combine all section generators
    combined_sections = itertools.chain(*section_generators)

    # Create index using FAISSDS
    local_dir_path = create_local_dir(datasource_name)

    # create FAISS index
    FAISSDS.create(section=combined_sections, index_name=datasource_name)

    # Save local copies of files
    for f in files:
        f.file.seek(0)
        save_local_copy(f, local_dir_path)

    return datasource_name
