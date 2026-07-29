from typing import Literal

from pydantic import BaseModel


class Feedback(BaseModel):
    feedback_id: str
    text: str


class FeedbackCorpus(BaseModel):
    feedback: list[Feedback]


class Theme(BaseModel):
    name: str
    evidence: list[str]


class ThemeReport(BaseModel):
    themes: list[Theme]


class Risk(BaseModel):
    issue: str
    severity: Literal["low", "medium", "high"]
    evidence: list[str]


class RiskReport(BaseModel):
    risks: list[Risk]


class CrmProductSignal(BaseModel):
    kind: Literal["risk", "theme"]
    headline: str
    evidence: list[str]


class CrmProductSignalBatch(BaseModel):
    signals: list[CrmProductSignal]


class CrmTask(BaseModel):
    external_id: str
    title: str


class CrmSyncResult(BaseModel):
    created: list[CrmTask]
    artifact_path: str
