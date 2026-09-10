"""Identidade visual do Monitor B3.

Fonte unica das cores. `charts.py` importa daqui, e `aplicar` injeta o CSS
que o `.streamlit/config.toml` sozinho nao alcanca.
"""

from __future__ import annotations

import streamlit as st

CORES = {
    "fundo": "#0E1217",
    "cartao": "#1B222C",
    "borda": "#2A3441",
    "positivo": "#00C087",
    "negativo": "#F43F5E",
    "texto": "#F1F5F9",
    "texto_secundario": "#8B95A5",
    "acento": "#3B82F6",
}

# Series auxiliares dos graficos, fora da paleta obrigatoria.
SMA_CURTA = "#F59E0B"
SMA_LONGA = "#8B5CF6"

PALETA = [
    CORES["acento"],
    CORES["positivo"],
    SMA_CURTA,
    SMA_LONGA,
    CORES["negativo"],
    "#06B6D4",
    "#EC4899",
    "#84CC16",
    "#F97316",
    "#14B8A6",
    "#A855F7",
]

TEMPLATE_PLOTLY = "plotly_dark"

FONTE_TEXTO = "'Inter', 'Roboto', -apple-system, 'Segoe UI', sans-serif"
FONTE_NUMEROS = "'Consolas', 'SFMono-Regular', 'Menlo', monospace"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {{
    font-family: {fonte_texto};
    background-color: {fundo};
    color: {texto};
}}

/* Numeros em tabelas e metricas pedem largura fixa para alinhar. */
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"],
[data-testid="stDataFrame"] div[role="gridcell"] {{
    font-family: {fonte_numeros};
    font-variant-numeric: tabular-nums;
}}

[data-testid="stMetric"] {{
    background-color: {cartao};
    border: 1px solid {borda};
    border-radius: 10px;
    padding: 14px 16px;
}}
[data-testid="stMetricLabel"] p {{
    color: {texto_secundario};
    font-size: 0.82rem;
}}
[data-testid="stMetricValue"] {{
    font-size: 1.6rem;
    color: {texto};
}}

[data-testid="stSidebar"] {{
    background-color: {cartao};
    border-right: 1px solid {borda};
}}

[data-testid="stDataFrame"], [data-testid="stPlotlyChart"] {{
    border: 1px solid {borda};
    border-radius: 10px;
    overflow: hidden;
}}

.stTabs [data-baseweb="tab-list"] {{
    gap: 6px;
    border-bottom: 1px solid {borda};
}}
.stTabs [data-baseweb="tab"] {{
    color: {texto_secundario};
}}
.stTabs [aria-selected="true"] {{
    color: {acento};
}}

a, a:visited {{ color: {acento}; }}

hr {{ border-color: {borda}; }}

[data-testid="stCaptionContainer"] p {{
    color: {texto_secundario};
}}
</style>
"""


def aplicar() -> None:
    """Injeta o CSS do tema. Chamar uma vez, logo apos set_page_config."""
    st.markdown(
        _CSS.format(
            fonte_texto=FONTE_TEXTO,
            fonte_numeros=FONTE_NUMEROS,
            **CORES,
        ),
        unsafe_allow_html=True,
    )
