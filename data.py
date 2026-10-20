"""Download e cache dos dados do Monitor B3.

Dois niveis de cache, como pede a especificacao:

* `st.cache_data(ttl=3600)` para cotacoes, na memoria da sessao;
* arquivos Parquet em `data/` para demonstrativos, validos por 24 horas.

Nenhuma funcao daqui levanta excecao por ticker sem dado. Falhas voltam
num dicionario `{ticker: motivo}` para a interface agrupar num unico aviso.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import yfinance as yf

from universe import SERIES_BCB, SUBSTITUTOS_YAHOO

PASTA_DADOS = Path(__file__).resolve().parent / "data"
VALIDADE_FUNDAMENTOS = dt.timedelta(hours=24)
URL_BCB = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"

COLUNAS_ESPERADAS = ["Open", "High", "Low", "Close", "Adj Close", "Volume", "Dividends"]


# ---------------------------------------------------------------- cotacoes


@st.cache_data(ttl=3600, show_spinner="Baixando cotacoes do Yahoo Finance...")
def baixar_cotacoes(
    tickers_yahoo: tuple[str, ...], periodo: str = "10y"
) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    """Uma unica chamada em lote para todos os tickers.

    Devolve `({ticker: DataFrame}, {ticker: motivo da falha})`. O DataFrame
    tem Close, Adj Close, Volume e Dividends com indice diario sem fuso.
    """
    tickers = list(dict.fromkeys(tickers_yahoo))
    if not tickers:
        return {}, {}

    series, falhas = _baixar_lote(tickers, periodo)

    # Segunda tentativa, so para quem tem substituto cadastrado.
    pendentes = {t: SUBSTITUTOS_YAHOO[t] for t in falhas if t in SUBSTITUTOS_YAHOO}
    if pendentes:
        extras, _ = _baixar_lote(list(pendentes.values()), periodo)
        for original, substituto in pendentes.items():
            if substituto in extras:
                series[original] = extras[substituto]
                series[original].attrs["substituto"] = substituto
                falhas.pop(original)

    return series, falhas


def _baixar_lote(
    tickers: list[str], periodo: str
) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    try:
        bruto = yf.download(
            tickers,
            period=periodo,
            interval="1d",
            auto_adjust=False,
            group_by="ticker",
            threads=True,
            progress=False,
            actions=True,
        )
    except Exception as erro:  # rede fora do ar, Yahoo instavel
        return {}, {t: f"download falhou ({type(erro).__name__})" for t in tickers}

    if bruto is None or bruto.empty:
        return {}, {t: "Yahoo devolveu resposta vazia" for t in tickers}

    series: dict[str, pd.DataFrame] = {}
    falhas: dict[str, str] = {}
    multi = isinstance(bruto.columns, pd.MultiIndex)

    for ticker in tickers:
        if multi:
            if ticker not in bruto.columns.get_level_values(0):
                falhas[ticker] = "ticker ausente na resposta do Yahoo"
                continue
            parcial = bruto[ticker]
        else:
            parcial = bruto

        limpo = _normalizar_cotacoes(parcial)
        if limpo is None:
            falhas[ticker] = "sem cotacoes no periodo pedido"
            continue
        series[ticker] = limpo

    return series, falhas


def _normalizar_cotacoes(df: pd.DataFrame) -> pd.DataFrame | None:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return None

    df = df.copy()
    indice = pd.to_datetime(df.index, errors="coerce")
    if getattr(indice, "tz", None) is not None:
        indice = indice.tz_localize(None)
    df.index = indice.normalize()
    df = df[~df.index.isna()]
    df = df[~df.index.duplicated(keep="last")].sort_index()

    if "Close" not in df.columns:
        return None
    if "Adj Close" not in df.columns:
        # Indices e alguns futuros nao trazem serie ajustada.
        df["Adj Close"] = df["Close"]
    if "Dividends" not in df.columns:
        df["Dividends"] = 0.0

    for coluna in COLUNAS_ESPERADAS:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    df = df.dropna(subset=["Close"])
    if df.empty:
        return None
    return df


def proventos(df: pd.DataFrame) -> pd.Series:
    """Serie de proventos por acao, indexada pela data ex.

    O Yahoo nao informa Data Com nem separa dividendo de JCP.
    """
    if df is None or "Dividends" not in df.columns:
        return pd.Series(dtype=float)
    serie = pd.to_numeric(df["Dividends"], errors="coerce").fillna(0.0)
    return serie[serie > 0]


# ------------------------------------------------------------ fundamentos


@st.cache_data(ttl=3600, show_spinner="Carregando demonstrativos financeiros...")
def carregar_fundamentos(
    tickers_yahoo: tuple[str, ...]
) -> tuple[dict[str, dict], dict[str, str]]:
    """Demonstrativos trimestrais e anuais, com cache em disco de 24 horas."""
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    dados: dict[str, dict] = {}
    falhas: dict[str, str] = {}

    for ticker in dict.fromkeys(tickers_yahoo):
        try:
            dados[ticker] = _fundamentos_de(ticker)
        except Exception as erro:
            falhas[ticker] = f"demonstrativos indisponiveis ({type(erro).__name__})"

    return dados, falhas


def _fundamentos_de(ticker: str) -> dict:
    base = PASTA_DADOS / ticker.replace(".", "_").replace("^", "idx_")
    marcador = base.with_name(base.name + "__meta.json")

    if _cache_fresco(marcador):
        do_disco = _ler_do_disco(base, marcador)
        if do_disco is not None:
            return do_disco

    acao = yf.Ticker(ticker)
    pacote = {
        "trimestral_dre": _tabela(getattr(acao, "quarterly_income_stmt", None)),
        "trimestral_bp": _tabela(getattr(acao, "quarterly_balance_sheet", None)),
        "anual_dre": _tabela(getattr(acao, "income_stmt", None)),
        "anual_bp": _tabela(getattr(acao, "balance_sheet", None)),
    }
    pacote["market_cap"] = _market_cap(acao)
    _gravar_no_disco(base, marcador, pacote)
    return pacote


def _market_cap(acao: yf.Ticker) -> float | None:
    """Market Cap atual. `info` so e usado para isso, nunca para historico."""
    try:
        valor = acao.fast_info.get("market_cap")
        if valor:
            return float(valor)
    except Exception:
        pass
    try:
        valor = acao.info.get("marketCap")
        if valor:
            return float(valor)
    except Exception:
        pass
    return None


def _tabela(bruto) -> pd.DataFrame:
    """Padroniza um demonstrativo: linhas em texto, colunas em data ISO."""
    if bruto is None or not isinstance(bruto, pd.DataFrame) or bruto.empty:
        return pd.DataFrame()

    tabela = bruto.copy()
    tabela.index = [str(linha) for linha in tabela.index]
    colunas = []
    for coluna in tabela.columns:
        marca = pd.Timestamp(coluna)
        colunas.append(marca.strftime("%Y-%m-%d"))
    tabela.columns = colunas
    tabela = tabela[~tabela.index.duplicated(keep="first")]
    tabela = tabela.loc[:, ~pd.Index(tabela.columns).duplicated(keep="first")]
    return tabela.apply(pd.to_numeric, errors="coerce")


def _cache_fresco(marcador: Path) -> bool:
    if not marcador.exists():
        return False
    try:
        meta = json.loads(marcador.read_text(encoding="utf-8"))
        gravado = dt.datetime.fromisoformat(meta["gravado_em"])
    except Exception:
        return False
    return dt.datetime.now() - gravado < VALIDADE_FUNDAMENTOS


def _ler_do_disco(base: Path, marcador: Path) -> dict | None:
    try:
        meta = json.loads(marcador.read_text(encoding="utf-8"))
    except Exception:
        return None

    pacote: dict = {"market_cap": meta.get("market_cap")}
    for chave in ("trimestral_dre", "trimestral_bp", "anual_dre", "anual_bp"):
        caminho = base.with_name(f"{base.name}__{chave}.parquet")
        if chave in meta.get("tabelas", []) and caminho.exists():
            try:
                pacote[chave] = pd.read_parquet(caminho)
            except Exception:
                return None
        else:
            pacote[chave] = pd.DataFrame()
    return pacote


def _gravar_no_disco(base: Path, marcador: Path, pacote: dict) -> None:
    gravadas = []
    for chave in ("trimestral_dre", "trimestral_bp", "anual_dre", "anual_bp"):
        tabela = pacote.get(chave)
        if tabela is None or tabela.empty:
            continue
        caminho = base.with_name(f"{base.name}__{chave}.parquet")
        try:
            tabela.to_parquet(caminho)
            gravadas.append(chave)
        except Exception:
            # Sem pyarrow ou disco cheio: seguimos so com o cache de memoria.
            pass

    meta = {
        "gravado_em": dt.datetime.now().isoformat(timespec="seconds"),
        "market_cap": pacote.get("market_cap"),
        "tabelas": gravadas,
    }
    try:
        marcador.write_text(json.dumps(meta), encoding="utf-8")
    except Exception:
        pass


def limpar_cache_de_disco() -> int:
    """Apaga os Parquet e marcadores. Devolve quantos arquivos sairam."""
    if not PASTA_DADOS.exists():
        return 0
    apagados = 0
    for arquivo in list(PASTA_DADOS.glob("*.parquet")) + list(PASTA_DADOS.glob("*.json")):
        try:
            arquivo.unlink()
            apagados += 1
        except OSError:
            pass
    return apagados


# ------------------------------------------------------- Banco Central


@st.cache_data(ttl=3600, show_spinner=False)
def serie_bcb(codigo: int, dias: int = 400) -> pd.Series:
    """Serie da API SGS do Banco Central. Devolve serie vazia se falhar."""
    fim = dt.date.today()
    inicio = fim - dt.timedelta(days=dias)
    try:
        resposta = requests.get(
            URL_BCB.format(codigo=codigo),
            params={
                "formato": "json",
                "dataInicial": inicio.strftime("%d/%m/%Y"),
                "dataFinal": fim.strftime("%d/%m/%Y"),
            },
            timeout=20,
        )
        resposta.raise_for_status()
        registros = resposta.json()
    except Exception:
        return pd.Series(dtype=float)

    if not registros:
        return pd.Series(dtype=float)

    tabela = pd.DataFrame(registros)
    tabela["data"] = pd.to_datetime(tabela["data"], format="%d/%m/%Y", errors="coerce")
    tabela["valor"] = pd.to_numeric(tabela["valor"], errors="coerce")
    tabela = tabela.dropna(subset=["data", "valor"]).set_index("data").sort_index()
    return tabela["valor"]


def selic_meta() -> float | None:
    serie = serie_bcb(SERIES_BCB["selic_meta"])
    if serie.empty:
        return None
    return float(serie.iloc[-1])
