from src.models.condition import ConditionResult


def format_condition_report(result: ConditionResult) -> str:
    """
    Format a ConditionResult into a readable text report.
    """
    lines: list[str] = []

    lines.append("Bitcoin Market Condition Report")
    lines.append("=" * 39)
    lines.append("")
    lines.append(f"Final Condition: {result.final_condition.value}")

    if result.confidence_score is None:
        lines.append("Confidence Score: Not scored")
    else:
        lines.append(f"Confidence Score: {result.confidence_score:.2f}")

    lines.append(
        f"Usable Signals: "
        f"{result.usable_signal_count} / {result.minimum_required_signals}"
    )

    lines.append("")
    lines.append("Usable Signals:")

    if result.usable_signals:
        for signal in result.usable_signals:
            score = "Not scored" if signal.score is None else f"{signal.score:.2f}"
            lines.append(f"- {signal.category}: {signal.condition}, score {score}")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("Built But Not Scored:")

    if result.not_scored_signals:
        for signal in result.not_scored_signals:
            lines.append(
                f"- {signal.category}: {signal.condition} "
                f"({signal.source_status.value})"
            )

            if signal.risks:
                for risk in signal.risks:
                    lines.append(f"  - {risk}")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("Missing Categories:")

    if result.missing_categories:
        for category in result.missing_categories:
            lines.append(f"- {category}")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("Summary:")
    lines.append(result.summary)

    lines.append("")
    lines.append("Evidence:")

    if result.evidence:
        for item in result.evidence:
            lines.append(f"- {item}")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("Risks:")

    if result.risks:
        for item in result.risks:
            lines.append(f"- {item}")
    else:
        lines.append("- None")

    return "\n".join(lines)