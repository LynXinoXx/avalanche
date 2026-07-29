# ruff: noqa: E501, F821, F841, N803, N806

import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import ast
    import csv
    import json
    import os
    from pathlib import Path
    from typing import Literal

    import marimo as mo
    from dotenv import load_dotenv
    from pydantic import BaseModel
    from skills import csv_analysis_skill

    import avalanche as ava

    return (
        BaseModel,
        Literal,
        Path,
        ast,
        ava,
        csv,
        csv_analysis_skill,
        json,
        load_dotenv,
        mo,
        os,
    )


@app.cell(hide_code=True)
def _(Path, ast, load_dotenv, os):
    load_dotenv()

    MODEL = os.getenv("PRESENTATION_MODEL", "openai/gpt-5.6-terra")
    SUB_MODEL = os.getenv("PRESENTATION_SUB_MODEL", "gemini/gemini-3.5-flash")
    FEEDBACK_PATH = Path(__file__).with_name("feedback.csv")
    SIGNALS_PATH = Path("presentation_artifacts") / "crm_product_signals.json"

    def source_code(file_name: str, *symbol_names: str) -> str:
        source = Path(__file__).with_name(file_name).read_text(encoding="utf-8")
        source_lines = source.splitlines()
        tree = ast.parse(source)
        nodes = {}
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                nodes[node.name] = node
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        nodes[target.id] = node
        blocks = []
        for symbol_name in symbol_names:
            node = nodes[symbol_name]
            decorators = (
                node.decorator_list
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                else []
            )
            first_line = min([node.lineno, *(item.lineno for item in decorators)])
            blocks.append("\n".join(source_lines[first_line - 1 : node.end_lineno]))
        return "\n\n\n".join(blocks)

    return FEEDBACK_PATH, MODEL, SIGNALS_PATH, SUB_MODEL, source_code


@app.cell(hide_code=True)
def _(mo):
    mo.vstack(
        (
            mo.md("# From customer feedback to product work"),
            mo.md(
                "A product team receives customer feedback faster than it can review it. "
                "Important requests repeat across accounts, retention risks are buried in "
                "individual comments, and neither becomes actionable product work reliably."
            ),
            mo.callout(
                "Given a bundled CSV of customer feedback, we want recurring product themes "
                "and material customer risks turned into reviewable CRM tasks—with the "
                "supporting feedback preserved as evidence.",
                kind="info",
            ),
        )
    )
    return


@app.cell(hide_code=True)
def _(FEEDBACK_PATH, csv, mo):
    with FEEDBACK_PATH.open(encoding="utf-8", newline="") as feedback_file:
        feedback_rows = list(csv.DictReader(feedback_file))

    mo.vstack(
        (
            mo.md("## 1. Start with the real input"),
            mo.md(
                "The example ships with this feedback. At this point there are no nodes, "
                "decorators, or agents—only the source material and the outcome we need."
            ),
            mo.ui.table(feedback_rows),
        )
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.vstack(
        (
            mo.md("## 2. Describe the work before the implementation"),
            mo.md(
                "A useful workflow starts as a set of logical responsibilities. Each one "
                "has a result we can name and inspect; none is a framework primitive yet."
            ),
            mo.md(
                """
                1. **Load the feedback** into one validated corpus.
                2. **Find recurring product themes** and retain their evidence.
                3. **Identify customer risks** and grade their severity.
                4. **Combine both analyses** into product signals.
                5. **Publish the signals** as CRM tasks.
                """
            ),
        )
    )
    return


@app.cell(hide_code=True)
def simple_live_rlm(mo):
    mo.vstack(
        (
            mo.md("### Dependencies come from the data"),
            mo.md(
                "Theme extraction and risk detection both consume the same corpus. Neither "
                "needs the other's result, so they form independent branches that join "
                "before signals can be composed."
            ),
            mo.md(
                r"""
                ```text
                                         ┌─ Find recurring themes ─┐
                Load customer feedback ──┤                         ├─ Combine signals ── Publish CRM tasks
                                         └─ Identify risks ────────┘
                ```
                """
            ),
        )
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.vstack(
        (
            mo.md("## 3. Zoom in: find recurring product themes"),
            mo.md(
                "Loading, combining, and publishing all have known procedures. Finding "
                "themes is different: the workflow must compare comments, decide which "
                "needs genuinely recur, avoid promoting one-off complaints, and preserve "
                "the evidence behind every conclusion."
            ),
            mo.callout(
                "This is one logical agent task. Searching, grouping, comparing, and "
                "validating are parts of its internal strategy—not separate workflow nodes.",
                kind="warn",
            ),
        )
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Define the task

    **Contract**: What should the agent's contract be? What does it receive, what should it do with it and how, and what should it return?

    | Boundary | Contract |
    |---|---|
    | **Input** | The complete typed feedback corpus |
    | **Responsibility** | Find recurring product needs and cite the supporting feedback |
    | **Strategy** | Searching, grouping, comparing, and validating |
    | **Output** | A validated `ThemeReport` |

    **Capabilities**: What knowledge & capabilities does it need? What services does it need to reach?

    | Surface | Capbility |
    |---|---|
    | **Knowledge** | CSV files |
    | **Services** | None |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## PredictRLM: Avalanche's agent runtime

    Avalanche runs each agent step with PredictRLM. It gives the outer model a
    stateful Python environment: on each turn, the model's only action is to
    write Python, observe what that code returns, and continue until it submits
    the typed result.

    **Organizing context.** Inputs, files, and intermediate results live in
    Python variables. The agent chooses what to inspect or pass into a focused
    subcall, so its entire working set is not dumped into every model context.

    **Organizing tool calls.** Tools are ordinary Python functions. One model
    turn can emit code that calls several tools, loops over their results,
    combines them, and preserves useful state for the next turn.

    ### Example PredictRLM turn

    ```python
    RLM turn 1/30 (ok)
      reasoning: We need answer a repo question, not make changes. I should inspect the
                 RFP/first_pass directory structure and key workflow files (likely
                 flow.py/run.py/etc.), then summarize the workflow. No edits planned.
      python: 9 lines
      output: 534 chars
      code:
        from pathlib import Path
        import os, subprocess, json, textwrap, re
        root = Path(workspace)
        print("workspace", root)
        target = root/"belts"/"RFP"/"first_pass"
        print("exists", target.exists(), "is_dir", target.is_dir())
        if target.exists():
            for p in sorted(target.iterdir()):
                print(("DIR " if p.is_dir() else "FILE"), p.name)
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, source_code):
    mo.vstack(
        (
            mo.md("## 4. The anatomy of an `agent_step`"),
            mo.md("### A. Signature: contract and strategy"),
            mo.md(
                "A signature defines the agent's **inputs**, **outputs** and **instructions** "
                "Here the agent receives a `FeedbackCorpus` and must return a `ThemeReport`."
            ),
            mo.ui.code_editor(
                value=source_code("signature.py", "ExtractThemes"),
                language="python",
                disabled=True,
                show_copy_button=True,
            ),
            mo.ui.code_editor(
                value=source_code(
                    "schema.py",
                    "Feedback",
                    "FeedbackCorpus",
                    "Theme",
                    "ThemeReport",
                ),
                language="python",
                disabled=True,
                show_copy_button=True,
            ),
        )
    )
    return


@app.cell(hide_code=True)
def _(mo, source_code):
    mo.vstack(
        (
            mo.md("### B. Skills: reusable sandbox knowledge"),
            mo.md(
                "A skill packages reusable guidance and sandbox capabilities. This CSV "
                "example pairs validation instructions with pandas, which Avalanche installs "
                "inside the agent sandbox."
            ),
            mo.ui.code_editor(
                value=source_code("skills.py", "csv_analysis_skill"),
                language="python",
                disabled=True,
                show_copy_button=True,
            ),
        )
    )
    return


@app.cell(hide_code=True)
def tools_example(mo):
    mo.vstack(
        (
            mo.md("### C. Tools: typed host capabilities"),
            mo.md(
                "A tool is a typed host capability exposed to PredictRLM as an ordinary "
                "Python function. The model can call it freely from its generated code—"
                "multiple times and composed with other Python—instead of issuing one "
                "discrete tool call per model turn like a conventional tool-calling agent."
            ),
            mo.ui.code_editor(
                value='class AccountPlan(BaseModel):\n    account_id: str\n    tier: str\n\n\ndef lookup_account_plan(account_id: str) -> AccountPlan:\n    """Return the current CRM plan for one account."""\n    return crm_client.fetch_plan(account_id)',
                language="python",
                disabled=True,
                show_copy_button=True,
            ),
        )
    )
    return


@app.cell(hide_code=True)
def quickstart_signature(mo, source_code):
    mo.vstack(
        (
            mo.md("## Putting it together: creating the agent"),
            mo.md(
                "`@ava.agent_step(...)` combines the signature with its model configuration "
                "and any skills or tools it needs. Avalanche injects the configured "
                "`ava.Agent`; the function passes it the typed input and returns the "
                "signature's validated output."
            ),
            mo.ui.code_editor(
                value=source_code("flow.py", "extract_themes"),
                language="python",
                disabled=True,
                show_copy_button=True,
            ),
        )
    )
    return


@app.cell(hide_code=True)
def quickstart_rlm_call(mo):
    mo.vstack(
        (
            mo.md("## 5. Zoom back out to the complete flow"),
            mo.md(
                "The theme agent is one branch, not the whole application. Put it back "
                "beside the other responsibilities and choose an execution type for each "
                "boundary."
            ),
            mo.md(
                r"""
                ```text
                                               ┌─ extract_themes (agent) ─┐
                load_feedback_csv (source) ────┤                          ├─ compose signals (step) ── publish tasks (dest)
                                               └─ detect_risks (agent) ───┘
                ```
                """
            ),
        )
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.vstack(
        (
            mo.md("### Avalanche is the orchestration layer"),
            mo.md(
                "PredictRLM supplies the adaptive agent runtime. Avalanche places that "
                "runtime beside deterministic Python and external writes, then schedules "
                "the resulting graph from its declared data dependencies."
            ),
            mo.md("### Steps"),
            mo.md(
                "A normal typed Python function becomes a deterministic workflow node with "
                "`@ava.step`."
            ),
            mo.ui.code_editor(
                value='@ava.step\ndef normalize_feedback(text: str) -> str:\n    return text.strip()',
                language="python",
                disabled=True,
                show_copy_button=True,
            ),
            mo.md("### Agent steps"),
            mo.md(
                "An `@ava.agent_step` wraps one logical agent task and receives its "
                "configured `ava.Agent` through dependency injection."
            ),
            mo.ui.code_editor(
                value="@ava.agent_step(AnalyzeFeedback, lm=MODEL)\nasync def analyze_feedback(\n    corpus: FeedbackCorpus, *, agent: ava.Agent\n) -> FeedbackAnalysis:\n    return (await agent(corpus=corpus)).analysis",
                language="python",
                disabled=True,
                show_copy_button=True,
            ),
            mo.md("### Workflows"),
            mo.md(
                "An `@ava.workflow` declares dependencies between nodes: `>>` orders work "
                "and `&` groups independent branches."
            ),
            mo.ui.code_editor(
                value="@ava.workflow\ndef example_workflow():\n    return (\n        load_data()\n        >> (analyze_a() & analyze_b())\n        >> publish()\n    )",
                language="python",
                disabled=True,
                show_copy_button=True,
            ),
        )
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    | Logical responsibility | Avalanche node | Why |
    |---|---|---|
    | Load feedback | `@ava.source` | Constructs the first runtime value |
    | Extract themes | `@ava.agent_step` | Requires adaptive synthesis |
    | Detect risks | `@ava.agent_step` | Independent judgment task |
    | Compose signals | `@ava.step` | Deterministic transformation |
    | Publish CRM tasks | `@ava.dest` | Owns the final external write |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.vstack(
        (
            mo.md("## 6. Implement the remaining steps"),
            mo.md(
                "The source reads the bundled CSV. A second agent independently detects "
                "risks. Deterministic Python then combines the two reports, and the "
                "destination writes the mock CRM import artifact."
            ),
        )
    )
    return


@app.cell(hide_code=True)
def _(BaseModel, Literal):
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

    return (
        CrmProductSignal,
        CrmProductSignalBatch,
        CrmSyncResult,
        CrmTask,
        Feedback,
        FeedbackCorpus,
        RiskReport,
        ThemeReport,
    )


@app.cell(hide_code=True)
def _(
    CrmProductSignal,
    CrmProductSignalBatch,
    CrmSyncResult,
    CrmTask,
    FEEDBACK_PATH,
    Feedback,
    FeedbackCorpus,
    MODEL,
    RiskReport,
    SIGNALS_PATH,
    SUB_MODEL,
    ThemeReport,
    ava,
    csv,
    csv_analysis_skill,
    json,
):
    @ava.source
    def load_feedback_csv() -> FeedbackCorpus:
        with FEEDBACK_PATH.open(encoding="utf-8", newline="") as feedback_file:
            reader = csv.DictReader(feedback_file)
            return FeedbackCorpus(
                feedback=[Feedback(feedback_id=row["id"], text=row["text"]) for row in reader]
            )

    class ExtractThemes(ava.Signature):
        """Find recurring product needs and cite the feedback behind each one.

        Review the complete corpus. Group only recurring needs, preserve the feedback IDs
        in the evidence, and do not turn a one-off complaint into a theme.
        """

        corpus: FeedbackCorpus = ava.InputField(
            desc="The complete product-feedback corpus to analyze."
        )
        report: ThemeReport = ava.OutputField(
            desc="Recurring themes with supporting feedback IDs and text."
        )

    @ava.agent_step(
        ExtractThemes,
        lm=MODEL,
        sub_lm=SUB_MODEL,
        skills=[csv_analysis_skill],
    )
    async def extract_themes(corpus: FeedbackCorpus, *, agent: ava.Agent) -> ThemeReport:
        return (await agent(corpus=corpus)).report

    class DetectRisks(ava.Signature):
        """Find product or customer risks and grade their severity.

        Review the complete corpus. Report only risks grounded in customer feedback, cite the
        feedback IDs in the evidence, and use high severity only for material retention or
        business-risk language.
        """

        corpus: FeedbackCorpus = ava.InputField(
            desc="The complete product-feedback corpus to analyze."
        )
        report: RiskReport = ava.OutputField(
            desc="Risks, severity, and supporting feedback IDs and text."
        )

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
    def publish_local_crm_import(signals: CrmProductSignalBatch) -> CrmSyncResult:
        created = [
            CrmTask(
                external_id=f"demo-signal-{index}",
                title=f"{signal.kind}: {signal.headline}",
            )
            for index, signal in enumerate(signals.signals, start=1)
        ]
        result = CrmSyncResult(
            created=created,
            artifact_path=str(SIGNALS_PATH),
        )
        SIGNALS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SIGNALS_PATH.write_text(
            json.dumps(
                {
                    "signals": [signal.model_dump() for signal in signals.signals],
                    "created": [task.model_dump() for task in created],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return result

    return (
        compose_crm_product_signals,
        detect_risks,
        extract_themes,
        load_feedback_csv,
        publish_local_crm_import,
    )


@app.cell(hide_code=True)
def _(mo, source_code):
    mo.vstack(
        (
            mo.md("### Load the corpus"),
            mo.ui.code_editor(
                value=source_code("flow.py", "load_feedback_csv"),
                language="python",
                disabled=True,
                show_copy_button=True,
            ),
            mo.md("### Detect risks independently"),
            mo.ui.code_editor(
                value=source_code("signature.py", "DetectRisks")
                + "\n\n\n"
                + source_code("flow.py", "detect_risks"),
                language="python",
                disabled=True,
                show_copy_button=True,
            ),
            mo.md("### Join the analyses deterministically"),
            mo.ui.code_editor(
                value=source_code("flow.py", "compose_crm_product_signals"),
                language="python",
                disabled=True,
                show_copy_button=True,
            ),
            mo.md("### Publish the final tasks"),
            mo.ui.code_editor(
                value=source_code("flow.py", "publish_local_crm_import"),
                language="python",
                disabled=True,
                show_copy_button=True,
            ),
        )
    )
    return


@app.cell(hide_code=True)
def _(
    ava,
    compose_crm_product_signals,
    detect_risks,
    extract_themes,
    load_feedback_csv,
    publish_local_crm_import,
):
    @ava.workflow
    def feedback_triage():
        return (
            load_feedback_csv()
            >> (extract_themes() & detect_risks())
            >> compose_crm_product_signals()
            >> publish_local_crm_import()
        )

    return


@app.cell(hide_code=True)
def _(mo, source_code):
    mo.vstack(
        (
            mo.md("## 7. Declare the workflow"),
            mo.md(
                "The nodes already own their individual responsibilities. The workflow "
                "body only declares their dependencies: `>>` orders stages, while `&` "
                "forms the two independent analysis branches."
            ),
            mo.ui.code_editor(
                value=source_code("flow.py", "feedback_triage"),
                language="python",
                disabled=True,
                show_copy_button=True,
            ),
        )
    )
    return


if __name__ == "__main__":
    app.run()
