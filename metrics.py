"""Calculos do Monitor B3.

Toda funcao devolve NaN quando faltam dados, nunca levanta excecao.

Convencoes da especificacao:
* Adj Close para retorno, volatilidade, beta e drawdown;
* Close para P/L, P/VP e Dividend Yield;
* 252 dias uteis por ano.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

DIAS_UTEIS_ANO = 252
SEMANAS_BETA_2A = 104
SEMANAS_BETA_5A = 260
ALIQUOTA_MIN, ALIQUOTA_MAX = 0.0, 0.45

# Nomes que o yfinance usa para a mesma linha, em ordem de preferencia.
LINHAS = {
    "lucro_liquido": [
        "Net Income",
        "Net Income Common Stockholders",
        "Net Income From Continuing Operation Net Minority Interest",
        "Net Income Continuous Operations",
    ],
    "receita": ["Total Revenue", "Operating Revenue"],
    "lucro_bruto": ["Gross Profit"],
    "imposto": ["Tax Provision", "Income Tax Expense Benefit"],
    "lair": ["Pretax Income", "Income Before Tax", "EBT"],
    "ebitda": ["EBITDA", "Normalized EBITDA"],
    "ebit": ["EBIT", "Operating Income", "Total Operating Income As Reported"],
    "depreciacao": [
        "Reconciled Depreciation",
        "Depreciation And Amortization",
        "Depreciation Amortization Depletion",
    ],
    "patrimonio": [
        "Stockholders Equity",
        "Total Stockholder Equity",
        "Common Stock Equity",
    ],
    "divida_bruta": ["Total Debt"],
    "divida_longa": ["Long Term Debt", "Long Term Debt And Capital Lease Obligation"],
    "divida_curta": ["Current Debt", "Current Debt And Capital Lease Obligation"],
    "caixa": [
        "Cash And Cash Equivalents",
        "Cash Cash Equivalents And Short Term Investments",
    ],
}


# ------------------------------------------------------------- auxiliares


def _serie(precos) -> pd.Series:
    if precos is None:
        return pd.Series(dtype=float)
    serie = pd.to_numeric(pd.Series(precos), errors="coerce").dropna()
    if serie.empty:
        return serie
    return serie.sort_index()


def _ate(serie: pd.Series, quando) -> pd.Series:
    if quando is None or serie.empty:
        return serie
    return serie[serie.index <= pd.Timestamp(quando)]


def retornos_log(precos) -> pd.Series:
    serie = _serie(precos)
    if len(serie) < 2:
        return pd.Series(dtype=float)
    return np.log(serie / serie.shift(1)).replace([np.inf, -np.inf], np.nan).dropna()


# --------------------------------------------------------------- retornos


def retorno_periodo(precos, inicio, fim) -> float:
    """(P_t - P_0) / P_0, com P_0 = ultimo fechamento em ou antes de `inicio`.

    Para YTD basta passar 1 de janeiro: a regra pega o ultimo pregao do ano
    anterior, exatamente como a especificacao pede.
    """
    serie = _serie(precos)
    if serie.empty:
        return np.nan
    p0 = serie.asof(pd.Timestamp(inicio))
    pt = serie.asof(pd.Timestamp(fim))
    if pd.isna(p0) or pd.isna(pt) or p0 == 0:
        return np.nan
    return float(pt / p0 - 1)


def volatilidade_anualizada(precos, janela: int = DIAS_UTEIS_ANO, fim=None) -> float:
    """Desvio padrao amostral dos retornos log diarios vezes raiz de 252."""
    serie = _ate(_serie(precos), fim)
    retornos = retornos_log(serie).tail(janela)
    minimo = max(20, janela // 4)
    if len(retornos) < minimo:
        return np.nan
    desvio = retornos.std(ddof=1)
    if pd.isna(desvio):
        return np.nan
    return float(desvio * np.sqrt(DIAS_UTEIS_ANO))


def beta(precos_ativo, precos_benchmark, periodicidade: str = "Semanal",
         observacoes: int = SEMANAS_BETA_2A, fim=None) -> float:
    """Cov(R_i, R_m) / Var(R_m) sobre retornos log alinhados."""
    ativo = _ate(_serie(precos_ativo), fim)
    bench = _ate(_serie(precos_benchmark), fim)
    if ativo.empty or bench.empty:
        return np.nan

    if periodicidade.lower().startswith("sem"):
        ativo = ativo.resample("W-FRI").last()
        bench = bench.resample("W-FRI").last()

    par = pd.concat(
        [retornos_log(ativo), retornos_log(bench)], axis=1, keys=["ativo", "bench"]
    ).dropna().tail(observacoes)

    if len(par) < 30:
        return np.nan
    variancia = par["bench"].var(ddof=1)
    if pd.isna(variancia) or variancia == 0:
        return np.nan
    covariancia = par["ativo"].cov(par["bench"])
    if pd.isna(covariancia):
        return np.nan
    return float(covariancia / variancia)


def distancia_52_semanas(precos_close, fim=None) -> tuple[float, float]:
    """(distancia da minima, distancia da maxima) em fracao decimal."""
    serie = _ate(_serie(precos_close), fim).tail(DIAS_UTEIS_ANO)
    if len(serie) < 20:
        return np.nan, np.nan
    atual = serie.iloc[-1]
    minima, maxima = serie.min(), serie.max()
    da_minima = float(atual / minima - 1) if minima else np.nan
    da_maxima = float(atual / maxima - 1) if maxima else np.nan
    return da_minima, da_maxima


def dividend_yield_ltm(proventos: pd.Series, precos_close, t_ref) -> float:
    """Soma dos proventos em [t_ref - 365 dias, t_ref] sobre o Close em t_ref."""
    close = _serie(precos_close)
    if close.empty:
        return np.nan
    preco = close.asof(pd.Timestamp(t_ref))
    if pd.isna(preco) or preco == 0:
        return np.nan
    if proventos is None or len(proventos) == 0:
        return 0.0
    serie = pd.to_numeric(pd.Series(proventos), errors="coerce").dropna()
    fim = pd.Timestamp(t_ref)
    inicio = fim - pd.Timedelta(days=365)
    janela = serie[(serie.index > inicio) & (serie.index <= fim)]
    return float(janela.sum() / preco)


# ------------------------------------------------- leitura de balanco


def linha(tabela: pd.DataFrame, chave: str) -> pd.Series:
    """Extrai uma linha do demonstrativo, indexada por data e ordenada."""
    if tabela is None or not isinstance(tabela, pd.DataFrame) or tabela.empty:
        return pd.Series(dtype=float)

    disponiveis = {str(nome).strip().lower(): nome for nome in tabela.index}
    for candidato in LINHAS.get(chave, []):
        achado = disponiveis.get(candidato.lower())
        if achado is None:
            continue
        serie = tabela.loc[achado]
        if isinstance(serie, pd.DataFrame):
            serie = serie.iloc[0]
        serie = pd.to_numeric(serie, errors="coerce")
        serie.index = pd.to_datetime(serie.index, errors="coerce")
        return serie[~serie.index.isna()].dropna().sort_index()
    return pd.Series(dtype=float)


def soma_ltm(serie: pd.Series, t_ref, trimestres: int = 4) -> float:
    """Soma dos 4 ultimos trimestres reportados antes de t_ref."""
    janela = _ate(_serie(serie), t_ref)
    if len(janela) < trimestres:
        return np.nan
    return float(janela.tail(trimestres).sum())


def ultimo_valor(serie: pd.Series, t_ref) -> float:
    janela = _ate(_serie(serie), t_ref)
    if janela.empty:
        return np.nan
    return float(janela.iloc[-1])


def _divida_bruta(balanco: pd.DataFrame, t_ref) -> float:
    total = ultimo_valor(linha(balanco, "divida_bruta"), t_ref)
    if not pd.isna(total):
        return total
    longa = ultimo_valor(linha(balanco, "divida_longa"), t_ref)
    curta = ultimo_valor(linha(balanco, "divida_curta"), t_ref)
    partes = [v for v in (longa, curta) if not pd.isna(v)]
    return float(sum(partes)) if partes else np.nan


def _ebitda_ltm(dre_trimestral: pd.DataFrame, dre_anual: pd.DataFrame, t_ref) -> float:
    valor = soma_ltm(linha(dre_trimestral, "ebitda"), t_ref)
    if not pd.isna(valor):
        return valor

    ebit = soma_ltm(linha(dre_trimestral, "ebit"), t_ref)
    depreciacao = soma_ltm(linha(dre_trimestral, "depreciacao"), t_ref)
    if not pd.isna(ebit) and not pd.isna(depreciacao):
        return float(ebit + depreciacao)

    # Menos de 4 trimestres publicados: cai para o anual mais recente.
    return ultimo_valor(linha(dre_anual, "ebitda"), t_ref)


def _lucro_ltm(dre_trimestral: pd.DataFrame, dre_anual: pd.DataFrame, t_ref) -> float:
    valor = soma_ltm(linha(dre_trimestral, "lucro_liquido"), t_ref)
    if not pd.isna(valor):
        return valor
    return ultimo_valor(linha(dre_anual, "lucro_liquido"), t_ref)


# ------------------------------------------------------- multiplos


def preco_lucro(fundamentos: dict, t_ref) -> float:
    """Market Cap / Lucro Liquido LTM. NaN quando o lucro nao e positivo."""
    market_cap = fundamentos.get("market_cap")
    lucro = _lucro_ltm(
        fundamentos.get("trimestral_dre"), fundamentos.get("anual_dre"), t_ref
    )
    if not market_cap or pd.isna(lucro) or lucro <= 0:
        return np.nan
    return float(market_cap / lucro)


def ev_ebitda(fundamentos: dict, t_ref) -> float:
    """(Market Cap + Divida Bruta - Caixa) / EBITDA LTM."""
    market_cap = fundamentos.get("market_cap")
    if not market_cap:
        return np.nan
    balanco = fundamentos.get("trimestral_bp")
    divida = _divida_bruta(balanco, t_ref)
    caixa = ultimo_valor(linha(balanco, "caixa"), t_ref)
    if pd.isna(divida):
        divida = 0.0
    if pd.isna(caixa):
        caixa = 0.0

    ebitda = _ebitda_ltm(
        fundamentos.get("trimestral_dre"), fundamentos.get("anual_dre"), t_ref
    )
    if pd.isna(ebitda) or ebitda <= 0:
        return np.nan
    return float((market_cap + divida - caixa) / ebitda)


def preco_valor_patrimonial(fundamentos: dict, t_ref) -> float:
    market_cap = fundamentos.get("market_cap")
    patrimonio = ultimo_valor(linha(fundamentos.get("trimestral_bp"), "patrimonio"), t_ref)
    if pd.isna(patrimonio):
        patrimonio = ultimo_valor(linha(fundamentos.get("anual_bp"), "patrimonio"), t_ref)
    if not market_cap or pd.isna(patrimonio) or patrimonio <= 0:
        return np.nan
    return float(market_cap / patrimonio)


def roe(fundamentos: dict, t_ref) -> float:
    """Lucro LTM sobre o patrimonio medio dos 4 trimestres da janela."""
    lucro = _lucro_ltm(
        fundamentos.get("trimestral_dre"), fundamentos.get("anual_dre"), t_ref
    )
    if pd.isna(lucro):
        return np.nan

    patrimonio = _ate(linha(fundamentos.get("trimestral_bp"), "patrimonio"), t_ref).tail(4)
    if len(patrimonio) < 2:
        unico = ultimo_valor(linha(fundamentos.get("anual_bp"), "patrimonio"), t_ref)
        if pd.isna(unico) or unico <= 0:
            return np.nan
        return float(lucro / unico)

    medio = (patrimonio.iloc[0] + patrimonio.iloc[-1]) / 2
    if pd.isna(medio) or medio <= 0:
        return np.nan
    return float(lucro / medio)


def _capital_investido(balanco: pd.DataFrame) -> pd.Series:
    """Patrimonio Liquido + Divida Bruta - Caixa, trimestre a trimestre."""
    patrimonio = linha(balanco, "patrimonio")
    if patrimonio.empty:
        return pd.Series(dtype=float)

    divida = linha(balanco, "divida_bruta")
    if divida.empty:
        divida = linha(balanco, "divida_longa").add(
            linha(balanco, "divida_curta"), fill_value=0.0
        )
    caixa = linha(balanco, "caixa")

    serie = patrimonio.add(divida, fill_value=0.0).sub(caixa, fill_value=0.0)
    return serie.reindex(patrimonio.index).dropna().sort_index()


def aliquota_efetiva(dre_trimestral: pd.DataFrame, t_ref) -> float:
    """Imposto / LAIR do periodo, limitada a [0, 0.45] como manda a spec."""
    imposto = soma_ltm(linha(dre_trimestral, "imposto"), t_ref)
    lair = soma_ltm(linha(dre_trimestral, "lair"), t_ref)
    if pd.isna(imposto) or pd.isna(lair) or lair <= 0:
        return np.nan
    return float(np.clip(imposto / lair, ALIQUOTA_MIN, ALIQUOTA_MAX))


def roic(fundamentos: dict, t_ref) -> float:
    """NOPAT sobre o capital investido medio dos 4 trimestres da janela."""
    dre = fundamentos.get("trimestral_dre")
    ebit = soma_ltm(linha(dre, "ebit"), t_ref)
    aliquota = aliquota_efetiva(dre, t_ref)
    if pd.isna(ebit) or pd.isna(aliquota):
        return np.nan

    capital = _ate(_capital_investido(fundamentos.get("trimestral_bp")), t_ref).tail(4)
    if capital.empty:
        return np.nan
    medio = (
        (capital.iloc[0] + capital.iloc[-1]) / 2 if len(capital) > 1 else capital.iloc[0]
    )
    if pd.isna(medio) or medio <= 0:
        return np.nan
    return float(ebit * (1 - aliquota) / medio)


def cagr(serie_anual: pd.Series, t_inicio, t_fim) -> float:
    """(Valor_fim / Valor_inicio)^(1/n) - 1 sobre os anuais mais proximos."""
    serie = _serie(serie_anual)
    if len(serie) < 2:
        return np.nan

    data_inicio = _data_mais_proxima(serie.index, t_inicio)
    data_fim = _data_mais_proxima(serie.index, t_fim)
    if data_inicio is None or data_fim is None or data_inicio >= data_fim:
        return np.nan

    inicial, final = serie[data_inicio], serie[data_fim]
    anos = (data_fim - data_inicio).days / 365.25
    if anos <= 0 or inicial <= 0 or final <= 0:
        return np.nan
    return float((final / inicial) ** (1 / anos) - 1)


def _data_mais_proxima(indice: pd.DatetimeIndex, alvo):
    if len(indice) == 0:
        return None
    alvo = pd.Timestamp(alvo)
    return min(indice, key=lambda data: abs((data - alvo).days))


def margens(fundamentos: dict, t_ref) -> dict[str, float]:
    """Margem bruta, EBITDA e liquida, sempre sobre a receita LTM."""
    dre = fundamentos.get("trimestral_dre")
    receita = soma_ltm(linha(dre, "receita"), t_ref)
    if pd.isna(receita) or receita <= 0:
        return {"bruta": np.nan, "ebitda": np.nan, "liquida": np.nan}

    bruto = soma_ltm(linha(dre, "lucro_bruto"), t_ref)
    ebitda = _ebitda_ltm(dre, fundamentos.get("anual_dre"), t_ref)
    liquido = _lucro_ltm(dre, fundamentos.get("anual_dre"), t_ref)
    return {
        "bruta": np.nan if pd.isna(bruto) else float(bruto / receita),
        "ebitda": np.nan if pd.isna(ebitda) else float(ebitda / receita),
        "liquida": np.nan if pd.isna(liquido) else float(liquido / receita),
    }


def divida_liquida_ebitda(fundamentos: dict, t_ref) -> float:
    balanco = fundamentos.get("trimestral_bp")
    divida = _divida_bruta(balanco, t_ref)
    caixa = ultimo_valor(linha(balanco, "caixa"), t_ref)
    ebitda = _ebitda_ltm(
        fundamentos.get("trimestral_dre"), fundamentos.get("anual_dre"), t_ref
    )
    if pd.isna(divida) or pd.isna(ebitda) or ebitda <= 0:
        return np.nan
    if pd.isna(caixa):
        caixa = 0.0
    return float((divida - caixa) / ebitda)


# ------------------------------------------------------------ series


def retorno_total(precos_close, proventos: pd.Series, inicio, fim) -> float:
    """(P_t - P_0 + D) / P_0. Ignora reinvestimento dos proventos."""
    close = _serie(precos_close)
    if close.empty:
        return np.nan
    p0 = close.asof(pd.Timestamp(inicio))
    pt = close.asof(pd.Timestamp(fim))
    if pd.isna(p0) or pd.isna(pt) or p0 == 0:
        return np.nan

    total = 0.0
    if proventos is not None and len(proventos) > 0:
        serie = pd.to_numeric(pd.Series(proventos), errors="coerce").dropna()
        janela = serie[
            (serie.index > pd.Timestamp(inicio)) & (serie.index <= pd.Timestamp(fim))
        ]
        total = float(janela.sum())
    return float((pt - p0 + total) / p0)


def media_movel(precos, janela: int) -> pd.Series:
    serie = _serie(precos)
    if len(serie) < janela:
        return pd.Series(dtype=float)
    return serie.rolling(janela).mean()


def drawdown(precos) -> pd.Series:
    """DD_t = P_t / max(P_0..P_t) - 1."""
    serie = _serie(precos)
    if serie.empty:
        return pd.Series(dtype=float)
    return serie / serie.cummax() - 1


def drawdown_maximo(precos) -> float:
    curva = drawdown(precos)
    if curva.empty:
        return np.nan
    return float(curva.min())


def _ebitda_por_trimestre(dre: pd.DataFrame) -> pd.Series:
    serie = linha(dre, "ebitda")
    if not serie.empty:
        return serie
    ebit = linha(dre, "ebit")
    depreciacao = linha(dre, "depreciacao")
    if ebit.empty:
        return pd.Series(dtype=float)
    if depreciacao.empty:
        return pd.Series(dtype=float)
    return ebit.add(depreciacao, fill_value=0.0).dropna()


def margens_por_trimestre(fundamentos: dict, quantidade: int = 8) -> pd.DataFrame:
    """Margem bruta, EBITDA e liquida de cada trimestre publicado."""
    dre = fundamentos.get("trimestral_dre")
    receita = linha(dre, "receita")
    if receita.empty:
        return pd.DataFrame()

    bruta = linha(dre, "lucro_bruto").div(receita)
    ebitda = _ebitda_por_trimestre(dre).div(receita)
    liquida = _lucro_por_trimestre(dre).div(receita)

    tabela = pd.DataFrame(
        {
            "Margem bruta": bruta,
            "Margem EBITDA": ebitda,
            "Margem liquida": liquida,
        }
    )
    tabela = tabela.reindex(receita.index).sort_index().tail(quantidade)
    return tabela.dropna(axis=1, how="all").dropna(how="all")


def _lucro_por_trimestre(dre: pd.DataFrame) -> pd.Series:
    return linha(dre, "lucro_liquido")


def balanco_por_trimestre(fundamentos: dict, quantidade: int = 8) -> pd.DataFrame:
    """Divida bruta, caixa e patrimonio liquido de cada trimestre."""
    balanco = fundamentos.get("trimestral_bp")
    patrimonio = linha(balanco, "patrimonio")
    if patrimonio.empty:
        return pd.DataFrame()

    divida = linha(balanco, "divida_bruta")
    if divida.empty:
        divida = linha(balanco, "divida_longa").add(
            linha(balanco, "divida_curta"), fill_value=0.0
        )
    caixa = linha(balanco, "caixa")

    tabela = pd.DataFrame(
        {
            "Divida bruta": divida,
            "Caixa": caixa,
            "Patrimonio liquido": patrimonio,
        }
    )
    tabela = tabela.reindex(patrimonio.index).sort_index().tail(quantidade)
    return tabela.dropna(axis=1, how="all").dropna(how="all")


def volatilidade_movel(precos, janela: int = 21) -> pd.Series:
    """Volatilidade anualizada em janela movel."""
    retornos = retornos_log(precos)
    if len(retornos) < janela:
        return pd.Series(dtype=float)
    return retornos.rolling(janela).std(ddof=1) * np.sqrt(DIAS_UTEIS_ANO)
