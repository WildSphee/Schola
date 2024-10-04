from datasources.ingest import DatasourceConfig, create_upload_file
from datasources.ingest import main as ingest_main

# Define the datasource name
datasource_name = "my_local_datasource"

existing_file_names = []  # e.g., ["existing_file.pdf"]

# List of local files to process
local_files = [
    "documents/file1.pdf",
    "documents/file2.docx",
]  # Replace with your file paths

# Create UploadFile-like objects for the local files
files = [
    create_upload_file(datasource=datasource_name, file_name=file_name)
    for file_name in local_files
]

# Define the configuration for processing
config = DatasourceConfig(
    csv_header=True,
    csv_key="issue",
    csv_out_template="Issue:{issue}\n\nCause:{cause}\n\nSolution:{solution}",
    doc_max_section_length=1000,
    doc_section_overlap=100,
    doc_sentence_search_limit=100,
    doc_slice=True,
)

try:
    # Call the main function from ingest.py to process the files
    datasource_created = ingest_main(
        files=files,
        existing_file_names=existing_file_names,
        datasource_name=datasource_name,
        config=config,
    )
    print(f"Datasource '{datasource_created}' created successfully.")
except Exception as e:
    print(f"An error occurred: {e}")
