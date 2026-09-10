"""Graficos Plotly do Monitor B3.

O template ainda e claro. A Etapa 5 troca `TEMPLATE` e as cores por
`theme.py`, sem mexer no resto do arquivo.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import metrics as calc

TEMPLATE = "plotly_white"
POSITIVO = "#00C087"
NEGATIVO = "#F43F5E"
ACENTO = "#3B82F6"
SECUNDARIO = "#8B95A5"
SMA_CURTA = "#F59E0B"
SMA_LONGA = "#8B5CF6"

ALTURA_PRECO = 560
ALTURA_AUXILIAR = 260


def _sem_dados(mensagem: str) -> go.Figure:
    figura = go.Figure()
    figura.add_annotation(
        text=mensagem, showarrow=False, font=dict(color=SECUNDARIO, size=14)
    )
    figura.update_layout(
        template=TEMPLATE,
        height=ALTURA_AUXILIAR,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return figura


def preco_com_medias(
    df: pd.DataFrame, nome: str, tipo: str = "Candlestick", intervalo=None
) -> go.Figure:
    """Preco com SMA 50 e SMA 200, e volume num subplot inferior.

    As medias sao calculadas sobre a serie inteira e so depois o eixo e
    limitado a `intervalo`, senao a SMA 200 nasceria vazia na janela curta.
    """
    if df is None or df.empty or "Close" not in df.columns:
        return _sem_dados("Sem cotacoes para este ativo.")

    tem_volume = "Volume" in df.columns and float(df["Volume"].fillna(0).sum()) > 0
    figura = make_subplots(
        rows=2 if tem_volume else 1,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.74, 0.26] if tem_volume else [1.0],
    )

    tem_ohlc = all(coluna in df.columns for coluna in ("Open", "High", "Low", "Close"))
    if tipo == "Candlestick" and tem_ohlc:
        figura.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name=nome,
                increasing_line_color=POSITIVO,
                decreasing_line_color=NEGATIVO,
            ),
            row=1,
            col=1,
        )
    else:
        figura.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Close"],
                name=nome,
                mode="lines",
                line=dict(color=ACENTO, width=1.6),
            ),
            row=1,
            col=1,
        )

    for janela, cor, rotulo in ((50, SMA_CURTA, "SMA 50"), (200, SMA_LONGA, "SMA 200")):
        media = calc.media_movel(df["Close"], janela)
        if media.empty:
            continue
        figura.add_trace(
            go.Scatter(
                x=media.index,
                y=media,
                name=rotulo,
                mode="lines",
                line=dict(color=cor, width=1.2),
            ),
            row=1,
            col=1,
        )

    if tem_volume:
        figura.add_trace(
            go.Bar(
                x=df.index,
                y=df["Volume"],
                name="Volume",
                marker_color=SECUNDARIO,
                opacity=0.55,
            ),
            row=2,
            col=1,
        )
        figura.update_yaxes(title_text="Volume", row=2, col=1)

    figura.update_layout(
        template=TEMPLATE,
        height=ALTURA_PRECO,
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode="x unified",
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
    )
    figura.update_yaxes(title_text="Preco", row=1, col=1)
    _limitar_eixo(figura, intervalo, df)
    return figura


def _limitar_eixo(figura: go.Figure, intervalo, df: pd.DataFrame) -> None:
    """Recorta o eixo x e reescala o y ao trecho visivel."""
    if not intervalo:
        return
    inicio, fim = pd.Timestamp(intervalo[0]), pd.Timestamp(intervalo[1])
    figura.update_xaxes(range=[inicio, fim])

    visivel = df.loc[(df.index >= inicio) & (df.index <= fim)]
    if visivel.empty or "Close" not in visivel.columns:
        return
    baixa = float(visivel["Low"].min()) if "Low" in visivel else float(visivel["Close"].min())
    alta = float(visivel["High"].max()) if "High" in visivel else float(visivel["Close"].max())
    if not (baixa < alta):
        return
    folga = (alta - baixa) * 0.06
    figura.update_yaxes(range=[baixa - folga, alta + folga], row=1, col=1)


def curva_drawdown(precos, nome: str = "Drawdown") -> go.Figure:
    curva = calc.drawdown(precos)
    if curva.empty:
        return _sem_dados("Sem serie suficiente para o drawdown.")

    figura = go.Figure(
        go.Scatter(
            x=curva.index,
            y=curva * 100,
            name=nome,
            mode="lines",
            line=dict(color=NEGATIVO, width=1.4),
            fill="tozeroy",
            fillcolor="rgba(244, 63, 94, 0.18)",
        )
    )
    figura.update_layout(
        template=TEMPLATE,
        height=ALTURA_AUXILIAR,
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode="x unified",
        yaxis_title="Drawdown %",
        showlegend=False,
    )
    return figura


def linhas_margens(tabela: pd.DataFrame) -> go.Figure:
    """Margem bruta, EBITDA e liquida por trimestre."""
    if tabela is None or tabela.empty:
        return _sem_dados("O Yahoo nao publica margens trimestrais para esta acao.")

    cores = {"Margem bruta": ACENTO, "Margem EBITDA": SMA_CURTA, "Margem liquida": POSITIVO}
    figura = go.Figure()
    for coluna in tabela.columns:
        figura.add_trace(
            go.Scatter(
                x=tabela.index,
                y=tabela[coluna] * 100,
                name=coluna,
                mode="lines+markers",
                line=dict(color=cores.get(coluna, SECUNDARIO), width=1.8),
            )
        )
    figura.update_layout(
        template=TEMPLATE,
        height=360,
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode="x unified",
        yaxis_title="Margem %",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
    )
    return figura


def barras_balanco(tabela: pd.DataFrame) -> go.Figure:
    """Divida bruta, caixa e patrimonio liquido por trimestre."""
    if tabela is None or tabela.empty:
        return _sem_dados("O Yahoo nao publica balanco trimestral para esta acao.")

    maximo = float(tabela.abs().to_numpy().max())
    divisor, unidade = (1e9, "R$ bilhoes") if maximo >= 1e9 else (1e6, "R$ milhoes")

    cores = {"Divida bruta": NEGATIVO, "Caixa": POSITIVO, "Patrimonio liquido": ACENTO}
    figura = go.Figure()
    for coluna in tabela.columns:
        figura.add_trace(
            go.Bar(
                x=tabela.index,
                y=tabela[coluna] / divisor,
                name=coluna,
                marker_color=cores.get(coluna, SECUNDARIO),
            )
        )
    figura.update_layout(
        template=TEMPLATE,
        height=360,
        barmode="group",
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode="x unified",
        yaxis_title=unidade,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
    )
    return figura


def serie_volatilidade(precos, janela: int = 21, intervalo=None) -> go.Figure:
    serie = calc.volatilidade_movel(precos, janela)
    if serie.empty:
        return _sem_dados("Sem serie suficiente para a volatilidade movel.")
    if intervalo:
        serie = serie[
            (serie.index >= pd.Timestamp(intervalo[0]))
            & (serie.index <= pd.Timestamp(intervalo[1]))
        ]
    serie = serie.dropna()
    if serie.empty:
        return _sem_dados("Sem serie suficiente para a volatilidade movel.")

    figura = go.Figure(
        go.Scatter(
            x=serie.index,
            y=serie * 100,
            mode="lines",
            line=dict(color=ACENTO, width=1.4),
        )
    )
    figura.update_layout(
        template=TEMPLATE,
        height=ALTURA_AUXILIAR,
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode="x unified",
        yaxis_title=f"Volatilidade {janela}d anualizada %",
        showlegend=False,
    )
    return figura
