"""
Replaces Celery. Runs the analysis task directly in FastAPI's background task system.
No separate worker process needed. No Redis queue needed.
"""
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from models.report import Report, Category, Issue, GoodPoint
from core.config import settings
from core.screenshot import take_screenshot
from analyzers.runner import run_all_analyzers
from ai.generate_report import generate_ai_report

_sync_url = (
    settings.DATABASE_URL
    .replace("+asyncpg", "+psycopg2")
    .replace("ssl=require", "sslmode=require")
)
sync_engine = create_engine(_sync_url)
SyncSession  = sessionmaker(bind=sync_engine)


def run_analysis(url: str, report_id: str) -> None:
    session = SyncSession()

    try:
        session.execute(update(Report).where(Report.id == report_id).values(status="processing"))
        session.commit()

        screenshot_url = take_screenshot(url)
        raw_findings   = run_all_analyzers(url)
        ai_report      = generate_ai_report(url, raw_findings)

        scores        = [cat["score"] for cat in ai_report["categories"].values()]
        overall_score = round(sum(scores) / len(scores))

        # ─── Save categories + issues FIRST, then mark done ───────────────────
        # Bug fix: status must be set to "done" ONLY after all data is saved.
        # If "done" is written first, the frontend fetches before categories exist.

        session.execute(
            update(Report).where(Report.id == report_id).values(
                screenshot_url=screenshot_url,
                overall_score=overall_score,
                overall_summary=ai_report.get("overall_summary"),
                status="processing",          # still processing while saving categories
            )
        )
        session.commit()

        for cat_name, cat_data in ai_report["categories"].items():
            category = Category(
                report_id=report_id,
                name=cat_name,
                score=cat_data["score"],
                summary=cat_data["summary"],
            )
            session.add(category)
            session.flush()

            for issue in cat_data.get("issues", []):
                session.add(Issue(
                    category_id=category.id,
                    severity=issue.get("severity", "minor"),
                    title=issue.get("title", ""),
                    description=issue.get("description", ""),
                    how_to_fix=issue.get("how_to_fix", ""),
                ))
            for text in cat_data.get("what_is_good", []):
                session.add(GoodPoint(category_id=category.id, text=text))

        session.commit()

        # ─── Only NOW mark as done ─────────────────────────────────────────────
        session.execute(update(Report).where(Report.id == report_id).values(status="done"))
        session.commit()

    except Exception as exc:
        try:
            session.execute(update(Report).where(Report.id == report_id).values(status="failed"))
            session.commit()
        except Exception:
            pass
        raise exc
    finally:
        session.close()
