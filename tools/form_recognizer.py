import os

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

AZURE_FORM_RECOGNIZER_ENDPOINT = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
AZURE_FORM_RECOGNIZER_KEY = os.getenv("AZURE_FORM_RECOGNIZER_KEY")


def analyze_image(image_path: str) -> str:
    """
    Analyze an image using Azure Form Recognizer and return the extracted text.

    Args:
        image_path (str): The file path to the image to be analyzed.

    Returns:
        str: The extracted text from the image.

    Raises:
        ValueError: If the Azure Form Recognizer endpoint or key is not set.
    """

    if not AZURE_FORM_RECOGNIZER_ENDPOINT or not AZURE_FORM_RECOGNIZER_KEY:
        raise ValueError(
            "Azure Form Recognizer endpoint and key must be set as environment variables."
        )

    client = DocumentAnalysisClient(
        endpoint=AZURE_FORM_RECOGNIZER_ENDPOINT,
        credential=AzureKeyCredential(AZURE_FORM_RECOGNIZER_KEY),
    )

    with open(image_path, "rb") as image:
        poller = client.begin_analyze_document("prebuilt-read", image)
        result = poller.result()

    extracted_text = ""
    for page in result.pages:
        for line in page.lines:
            extracted_text += line.content + "\n"

    return extracted_text
