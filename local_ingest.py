from typing import List

from datasources.ingest import DatasourceConfig, create_upload_file
from datasources.ingest import main as ingest_main

# Define the datasource name
datasource_name = "my_local_datasource"

existing_file_names: List[str] = []

# List of local files to process
local_files = [
    r"A Guide to the Project Management Body of Knowledge PMBOK Project Management Institute 7 2021 Project Management Institute.pdf",
]

files = [
    create_upload_file(datasource=datasource_name, file_name=file_name)
    for file_name in local_files
]

config = DatasourceConfig(
    csv_header=True,
    csv_key="issue",
    csv_out_template="Issue:{issue}\n\nCause:{cause}\n\nSolution:{solution}",
    doc_max_section_length=1000,
    doc_section_overlap=100,
    doc_sentence_search_limit=100,
    doc_slice=True,
)
datasource_created = ingest_main(
    files=files,
    existing_file_names=existing_file_names,
    datasource_name=datasource_name,
    config=config,
)
print(f"Datasource '{datasource_created}' created successfully.")
