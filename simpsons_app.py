"""
The Simpsons — Visual Analytics
Authors: Pablo Rodríguez Elvira, Adrián Segura Onorato
Course:  Data Visualization · MDS/MEI · 2025–2026

Run with:
    streamlit run simpsons_app.py

Expected CSV files in the same folder:
    simpsons_character_totals.csv   columns: character, total_words, total_sentences, total_lines
    simpsons_character_season.csv   columns: character, season, total_words, total_sentences, total_lines
    simpsons_character_episode.csv  columns: character, season, number_in_season, title,
                                              total_words, total_sentences, total_lines
    simpsons_lines.csv              columns: character, season, number_in_season, title,
                                              timestamp_in_ms, word_count, sentence_count
"""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Simpsons — Visual Analytics",
    page_icon="🍩",
    layout="wide",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 3rem; padding-bottom: 1rem; max-width: 100%; }
      h1, h2, h3, h4 { margin: 0.3rem 0; }
      div[data-testid="stSidebar"] { padding-top: 0.5rem; }
      div[data-testid="stVerticalBlock"] { gap: 0.6rem; }
      /* Center every Altair chart inside its Streamlit container */
      div[data-testid="stAltairChart"] {
          display: flex;
          justify-content: center;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# Try vegafusion for big dataframes; fall back to disabling the 5k-row limit.
try:
    alt.data_transformers.enable("vegafusion")
except Exception:  # noqa: BLE001
    alt.data_transformers.disable_max_rows()

# ─────────────────────────────────────────────────────────────────────────────
# Data
# ─────────────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent if "__file__" in globals() else Path(".")


@st.cache_data(show_spinner=False)
def load_data():
    df_total   = pd.read_csv(DATA_DIR / "simpsons_character_totals.csv")
    df_season  = pd.read_csv(DATA_DIR / "simpsons_character_season.csv")
    df_episode = pd.read_csv(DATA_DIR / "simpsons_character_episode.csv")
    df_lines   = pd.read_csv(DATA_DIR / "simpsons_lines.csv")
    return df_total, df_season, df_episode, df_lines


try:
    df_total, df_season, df_episode, df_lines = load_data()
except FileNotFoundError as e:
    st.error(
        f"Missing data file. Place the four cleaned CSVs in `{DATA_DIR}` "
        "(see the docstring at the top of this script).\n\n"
        f"Original error: `{e}`"
    )
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Shared constants
# ─────────────────────────────────────────────────────────────────────────────
NONE = "— none —"

LEVEL_COLS = {
    "words":     {"agg": "total_words",     "line": "word_count"},
    "sentences": {"agg": "total_sentences", "line": "sentence_count"},
    "lines":     {"agg": "total_lines",     "line": None},  # 1 row in df_lines = 1 line
}
LEVEL_LABEL = {"words": "Words", "sentences": "Sentences", "lines": "Lines"}

characters_all = sorted(df_total["character"].unique().tolist())

# Colour-blind-friendly palette (Tableau 10). Same character → same colour everywhere.
tableau10 = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
]
palette = (tableau10 * ((len(characters_all) // 10) + 1))[: len(characters_all)]
COLOR_SCALE = alt.Scale(domain=characters_all, range=palette)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — single source of truth for all charts
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🍩 Simpsons Analytics")
    st.caption("Pablo Rodríguez Elvira · Adrián Segura Onorato")
    st.markdown("---")

    level = st.radio(
        "Metric level",
        options=["words", "sentences", "lines"],
        index=0,
        horizontal=True,
        format_func=lambda x: LEVEL_LABEL[x],
        help="What to count across the dashboard: dialogue words, sentences, or speaking turns (lines).",
    )

    st.markdown("##### Character selection")
    st.caption("Selecting a character here updates **every** chart.")
    char1 = st.selectbox(
        "Character 1",
        options=[NONE] + characters_all,
        index=0,
        help="Highlighted in Q1 & Q2; first comparand in Q3 & Q4.",
    )
    char2 = st.selectbox(
        "Character 2",
        options=[NONE] + characters_all,
        index=0,
        help="Highlighted in Q1 & Q2; second comparand in Q3 & Q4.",
    )

    if char1 != NONE and char2 != NONE and char1 == char2:
        st.warning("Pick two **different** characters for Q3 and Q4 to be meaningful.")

    st.markdown("##### Time scope")
    seasons_all = sorted(df_episode["season"].unique().tolist())

    s_min_q1, s_max_q1 = int(min(seasons_all)), int(max(seasons_all))
    season_range_q1 = st.slider(
        "Season range (Q1)",
        min_value=s_min_q1,
        max_value=s_max_q1,
        value=(s_min_q1, s_max_q1),
        help="Q1 aggregates totals only for seasons inside this range.",
    )

    season_sel  = st.selectbox("Season (Q3 & Q4)", options=seasons_all, index=0)

    eps_in_season = sorted(
        df_episode.loc[df_episode["season"] == season_sel, "number_in_season"]
                  .unique().tolist()
    )
    if not eps_in_season:
        eps_in_season = [1]
    episode_sel = st.selectbox("Episode (Q4)", options=eps_in_season, index=0)

    st.markdown("---")
    if st.button("Clear character selection", use_container_width=True):
        st.session_state["char1"] = NONE
        st.session_state["char2"] = NONE
        st.rerun()

    with st.expander("About"):
        st.markdown(
            "**Authors:** Pablo Rodríguez Elvira, Adrián Segura Onorato\n\n"
            "**Course:** Data Visualization — MDS/MEI 2025–2026\n\n"
            "Dataset: *The Simpsons by the Data* (Kaggle, P. Patil)."
        )


# Characters actively selected (in order)
selected_chars = [c for c in (char1, char2) if c != NONE]


def _predicate_selected() -> str:
    """Return a Vega expression that is true for selected characters."""
    return " || ".join([f"datum.character === {repr(c)}" for c in selected_chars])


def opacity_for_selection():
    if not selected_chars:
        return alt.value(1.0)
    return alt.condition(_predicate_selected(), alt.value(1.0), alt.value(0.15))


def stroke_for_selection():
    if not selected_chars:
        return alt.value(2)
    return alt.condition(_predicate_selected(), alt.value(3.2), alt.value(1))


# ─────────────────────────────────────────────────────────────────────────────
# Q1 — totals per character (filtered by sidebar season range)
# ─────────────────────────────────────────────────────────────────────────────
def build_q1():
    col = LEVEL_COLS[level]["agg"]
    if col not in df_season.columns:
        return None

    s_lo, s_hi = season_range_q1
    sub = df_season[(df_season["season"] >= s_lo) & (df_season["season"] <= s_hi)]
    if sub.empty:
        return None

    label = LEVEL_LABEL[level].lower()
    subtitle = (
        f"Seasons {s_lo}–{s_hi}" if s_lo != s_hi else f"Season {s_lo}"
    ) + "  ·  Sidebar selection highlights"

    return (
        alt.Chart(sub)
        .mark_bar()
        .encode(
            x=alt.X(f"sum({col}):Q", title=f"Total {label}"),
            y=alt.Y("character:N", sort="-x", title=None),
            color=alt.Color("character:N", scale=COLOR_SCALE, legend=None),
            opacity=opacity_for_selection(),
            tooltip=[
                alt.Tooltip("character:N", title="Character"),
                alt.Tooltip(f"sum({col}):Q", title=f"Total {label}", format=","),
            ],
        )
        .properties(
            height=340,
            title=alt.TitleParams(
                f"Q1 · Total {label} per character",
                subtitle=subtitle,
                fontSize=15,
            ),
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# Q2 — evolution per season
# ─────────────────────────────────────────────────────────────────────────────
def build_q2():
    col = LEVEL_COLS[level]["agg"]
    if col not in df_season.columns:
        return None

    label = LEVEL_LABEL[level].lower()

    return (
        alt.Chart(df_season)
        .mark_line(point=True)
        .encode(
            x=alt.X("season:O", title="Season", axis=alt.Axis(labelAngle=0)),
            y=alt.Y(f"{col}:Q", title=f"Total {label}"),
            color=alt.Color(
                "character:N",
                scale=COLOR_SCALE,
                legend=alt.Legend(
                    title="Character",
                    columns=1,
                    symbolLimit=30,
                    labelFontSize=12,
                    titleFontSize=12,
                    symbolSize=110,
                    rowPadding=2,
                ),
            ),
            opacity=opacity_for_selection(),
            strokeWidth=stroke_for_selection(),
            tooltip=[
                alt.Tooltip("character:N", title="Character"),
                alt.Tooltip("season:O", title="Season"),
                alt.Tooltip(f"{col}:Q", title=f"Total {label}", format=","),
            ],
        )
        .properties(
            height=340,
            title=alt.TitleParams(
                f"Q2 · {LEVEL_LABEL[level]} evolution per season",
                subtitle="Sidebar selection highlights the chosen characters",
                fontSize=15,
            ),
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# Q3 — episode-level comparison within a selected season
# ─────────────────────────────────────────────────────────────────────────────
def build_q3():
    col = LEVEL_COLS[level]["agg"]
    if col not in df_episode.columns:
        return None
    if char1 == NONE or char2 == NONE:
        return None

    sub = df_episode[
        (df_episode["season"] == season_sel)
        & (df_episode["character"].isin([char1, char2]))
    ].copy()
    if sub.empty:
        return None

    # Stable left/right grouping so colour order matches sidebar order
    sub["__grp"] = sub["character"].map({char1: "A", char2: "B"})

    bars = (
        alt.Chart(sub)
        .mark_bar()
        .encode(
            x=alt.X("number_in_season:O", title="Episode #", axis=alt.Axis(labelAngle=0)),
            xOffset=alt.XOffset("__grp:N", scale=alt.Scale(domain=["A", "B"])),
            y=alt.Y(f"{col}:Q", title=f"{LEVEL_LABEL[level]} per episode"),
            color=alt.Color("character:N", scale=COLOR_SCALE, legend=None),
            tooltip=[
                alt.Tooltip("character:N", title="Character"),
                alt.Tooltip("title:N", title="Episode"),
                alt.Tooltip("number_in_season:O", title="Ep. #"),
                alt.Tooltip(f"{col}:Q", title=LEVEL_LABEL[level], format=","),
            ],
        )
        .properties(width=900, height=300)
    )

    box = (
        alt.Chart(sub)
        .mark_boxplot(extent=1.5)
        .encode(
            x=alt.X("character:N", title=None,
                    axis=alt.Axis(labelAngle=-15, labelLimit=120)),
            y=alt.Y(f"{col}:Q", title=LEVEL_LABEL[level],
                    axis=alt.Axis(title=None)),
            color=alt.Color("character:N", scale=COLOR_SCALE, legend=None),
            tooltip=[
                alt.Tooltip("character:N", title="Character"),
                alt.Tooltip(f"{col}:Q", title=LEVEL_LABEL[level], format=","),
            ],
        )
        .properties(width=140, height=300,
                    title=alt.TitleParams("Season distribution", fontSize=12))
    )

    return alt.hconcat(bars, box).resolve_scale(color="shared").properties(
        title=alt.TitleParams(
            f"Q3 · {LEVEL_LABEL[level]} per episode · Season {season_sel}",
            subtitle=f"{char1}  vs.  {char2}",
            fontSize=15,
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# Q4 — line-level comparison within a selected episode
# ─────────────────────────────────────────────────────────────────────────────
def build_q4():
    if char1 == NONE or char2 == NONE:
        return None

    sub = df_lines[
        (df_lines["season"] == season_sel)
        & (df_lines["number_in_season"] == episode_sel)
        & (df_lines["character"].isin([char1, char2]))
    ].copy()
    if sub.empty:
        return None

    if "timestamp_in_ms" in sub.columns:
        sub["timestamp_min"] = sub["timestamp_in_ms"] / 60000.0
    else:
        # Fallback: ordinal position within the episode
        sub = sub.sort_values(["character"]).reset_index(drop=True)
        sub["timestamp_min"] = sub.index.astype(float)

    # ── lines level: strip plot (1 tick = 1 line) + count bar
    if level == "lines":
        main = (
            alt.Chart(sub)
            .mark_tick(thickness=2, size=22)
            .encode(
                x=alt.X("timestamp_min:Q", title="Time (minutes)",
                        scale=alt.Scale(nice=False)),
                y=alt.Y("character:N", title=None, axis=alt.Axis(labelLimit=120)),
                color=alt.Color("character:N", scale=COLOR_SCALE, legend=None),
                tooltip=[
                    alt.Tooltip("character:N", title="Character"),
                    alt.Tooltip("timestamp_min:Q", title="Time (min)", format=".2f"),
                ],
            )
            .properties(width=900, height=300)
        )
        side = (
            alt.Chart(sub)
            .mark_bar()
            .encode(
                x=alt.X("count():Q", title="# lines"),
                y=alt.Y("character:N", title=None, axis=alt.Axis(labelLimit=120)),
                color=alt.Color("character:N", scale=COLOR_SCALE, legend=None),
                tooltip=[
                    alt.Tooltip("character:N", title="Character"),
                    alt.Tooltip("count():Q", title="Lines"),
                ],
            )
            .properties(width=140, height=300,
                        title=alt.TitleParams("Total lines", fontSize=12))
        )
        return alt.hconcat(main, side).resolve_scale(color="shared").properties(
            title=alt.TitleParams(
                f"Q4 · Lines through episode · S{season_sel} · E{episode_sel}",
                subtitle=f"{char1}  vs.  {char2}",
                fontSize=15,
            )
        )

    # ── words / sentences level: scatter (per-line metric over time) + boxplot
    col = LEVEL_COLS[level]["line"]
    if col is None or col not in sub.columns:
        return None

    scatter = (
        alt.Chart(sub)
        .mark_circle(size=55, opacity=0.75)
        .encode(
            x=alt.X("timestamp_min:Q", title="Time (minutes)",
                    scale=alt.Scale(nice=False)),
            y=alt.Y(f"{col}:Q", title=f"{LEVEL_LABEL[level]} per line"),
            color=alt.Color("character:N", scale=COLOR_SCALE, legend=None),
            tooltip=[
                alt.Tooltip("character:N", title="Character"),
                alt.Tooltip("title:N", title="Episode"),
                alt.Tooltip("timestamp_min:Q", title="Time (min)", format=".2f"),
                alt.Tooltip(f"{col}:Q", title=LEVEL_LABEL[level]),
            ],
        )
        .properties(width=900, height=300)
    )

    box = (
        alt.Chart(sub)
        .mark_boxplot(extent=1.5)
        .encode(
            x=alt.X("character:N", title=None,
                    axis=alt.Axis(labelAngle=-15, labelLimit=120)),
            y=alt.Y(f"{col}:Q", title=LEVEL_LABEL[level],
                    axis=alt.Axis(title=None)),
            color=alt.Color("character:N", scale=COLOR_SCALE, legend=None),
            tooltip=[
                alt.Tooltip("character:N", title="Character"),
                alt.Tooltip(f"{col}:Q", title=LEVEL_LABEL[level]),
            ],
        )
        .properties(width=140, height=300,
                    title=alt.TitleParams("Episode distribution", fontSize=12))
    )

    return alt.hconcat(scatter, box).resolve_scale(color="shared").properties(
        title=alt.TitleParams(
            f"Q4 · {LEVEL_LABEL[level]} per line · S{season_sel} · E{episode_sel}",
            subtitle=f"{char1}  vs.  {char2}",
            fontSize=15,
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# Layout — 2 × 2 grid
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"### 🍩 The Simpsons — Visual Analytics  ·  *{LEVEL_LABEL[level]}*")

# Row 1: Q1 — Q2
r1c1, r1c2 = st.columns(2, gap="medium")

with r1c1:
    chart = build_q1()
    if chart is not None:
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info(f"No `{LEVEL_COLS[level]['agg']}` column found in the season dataset.")

with r1c2:
    chart = build_q2()
    if chart is not None:
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info(f"No `{LEVEL_COLS[level]['agg']}` column found in the season dataset.")

# Row 2: Q3 (centered via CSS)
if char1 == NONE or char2 == NONE:
    st.info(
        "⬅️ Pick **Character 1** *and* **Character 2** in the sidebar to "
        "enable the episode-level comparison (Q3)."
    )
else:
    chart = build_q3()
    if chart is not None:
        st.altair_chart(chart, use_container_width=False)
    else:
        st.warning(
            f"No data for **{char1}** vs **{char2}** in season {season_sel}."
        )

# Row 3: Q4 (centered via CSS)
if char1 == NONE or char2 == NONE:
    st.info(
        "⬅️ Pick **Character 1** *and* **Character 2** in the sidebar to "
        "enable the line-level comparison (Q4)."
    )
else:
    chart = build_q4()
    if chart is not None:
        st.altair_chart(chart, use_container_width=False)
    else:
        st.warning(
            f"No data for **{char1}** vs **{char2}** in S{season_sel} · E{episode_sel}."
        )
