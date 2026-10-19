"""Universo de ativos do Monitor B3.

Tickers da B3 sao guardados sem sufixo. O sufixo .SA exigido pelo Yahoo
Finance e adicionado apenas na hora da consulta, por `para_yahoo`.
"""

from __future__ import annotations

SUFIXO_B3 = ".SA"

# {setor: {ticker: nome de exibicao}}
# Classificacao em 12 setores pela atividade que gera a maior parte da receita.
# Saude e Telecom nao tem setor proprio nesta classificacao e ficaram de fora
# (RDOR3, HAPV3, FLRY3, HYPE3, VIVT3, TIMS3, DESK3, BRST3).
SETORES: dict[str, dict[str, str]] = {
    "Instituicoes Financeiras": {
        "ITUB4": "Itau Unibanco",
        "BBDC4": "Bradesco",
        "BBAS3": "Banco do Brasil",
        "BPAC11": "BTG Pactual",
        "SANB11": "Santander Brasil",
        "B3SA3": "B3",
        "BBSE3": "BB Seguridade",
        "CXSE3": "Caixa Seguridade",
        "PSSA3": "Porto Seguro",
        # BDRs opcionais: nao sao acoes locais, mas dao exposicao ao setor.
        "ROXO34": "Nu Holdings (BDR)",
        "STOC34": "StoneCo (BDR, ex-STOC31)",
        "PAGS34": "PagSeguro (BDR)",
    },
    "Utilidades Publicas": {
        "SBSP3": "Sabesp",
        "CSMG3": "Copasa",
        "SAPR11": "Sanepar",
        # ELET3 saiu: o Yahoo nao devolve mais serie para Eletrobras.
        "EQTL3": "Equatorial",
        "CPFE3": "CPFL Energia",
        "EGIE3": "Engie Brasil",
        "TAEE11": "Taesa",
        "ENEV3": "Eneva",
        "CMIG4": "Cemig",
        "CPLE3": "Copel (ex-CPLE6)",
    },
    "Oleo & Gas": {
        "PETR4": "Petrobras",
        "PRIO3": "PRIO",
        "BRAV3": "Brava Energia",
        "RECV3": "PetroReconcavo",
        "VBBR3": "Vibra Energia",
        "UGPA3": "Ultrapar",
        "CSAN3": "Cosan",
    },
    "Transporte": {
        "RAIL3": "Rumo",
        "MOTV3": "Motiva (ex-CCRO3)",
        "ECOR3": "EcoRodovias",
        # STBP3 saiu: Santos Brasil deixou de ter serie no Yahoo apos a OPA.
        "RENT3": "Localiza",
        "MOVI3": "Movida",
    },
    "Varejo": {
        "LREN3": "Lojas Renner",
        "AZZA3": "Azzas 2154",
        "CEAB3": "C&A",
        "MGLU3": "Magazine Luiza",
        "RADL3": "Raia Drogasil",
        "ASAI3": "Assai",
        "PCAR3": "Grupo Pao de Acucar",
    },
    "Metais & Mineracao": {
        "VALE3": "Vale",
        "CMIN3": "CSN Mineracao",
        "GGBR4": "Gerdau",
        "USIM5": "Usiminas",
        "CSNA3": "CSN",
    },
    "Bens de Capital": {
        "WEGE3": "WEG",
        "EMBJ3": "Embraer (ex-EMBR3)",
        "POMO4": "Marcopolo",
    },
    "Alimentos & Bebidas": {
        "ABEV3": "Ambev",
        "JBSS32": "JBS N.V. (DR, ex-JBSS3)",
        # BRF e Marfrig se fundiram: MBRF3 e o unico ticker sobrevivente.
        "MBRF3": "Marfrig Global Foods (ex-BRFS3 e MRFG3)",
        "MDIA3": "M. Dias Branco",
        "SLCE3": "SLC Agricola",
        "AGRO3": "BrasilAgro",
        "SMTO3": "Sao Martinho",
    },
    "Imobiliario": {
        "CYRE3": "Cyrela",
        "CURY3": "Cury",
        "DIRR3": "Direcional",
        "MRVE3": "MRV",
        "EZTC3": "EZTEC",
        "ALOS3": "Allos",
        "MULT3": "Multiplan",
        "IGTI11": "Iguatemi",
    },
    "Papel & Celulose": {
        "SUZB3": "Suzano",
        "KLBN11": "Klabin",
    },
    "Tecnologia": {
        "TOTS3": "Totvs",
        "INTB3": "Intelbras",
        "LWSA3": "Locaweb",
        "BMOB3": "Bemobi",
    },
    "Educacao": {
        "YDUQ3": "YDUQS",
        "COGN3": "Cogna",
    },
}

# Ativos macro. Sao tickers do Yahoo Finance e nao levam sufixo.
MACRO: dict[str, dict[str, str]] = {
    "Indices": {
        "^BVSP": "Ibovespa",
        "^GSPC": "S&P 500",
        "^NDX": "Nasdaq 100",
        "^STOXX50E": "Euro Stoxx 50",
        "^N225": "Nikkei 225",
        "EEM": "MSCI Emergentes (ETF)",
    },
    "Juros": {
        "^TNX": "Treasury 10 anos",
        "^FVX": "Treasury 5 anos",
        "^IRX": "Treasury 13 semanas",
    },
    "Commodities": {
        "BZ=F": "Brent",
        "CL=F": "WTI",
        "GC=F": "Ouro",
        "HG=F": "Cobre",
        "ZS=F": "Soja",
        "SI=F": "Prata",
    },
    "Cambio": {
        "BRL=X": "USD/BRL",
        "DX-Y.NYB": "Indice Dolar (DXY)",
        "EURUSD=X": "EUR/USD",
    },
}

# Juros brasileiros vem da API SGS do Banco Central, nao do Yahoo.
SERIES_BCB = {"selic_meta": 432, "cdi_diario": 12}

BENCHMARKS = {"^BVSP": "Ibovespa", "^GSPC": "S&P 500"}


def setores() -> list[str]:
    return list(SETORES.keys())


def tickers_do_setor(setor: str) -> list[str]:
    return list(SETORES.get(setor, {}).keys())


def todos_tickers_b3() -> list[str]:
    return [t for tickers in SETORES.values() for t in tickers]


def tickers_macro() -> list[str]:
    return [t for grupo in MACRO.values() for t in grupo]


def para_yahoo(ticker: str) -> str:
    """Adiciona .SA apenas em tickers da B3."""
    if ticker in _INDICE_B3:
        return ticker + SUFIXO_B3
    return ticker


def de_yahoo(ticker: str) -> str:
    """Remove o sufixo .SA para exibicao."""
    if ticker.endswith(SUFIXO_B3):
        return ticker[: -len(SUFIXO_B3)]
    return ticker


def nome_de(ticker: str) -> str:
    limpo = de_yahoo(ticker)
    if limpo in _INDICE_B3:
        return _INDICE_B3[limpo][1]
    for grupo in MACRO.values():
        if limpo in grupo:
            return grupo[limpo]
    return limpo


def setor_de(ticker: str) -> str:
    limpo = de_yahoo(ticker)
    if limpo in _INDICE_B3:
        return _INDICE_B3[limpo][0]
    for classe, grupo in MACRO.items():
        if limpo in grupo:
            return classe
    return "Desconhecido"


# {ticker: (setor, nome)} construido uma vez na importacao.
_INDICE_B3: dict[str, tuple[str, str]] = {
    ticker: (setor, nome)
    for setor, tickers in SETORES.items()
    for ticker, nome in tickers.items()
}
