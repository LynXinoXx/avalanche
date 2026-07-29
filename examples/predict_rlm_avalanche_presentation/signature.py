import avalanche as ava

from .schema import FeedbackCorpus, RiskReport, ThemeReport


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
