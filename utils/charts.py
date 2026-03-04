"""
Visualisation helpers — pitch plots, radar charts, scatter plots.
All return Plotly figures (works in Streamlit with st.plotly_chart).
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# ── Colour palette ────────────────────────────────────────────────────────────
PITCH_GREEN   = "#1a4731"
PITCH_LINE    = "#2ecc71"
ACCENT_GOLD   = "#f0c040"
ACCENT_RED    = "#e74c3c"
ACCENT_BLUE   = "#3498db"
BG_DARK       = "#0d1117"
CARD_BG       = "#161b22"
TEXT_LIGHT    = "#e6edf3"
TEXT_MUTED    = "#8b949e"


def team_color(team: str) -> str:
    """Returns a primary hex colour for a PL club."""
    colors = {
        "Arsenal":           "#EF0107",
        "Aston Villa":       "#95BFE5",
        "Bournemouth":       "#DA291C",
        "Brentford":         "#e30613",
        "Brighton":          "#0057B8",
        "Burnley":           "#6C1D45",
        "Chelsea":           "#034694",
        "Crystal Palace":    "#1B458F",
        "Everton":           "#003399",
        "Fulham":            "#CC0000",
        "Liverpool":         "#C8102E",
        "Luton Town":        "#F78F1E",
        "Manchester City":   "#6CABDD",
        "Manchester United": "#DA291C",
        "Newcastle United":  "#241F20",
        "Nottingham Forest": "#DD0000",
        "Sheffield United":  "#EE2737",
        "Tottenham":         "#132257",
        "West Ham":          "#7A263A",
        "Wolves":            "#FDB913",
    }
    return colors.get(team, ACCENT_BLUE)


def make_scatter(df: pd.DataFrame, x_col: str, y_col: str,
                 x_label: str, y_label: str, title: str) -> go.Figure:
    """Interactive scatter plot coloured by team."""

    df = df.copy().dropna(subset=[x_col, y_col])
    df['color'] = df['team'].apply(team_color)

    fig = go.Figure()

    for team in df['team'].unique():
        t = df[df['team'] == team]
        fig.add_trace(go.Scatter(
            x=t[x_col], y=t[y_col],
            mode='markers',
            name=team,
            marker=dict(
                color=team_color(team),
                size=10,
                line=dict(width=1, color='rgba(255,255,255,0.3)'),
                opacity=0.85,
            ),
            text=t['player'],
            customdata=t[['team', 'position_group', 'nineties']],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "%{customdata[0]} · %{customdata[1]}<br>"
                f"{x_label}: %{{x:.2f}}<br>"
                f"{y_label}: %{{y:.2f}}<br>"
                "90s played: %{customdata[2]:.1f}<extra></extra>"
            )
        ))

    # Average lines
    fig.add_hline(y=df[y_col].mean(), line_dash="dot",
                  line_color="rgba(240,192,64,0.35)", line_width=1)
    fig.add_vline(x=df[x_col].mean(), line_dash="dot",
                  line_color="rgba(240,192,64,0.35)", line_width=1)

    fig.update_layout(**_dark_layout(title))
    fig.update_xaxes(title_text=x_label, **_axis_style())
    fig.update_yaxes(title_text=y_label, **_axis_style())
    return fig


def make_bar(df: pd.DataFrame, metric: str, label: str,
             top_n: int = 15) -> go.Figure:
    """Horizontal bar chart of top N players by a metric."""

    df = df.nlargest(top_n, metric)[['player', 'team', metric]].copy()
    df = df.sort_values(metric)
    df['color'] = df['team'].apply(team_color)

    fig = go.Figure(go.Bar(
        x=df[metric],
        y=df['player'],
        orientation='h',
        marker_color=df['color'],
        marker_line=dict(width=0),
        text=df[metric].round(2),
        textposition='outside',
        textfont=dict(color=TEXT_LIGHT, size=11),
        hovertemplate="<b>%{y}</b><br>" + label + ": %{x:.2f}<extra></extra>",
    ))

    fig.update_layout(**_dark_layout(f"Top {top_n} — {label}"))
    fig.update_xaxes(title_text=label, **_axis_style())
    # fig.update_yaxes(tickfont=dict(size=11, color=TEXT_LIGHT), **_axis_style())
    fig.update_yaxes(**_axis_style())
    return fig


def make_radar(players_data: list[dict], metrics: list[str],
               labels: list[str]) -> go.Figure:
    """Radar / spider chart comparing up to 3 players."""

    colors = [ACCENT_GOLD, ACCENT_BLUE, ACCENT_RED]
    fig = go.Figure()

    for i, p in enumerate(players_data):
        values = [p.get(m, 0) or 0 for m in metrics]
        # Normalise 0–1 within the passed data
        max_vals = [max(pd.DataFrame(players_data)[m].max(), 0.01) for m in metrics]
        norm_vals = [v / mv for v, mv in zip(values, max_vals)]
        norm_vals.append(norm_vals[0])  # close the polygon

        fig.add_trace(go.Scatterpolar(
            r=norm_vals,
            theta=labels + [labels[0]],
            fill='toself',
            name=p['player'],
            line=dict(color=colors[i % 3], width=2),
            # fillcolor=colors[i % 3].replace('#', 'rgba(').rstrip(')') + ',0.15)',               ... Bug fix
            fillcolor=f"rgba({int(colors[i%3][1:3],16)},{int(colors[i%3][3:5],16)},{int(colors[i%3][5:7],16)},0.15)",
            marker=dict(size=5),
        ))

    fig.update_layout(
        polar=dict(
            bgcolor=CARD_BG,
            radialaxis=dict(visible=True, showticklabels=False,
                            gridcolor='rgba(255,255,255,0.08)', range=[0, 1.1]),
            angularaxis=dict(tickfont=dict(size=12, color=TEXT_LIGHT),
                             gridcolor='rgba(255,255,255,0.08)'),
        ),
        **_dark_layout("Player Comparison Radar"),
        showlegend=True,
    )
    return fig


def make_team_summary(df: pd.DataFrame) -> go.Figure:
    """Grouped bar: goals & assists by team."""
    team_stats = (df.groupby('team')
                    .agg(goals=('goals', 'sum'), assists=('assists', 'sum'))
                    .reset_index()
                    .sort_values('goals', ascending=False)
                    .head(15))

    fig = go.Figure()
    fig.add_trace(go.Bar(name='Goals',   x=team_stats['team'], y=team_stats['goals'],
                         marker_color=ACCENT_RED,  marker_line_width=0))
    fig.add_trace(go.Bar(name='Assists', x=team_stats['team'], y=team_stats['assists'],
                         marker_color=ACCENT_BLUE, marker_line_width=0))

    fig.update_layout(barmode='group', **_dark_layout("Goals & Assists by Club"))
    fig.update_xaxes(tickangle=-35, **_axis_style())
    fig.update_yaxes(**_axis_style())
    return fig


def make_xg_vs_goals(df: pd.DataFrame) -> go.Figure:
    """xG vs actual goals — shows over/underperformers."""
    df = df[df['position_group'].isin(['Forward', 'Midfielder'])].copy()
    df = df.dropna(subset=['xg', 'goals'])

    # Diagonal parity line
    max_val = max(df['xg'].max(), df['goals'].max()) + 2
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val],
        mode='lines',
        line=dict(color='rgba(240,192,64,0.4)', dash='dot', width=1),
        showlegend=False, hoverinfo='skip'
    ))

    for team in df['team'].unique():
        t = df[df['team'] == team]
        fig.add_trace(go.Scatter(
            x=t['xg'], y=t['goals'],
            mode='markers', name=team,
            marker=dict(color=team_color(team), size=10,
                        line=dict(width=1, color='rgba(255,255,255,0.2)')),
            text=t['player'],
            hovertemplate="<b>%{text}</b><br>xG: %{x:.2f}<br>Goals: %{y}<extra></extra>"
        ))

    fig.update_layout(**_dark_layout("xG vs Actual Goals (over/underperformance)"))
    fig.update_xaxes(title_text="Expected Goals (xG)", **_axis_style())
    fig.update_yaxes(title_text="Actual Goals",         **_axis_style())
    return fig


# ── Layout helpers ────────────────────────────────────────────────────────────

def _dark_layout(title: str) -> dict:
    return dict(
        title=dict(text=title, font=dict(size=16, color=TEXT_LIGHT, family="Barlow, sans-serif"),
                   x=0.01, xanchor='left'),
        paper_bgcolor=BG_DARK,
        plot_bgcolor=CARD_BG,
        font=dict(color=TEXT_LIGHT, family="Barlow, sans-serif"),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=11, color=TEXT_MUTED)),
        margin=dict(l=20, r=20, t=50, b=20),
        hoverlabel=dict(bgcolor=CARD_BG, font_color=TEXT_LIGHT, bordercolor='rgba(255,255,255,0.1)'),
    )


def _axis_style() -> dict:
    return dict(
        gridcolor='rgba(255,255,255,0.05)',
        zerolinecolor='rgba(255,255,255,0.1)',
        tickfont=dict(size=10, color=TEXT_MUTED),
    )
