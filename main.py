from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from api.routes import analyze, jobs, reports, chat, techstack

app = FastAPI(
    title="AI Website Reviewer",
    description="Analyze any website and get an AI-powered audit report.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Open for frontend on any domain (Vercel, localhost, etc.)
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve screenshots
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(analyze.router,    prefix="/api")
app.include_router(jobs.router,       prefix="/api")
app.include_router(reports.router,    prefix="/api")
app.include_router(chat.router,       prefix="/api")
app.include_router(techstack.router,  prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-website-reviewer"}
