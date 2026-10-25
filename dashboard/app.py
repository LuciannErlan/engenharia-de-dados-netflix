"""Data App Executivo — Netflix / MovieLens Streaming & Recommendation Analytics."""

from __future__ import annotations

import html
import os
from pathlib import Path

import db_dtypes  # noqa: F401
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

st.set_page_config(
    page_title="Streaming & RecSys Analytics — MovieLens 2024",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "theme" not in st.session_state:
    st.session_state.theme = "dark"


def toggle_theme() -> None:
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"


IS_DARK = st.session_state.theme == "dark"

# ---------------------------------------------------------------------------
# Design System CSS (Zinc SaaS Palette + DM Sans & JetBrains Mono)
# ---------------------------------------------------------------------------
BG = "#09090b" if IS_DARK else "#ffffff"
BG_SUBTLE = "#0c0c0f" if IS_DARK else "#f9fafb"
CARD = "#0c0c0f" if IS_DARK else "#ffffff"
CARD_HOVER = "#131316" if IS_DARK else "#f4f4f5"
BORDER = "#1e1e24" if IS_DARK else "#e4e4e7"
BORDER_SUBTLE = "#16161a" if IS_DARK else "#f0f0f2"
TEXT = "#fafafa" if IS_DARK else "#09090b"
TEXT_MUTED = "#71717a"
TEXT_DIM = "#52525b" if IS_DARK else "#a1a1aa"
ACCENT = "#2563eb"
BRAND_RED = "#e11d48"
GREEN = "#22c55e" if IS_DARK else "#16a34a"
GREEN_MUTED = "rgba(34,197,94,0.12)" if IS_DARK else "rgba(22,163,74,0.08)"
RED = "#ef4444" if IS_DARK else "#dc2626"
RED_MUTED = "rgba(239,68,68,0.12)" if IS_DARK else "rgba(220,38,38,0.08)"
AMBER = "#f59e0b" if IS_DARK else "#d97706"
AMBER_MUTED = "rgba(245,158,11,0.12)" if IS_DARK else "rgba(217,119,6,0.08)"
SHADOW = "none" if IS_DARK else "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03)"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {{
        --bg: {BG};
        --bg-subtle: {BG_SUBTLE};
        --card: {CARD};
        --card-hover: {CARD_HOVER};
        --border: {BORDER};
        --border-subtle: {BORDER_SUBTLE};
        --text: {TEXT};
        --text-muted: {TEXT_MUTED};
        --text-dim: {TEXT_DIM};
        --accent: {ACCENT};
        --brand-red: {BRAND_RED};
        --green: {GREEN};
        --green-muted: {GREEN_MUTED};
        --red: {RED};
        --red-muted: {RED_MUTED};
        --amber: {AMBER};
        --amber-muted: {AMBER_MUTED};
        --shadow: {SHADOW};
        --radius: 10px;
    }}

    header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
    div[data-testid="stSidebarCollapsedControl"] {{
        display: none !important;
    }}

    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"],
    .main, .block-container, section[data-testid="stMain"] {{
        background-color: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    .block-container {{
        padding: 1.8rem 2.4rem 3rem !important;
        max-width: 1380px !important;
    }}

    @media (max-width: 900px) {{
        .block-container {{
            padding: 1rem 1rem 2rem !important;
        }}
    }}

    [data-testid="stHorizontalBlock"] {{
        gap: 1.25rem !important;
    }}

    div[data-baseweb="select"], div[data-baseweb="popover"] {{
        position: relative;
        z-index: 30;
    }}

    button[data-baseweb="tab"] {{
        background: transparent !important;
        color: var(--text-muted) !important;
        font-size: 0.84rem !important;
        font-weight: 500 !important;
        padding: 0.55rem 1.05rem !important;
        border: 1px solid transparent !important;
        border-radius: 7px !important;
        transition: all 0.18s ease !important;
    }}
    button[data-baseweb="tab"]:hover {{
        color: var(--text) !important;
        background: var(--card-hover) !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: var(--text) !important;
        background: var(--card) !important;
        border-color: var(--border) !important;
    }}
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{
        display: none !important;
    }}
    [data-baseweb="tab-list"] {{
        gap: 4px !important;
        background: var(--bg-subtle) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 4px;
        margin-bottom: 1.25rem;
    }}

    .brand-bar {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.25rem;
    }}
    .brand-dot {{
        width: 10px;
        height: 24px;
        border-radius: 3px;
        background: linear-gradient(180deg, #e11d48 0%, #2563eb 100%);
        display: inline-block;
    }}
    .brand-title {{
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: var(--text);
    }}
    .brand-sub {{
        font-size: 0.82rem;
        color: var(--text-muted);
        margin-bottom: 1.1rem;
    }}

    .metric-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.25rem 1.4rem;
        box-shadow: var(--shadow);
        transition: border-color 0.18s ease, background-color 0.18s ease, transform 0.18s ease;
        margin-bottom: 0.5rem;
    }}
    .metric-card:hover {{
        background: var(--card-hover);
        border-color: var(--accent);
        transform: translateY(-1px);
    }}
    .metric-label {{
        font-size: 0.78rem;
        color: var(--text-muted);
        font-weight: 500;
    }}
    .metric-value {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.68rem;
        font-weight: 700;
        color: var(--text);
        letter-spacing: -0.03em;
        margin-top: 0.2rem;
    }}
    .metric-delta {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.73rem;
        font-weight: 500;
        margin-top: 0.45rem;
        padding: 2px 8px;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }}
    .delta-up {{ color: var(--green); background: var(--green-muted); }}
    .delta-down {{ color: var(--red); background: var(--red-muted); }}
    .delta-warn {{ color: var(--amber); background: var(--amber-muted); }}
    .delta-info {{ color: var(--accent); background: rgba(37,99,235,0.12); }}

    .chart-wrap,
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 1.2rem 1.25rem 0.65rem !important;
        box-shadow: var(--shadow) !important;
        transition: border-color 0.18s ease, background-color 0.18s ease !important;
        margin-bottom: 1.1rem !important;
    }}
    .chart-wrap:hover,
    [data-testid="stVerticalBlockBorderWrapper"]:hover {{
        border-color: var(--text-dim) !important;
    }}
    .chart-title {{
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--text);
    }}
    .chart-subtitle {{
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-bottom: 0.65rem;
    }}

    .table-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.25rem;
        box-shadow: var(--shadow);
        overflow-x: auto;
        margin-bottom: 1.1rem;
    }}
    .data-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 0.8rem;
    }}
    .data-table th {{
        text-align: left;
        padding: 0.65rem 0.8rem;
        color: var(--text-muted);
        font-weight: 600;
        font-size: 0.71rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border-bottom: 1px solid var(--border);
    }}
    .data-table td {{
        padding: 0.65rem 0.8rem;
        color: var(--text);
        border-bottom: 1px solid var(--border-subtle);
        transition: background-color 0.15s ease;
    }}
    .data-table tbody tr:hover td {{
        background-color: var(--card-hover);
    }}
    .data-table tr:last-child td {{
        border-bottom: none;
    }}
    .mono {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
    }}

    .badge {{
        display: inline-block;
        padding: 2px 9px;
        border-radius: 6px;
        font-size: 0.71rem;
        font-weight: 500;
    }}
    .badge-green {{ color: var(--green); background: var(--green-muted); }}
    .badge-red {{ color: var(--red); background: var(--red-muted); }}
    .badge-amber {{ color: var(--amber); background: var(--amber-muted); }}
    .badge-blue {{ color: var(--accent); background: rgba(37,99,235,0.12); }}
    </style>
    """,
    unsafe_allow_html=True,
)

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        family="DM Sans, sans-serif",
        color="#a1a1aa" if IS_DARK else "#52525b",
        size=11,
    ),
    margin=dict(l=8, r=8, t=12, b=8),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.05)" if IS_DARK else "rgba(0,0,0,0.05)",
        zerolinecolor="rgba(255,255,255,0.06)" if IS_DARK else "rgba(0,0,0,0.06)",
        tickfont=dict(size=10, color="#71717a"),
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.05)" if IS_DARK else "rgba(0,0,0,0.05)",
        zerolinecolor="rgba(255,255,255,0.06)" if IS_DARK else "rgba(0,0,0,0.06)",
        tickfont=dict(size=10, color="#71717a"),
    ),
)


def metric_card(label: str, value: str, delta: str | None = None, delta_type: str = "info") -> None:
    arrows = {"up": "↑", "down": "↓", "warn": "◆", "info": "→"}
    arrow = arrows.get(delta_type, "→")
    delta_html = (
        f'<div class="metric-delta delta-{delta_type}">{arrow} {html.escape(delta)}</div>'
        if delta
        else ""
    )
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{html.escape(label)}</div>
            <div class="metric-value">{html.escape(value)}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chart_card(title: str, subtitle: str, fig: go.Figure) -> None:
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="chart-title">{html.escape(title)}</div>
            <div class="chart-subtitle">{html.escape(subtitle)}</div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def format_readable_date(val: object) -> str:
    if val is None or pd.isna(val):
        return "—"
    ts = pd.to_datetime(val, errors="coerce")
    if pd.isna(ts):
        return str(val)
    return ts.strftime("%b %d, %Y")


def format_compact_int(num: float | int) -> str:
    n = float(num)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{int(n):,}"


# ---------------------------------------------------------------------------
# Data Layer (Gold Parquet Cache + Live BigQuery Fallback)
# ---------------------------------------------------------------------------
GOLD_CACHE_DIR = PROJECT_ROOT / "data" / "gold_cache"


@st.cache_data(ttl=600, show_spinner=False)
def load_gold_view(view_name: str) -> tuple[pd.DataFrame, str]:
    """Carrega dados da camada Gold (priorizando Parquet local ultra-rápido ou BigQuery ao vivo)."""
    source_mode = os.getenv("DASHBOARD_DATA_SOURCE", "auto").strip().lower()
    parquet_file = GOLD_CACHE_DIR / f"{view_name}.parquet"

    if source_mode != "bigquery" and parquet_file.exists():
        return pd.read_parquet(parquet_file), "Gold Parquet Cache"

    from google.cloud import bigquery

    project_id = os.getenv("GCP_PROJECT_ID", "netflix-analytics-de").strip()
    dataset_id = os.getenv("BQ_ANALYTICS_DATASET", "netflix_analytics").strip()
    location = os.getenv("GCP_LOCATION", "us-central1").strip()

    client = bigquery.Client(project=project_id, location=location)
    query = f"SELECT * FROM `{project_id}.{dataset_id}.{view_name}`"
    job_config = bigquery.QueryJobConfig(labels={"datacloud": "antigravity"})
    df = client.query(query, job_config=job_config).to_dataframe()
    return df, f"BigQuery Live ({project_id}.{dataset_id})"


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
head_left, head_right = st.columns([7, 1.4])
with head_left:
    st.markdown(
        """
        <div class="brand-bar">
            <span class="brand-dot"></span>
            <span class="brand-title">Streaming & RecSys Analytics Platform</span>
        </div>
        <div class="brand-sub">
            MovieLens Beliefs 2024 • Arquitetura Medallion & Star Schema (Parquet + Google BigQuery + dbt Core)
        </div>
        """,
        unsafe_allow_html=True,
    )
with head_right:
    theme_btn = "☀️ Light Mode" if IS_DARK else "🌙 Dark Mode"
    st.button(theme_btn, on_click=toggle_theme, width="stretch")

# ---------------------------------------------------------------------------
# Load Datasets with Graceful Error Handling
# ---------------------------------------------------------------------------
try:
    with st.spinner("Carregando modelos analíticos Gold..."):
        df_kpi, data_origin = load_gold_view("vw_kpi_overview")
        df_heatmap, _ = load_gold_view("vw_ratings_heatmap_monthly")
        df_top_movies, _ = load_gold_view("vw_top_movies_ranking")
        df_scatter_movies, _ = load_gold_view("vw_movies_popularity_vs_quality")
        df_genres, _ = load_gold_view("vw_genre_popularity_quality")
        df_users, _ = load_gold_view("vw_user_activity_summary")
        df_recsys, _ = load_gold_view("vw_recsys_belief_vs_reality")
        df_certainty, _ = load_gold_view("vw_recsys_certainty_calibration")
except Exception as exc:
    st.error(
        f"Não foi possível carregar as tabelas Gold ({exc}). "
        "Certifique-se de ter executado a ingestão (`python -m src.ingestion.run_pipeline`), "
        "o `dbt run` e o exportador (`python -m src.ingestion.export_gold_cache`)."
    )
    st.stop()

if df_kpi.empty:
    st.warning("As views analíticas retornaram vazias. Verifique a execução do dbt no BigQuery.")
    st.stop()

kpi = df_kpi.iloc[0]

st.markdown(
    f'<div style="margin-bottom:0.9rem;"><span class="badge badge-blue">Fonte Ativa: {html.escape(data_origin)}</span> '
    f'<span class="badge badge-green">Período Avaliado: {format_readable_date(kpi["min_rating_date"])} — {format_readable_date(kpi["max_rating_date"])}</span></div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Navigation Tabs
# ---------------------------------------------------------------------------
tab_overview, tab_movies, tab_genres_users, tab_recsys = st.tabs(
    [
        "Visão Geral & Sazonalidade",
        "Catálogo & Ranking de Filmes",
        "Gêneros & Audiência",
        "Lab de Recomendação (Beliefs vs. Realidade)",
    ]
)

# ===========================================================================
# TAB 1: Overview & Heatmap
# ===========================================================================
with tab_overview:
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card(
            "Total de Avaliações Reais",
            format_compact_int(kpi["total_ratings"]),
            delta=f"{int(kpi['total_active_users']):,} usuários ativos",
            delta_type="up",
        )
    with k2:
        metric_card(
            "Catálogo de Filmes",
            f"{int(kpi['total_catalog_movies']):,}",
            delta=f"{int(kpi['rated_movies_count']):,} com avaliações",
            delta_type="info",
        )
    with k3:
        metric_card(
            "Nota Média Global",
            f"{float(kpi['global_avg_rating']):.2f} ★",
            delta=f"Desvio Padrão σ = {float(kpi['global_stddev_rating']):.2f}",
            delta_type="up",
        )
    with k4:
        metric_card(
            "Interações de Expectativa (Beliefs)",
            format_compact_int(kpi["total_belief_records"]),
            delta=f"MAE Algoritmo: {float(kpi['global_system_mae']):.3f}",
            delta_type="warn",
        )

    min_yr = int(df_heatmap["rating_year"].min())
    max_yr = int(df_heatmap["rating_year"].max())
    default_start = max(min_yr, max_yr - 14)

    f_col1, f_col2 = st.columns([3, 1])
    with f_col1:
        yr_range = st.slider(
            "Recorte Temporal do Heatmap (Anos)",
            min_value=min_yr,
            max_value=max_yr,
            value=(default_start, max_yr),
        )
    with f_col2:
        heatmap_metric = st.selectbox(
            "Métrica de Intensidade",
            options=["Volume de Avaliações", "Nota Média Mensal"],
        )

    hm_filtered = df_heatmap[
        (df_heatmap["rating_year"] >= yr_range[0]) & (df_heatmap["rating_year"] <= yr_range[1])
    ].copy()

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    val_col = "total_ratings" if heatmap_metric == "Volume de Avaliações" else "avg_rating"

    pivot_hm = hm_filtered.pivot(index="rating_year", columns="rating_month", values=val_col)
    pivot_hm = pivot_hm.reindex(columns=range(1, 13))
    pivot_hm.columns = month_names
    pivot_hm = pivot_hm.sort_index(ascending=True)

    fig_hm = go.Figure(
        data=go.Heatmap(
            z=pivot_hm.values,
            x=pivot_hm.columns,
            y=[str(y) for y in pivot_hm.index],
            colorscale="Blues" if heatmap_metric == "Volume de Avaliações" else "Viridis",
            hoverongaps=False,
            hovertemplate="Ano %{y} • %{x}<br>Valor: %{z:,}<extra></extra>",
        )
    )
    fig_hm.update_layout(**PLOT_LAYOUT, height=430)
    render_chart_card(
        "Evolução de Ratings ao Longo do Tempo (Heatmap Ano × Mês)",
        "Intensidade mensal de engajamento e sazonalidade de avaliações na plataforma",
        fig_hm,
    )

    annual_df = (
        hm_filtered.groupby("rating_year", as_index=False)
        .agg(total_ratings=("total_ratings", "sum"), avg_rating=("avg_rating", "mean"))
        .sort_values("rating_year")
    )
    fig_annual = px.bar(
        annual_df,
        x="rating_year",
        y="total_ratings",
        color_discrete_sequence=[ACCENT],
        labels={"rating_year": "Ano", "total_ratings": "Total de Avaliações"},
    )
    fig_annual.update_layout(**PLOT_LAYOUT, height=280)
    render_chart_card(
        "Volume Consolidado Anual de Avaliações",
        "Crescimento histórico da base ativa no recorte selecionado",
        fig_annual,
    )

# ===========================================================================
# TAB 2: Catalog, Top 10 & Popularity vs Quality Scatter
# ===========================================================================
with tab_movies:
    ctrl1, ctrl2, ctrl3 = st.columns([1.4, 1.6, 1.0])
    genres_available = ["Todos"] + sorted(df_top_movies["primary_genre"].dropna().unique().tolist())

    with ctrl1:
        min_votes = st.selectbox(
            "Corte Mínimo de Avaliações",
            options=[50, 100, 250, 500, 1000],
            index=1,
        )
    with ctrl2:
        selected_genre = st.selectbox("Filtrar por Gênero Principal", options=genres_available)
    with ctrl3:
        top_n = st.selectbox("Quantidade no Ranking", options=[10, 15, 20], index=0)

    movies_f = df_top_movies[df_top_movies["total_ratings"] >= min_votes].copy()
    scatter_f = df_scatter_movies[df_scatter_movies["total_ratings"] >= min_votes].copy()
    if selected_genre != "Todos":
        movies_f = movies_f[movies_f["primary_genre"] == selected_genre]
        scatter_f = scatter_f[scatter_f["primary_genre"] == selected_genre]

    if movies_f.empty:
        st.info("Nenhum filme atende aos filtros selecionados. Reduza o corte mínimo de avaliações.")
    else:
        col_top_qual, col_top_pop = st.columns(2)

        with col_top_qual:
            top_qual = movies_f.sort_values("weighted_score", ascending=False).head(top_n).iloc[::-1]
            fig_top_q = px.bar(
                top_qual,
                x="weighted_score",
                y="clean_title",
                orientation="h",
                color_discrete_sequence=[BRAND_RED],
                hover_data={"avg_rating": True, "total_ratings": ":,", "release_year": True},
                labels={"weighted_score": "Bayesian Score", "clean_title": ""},
            )
            fig_top_q.update_layout(**PLOT_LAYOUT, height=390)
            fig_top_q.update_xaxes(range=[3.5, 5.0])
            render_chart_card(
                f"Ranking de Filmes — Top {top_n} Melhor Qualidade (Score Bayesiano)",
                f"Nota ponderada pelo volume de votos (mín. {min_votes} avaliações)",
                fig_top_q,
            )

        with col_top_pop:
            # Usa df_scatter_movies completo (ou top_movies) ordenado por total_ratings
            pop_pool = scatter_f if not scatter_f.empty else movies_f
            top_pop = pop_pool.sort_values("total_ratings", ascending=False).head(top_n).iloc[::-1]
            fig_top_p = px.bar(
                top_pop,
                x="total_ratings",
                y="clean_title",
                orientation="h",
                color_discrete_sequence=[ACCENT],
                hover_data={"avg_rating": True, "release_year": True},
                labels={"total_ratings": "Total de Avaliações", "clean_title": ""},
            )
            fig_top_p.update_layout(**PLOT_LAYOUT, height=390)
            render_chart_card(
                f"Filmes Mais Avaliados — Top {top_n} em Popularidade",
                "Títulos de maior alcance e volume histórico de avaliações",
                fig_top_p,
            )

        if not scatter_f.empty:
            quad_colors = {
                "Muito Popular + Bem Avaliado": GREEN,
                "Joia Cult (Bem Avaliado, Menos Popular)": ACCENT,
                "Popular com Nota Abaixo da Média": AMBER,
                "Baixa Popularidade + Nota Baixa": RED,
            }
            fig_sc_m = px.scatter(
                scatter_f.head(1500),
                x="total_ratings",
                y="avg_rating",
                color="quadrant_label",
                color_discrete_map=quad_colors,
                hover_name="title",
                hover_data={
                    "primary_genre": True,
                    "total_ratings": ":,",
                    "avg_rating": ":.2f",
                    "stddev_rating": ":.2f",
                    "quadrant_label": False,
                },
                log_x=True,
                opacity=0.78,
                labels={
                    "total_ratings": "Popularidade (Total de Avaliações — Escala Log)",
                    "avg_rating": "Qualidade (Nota Média ★)",
                    "quadrant_label": "Quadrante",
                },
            )
            fig_sc_m.update_layout(
                **PLOT_LAYOUT,
                height=440,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            )
            render_chart_card(
                "Filmes: Popularidade vs. Qualidade (Scatter Plot por Quadrantes)",
                "Relação entre alcance de público e aprovação crítica (passe o mouse para ver título e desvio padrão σ)",
                fig_sc_m,
            )

# ===========================================================================
# TAB 3: Genres & User Activity Table
# ===========================================================================
with tab_genres_users:
    g_col1, g_col2 = st.columns(2)

    genres_sorted = df_genres.sort_values("total_ratings", ascending=True)
    with g_col1:
        fig_g_bar = px.bar(
            genres_sorted,
            x="total_ratings",
            y="genre_name",
            orientation="h",
            color_discrete_sequence=[ACCENT],
            hover_data={"total_movies": ":,", "avg_rating": ":.2f"},
            labels={"total_ratings": "Total de Avaliações", "genre_name": ""},
        )
        fig_g_bar.update_layout(**PLOT_LAYOUT, height=430)
        render_chart_card(
            "Popularidade dos Gêneros Cinematográficos",
            "Volume total de avaliações recebidas por gênero (explosão N:N normalizada)",
            fig_g_bar,
        )

    with g_col2:
        fig_g_sc = px.scatter(
            df_genres,
            x="total_ratings",
            y="avg_rating",
            size="total_movies",
            text="genre_name",
            color="stddev_rating",
            color_continuous_scale="RdYlGn_r",
            hover_data={
                "total_movies": ":,",
                "ratings_per_movie": ":,.1f",
                "stddev_rating": ":.3f",
            },
            labels={
                "total_ratings": "Popularidade (Total de Avaliações)",
                "avg_rating": "Qualidade Média (★)",
                "stddev_rating": "Desvio σ",
            },
        )
        fig_g_sc.update_traces(textposition="top center", textfont=dict(size=10))
        fig_g_sc.update_layout(**PLOT_LAYOUT, height=430)
        render_chart_card(
            "Gênero: Popularidade vs. Qualidade (Scatter Plot)",
            "Tamanho da bolha = tamanho do catálogo • Cor = divergência de opiniões (desvio padrão σ)",
            fig_g_sc,
        )

    u_ctrl1, u_ctrl2 = st.columns([2, 1])
    tiers = ["Todos"] + sorted(df_users["activity_tier"].dropna().unique().tolist())
    with u_ctrl1:
        selected_tier = st.selectbox("Filtrar Segmento de Atividade de Usuários", options=tiers)
    with u_ctrl2:
        rows_to_show = st.selectbox("Registros Exibidos", options=[15, 30, 50], index=0)

    users_view = df_users.copy()
    if selected_tier != "Todos":
        users_view = users_view[users_view["activity_tier"] == selected_tier]
    users_view = users_view.head(rows_to_show)

    tier_badge_map = {
        "Power Reviewer (500+)": "badge-green",
        "Heavy Watcher (100-499)": "badge-blue",
        "Engaged (20-99)": "badge-amber",
        "Casual (<20)": "badge-red",
    }

    rows_html = []
    for _, row in users_view.iterrows():
        tier_str = str(row["activity_tier"])
        badge_cls = tier_badge_map.get(tier_str, "badge-blue")
        rows_html.append(
            f"<tr>"
            f'<td class="mono">#{int(row["user_id"])}</td>'
            f'<td><span class="badge {badge_cls}">{html.escape(tier_str)}</span></td>'
            f'<td class="mono">{int(row["total_ratings"]):,}</td>'
            f'<td class="mono">{float(row["avg_rating"]):.2f} ★</td>'
            f'<td class="mono">{float(row["stddev_rating"]):.2f}</td>'
            f'<td>{format_readable_date(row["first_rating_date"])}</td>'
            f'<td>{format_readable_date(row["last_rating_date"])}</td>'
            f'<td class="mono">{int(row["active_days_span"]):,}d</td>'
            f"</tr>"
        )

    st.markdown(
        f"""
        <div class="table-card">
            <div class="chart-title">Atividade de Usuários — Ranking Comportamental</div>
            <div class="chart-subtitle">Volume de avaliações, rigor crítico (média e σ) e janela de retenção na plataforma</div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>User ID</th>
                        <th>Segmento</th>
                        <th>Avaliações</th>
                        <th>Nota Média</th>
                        <th>Desvio (σ)</th>
                        <th>Primeira Avaliação</th>
                        <th>Última Avaliação</th>
                        <th>Retenção</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows_html)}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ===========================================================================
# TAB 4: RecSys Lab — Beliefs vs Reality (Portfolio Differentiator)
# ===========================================================================
with tab_recsys:
    r1, r2, r3, r4 = st.columns(4)
    best_conv_row = df_recsys.sort_values("watch_conversion_pct", ascending=False).iloc[0]
    best_surprise_row = df_recsys.sort_values("avg_surprise_gap", ascending=False).iloc[0]

    with r1:
        metric_card(
            "Pares Avaliados (Já Assistidos)",
            f"{int(kpi['verified_watch_beliefs']):,}",
            delta="Base real pós-consumo",
            delta_type="info",
        )
    with r2:
        metric_card(
            "MAE do Motor de Recomendação",
            f"{float(kpi['global_system_mae']):.3f} ★",
            delta="Erro médio absoluto do sistema",
            delta_type="up",
        )
    with r3:
        metric_card(
            "Maior Taxa de Descoberta",
            f"{float(best_conv_row['watch_conversion_pct']):.1f}%",
            delta=str(best_conv_row["discovery_source"]),
            delta_type="up",
        )
    with r4:
        metric_card(
            "Canal Mais Surpreendente",
            f"{float(best_surprise_row['avg_surprise_gap']):+.3f} ★",
            delta=str(best_surprise_row["discovery_source"]),
            delta_type="warn",
        )

    rc1, rc2 = st.columns(2)
    with rc1:
        melted = df_recsys.melt(
            id_vars=["discovery_source"],
            value_vars=[
                "avg_user_predicted_rating",
                "avg_system_predicted_rating",
                "avg_actual_watched_rating",
            ],
            var_name="metric_type",
            value_name="rating_value",
        )
        label_map = {
            "avg_user_predicted_rating": "Expectativa Humana (Antes)",
            "avg_system_predicted_rating": "Previsão do Algoritmo",
            "avg_actual_watched_rating": "Nota Real (Pós-Assistir)",
        }
        melted["metric_label"] = melted["metric_type"].map(label_map)

        fig_belief = px.bar(
            melted,
            x="discovery_source",
            y="rating_value",
            color="metric_label",
            barmode="group",
            color_discrete_sequence=[AMBER, ACCENT, GREEN],
            labels={"discovery_source": "Estratégia de Recomendação", "rating_value": "Nota Média (★)", "metric_label": ""},
        )
        fig_belief.update_layout(
            **PLOT_LAYOUT,
            height=380,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        )
        fig_belief.update_yaxes(range=[2.5, 4.6])
        render_chart_card(
            "Expectativa Humana vs. Algoritmo vs. Nota Real por Estratégia",
            "Comparação direta entre o que o usuário esperava, o que o modelo previu e a avaliação real",
            fig_belief,
        )

    with rc2:
        cert_plot_df = df_certainty.rename(
            columns={
                "avg_expected_rating": "Expectativa do Usuário",
                "avg_algorithm_rating": "Previsão do Algoritmo",
            }
        )
        fig_cert = px.line(
            cert_plot_df,
            x="certainty_label",
            y=["Expectativa do Usuário", "Previsão do Algoritmo"],
            markers=True,
            color_discrete_sequence=[BRAND_RED, ACCENT],
            labels={"certainty_label": "Nível de Certeza do Usuário", "value": "Nota Média (★)", "variable": ""},
        )
        fig_cert.update_layout(
            **PLOT_LAYOUT,
            height=380,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        )
        render_chart_card(
            "Calibração de Confiança do Usuário (Escala 1 a 5)",
            "Como a certeza declarada pelo espectador se alinha à nota prevista pelo algoritmo",
            fig_cert,
        )

    rec_rows = []
    for _, row in df_recsys.iterrows():
        gap = float(row["avg_surprise_gap"]) if pd.notna(row["avg_surprise_gap"]) else 0.0
        gap_cls = "badge-green" if gap >= 0 else "badge-amber"
        rec_rows.append(
            f"<tr>"
            f'<td><strong>{html.escape(str(row["discovery_source"]))}</strong></td>'
            f'<td class="mono">{int(row["total_impressions"]):,}</td>'
            f'<td class="mono">{float(row["watch_conversion_pct"]):.2f}%</td>'
            f'<td class="mono">{float(row["avg_user_predicted_rating"]):.2f} ★</td>'
            f'<td class="mono">{float(row["avg_system_predicted_rating"]):.2f} ★</td>'
            f'<td class="mono">{float(row["avg_actual_watched_rating"]):.2f} ★</td>'
            f'<td><span class="badge {gap_cls}">{gap:+.3f} ★</span></td>'
            f'<td class="mono">{float(row["system_mae"]):.3f}</td>'
            f"</tr>"
        )

    st.markdown(
        f"""
        <div class="table-card">
            <div class="chart-title">Matriz de Performance das Estratégias de Descoberta (<span class="mono">belief_data</span>)</div>
            <div class="chart-subtitle">Métricas consolidadas para tomada de decisão de Produto e Machine Learning</div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Canal de Seleção</th>
                        <th>Impressões</th>
                        <th>Taxa Já Assistido</th>
                        <th>Expectativa Usuário</th>
                        <th>Nota Sistema</th>
                        <th>Nota Real</th>
                        <th>Surprise Gap</th>
                        <th>MAE Sistema</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rec_rows)}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

