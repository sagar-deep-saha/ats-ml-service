from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile, os, docx, pdfplumber, re
import spacy

app = FastAPI()

# Allow communication with specific front-end origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://ats.sagar.ltd"],  # Update with your front-end URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

nlp = spacy.load("en_core_web_sm")

# Response model for analysis results
class AnalysisResult(BaseModel):
    professionalityScore: int
    careerRecommendations: list[dict]
    strengthPoints: list[str]
    improvementPoints: list[str]
    skillsIdentified: list[str]

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def is_probably_resume(text):
    resume_keywords = [
        "education", "experience", "skills", "project", "summary", "contact",
        "certification", "objective", "profile", "work history", "employment",
        "professional", "responsibilities", "achievements", "references"
    ]
    found = sum(1 for kw in resume_keywords if re.search(rf'\b{kw}\b', text, re.IGNORECASE))
    has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
    has_phone = bool(re.search(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text))
    return (found >= 2) and (has_email or has_phone)

def analyze_resume(text):
    # Example: extract nouns as skills
    doc = nlp(text)
    skills = list({token.text.lower() for token in doc if token.pos_ == "NOUN"})
    return {
        "professionalityScore": 80,
        "careerRecommendations": [{"field": "Software Engineering", "score": 90}],
        "strengthPoints": ["Good structure"],
        "improvementPoints": ["Add more quantifiable achievements"],
        "skillsIdentified": skills[:10],
    }

@app.post("/analyze", response_model=AnalysisResult)
async def analyze(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        if suffix in [".docx"]:
            text = extract_text_from_docx(tmp_path)
        elif suffix in [".pdf"]:
            text = extract_text_from_pdf(tmp_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        if not is_probably_resume(text):
            raise HTTPException(status_code=400, detail="The uploaded file does not appear to be a resume.")

        result = analyze_resume(text)
        return result
    finally:
        os.unlink(tmp_path)