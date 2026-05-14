from fastapi import APIRouter, HTTPException
from analyzers.techstack import detect_tech_stack

router = APIRouter()


@router.get("/tech-stack")
def get_tech_stack(url: str):
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
    stack = detect_tech_stack(url)
    return {"url": url, "technologies": stack}
