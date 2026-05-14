from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.report import Report, Category
from core.config import settings
from ai.client import ai_client, AI_MODEL
import json

router = APIRouter()

_sync_url = (
    settings.DATABASE_URL
    .replace("+asyncpg", "+psycopg2")
    .replace("ssl=require", "sslmode=require")
)
sync_engine = create_engine(_sync_url)
SyncSession  = sessionmaker(bind=sync_engine)


class ChatRequest(BaseModel):
    message: str


def _build_chat_context(report_id: str) -> str:
    session = SyncSession()
    try:
        from sqlalchemy.orm import joinedload
        report = session.query(Report).options(
            joinedload(Report.categories).joinedload(Category.issues)
        ).filter(Report.id == report_id).first()

        if not report:
            return "No report found."

        lines = [
            f"Website: {report.url}",
            f"Overall score: {report.overall_score}/100",
            f"Summary: {report.overall_summary or 'N/A'}",
            "",
            "Category scores and issues:",
        ]
        for cat in report.categories:
            lines.append(f"\n{cat.name.upper()} — Score: {cat.score}/100")
            lines.append(f"  Summary: {cat.summary}")
            for issue in cat.issues[:4]:
                lines.append(f"  [{issue.severity}] {issue.title}: {issue.description[:100]}")
        return "\n".join(lines)
    finally:
        session.close()


@router.post("/chat/{report_id}")
def chat(report_id: str, request: ChatRequest):
    context = _build_chat_context(report_id)

    system_prompt = f"""You are an expert web performance and development consultant.
You have just completed an audit of a website. Here are the audit results:

{context}

Answer the user's questions about this specific website and its issues.
Be concise, practical, and technical. Use bullet points for steps.
Focus on actionable advice specific to this site's issues."""

    def stream():
        try:
            response = ai_client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": request.message},
                ],
                temperature=0.4,
                max_tokens=800,
                stream=True,
            )
            for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield f"data: {json.dumps({'text': delta})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
