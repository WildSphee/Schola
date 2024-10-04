# this script creates a text reply
import re


async def schola_reply(
    update, message, reply_markup=None, parse_mode="HTML", *args, **kwargs
) -> None:
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
