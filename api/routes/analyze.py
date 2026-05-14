from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.report import Report
from models.schemas import AnalyzeRequest
from workers.background import run_analysis

router = APIRouter()


@router.post("/analyze", status_code=202)
async def analyze(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    url = request.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    try:
        report = Report(url=url, status="pending")
        db.add(report)
        await db.commit()
        await db.refresh(report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Run analysis in FastAPI's background thread pool — no Celery worker needed
    background_tasks.add_task(run_analysis, url, report.id)

    return {"report_id": report.id, "status": "pending"}
