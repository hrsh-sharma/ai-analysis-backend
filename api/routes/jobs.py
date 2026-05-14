from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from models.report import Report
from models.schemas import JobStatusSchema

router = APIRouter()


@router.get("/job/{report_id}", response_model=JobStatusSchema)
async def get_job_status(report_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return JobStatusSchema(
        report_id=report.id,
        status=report.status,
        done=report.status == "done",
        failed=report.status == "failed",
    )
