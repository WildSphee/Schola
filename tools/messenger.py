import re

from datasources.faiss_ds import FAISSDS
from db.db import db


async def schola_reply(
    update, message, reply_markup=None, parse_mode="HTML", *args, **kwargs
) -> None:
    """Create a telegram text reply, given formatting option"""
    try:
        # remove code blocks around
        code_fence_pattern = r"^```(?:json)?\s*([\s\S]*?)\s*```$"
        match = re.match(code_fence_pattern, message)
        if match:
            message = match.group(1).strip()
        else:
            message = message.strip("`")

        # send text reply
        await update.message.reply_text(
            message, reply_markup=reply_markup, parse_mode=parse_mode, *args, **kwargs
        )
        return
    except Exception as e:
        await update.message.reply_text(f"Exception occured: {e}\n:(")
        return


def retrieve_from_subject(query: str, subject: str, topk: int = 5) -> str:
    """search if given subject has a datasource, and return formatting search results

    Return:
        str: the retrieved docs if hit, "" if not hit / no subject info / doesn't use datasource
    """

    info = db.get_subject_info_by_subject_name(subject)

    if not info:
        return ""

    ds: bool = dict(info).get("use_datasource", False)

    if not ds:
        return ""

    faiss_ds = FAISSDS(index_name=subject)
    hits = faiss_ds.search_request(query, topk=topk)
    res = ""
    for i, result in enumerate(hits, start=1):
        res += f"<b>Result {i}:</b>"
        res += f"Content: {result['content']}"
        res += f"File URL: {result['file_url']}"
        res += f"<i>Score: {result['score']} </i>"
        res += "<hr class=\"solid\">"

    return res
