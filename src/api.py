"""
API layer. Turns the CLI agent into a real service with auto-generated
docs (OpenAPI/Swagger at /docs) — this is the "provide technical support
for implementing and improving AI-enabled institutional solutions" piece:
a deployable, documented, testable service, not just a script.

Run with: uvicorn src.api:app --reload
Then open http://127.0.0.1:8000/docs
"""
import sys
import os

sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent import answer_question
from materials import draft_and_review
from freshness_check import check as freshness_check
from audit_log import failure_rate

app = FastAPI(
    title="Academic Process Copilot API",
    description="AI-assisted institutional process guidance and academic "
                 "material drafting, backed by a verified database.",
    version="1.0.0",
)


class QuestionRequest(BaseModel):
    question: str
    role: str = "student"


class QuestionResponse(BaseModel):
    answer: str
    prompt_used: str


class MaterialRequest(BaseModel):
    topic: str
    curriculum_requirements: str


class MaterialResponse(BaseModel):
    draft: str
    qa_passed: bool
    qa_notes: list[str]


@app.get("/health")
def health():
    """Basic liveness check plus a rolling QA failure-rate signal —
    what a real ops dashboard would poll."""
    return {"status": "ok", "recent_qa_failure_rate": failure_rate()}


@app.post("/ask", response_model=QuestionResponse)
def ask(req: QuestionRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")
    answer, prompt = answer_question(req.question, role=req.role)
    return {"answer": answer, "prompt_used": prompt}


@app.post("/materials/draft", response_model=MaterialResponse)
def draft_material(req: MaterialRequest):
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="topic must not be empty")
    draft, qa_report, _ = draft_and_review(req.topic, req.curriculum_requirements)
    return {"draft": draft, "qa_passed": qa_report.passed, "qa_notes": qa_report.notes}


@app.get("/admin/freshness")
def freshness():
    """Surfaces stale FAQ rows so a real institution knows what needs
    re-verification — the automated half of the QA process in
    docs/QA_PROCESS.md; the sign-off itself still has to be a human."""
    stale = freshness_check()
    return {"stale_count": len(stale), "rows": stale}
