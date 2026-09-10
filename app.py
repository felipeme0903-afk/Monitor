"""Monitor B3 - interface Streamlit.

Etapa 1: barra lateral com os controles globais e a Aba 3 (screener do
setor). As demais abas ficam sinalizadas ate as etapas seguintes.

Rodar com:  streamlit run app.py
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st

import data as fonte
import metrics as calc
import universe as uni

st.set_page_config(page_title="Monitor B3", page_icon="B3", layout="wide")

JANELAS = {
    "1M": 30,
    "3M": 90,
    "6M": 180,
    "YTD": None,
    "1A": 365,
    "2A": 730,
    "3A": 1095,
    "5A": 1825,
    "Personalizada": None,
}

COLUNAS_SCREENER = [
    "Ticker",
    "Nome",
    "Preco",
    "Retorno periodo %",
    "Volatilidade 252d %",
    "Beta 2A",
    "Dist. minima 52s %",
    "Dist. maxima 52s %",
    "P/L LTM",
    "EV/EBITDA",
    "P/VP",
    "DY LTM %",
    "ROE %",
]


# ------------------------------------------------------------ barra lateral


def barra_lateral() -> dict:
    st.sidebar.title("Monitor B3")

    janela = st.sidebar.radio("Janela temporal", list(JANELAS.keys()), index=4)

    inicio_custom = fim_custom = None
    if janela == "Personalizada":
        hoje = dt.date.today()
        inicio_custom = st.sidebar.date_input(
            "Inicio", value=hoje - dt.timedelta(days=365), max_value=hoje
        )
        fim_custom = st.sidebar.date_input("Fim", value=hoje, max_value=hoje)

    benchmark = st.sidebar.selectbox(
        "Benchmark",
        list(uni.BENCHMARKS.keys()),
        format_func=lambda t: f"{t} - {uni.BENCHMARKS[t]}",
    )
    periodicidade = st.sidebar.selectbox("Periodicidade do beta", ["Semanal", "Diaria"])
    setor = st.sidebar.selectbox("Setor", uni.setores(), index=uni.setores().index("Financeiro"))

    disponiveis = uni.tickers_do_setor(setor)
    escolhidos = st.sidebar.multiselect(
        "Tickers", disponiveis, default=disponiveis,
        format_func=lambda t: f"{t} - {uni.nome_de(t)}",
    )

    st.sidebar.divider()
    if st.sidebar.button("Atualizar dados", width="stretch"):
        st.cache_data.clear()
        apagados = fonte.limpar_cache_de_disco()
        st.sidebar.success(f"Cache limpo ({apagados} arquivos em disco).")
        st.rerun()

    return {
        "janela": janela,
        "inicio_custom": inicio_custom,
        "fim_custom": fim_custom,
        "benchmark": benchmark,
        "periodicidade": periodicidade,
        "setor": setor,
        "tickers": escolhidos,
    }


def intervalo(controles: dict, ultimo_pregao: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Converte a escolha da barra lateral em (inicio, fim)."""
    janela = controles["janela"]
    fim = pd.Timestamp(ultimo_pregao)

    if janela == "Personalizada":
        inicio = pd.Timestamp(controles["inicio_custom"] or fim - pd.Timedelta(days=365))
        fim = pd.Timestamp(controles["fim_custom"] or fim)
        if inicio > fim:
            inicio, fim = fim, inicio
        return inicio, fim

    if janela == "YTD":
        # P_0 vira o ultimo pregao do ano anterior, via `asof` em metrics.
        return pd.Timestamp(year=fim.year, month=1, day=1), fim

    return fim - pd.Timedelta(days=JANELAS[janela]), fim


# ---------------------------------------------------------------- screener


def montar_screener(
    controles: dict,
    cotacoes: dict[str, pd.DataFrame],
    fundamentos: dict[str, dict],
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
) -> pd.DataFrame:
    bench_df = cotacoes.get(controles["benchmark"])
    bench_adj = bench_df["Adj Close"] if bench_df is not None else pd.Series(dtype=float)
    observacoes = calc.SEMANAS_BETA_2A if controles["periodicidade"] == "Semanal" else 504

    linhas = []
    for ticker in controles["tickers"]:
        chave = uni.para_yahoo(ticker)
        df = cotacoes.get(chave)
        if df is None:
            continue

        adj, close = df["Adj Close"], df["Close"]
        fund = fundamentos.get(chave, {})
        da_minima, da_maxima = calc.distancia_52_semanas(close, fim)

        linhas.append(
            {
                "Ticker": ticker,
                "Nome": uni.nome_de(ticker),
                "Preco": calc.ultimo_valor(close, fim),
                "Retorno periodo %": _pct(calc.retorno_periodo(adj, inicio, fim)),
                "Volatilidade 252d %": _pct(calc.volatilidade_anualizada(adj, 252, fim)),
                "Beta 2A": calc.beta(adj, bench_adj, controles["periodicidade"], observacoes, fim),
                "Dist. minima 52s %": _pct(da_minima),
                "Dist. maxima 52s %": _pct(da_maxima),
                "P/L LTM": calc.preco_lucro(fund, fim),
                "EV/EBITDA": calc.ev_ebitda(fund, fim),
                "P/VP": calc.preco_valor_patrimonial(fund, fim),
                "DY LTM %": _pct(calc.dividend_yield_ltm(fonte.proventos(df), close, fim)),
                "ROE %": _pct(calc.roe(fund, fim)),
            }
        )

    if not linhas:
        return pd.DataFrame(columns=COLUNAS_SCREENER)
    return pd.DataFrame(linhas)[COLUNAS_SCREENER]


def _pct(valor) -> float:
    return np.nan if pd.isna(valor) else float(valor) * 100


def aplicar_filtros(tabela: pd.DataFrame) -> pd.DataFrame:
    if tabela.empty:
        return tabela

    coluna_a, coluna_b, coluna_c = st.columns(3)
    pl_max = coluna_a.slider("P/L maximo", 0, 100, 100, step=1)
    vol_max = coluna_b.slider("Volatilidade 252d maxima %", 0, 150, 150, step=5)
    dy_min = coluna_c.slider("DY LTM minimo %", 0.0, 20.0, 0.0, step=0.5)
    st.caption("Linhas sem dado suficiente (n/d) nao sao removidas pelos filtros.")

    filtrada = tabela
    filtrada = filtrada[filtrada["P/L LTM"].isna() | (filtrada["P/L LTM"] <= pl_max)]
    filtrada = filtrada[
        filtrada["Volatilidade 252d %"].isna() | (filtrada["Volatilidade 252d %"] <= vol_max)
    ]
    filtrada = filtrada[filtrada["DY LTM %"].isna() | (filtrada["DY LTM %"] >= dy_min)]
    return filtrada


def _cor_do_sinal(valor) -> str:
    if pd.isna(valor):
        return ""
    return "color: #00C087" if valor >= 0 else "color: #F43F5E"


def exibir_tabela(tabela: pd.DataFrame) -> None:
    if tabela.empty:
        st.info("Nenhum ticker atende aos filtros escolhidos.")
        return

    duas_casas = {
        coluna: "{:,.2f}"
        for coluna in tabela.columns
        if coluna not in ("Ticker", "Nome")
    }
    estilo = (
        tabela.style.format(duas_casas, na_rep="n/d")
        .map(_cor_do_sinal, subset=["Retorno periodo %", "DY LTM %", "ROE %"])
    )
    st.dataframe(estilo, width="stretch", hide_index=True)


# -------------------------------------------------------------------- main


def main() -> None:
    controles = barra_lateral()

    do_setor = [uni.para_yahoo(t) for t in uni.tickers_do_setor(controles["setor"])]
    alvo = tuple(dict.fromkeys(do_setor + [controles["benchmark"]]))

    cotacoes, falhas_preco = fonte.baixar_cotacoes(alvo)
    if not cotacoes:
        st.error(
            "Nenhuma cotacao foi baixada. Verifique a conexao e clique em "
            "Atualizar dados na barra lateral."
        )
        _listar_falhas(falhas_preco, {})
        return

    ultimo_pregao = max(df.index.max() for df in cotacoes.values())
    inicio, fim = intervalo(controles, ultimo_pregao)

    st.title(f"Screener - {controles['setor']}")
    st.caption(
        f"Janela {inicio:%d/%m/%Y} a {fim:%d/%m/%Y} | benchmark {controles['benchmark']} | "
        f"beta {controles['periodicidade'].lower()} | ultimo pregao {ultimo_pregao:%d/%m/%Y}"
    )

    abas = st.tabs(
        ["Panorama Macro", "Setores", "Screener", "Raio-X", "Fundamentos"]
    )
    for indice, etapa in ((0, 4), (1, 4), (3, 2), (4, 3)):
        with abas[indice]:
            st.info(f"Aba prevista para a Etapa {etapa} da implementacao.")

    with abas[2]:
        if not controles["tickers"]:
            st.warning("Selecione ao menos um ticker na barra lateral.")
            return

        selecionados = tuple(uni.para_yahoo(t) for t in controles["tickers"])
        fundamentos, falhas_fund = fonte.carregar_fundamentos(selecionados)

        tabela = montar_screener(controles, cotacoes, fundamentos, inicio, fim)
        exibir_tabela(aplicar_filtros(tabela))
        _listar_falhas(falhas_preco, falhas_fund)


def _listar_falhas(falhas_preco: dict, falhas_fund: dict) -> None:
    if not falhas_preco and not falhas_fund:
        return

    total = len(set(falhas_preco) | set(falhas_fund))
    st.warning(f"{total} ticker(s) com dado incompleto. Detalhes abaixo.")
    with st.expander("Tickers que falharam"):
        registros = [
            {"Ticker": uni.de_yahoo(t), "Origem": "Cotacoes", "Motivo": motivo}
            for t, motivo in sorted(falhas_preco.items())
        ] + [
            {"Ticker": uni.de_yahoo(t), "Origem": "Demonstrativos", "Motivo": motivo}
            for t, motivo in sorted(falhas_fund.items())
        ]
        st.dataframe(pd.DataFrame(registros), width="stretch", hide_index=True)


if __name__ == "__main__":
    main()
