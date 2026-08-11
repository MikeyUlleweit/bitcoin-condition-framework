import os
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.pipeline.live_research import run_live_research
from src.storage.research_database import ResearchDatabase, SnapshotSummary

DEFAULT_DATABASE_PATH = "data/research.sqlite3"


DASHBOARD_CSS = """
<style>
    :root { --btc: #f5a524; --panel: #172135; --line: #42506a; --muted: #a3aec2; }
    .stApp {
        background:
            radial-gradient(circle at 92% 0%, rgba(91,71,137,.35), transparent 31rem),
            linear-gradient(135deg, #101b2b 0%, #1b2941 52%, #201d3d 100%);
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background: rgba(13,23,38,.93); border-right: 1px solid #384761;
    }
    [data-testid="stSidebar"] > div { padding-top: 2rem; }
    .block-container { max-width: 1500px; padding-top: 2.2rem; padding-bottom: 5rem; }
    h1 { letter-spacing: -0.045em !important; font-size: 2.65rem !important; }
    h2, h3, h4 { letter-spacing: -0.025em !important; }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(38,52,78,.92), rgba(25,34,55,.94));
        border: 1px solid var(--line); border-radius: 14px; padding: 1.15rem 1.25rem;
        box-shadow: 0 12px 35px rgba(0,0,0,.18); min-height: 112px;
    }
    [data-testid="stMetricLabel"] {
        color: var(--muted); text-transform: uppercase; letter-spacing: .08em;
    }
    [data-testid="stMetricLabel"] p {
        white-space: normal !important; overflow: visible !important;
        text-overflow: clip !important; line-height: 1.2 !important;
        font-size: .7rem !important; letter-spacing: .065em !important;
        margin-bottom: .65rem !important;
    }
    [data-testid="stMetricValue"] { color: #fff; font-weight: 650; }
    [data-testid="stMetricValue"] p {
        white-space: normal !important; overflow: visible !important;
        text-overflow: clip !important; line-height: 1.12 !important;
        overflow-wrap: anywhere !important; font-size: clamp(1.35rem, 1.8vw, 2rem) !important;
        letter-spacing: -.025em !important; margin: 0 !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(27,39,61,.78); border-color: var(--line) !important;
        border-radius: 16px !important; box-shadow: 0 16px 40px rgba(0,0,0,.16);
    }
    .hero-kicker {
        color: var(--btc); font-size: .76rem; font-weight: 750;
        letter-spacing: .16em; text-transform: uppercase;
    }
    .hero-copy {
        color: #9aa8ba; max-width: 760px; font-size: 1.03rem;
        line-height: 1.65; margin: -.35rem 0 1.4rem;
    }
    .status-row { display:flex; gap:.55rem; align-items:center; margin:.2rem 0 1.2rem; }
    .status-dot {
        width:.55rem; height:.55rem; border-radius:99px;
        background:#3ddc97; box-shadow:0 0 12px #3ddc97;
    }
    .status-text { color:#93a1b3; font-size:.82rem; letter-spacing:.04em; }
    div[data-testid="stProgress"] > div > div > div {
        background: linear-gradient(90deg, #b85e00, var(--btc));
    }
    button[kind="primary"] {
        background: var(--btc) !important; color:#100a03 !important;
        border:none !important; font-weight:750 !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: .35rem; border-bottom: 1px solid var(--line); }
    .stTabs [data-baseweb="tab"] { border-radius: 9px 9px 0 0; padding: .7rem 1rem; color:#8d9bad; }
    .stTabs [aria-selected="true"] { color:#fff !important; background:#151c26; }
    [data-testid="stDataFrame"], [data-testid="stJson"] {
        border:1px solid var(--line); border-radius:12px; overflow:hidden;
    }
    .signal-meta { color:#8291a4; font-size:.82rem; padding:.15rem 0 .65rem; }
    .signal-summary {
        display:grid;
        grid-template-columns:minmax(0, 2fr) minmax(68px, .62fr) minmax(68px, .62fr);
        gap:.75rem; margin:.35rem 0 .75rem; padding:.9rem 0;
        border-top:1px solid rgba(66,80,106,.6);
        border-bottom:1px solid rgba(66,80,106,.6);
    }
    .signal-stat { min-width:0; }
    .signal-stat + .signal-stat {
        border-left:1px solid rgba(66,80,106,.6); padding-left:.75rem;
    }
    .signal-stat-label {
        color:#91a0b5; font-size:.62rem; font-weight:700; letter-spacing:.09em;
        text-transform:uppercase; margin-bottom:.38rem;
    }
    .signal-stat-value {
        color:#f3f6fb; font-size:.98rem; font-weight:700; line-height:1.2;
        white-space:nowrap; letter-spacing:-.015em;
    }
    .signal-stat:first-child .signal-stat-value {
        font-size:clamp(.82rem, 1.05vw, 1rem);
    }
    .section-label {
        color:#97a5bb; font-size:.72rem; font-weight:750; letter-spacing:.14em;
        text-transform:uppercase; margin:1.35rem 0 .75rem;
    }
    .rank-panel {
        border:1px solid var(--line); border-radius:16px; overflow:hidden;
        background:rgba(27,39,61,.76); min-height:420px;
    }
    .rank-head { padding:1.1rem 1.2rem; font-weight:700; border-bottom:1px solid var(--line); }
    .rank-item {
        display:grid; grid-template-columns:2rem 1fr auto; gap:.6rem;
        align-items:center; padding:.92rem 1.1rem; border-bottom:1px solid rgba(66,80,106,.65);
    }
    .rank-number { color:#77869e; font-size:.78rem; }
    .rank-name { color:#edf2fa; font-size:.88rem; font-weight:600; line-height:1.25; }
    .rank-condition { color:#97a5bb; font-size:.7rem; margin-top:.18rem; }
    .rank-score { color:var(--btc); font-size:1rem; font-weight:750; }
    hr { border-color: var(--line) !important; }
</style>
"""


def inject_dashboard_style() -> None:
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)


def render_signal_ranking(signals: list[object]) -> None:
    from src.models.signal import SignalOutput

    scored = sorted(
        (signal for signal in signals if isinstance(signal, SignalOutput)),
        key=lambda signal: signal.score if signal.score is not None else -1,
        reverse=True,
    )
    items = []
    for index, signal in enumerate(scored, start=1):
        score = "—" if signal.score is None else f"{signal.score:.0f}"
        items.append(
            '<div class="rank-item">'
            f'<div class="rank-number">{index:02d}</div>'
            f'<div><div class="rank-name">{escape(signal.category)}</div>'
            f'<div class="rank-condition">{escape(signal.condition)}</div></div>'
            f'<div class="rank-score">{score}</div></div>'
        )
    st.markdown(
        '<div class="rank-panel"><div class="rank-head">Signal ranking</div>'
        + "".join(items)
        + "</div>",
        unsafe_allow_html=True,
    )


def build_signal_overview(signals: list[object]) -> object:
    from src.models.signal import SignalOutput

    rows = [
        {"Signal": signal.category, "Score": signal.score}
        for signal in signals
        if isinstance(signal, SignalOutput) and signal.score is not None
    ]
    frame = pd.DataFrame(rows, columns=["Signal", "Score"]).sort_values("Score")
    figure = px.bar(
        frame,
        x="Score",
        y="Signal",
        orientation="h",
        range_x=[0, 100],
        text="Score",
    )
    figure.update_traces(
        marker_color="#f5a524",
        marker_line_color="#ffd07a",
        marker_line_width=0.7,
        texttemplate="%{text:.1f}",
        textposition="outside",
    )
    figure.update_layout(
        height=420,
        margin=dict(l=15, r=30, t=35, b=20),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(27,39,61,.55)",
        font_color="#aeb9ca",
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
    )
    figure.update_xaxes(gridcolor="rgba(111,128,156,.22)", zeroline=False)
    figure.update_yaxes(gridcolor="rgba(0,0,0,0)")
    return figure


@st.cache_resource
def get_database(path: str) -> ResearchDatabase:
    database = ResearchDatabase(path)
    database.initialize()
    return database


def refresh_live_data(database: ResearchDatabase) -> None:
    with st.spinner("Collecting real provider data and validating observations…"):
        run = run_live_research(database)
    st.success(
        f"Stored snapshot {run.snapshot.snapshot_id[:8]} with "
        f"{len(run.provider_failures)} provider failure(s)."
    )
    st.cache_data.clear()


def summary_label(summary: SnapshotSummary) -> str:
    cutoff = pd.Timestamp(summary.information_cutoff).strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"{cutoff} · {summary.final_condition.value} · {summary.snapshot_id[:8]}"


def render_signal(signal: object) -> None:
    from src.models.signal import SignalOutput

    if not isinstance(signal, SignalOutput):
        return

    score_label = "—" if signal.score is None else f"{signal.score:.1f}"
    st.markdown(f"#### {signal.category}")
    st.markdown(
        '<div class="signal-summary">'
        '<div class="signal-stat"><div class="signal-stat-label">Condition</div>'
        f'<div class="signal-stat-value">{escape(signal.condition)}</div></div>'
        '<div class="signal-stat"><div class="signal-stat-label">Score</div>'
        f'<div class="signal-stat-value">{score_label}</div></div>'
        '<div class="signal-stat"><div class="signal-stat-label">Coverage</div>'
        f'<div class="signal-stat-value">{signal.data_coverage:.0%}</div></div></div>'
        f'<div class="signal-meta">{signal.calibration_status.value.upper()} &nbsp;·&nbsp; '
        f"{escape(signal.source_status.value.upper())} &nbsp;·&nbsp; "
        f"{escape(signal.scope)}</div>",
        unsafe_allow_html=True,
    )

    if signal.score is not None:
        st.progress(signal.score / 100)

    if signal.score_breakdown:
        st.caption("Explainable score contributions")
        st.dataframe(
            [item.model_dump() for item in signal.score_breakdown],
            width="stretch",
            hide_index=True,
        )

    evidence_tab, missing_tab, risks_tab = st.tabs(["Evidence", "Missing data", "Risks"])
    with evidence_tab:
        if signal.evidence:
            for item in signal.evidence:
                st.write(f"- {item}")
        else:
            st.caption("No evidence recorded.")
    with missing_tab:
        if signal.missing_data:
            for item in signal.missing_data:
                st.warning(item)
        else:
            st.caption("No required observation is missing.")
    with risks_tab:
        if signal.risks:
            for item in signal.risks:
                st.write(f"- {item}")
        else:
            st.caption("No signal-specific risks recorded.")


def main() -> None:
    st.set_page_config(
        page_title="Bitcoin Condition Research",
        page_icon="₿",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_dashboard_style()
    st.markdown(
        '<div class="hero-kicker">Quantitative research console</div>', unsafe_allow_html=True
    )
    st.title("Bitcoin Market Condition Research")
    st.markdown(
        '<div class="hero-copy">A point-in-time view of Bitcoin market structure, '
        "built from explainable public-data signals. Research infrastructure—not a "
        "trading recommendation or execution system.</div>",
        unsafe_allow_html=True,
    )

    database_path = os.getenv("BITCOIN_RESEARCH_DB", DEFAULT_DATABASE_PATH)
    database = get_database(database_path)

    with st.sidebar:
        st.markdown("## ₿ Condition Lab")
        st.caption("RESEARCH CONTROL PLANE")
        st.divider()
        st.caption("LIVE INGESTION")
        if st.button("Refresh real data", type="primary", width="stretch"):
            try:
                refresh_live_data(database)
            except Exception as exc:
                st.error(f"Refresh failed: {type(exc).__name__}: {exc}")
        st.caption(f"Storage · `{Path(database_path).name}`")
        st.divider()
        st.info(
            "Scores are provisional public-data proxies with visible scope and coverage. "
            "No placeholder observations are generated."
        )

    summaries = database.list_snapshot_summaries(limit=500)
    if not summaries:
        st.info(
            "The database is initialized but contains no snapshots. "
            "Choose **Refresh real data** to create the first one."
        )
        return

    selected_id = st.selectbox(
        "Research snapshot",
        options=[summary.snapshot_id for summary in summaries],
        format_func=lambda value: summary_label(
            next(summary for summary in summaries if summary.snapshot_id == value)
        ),
    )
    selected_summary = next(summary for summary in summaries if summary.snapshot_id == selected_id)
    snapshot = database.load_snapshot(selected_id)
    condition = database.load_condition(selected_id)
    failures = database.list_provider_failures(selected_id)

    provider_state = "Healthy" if not failures else f"{len(failures)} failed"
    st.markdown(
        '<div class="status-row"><span class="status-dot"></span>'
        f'<span class="status-text">SNAPSHOT {snapshot.snapshot_id[:8].upper()} · '
        f"{provider_state.upper()} · {snapshot.information_cutoff:%Y-%m-%d %H:%M UTC}</span></div>",
        unsafe_allow_html=True,
    )
    headline = st.columns([1.45, 1.05, 1, 1], gap="medium")
    headline[0].metric("Market condition", condition.final_condition.value)
    headline[1].metric(
        "Usable / required",
        f"{condition.usable_signal_count} / {condition.minimum_required_signals}",
    )
    headline[2].metric("Observations", selected_summary.observation_count)
    headline[3].metric("Data coverage", f"{condition.confidence_score or 0:.0f}%")

    if not condition.is_classified():
        st.warning(condition.summary)
    else:
        st.success(condition.summary)

    overview_tab, history_tab, data_tab, health_tab = st.tabs(
        ["Signals", "History", "Observations", "Provider health"]
    )

    with overview_tab:
        st.markdown(
            '<div class="section-label">Market condition overview</div>', unsafe_allow_html=True
        )
        chart_column, ranking_column = st.columns([2.25, 1], gap="medium")
        with chart_column:
            with st.container(border=True):
                st.markdown("### Cross-signal condition map")
                st.caption("Current standardized scores · 0–100 provisional scale")
                st.plotly_chart(build_signal_overview(snapshot.signals), width="stretch")
        with ranking_column:
            render_signal_ranking(snapshot.signals)

        st.markdown('<div class="section-label">Signal diagnostics</div>', unsafe_allow_html=True)
        detail_columns = st.columns(2, gap="medium")
        for index, signal in enumerate(snapshot.signals):
            with detail_columns[index % 2]:
                with st.container(border=True):
                    render_signal(signal)

    with history_tab:
        categories = [signal.category for signal in snapshot.signals]
        selected_category = st.selectbox("Signal category", categories)
        history = database.get_signal_history(selected_category)
        if history:
            history_frame = pd.DataFrame([point.model_dump(mode="json") for point in history])
            scored = history_frame.dropna(subset=["score"])
            if not scored.empty:
                figure = px.line(
                    scored,
                    x="information_cutoff",
                    y="score",
                    markers=True,
                    title=f"{selected_category} score history",
                )
                figure.update_yaxes(range=[0, 100])
                figure.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(12,17,24,.75)",
                    font_color="#a9b5c5",
                    title_font_color="#f5f7fa",
                    hovermode="x unified",
                )
                figure.update_traces(line_color="#f7931a", marker_color="#f7931a")
                figure.update_xaxes(gridcolor="#202a36")
                figure.update_yaxes(gridcolor="#202a36")
                st.plotly_chart(figure, width="stretch")
            else:
                st.info("This category has no scored historical observations yet.")
            st.dataframe(history_frame, width="stretch", hide_index=True)

    with data_tab:
        if snapshot.observations:
            for observation in snapshot.observations:
                with st.expander(
                    f"{observation.observation_type} · {observation.source}",
                    expanded=True,
                ):
                    st.json(observation.model_dump(mode="json"))
        else:
            st.warning("No provider observations were stored in this snapshot.")

    with health_tab:
        if failures:
            st.error("One or more providers failed during this snapshot.")
            st.dataframe(
                [failure.model_dump(mode="json") for failure in failures],
                width="stretch",
                hide_index=True,
            )
        else:
            st.success("All configured public providers completed successfully.")


if __name__ == "__main__":
    main()
