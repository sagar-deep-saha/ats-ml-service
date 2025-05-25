from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import tempfile, os, httpx

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ATS_API_URL = "https://ats.sagar.ltd/analyze"

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[-1].lower()
    if suffix not in [".docx", ".pdf"]:
        return {"error": "Unsupported file type"}

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # Send the file to the external ATS service
        with open(tmp_path, "rb") as f:
            files = {"file": (file.filename, f, file.content_type)}
            async with httpx.AsyncClient() as client:
                response = await client.post(ATS_API_URL, files=files)

        if response.status_code != 200:
            return {"error": "Failed to analyze the resume using ATS service."}

        # Return the response from the ATS service
        return response.json()
    finally:
        os.unlink(tmp_path)
