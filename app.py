"""
Premier League 2023/24 — Player Performance Dashboard
======================================================
Run:  streamlit run app.py
"""

import streamlit as st
import pandas as pd

# ── Page config (MUST be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="PL Analytics | 2023/24",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700&family=Barlow+Condensed:wght@700&display=swap');

html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif;
    background-color: #0d1117;
    color: #e6edf3;
}

/* Hero header */
.hero {
    background: linear-gradient(135deg, #1a4731 0%, #0d1117 60%);
    border-bottom: 2px solid #2ecc71;
    padding: 1.5rem 2rem 1rem;
    margin: -1rem -1rem 1.5rem;
}
.hero h1 {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 2.6rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #f0c040;
    margin: 0;
    line-height: 1;
}
.hero p { color: #8b949e; font-size: 0.95rem; margin: 0.3rem 0 0; }

/* KPI metric cards */
.kpi-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
.kpi-card {
    background: #161b22;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 1rem 1.4rem;
    flex: 1;
    min-width: 120px;
}
.kpi-card .kpi-label { font-size: 0.72rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.08em; }
.kpi-card .kpi-value { font-family: 'Barlow Condensed', sans-serif; font-size: 2rem; font-weight: 700; color: #f0c040; line-height: 1.2; }
.kpi-card .kpi-sub   { font-size: 0.75rem; color: #3ebd78; }

/* Section headers */
.section-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.2rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.06em;
    color: #e6edf3; border-left: 3px solid #f0c040;
    padding-left: 0.75rem; margin: 1.5rem 0 0.75rem;
}

/* Sidebar */
[data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid rgba(255,255,255,0.06); }
[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }

/* Remove default Streamlit metric box styling */
[data-testid="metric-container"] { display: none; }

/* Player card */
.player-card {
    background: #161b22;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
}
.player-card h3 { margin: 0 0 0.2rem; font-size: 1.1rem; color: #e6edf3; }
.player-card .sub { color: #8b949e; font-size: 0.8rem; }

/* Tab override */
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: transparent; }
.stTabs [data-baseweb="tab"] {
    background: #161b22; border-radius: 8px 8px 0 0;
    color: #8b949e; padding: 0.4rem 1rem; font-size: 0.85rem;
    border: 1px solid rgba(255,255,255,0.06); border-bottom: none;
}
.stTabs [aria-selected="true"] { background: #1a4731 !important; color: #f0c040 !important; }

div[data-testid="stHorizontalBlock"] > div { gap: 0.75rem; }
</style>
""", unsafe_allow_html=True)

# ── Imports ───────────────────────────────────────────────────────────────────
from utils.data_loader import load_player_data
from utils.charts import (
    make_scatter, make_bar, make_radar, make_team_summary, make_xg_vs_goals
)

# ── Data ──────────────────────────────────────────────────────────────────────
with st.spinner("Loading Premier League data…"):
    df = load_player_data()

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>⚽ PREMIER LEAGUE ANALYTICS</h1>
  <p>2023/24 Season · Player Performance Intelligence · Data via FBref & Kaggle</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Filters")

    positions = ["All"] + sorted(df['position_group'].dropna().unique().tolist())
    sel_pos = st.selectbox("Position", positions)

    teams = ["All"] + sorted(df['team'].dropna().unique().tolist())
    sel_team = st.selectbox("Club", teams)

    min90, max90 = float(df['nineties'].min()), float(df['nineties'].max())
    sel_90s = st.slider("Min 90s played", min_value=min90, max_value=max90,
                        value=5.0, step=1.0)

    st.markdown("---")
    st.markdown("### 📊 Scatter Axes")
    metric_options = {
        "Goals per 90":    "goals_per90",
        "Assists per 90":  "assists_per90",
        "xG per 90":       "xg_per90",
        "xA per 90":       "xa_per90",
        "Total Goals":     "goals",
        "Total Assists":   "assists",
        "xG Overperformance": "xg_overperformance",
        "Progressive Passes":  "progressive_passes",
        "Progressive Carries": "progressive_carries",
    }
    x_label = st.selectbox("X Axis", list(metric_options.keys()), index=2)
    y_label = st.selectbox("Y Axis", list(metric_options.keys()), index=0)
    x_col = metric_options[x_label]
    y_col = metric_options[y_label]

# ── Apply filters ─────────────────────────────────────────────────────────────
fdf = df.copy()
if sel_pos  != "All":  fdf = fdf[fdf['position_group'] == sel_pos]
if sel_team != "All":  fdf = fdf[fdf['team'] == sel_team]
fdf = fdf[fdf['nineties'] >= sel_90s]

# ── KPI row ───────────────────────────────────────────────────────────────────
st.markdown('<div class="kpi-row">', unsafe_allow_html=True)

kpis = [
    ("Players", len(fdf), "in selection"),
    ("Total Goals", int(fdf['goals'].sum()), f"avg {fdf['goals_per90'].mean():.2f}/90"),
    ("Total Assists", int(fdf['assists'].sum()), f"avg {fdf['assists_per90'].mean():.2f}/90"),
    ("Avg xG/90", f"{fdf['xg_per90'].mean():.2f}", "expected goals rate"),
    ("Top Scorer", fdf.nlargest(1,'goals')['player'].values[0] if len(fdf) else "—",
                   f"{int(fdf['goals'].max()) if len(fdf) else 0} goals"),
]

kpi_html = "".join(f"""
<div class="kpi-card">
  <div class="kpi-label">{label}</div>
  <div class="kpi-value">{val}</div>
  <div class="kpi-sub">{sub}</div>
</div>""" for label, val, sub in kpis)

st.markdown(f'<div class="kpi-row">{kpi_html}</div>', unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈  Scatter Explorer",
    "🏆  Top Performers",
    "🕸️  Player Comparison",
    "🏟️  Club Overview",
])

# ─── TAB 1 — Scatter ─────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-title">Interactive Scatter Explorer</div>', unsafe_allow_html=True)
    st.caption("Each dot = one player. Hover for details. Dashed lines = dataset averages.")

    if len(fdf) < 2 or x_col not in fdf.columns or y_col not in fdf.columns:
        st.info("Not enough data for this filter combination. Try relaxing filters.")
    else:
        fig = make_scatter(fdf, x_col, y_col, x_label, y_label,
                           f"{x_label} vs {y_label}")
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 View filtered data table"):
        show_cols = [c for c in ['player','team','position_group','nineties',
                                  'goals','assists','xg','xa',
                                  'goals_per90','assists_per90','xg_per90'] if c in fdf.columns]
        st.dataframe(
            fdf[show_cols].sort_values('goals', ascending=False).reset_index(drop=True),
            use_container_width=True, height=300
        )

# ─── TAB 2 — Top Performers ──────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-title">Top Performers</div>', unsafe_allow_html=True)

    bar_metric_opts = {
        "Goals":          ("goals",       "Goals"),
        "Assists":        ("assists",      "Assists"),
        "Goals per 90":   ("goals_per90",  "Goals/90"),
        "xG":             ("xg",           "Expected Goals"),
        "xG per 90":      ("xg_per90",     "xG/90"),
        "xG Overperf.":   ("xg_overperformance", "Goals − xG"),
        "Progressive Passes": ("progressive_passes", "Prog. Passes"),
    }
    chosen = st.selectbox("Metric", list(bar_metric_opts.keys()))
    col_name, col_label = bar_metric_opts[chosen]

    if col_name in fdf.columns and fdf[col_name].notna().sum() > 0:
        fig2 = make_bar(fdf, col_name, col_label, top_n=15)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Metric not available for current filters.")

    # xG vs Goals chart below
    st.markdown('<div class="section-title">xG vs Actual Goals</div>', unsafe_allow_html=True)
    st.caption("Players above the diagonal line are overperforming their xG.")
    if 'xg' in fdf.columns and 'goals' in fdf.columns:
        fig_xg = make_xg_vs_goals(fdf)
        st.plotly_chart(fig_xg, use_container_width=True)

# ─── TAB 3 — Player Comparison ───────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-title">Head-to-Head Radar Comparison</div>', unsafe_allow_html=True)
    st.caption("Select 2 or 3 players to compare across key metrics.")

    all_players = sorted(fdf['player'].dropna().unique().tolist())
    if len(all_players) < 2:
        st.info("Select fewer filters to compare players.")
    else:
        defaults = all_players[:2] if len(all_players) >= 2 else all_players
        selected_players = st.multiselect("Choose players (2–3)", all_players,
                                          default=defaults[:2], max_selections=3)

        if len(selected_players) >= 2:
            radar_metrics = ['goals_per90','assists_per90','xg_per90','xa_per90',
                             'progressive_passes','progressive_carries']
            radar_labels  = ['Goals/90','Assists/90','xG/90','xA/90',
                             'Prog. Passes','Prog. Carries']
            # Only keep metrics that exist
            valid = [(m, l) for m, l in zip(radar_metrics, radar_labels) if m in fdf.columns]
            radar_metrics = [v[0] for v in valid]
            radar_labels  = [v[1] for v in valid]

            players_data = fdf[fdf['player'].isin(selected_players)].to_dict('records')
            fig3 = make_radar(players_data, radar_metrics, radar_labels)
            st.plotly_chart(fig3, use_container_width=True)

            # Stat comparison table
            st.markdown('<div class="section-title">Stat Breakdown</div>', unsafe_allow_html=True)
            display_cols = [c for c in ['player','team','position_group','nineties',
                                         'goals','assists','xg','xa',
                                         'goals_per90','xg_per90','xg_overperformance']
                            if c in fdf.columns]
            comp_df = fdf[fdf['player'].isin(selected_players)][display_cols]
            st.dataframe(comp_df.set_index('player'), use_container_width=True)
        else:
            st.info("Please select at least 2 players.")

# ─── TAB 4 — Club Overview ───────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-title">Club Attacking Output</div>', unsafe_allow_html=True)

    fig4 = make_team_summary(df)  # use full df for club view
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown('<div class="section-title">Squad Stats by Club</div>', unsafe_allow_html=True)
    team_agg = (df.groupby('team')
                  .agg(
                      players=('player','count'),
                      goals=('goals','sum'),
                      assists=('assists','sum'),
                      xg=('xg','sum'),
                      avg_goals_p90=('goals_per90','mean'),
                      avg_xg_p90=('xg_per90','mean'),
                  )
                  .round(2)
                  .sort_values('goals', ascending=False)
                  .reset_index())
    st.dataframe(team_agg, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='color:#444;font-size:0.75rem;text-align:center'>"
    "Data sourced from FBref via soccerdata · Built by Aditya Gaisamudre · "
    "MSc Data Science, King's College London"
    "</p>",
    unsafe_allow_html=True
)
