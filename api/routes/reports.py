from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from core.database import get_db
from models.report import Report, Category
from models.schemas import ReportSchema

router = APIRouter()


@router.get("/report/{report_id}", response_model=ReportSchema)
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report)
        .where(Report.id == report_id)
        .options(
            selectinload(Report.categories).selectinload(Category.issues),
            selectinload(Report.categories).selectinload(Category.good_points),
        )
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return report
