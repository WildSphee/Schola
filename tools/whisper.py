import openai


def transcribe_voice(file_path: str) -> str:
    """
    Transcribe the voice file to text using OpenAI's Whisper API.
    Able to automatically detect language and output string accordingly.

    Args:
        file_path (str): The path to the voice file.

    Returns:
        str: The transcribed text.
    """
    client = openai.OpenAI()

    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )

    return transcript.text
