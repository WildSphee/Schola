from typing import Dict, List

from openai import OpenAI

client = OpenAI()


def call_openai(
    history: List[Dict[str, str]],
    query: str,
) -> str:
    """
    Call the OpenAI API to generate a response based on chat history and a user query.

    Args:
        history (List[Dict[str, str]]): The conversation history.
        query (str): The user's query.

    Returns:
        str: The generated response from OpenAI.
    """

    messages = history + [
        {"role": "system", "content": query},
    ]

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )

    res: str = completion.choices[0].message.content
    print(f"LLM output: \n {res}")
    return res
