import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/view-pdf/{file_path:path}")
async def view_pdf(file_path: str):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found :(")

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"},
    )
