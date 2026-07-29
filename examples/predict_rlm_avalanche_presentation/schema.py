from typing import Literal

from pydantic import BaseModel


class Feedback(BaseModel):
    feedback_id: str
    text: str
    product_area: str
    customer_segment: Literal["enterprise", "mid_market", "small_business", "startup"]
    channel: Literal[
        "community",
        "customer_call",
        "email",
        "in_app",
        "support_ticket",
        "survey",
    ]
    sentiment: Literal["negative", "neutral", "positive"]


class FeedbackCorpus(BaseModel):
    feedback: list[Feedback]


class Theme(BaseModel):
    name: str
    evidence: list[str]
    market_counts: dict[str, int]


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
