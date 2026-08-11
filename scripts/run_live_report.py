from src.pipeline.live_research import run_live_research
from src.reports.format_report import format_condition_report
from src.storage.research_database import ResearchDatabase


def main() -> None:
    database = ResearchDatabase()
    run = run_live_research(database)
    report = format_condition_report(run.condition)
    print(report)
    print("")
    print(f"Snapshot: {run.snapshot.snapshot_id}")
    print(f"Database: {database.path}")


if __name__ == "__main__":
    main()
