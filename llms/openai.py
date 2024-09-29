from typing import Dict, List

from openai import OpenAI
from telegram import User


def call_openai(
    history: List[Dict[str, str]], user: User, query: str,
) -> str:
    client = OpenAI()

    messages = history + [
        {
            "role": "system",
            "content": query
        },
    ]

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )

    res: str = completion.choices[0].message.content
    return res
