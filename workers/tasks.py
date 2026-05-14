from workers.celery_app import celery_app
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from models.report import Report, Category, Issue, GoodPoint
from core.config import settings

# Sync engine for Celery (Celery does not support async natively)
# asyncpg uses ssl=require, psycopg2 uses sslmode=require
_sync_url = (
    settings.DATABASE_URL
    .replace("+asyncpg", "+psycopg2")
    .replace("ssl=require", "sslmode=require")
)
sync_engine = create_engine(_sync_url)
SyncSession = sessionmaker(bind=sync_engine)


@celery_app.task(bind=True, max_retries=0)
def analyze_website(self, url: str, report_id: str):
    session = SyncSession()

    try:
        # Mark as processing
        session.execute(
            update(Report).where(Report.id == report_id).values(status="processing")
        )
        session.commit()

        # Import here to avoid circular imports at module load
        from core.screenshot import take_screenshot
        from analyzers.runner import run_all_analyzers
        from ai.generate_report import generate_ai_report

        screenshot_url = take_screenshot(url)
        raw_findings = run_all_analyzers(url)
        ai_report = generate_ai_report(url, raw_findings)

        scores = [cat["score"] for cat in ai_report["categories"].values()]
        overall_score = round(sum(scores) / len(scores))

        session.execute(
            update(Report)
            .where(Report.id == report_id)
            .values(
                screenshot_url=screenshot_url,
                overall_score=overall_score,
                overall_summary=ai_report.get("overall_summary"),
                status="done",
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

            for issue_data in cat_data.get("issues", []):
                session.add(Issue(
                    category_id=category.id,
                    severity=issue_data.get("severity", "minor"),
                    title=issue_data.get("title", ""),
                    description=issue_data.get("description", ""),
                    how_to_fix=issue_data.get("how_to_fix", ""),
                ))

            for good_text in cat_data.get("what_is_good", []):
                session.add(GoodPoint(category_id=category.id, text=good_text))

        session.commit()

    except Exception as exc:
        session.execute(
            update(Report).where(Report.id == report_id).values(status="failed")
        )
        session.commit()
        raise exc

    finally:
        session.close()
