"""Monitor B3 - interface Streamlit.

Cinco abas: panorama macro, setores lado a lado, screener do setor,
raio-X individual e fundamentos.

Rodar com:  streamlit run app.py
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st

import charts as graf
import data as fonte
import metrics as calc
import theme
import universe as uni

st.set_page_config(page_title="Monitor B3", page_icon="B3", layout="wide")
theme.aplicar()

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
    "Market Equity/Debt",
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
        fund = _fundamentos_com_market_cap(chave, fundamentos.get(chave, {}), close, fim)

        linhas.append(
            {
                "Ticker": ticker,
                "Nome": uni.nome_de(ticker),
                "Preco": calc.ultimo_valor(close, fim),
                "Retorno periodo %": _pct(calc.retorno_periodo(adj, inicio, fim)),
                "Volatilidade 252d %": _pct(calc.volatilidade_anualizada(adj, 252, fim)),
                "Beta 2A": calc.beta(adj, bench_adj, controles["periodicidade"], observacoes, fim),
                "Market Equity/Debt": calc.market_equity_divida(fund, fim),
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


def _fundamentos_com_market_cap(
    chave: str, fund: dict, close: pd.Series | None, fim: pd.Timestamp
) -> dict:
    """Garante market cap: o do Yahoo ou preco x acoes do balanco."""
    if close is None:
        return fund
    return calc.com_market_cap(fund, close, fim, uni.acoes_por_unit(chave))


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


# ------------------------------------------------------------ kpis do topo


def variacao_diaria(df: pd.DataFrame, fim: pd.Timestamp) -> tuple[float, float]:
    """(ultimo fechamento, variacao contra o pregao anterior)."""
    if df is None or "Close" not in df.columns:
        return np.nan, np.nan
    serie = pd.to_numeric(df["Close"], errors="coerce").dropna()
    serie = serie[serie.index <= pd.Timestamp(fim)]
    if len(serie) < 2:
        return (float(serie.iloc[-1]) if len(serie) == 1 else np.nan), np.nan
    atual, anterior = float(serie.iloc[-1]), float(serie.iloc[-2])
    if anterior == 0:
        return atual, np.nan
    return atual, atual / anterior - 1


def kpis_do_topo(
    controles: dict, cotacoes: dict[str, pd.DataFrame], fim: pd.Timestamp
) -> None:
    colunas = st.columns(5)

    ibov, var_ibov = variacao_diaria(cotacoes.get("^BVSP"), fim)
    colunas[0].metric("Ibovespa", _texto(ibov, " pts", casas=0), _delta(_pct(var_ibov)))

    dolar, var_dolar = variacao_diaria(cotacoes.get("BRL=X"), fim)
    colunas[1].metric("USD/BRL", _texto(dolar), _delta(_pct(var_dolar)))

    selic = fonte.selic_meta()
    colunas[2].metric("Selic meta", _texto(selic, "%"))

    movimentos = {}
    for ticker in uni.tickers_do_setor(controles["setor"]):
        _, variacao = variacao_diaria(cotacoes.get(uni.para_yahoo(ticker)), fim)
        if not pd.isna(variacao):
            movimentos[ticker] = variacao

    if movimentos:
        alta = max(movimentos, key=movimentos.get)
        baixa = min(movimentos, key=movimentos.get)
        colunas[3].metric(f"Maior alta - {alta}", _delta(_pct(movimentos[alta])))
        colunas[4].metric(f"Maior baixa - {baixa}", _delta(_pct(movimentos[baixa])))
    else:
        colunas[3].metric("Maior alta", "n/d")
        colunas[4].metric("Maior baixa", "n/d")

    st.caption(f"Maior alta e maior baixa do pregao dentro do setor {controles['setor']}.")


def _delta(valor) -> str | None:
    if valor is None or pd.isna(valor):
        return None
    return f"{valor:,.2f}%"


# ------------------------------------------------------------ panorama macro


def aba_macro(
    cotacoes: dict[str, pd.DataFrame], inicio: pd.Timestamp, fim: pd.Timestamp
) -> None:
    primeiro_do_ano = pd.Timestamp(year=fim.year, month=1, day=1)

    linhas = []
    for classe, grupo in uni.MACRO.items():
        for ticker, nome in grupo.items():
            df = cotacoes.get(ticker)
            if df is None:
                continue
            fechamento, variacao = variacao_diaria(df, fim)
            adj = df["Adj Close"]
            linhas.append(
                {
                    "Classe": classe,
                    "Ativo": nome,
                    "Ticker": ticker,
                    "Ultimo": fechamento,
                    "Retorno 1D %": _pct(variacao),
                    "Retorno 1M %": _pct(
                        calc.retorno_periodo(adj, fim - pd.Timedelta(days=30), fim)
                    ),
                    "YTD %": _pct(calc.retorno_periodo(adj, primeiro_do_ano, fim)),
                    "Volatilidade 30D %": _pct(calc.volatilidade_anualizada(adj, 30, fim)),
                }
            )

    if not linhas:
        st.warning("Nenhum ativo macro foi baixado.")
        return

    tabela = pd.DataFrame(linhas)
    numericas = ["Ultimo", "Retorno 1D %", "Retorno 1M %", "YTD %", "Volatilidade 30D %"]
    estilo = (
        tabela.style.format({coluna: "{:,.2f}" for coluna in numericas}, na_rep="n/d")
        .map(_cor_do_sinal, subset=["Retorno 1D %", "Retorno 1M %", "YTD %"])
    )
    st.dataframe(estilo, width="stretch", hide_index=True)

    st.divider()
    rotulos = {f"{linha['Ativo']} ({linha['Classe']})": linha["Ticker"] for linha in linhas}
    padrao = [nome for nome in rotulos if "Indices" in nome][:4]
    escolhidos = st.multiselect(
        "Comparar em base 100", list(rotulos), default=padrao or list(rotulos)[:4]
    )

    series = {
        nome: cotacoes[rotulos[nome]]["Adj Close"]
        for nome in escolhidos
        if rotulos[nome] in cotacoes
    }
    st.plotly_chart(graf.linhas_base_100(series, inicio, fim), width="stretch")


# ----------------------------------------------------------- setores


def resumo_setorial(
    controles: dict,
    cotacoes: dict[str, pd.DataFrame],
    fundamentos: dict[str, dict],
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
) -> pd.DataFrame:
    """Uma linha por setor. Medias para risco, medianas para multiplos."""
    bench_df = cotacoes.get(controles["benchmark"])
    bench = bench_df["Adj Close"] if bench_df is not None else pd.Series(dtype=float)
    observacoes = calc.SEMANAS_BETA_2A if controles["periodicidade"] == "Semanal" else 504

    linhas = []
    for setor in uni.setores():
        retornos, volatilidades, betas, precos_lucro, yields, capital = [], [], [], [], [], []
        equity_divida = []

        for ticker in uni.tickers_do_setor(setor):
            chave = uni.para_yahoo(ticker)
            df = cotacoes.get(chave)
            if df is None:
                continue
            adj, close = df["Adj Close"], df["Close"]
            fund = _fundamentos_com_market_cap(chave, fundamentos.get(chave, {}), close, fim)

            retornos.append(calc.retorno_periodo(adj, inicio, fim))
            volatilidades.append(calc.volatilidade_anualizada(adj, 252, fim))
            betas.append(
                calc.beta(adj, bench, controles["periodicidade"], observacoes, fim)
            )
            precos_lucro.append(calc.preco_lucro(fund, fim))
            yields.append(calc.dividend_yield_ltm(fonte.proventos(df), close, fim))
            equity_divida.append(calc.market_equity_divida(fund, fim))
            if fund.get("market_cap") and not pd.isna(fund["market_cap"]):
                capital.append(float(fund["market_cap"]))

        if not retornos:
            continue
        linhas.append(
            {
                "Setor": setor,
                "Retorno periodo %": _pct(_media(retornos)),
                "Volatilidade media %": _pct(_media(volatilidades)),
                "Beta medio": _media(betas),
                "P/L mediano": _mediana(precos_lucro),
                "DY mediano %": _pct(_mediana(yields)),
                "Market Equity/Debt mediano": _mediana(equity_divida),
                "Market Cap total": float(sum(capital)) if capital else np.nan,
                "Acoes": len(retornos),
            }
        )

    return pd.DataFrame(linhas)


def _media(valores) -> float:
    serie = pd.Series(valores, dtype=float).dropna()
    return float(serie.mean()) if not serie.empty else np.nan


def _mediana(valores) -> float:
    serie = pd.Series(valores, dtype=float).dropna()
    return float(serie.median()) if not serie.empty else np.nan


def aba_setores(
    controles: dict,
    cotacoes: dict[str, pd.DataFrame],
    fundamentos: dict[str, dict],
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
) -> None:
    tabela = resumo_setorial(controles, cotacoes, fundamentos, inicio, fim)
    if tabela.empty:
        st.warning("Nao foi possivel consolidar nenhum setor.")
        return

    visivel = tabela.drop(columns=["Market Cap total"]).assign(
        **{"Market Cap total (R$ bi)": tabela["Market Cap total"] / 1e9}
    )
    numericas = [
        "Retorno periodo %",
        "Volatilidade media %",
        "Beta medio",
        "P/L mediano",
        "DY mediano %",
        "Market Equity/Debt mediano",
        "Market Cap total (R$ bi)",
    ]
    estilo = (
        visivel.style.format({coluna: "{:,.2f}" for coluna in numericas}, na_rep="n/d")
        .map(_cor_do_sinal, subset=["Retorno periodo %"])
    )
    st.dataframe(estilo, width="stretch", hide_index=True)
    st.caption(
        "Retorno, volatilidade e beta sao medias simples das acoes do setor. "
        "P/L, DY e Market Equity/Debt sao medianas, que ignoram n/d e P/L negativo."
    )

    st.divider()
    ordenado = tabela.set_index("Setor")["Retorno periodo %"]
    st.plotly_chart(
        graf.barras_horizontais(ordenado, "Retorno no periodo %"), width="stretch"
    )

    st.divider()
    st.caption("Cada bolha e um setor. O tamanho e o Market Cap somado das acoes.")
    st.plotly_chart(graf.dispersao_setores(tabela), width="stretch")


# ---------------------------------------------------------------- raio-x


def opcoes_raio_x(setor: str) -> list[str]:
    """Acoes do setor escolhido mais todos os ativos macro."""
    return uni.tickers_do_setor(setor) + uni.tickers_macro()


def rotulo_raio_x(ticker: str) -> str:
    classe = uni.setor_de(ticker)
    return f"{ticker} - {uni.nome_de(ticker)} ({classe})"


def aba_raio_x(
    controles: dict,
    cotacoes: dict[str, pd.DataFrame],
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
) -> None:
    esquerda, direita = st.columns([3, 1])
    escolhido = esquerda.selectbox(
        "Ativo", opcoes_raio_x(controles["setor"]), format_func=rotulo_raio_x
    )
    tipo = direita.radio("Grafico", ["Candlestick", "Linha"], horizontal=True)

    chave = uni.para_yahoo(escolhido)
    df = cotacoes.get(chave)
    if df is None:
        # Indices e commodities nao vem no lote do setor: buscamos sob demanda.
        avulso, falhas = fonte.baixar_cotacoes((chave,))
        df = avulso.get(chave)
        if df is None:
            st.error(f"Sem cotacoes para {escolhido}: {falhas.get(chave, 'motivo desconhecido')}")
            return

    janela = df.loc[(df.index >= inicio) & (df.index <= fim)]
    if janela.empty:
        st.warning("A janela escolhida nao cobre nenhum pregao deste ativo.")
        return

    _cartoes_raio_x(chave, df, janela, inicio, fim)

    st.plotly_chart(
        graf.preco_com_medias(df, escolhido, tipo, (inicio, fim)), width="stretch"
    )

    coluna_a, coluna_b = st.columns(2)
    with coluna_a:
        st.caption("Drawdown a partir do inicio da janela")
        st.plotly_chart(graf.curva_drawdown(janela["Adj Close"]), width="stretch")
    with coluna_b:
        st.caption("Volatilidade movel de 21 dias, anualizada")
        st.plotly_chart(
            graf.serie_volatilidade(df["Adj Close"], 21, (inicio, fim)), width="stretch"
        )


def _cartoes_raio_x(
    chave: str,
    df: pd.DataFrame,
    janela: pd.DataFrame,
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
) -> None:
    retorno = calc.retorno_periodo(df["Adj Close"], inicio, fim)
    total = calc.retorno_total(df["Close"], fonte.proventos(df), inicio, fim)
    maximo = calc.drawdown_maximo(janela["Adj Close"])

    linha_um = st.columns(4)
    linha_um[0].metric("Preco", _texto(calc.ultimo_valor(df["Close"], fim)))
    linha_um[1].metric("Retorno no periodo", _texto(_pct(retorno), "%"))
    linha_um[2].metric("Retorno total", _texto(_pct(total), "%"))
    linha_um[3].metric("Drawdown maximo", _texto(_pct(maximo), "%"))
    st.caption("Retorno total soma os proventos do intervalo e ignora reinvestimento.")

    if uni.de_yahoo(chave) not in uni.todos_tickers_b3():
        st.caption("Indicadores fundamentalistas nao se aplicam a indices e commodities.")
        return

    fundamentos, _ = fonte.carregar_fundamentos((chave,))
    fund = _fundamentos_com_market_cap(chave, fundamentos.get(chave, {}), df["Close"], fim)
    margem = calc.margens(fund, fim)

    linha_dois = st.columns(5)
    linha_dois[0].metric("P/L LTM", _texto(calc.preco_lucro(fund, fim)))
    linha_dois[1].metric("EV/EBITDA", _texto(calc.ev_ebitda(fund, fim)))
    linha_dois[2].metric("ROE", _texto(_pct(calc.roe(fund, fim)), "%"))
    linha_dois[3].metric("Margem liquida", _texto(_pct(margem["liquida"]), "%"))
    linha_dois[4].metric(
        "Divida liquida/EBITDA", _texto(calc.divida_liquida_ebitda(fund, fim), "x")
    )


def _texto(valor, sufixo: str = "", casas: int = 2) -> str:
    if valor is None or pd.isna(valor):
        return "n/d"
    return f"{valor:,.{casas}f}{sufixo}"


# ----------------------------------------------------------- fundamentos


def aba_fundamentos(
    controles: dict,
    cotacoes: dict[str, pd.DataFrame],
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
) -> None:
    acoes = uni.tickers_do_setor(controles["setor"])
    if not acoes:
        st.info("Nenhuma acao cadastrada neste setor.")
        return

    escolhida = st.selectbox(
        "Acao", acoes, format_func=lambda t: f"{t} - {uni.nome_de(t)}", key="fundamentos"
    )
    chave = uni.para_yahoo(escolhida)
    fundamentos, falhas = fonte.carregar_fundamentos((chave,))
    if chave in falhas:
        st.error(f"{escolhida}: {falhas[chave]}")
        return
    fund = fundamentos.get(chave, {})

    st.caption("Margens por trimestre publicado")
    st.plotly_chart(
        graf.linhas_margens(calc.margens_por_trimestre(fund)), width="stretch"
    )

    st.caption("Divida bruta, caixa e patrimonio liquido por trimestre")
    st.plotly_chart(
        graf.barras_balanco(calc.balanco_por_trimestre(fund)), width="stretch"
    )

    st.caption(f"Proventos entre {inicio:%d/%m/%Y} e {fim:%d/%m/%Y}")
    _tabela_proventos(chave, cotacoes, inicio, fim)


def _tabela_proventos(
    chave: str,
    cotacoes: dict[str, pd.DataFrame],
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
) -> None:
    df = cotacoes.get(chave)
    if df is None:
        avulso, _ = fonte.baixar_cotacoes((chave,))
        df = avulso.get(chave)
    if df is None:
        st.info("Sem cotacoes para levantar os proventos.")
        return

    serie = fonte.proventos(df)
    janela = serie[(serie.index >= inicio) & (serie.index <= fim)]
    if janela.empty:
        st.info("Nenhum provento com data ex dentro da janela escolhida.")
        return

    tabela = pd.DataFrame(
        {
            "Data ex": janela.index.strftime("%d/%m/%Y"),
            "Valor por acao": janela.to_numpy(),
        }
    ).iloc[::-1]

    st.dataframe(
        tabela.style.format({"Valor por acao": "{:,.4f}"}),
        width="stretch",
        hide_index=True,
    )
    st.caption(
        f"Total no periodo: {janela.sum():,.4f} por acao em {len(janela)} pagamento(s). "
        "O Yahoo nao informa Data Com nem separa dividendo de JCP."
    )


# -------------------------------------------------------------------- main


def main() -> None:
    controles = barra_lateral()

    # Um unico lote cobre as cinco abas: acoes, macro e benchmark.
    alvo = tuple(
        dict.fromkeys(
            [uni.para_yahoo(t) for t in uni.todos_tickers_b3()]
            + uni.tickers_macro()
            + [controles["benchmark"]]
        )
    )
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

    st.title(f"Monitor B3 - {controles['setor']}")
    st.caption(
        f"Janela {inicio:%d/%m/%Y} a {fim:%d/%m/%Y} | benchmark {controles['benchmark']} | "
        f"beta {controles['periodicidade'].lower()} | ultimo pregao {ultimo_pregao:%d/%m/%Y}"
    )

    kpis_do_topo(controles, cotacoes, ultimo_pregao)
    st.divider()

    abas = st.tabs(["Panorama Macro", "Setores", "Screener", "Raio-X", "Fundamentos"])

    with abas[0]:
        aba_macro(cotacoes, inicio, fim)

    with abas[1]:
        st.caption(
            "A primeira consolidacao dos 10 setores baixa os demonstrativos de "
            "todas as acoes e demora alguns minutos. Depois disso o cache em "
            "disco responde na hora por 24 horas."
        )
        todas = tuple(uni.para_yahoo(t) for t in uni.todos_tickers_b3())
        fundamentos_todos, falhas_todos = fonte.carregar_fundamentos(todas)
        aba_setores(controles, cotacoes, fundamentos_todos, inicio, fim)
        if falhas_todos:
            with st.expander(f"{len(falhas_todos)} acao(oes) sem demonstrativos"):
                st.write(sorted(uni.de_yahoo(t) for t in falhas_todos))

    with abas[2]:
        aba_screener(controles, cotacoes, falhas_preco, inicio, fim)

    with abas[3]:
        aba_raio_x(controles, cotacoes, inicio, fim)

    with abas[4]:
        aba_fundamentos(controles, cotacoes, inicio, fim)


def aba_screener(
    controles: dict,
    cotacoes: dict[str, pd.DataFrame],
    falhas_preco: dict[str, str],
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
) -> None:
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
    try:
        main()
    except Exception as erro:  # rede, Yahoo instavel, formato inesperado
        st.error(
            "O app encontrou um erro inesperado e parou de desenhar esta pagina. "
            "Clique em Atualizar dados na barra lateral para recarregar."
        )
        with st.expander("Detalhes tecnicos"):
            st.exception(erro)
