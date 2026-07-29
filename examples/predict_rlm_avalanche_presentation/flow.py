import csv
import os
from pathlib import Path

import avalanche as ava

from .schema import (
    CrmProductSignal,
    CrmProductSignalBatch,
    Feedback,
    FeedbackCorpus,
    RiskReport,
    ThemeReport,
)
from .signature import DetectRisks, ExtractThemes
from .skills import csv_analysis_skill
from .util import push_to_crm

MODEL = os.getenv("PRESENTATION_MODEL", "openai/gpt-5.6-terra")
SUB_MODEL = os.getenv("PRESENTATION_SUB_MODEL", "gemini/gemini-3.5-flash")
FEEDBACK_PATH = Path(__file__).with_name("feedback.csv")


@ava.source
def load_feedback_csv() -> FeedbackCorpus:
    with FEEDBACK_PATH.open(encoding="utf-8", newline="") as feedback_file:
        reader = csv.DictReader(feedback_file)
        return FeedbackCorpus(
            feedback=[
                Feedback(
                    feedback_id=row["id"],
                    text=row["text"],
                    product_area=row["product_area"],
                    customer_segment=row["customer_segment"],
                    channel=row["channel"],
                    sentiment=row["sentiment"],
                )
                for row in reader
            ]
        )


@ava.agent_step(
    ExtractThemes,
    lm=MODEL,
    sub_lm=SUB_MODEL,
    skills=[csv_analysis_skill],
)
async def extract_themes(corpus: FeedbackCorpus, *, agent: ava.Agent) -> ThemeReport:
    return (await agent(corpus=corpus)).report


@ava.agent_step(
    DetectRisks,
    lm=MODEL,
    sub_lm=SUB_MODEL,
)
async def detect_risks(corpus: FeedbackCorpus, *, agent: ava.Agent) -> RiskReport:
    return (await agent(corpus=corpus)).report


@ava.step
def compose_crm_product_signals(
    themes: ThemeReport,
    risks: RiskReport,
) -> CrmProductSignalBatch:
    return CrmProductSignalBatch(
        signals=[
            CrmProductSignal(
                kind="risk",
                headline=risk.issue,
                evidence=risk.evidence,
            )
            for risk in risks.risks
        ]
        + [
            CrmProductSignal(
                kind="theme",
                headline=theme.name,
                evidence=theme.evidence,
            )
            for theme in themes.themes
        ]
    )


@ava.dest
def publish_local_crm_import(signals: CrmProductSignalBatch) -> None:
    for item in signals.signals:
        push_to_crm(item)
    print(signals.model_dump())


@ava.workflow
def feedback_triage():
    return (
        load_feedback_csv()
        >> (extract_themes() & detect_risks())
        >> compose_crm_product_signals()
        >> publish_local_crm_import()
    )
