import re

from telegram import Update

from datasources.faiss_ds import FAISSDS
from db.db import db
import os


async def schola_reply(
    update: Update,
    message: str,
    reply_markup: bool = None,
    parse_mode: str = "HTML",
    *args,
    **kwargs,
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

        # turn **text** markdowns into HTML format <b>text</b>
        message = re.sub(r"\*\*([^\*]{1,23}?)\*\*", r"<b>\1</b>", message)

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

    DS_RETRIEVAL_URL_PREFIX = os.getenv("DS_RETRIEVAL_URL_PREFIX")
    if not DS_RETRIEVAL_URL_PREFIX:
        raise Exception("DS retrieval URL Prefix not set.")

    info = db.get_subject_info_by_subject_name(subject)

    # check if the subject the user enrolled to has an entry in the DB, if not return ""
    if not info:
        return ""

    ds: bool = dict(info).get("use_datasource", False)

    # the subject has an entry, check if it uses any datasource files, if not return ""
    if not ds:
        return ""

    # perform a search on its datasource, and return the search results.
    faiss_ds = FAISSDS(index_name=subject)
    hits = faiss_ds.search_request(query, topk=topk)
    res = ""
    for i, result in enumerate(hits, start=1):
        res += f"<b>Result {i}:</b>"
        res += f"Content: {result['content']}"
        res += f"File URL: {os.path.join(DS_RETRIEVAL_URL_PREFIX, result['file_url'])}"
        res += f"<i>Score: {result['score']} </i>"
        res += '<hr class="solid">'

    return res
