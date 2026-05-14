from pydantic import BaseModel
from datetime import datetime


class AnalyzeRequest(BaseModel):
    url: str


class IssueSchema(BaseModel):
    id: str
    severity: str
    title: str
    description: str
    how_to_fix: str

    model_config = {"from_attributes": True}


class GoodPointSchema(BaseModel):
    id: str
    text: str

    model_config = {"from_attributes": True}


class CategorySchema(BaseModel):
    id: str
    name: str
    score: int
    summary: str
    issues: list[IssueSchema] = []
    good_points: list[GoodPointSchema] = []

    model_config = {"from_attributes": True}


class ReportSchema(BaseModel):
    id: str
    url: str
    screenshot_url: str | None
    overall_score: int
    overall_summary: str | None
    status: str
    created_at: datetime
    categories: list[CategorySchema] = []

    model_config = {"from_attributes": True}


class JobStatusSchema(BaseModel):
    report_id: str
    status: str
    done: bool
    failed: bool
