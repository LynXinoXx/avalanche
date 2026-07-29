import avalanche as ava

csv_analysis_skill = ava.agent.Skill(
    name="csv-analysis",
    instructions="""Use pandas to inspect and transform CSV files.

Import pandas as `pd` and load each CSV with `pd.read_csv(path)`. Inspect its
headers and inferred schema before analyzing rows. Require headers to be
non-empty and unique. Verify that every requested column exists. Reject
malformed rows instead of guessing their shape. Preserve identifier columns
as strings. Report nulls, duplicate records, and parse failures explicitly;
never silently drop or coerce invalid data.""",
    packages=["pandas"],
)
