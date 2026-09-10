"""Universo de ativos do Monitor B3.

Tickers da B3 sao guardados sem sufixo. O sufixo .SA exigido pelo Yahoo
Finance e adicionado apenas na hora da consulta, por `para_yahoo`.
"""

from __future__ import annotations

SUFIXO_B3 = ".SA"

# {setor GICS: {ticker: nome de exibicao}}
SETORES: dict[str, dict[str, str]] = {
    "Tecnologia": {
        "TOTS3": "Totvs",
        "INTB3": "Intelbras",
        "LWSA3": "Locaweb",
        "BMOB3": "Bemobi",
        # BDRs opcionais: nao sao acoes locais, mas dao exposicao ao setor.
        "ROXO34": "Nu Holdings (BDR)",
        "STOC31": "StoneCo (BDR)",
        "PAGS34": "PagSeguro (BDR)",
    },
    "Financeiro": {
        "ITUB4": "Itau Unibanco",
        "BBDC4": "Bradesco",
        "BBAS3": "Banco do Brasil",
        "BPAC11": "BTG Pactual",
        "SANB11": "Santander Brasil",
        "B3SA3": "B3",
        "BBSE3": "BB Seguridade",
        "CXSE3": "Caixa Seguridade",
        "PSSA3": "Porto Seguro",
    },
    "Bens Industriais": {
        "WEGE3": "WEG",
        "EMBR3": "Embraer",
        "RAIL3": "Rumo",
        "MOTV3": "Motiva (ex-CCRO3)",
        "ECOR3": "EcoRodovias",
        "STBP3": "Santos Brasil",  # conferir se segue listada apos a OPA
        "POMO4": "Marcopolo",
    },
    "Saude": {
        "RDOR3": "Rede D'Or",
        "HAPV3": "Hapvida",
        "RADL3": "Raia Drogasil",
        "FLRY3": "Fleury",
        "HYPE3": "Hypera",
    },
    "Consumo Ciclico": {
        "RENT3": "Localiza",
        "MOVI3": "Movida",
        "LREN3": "Lojas Renner",
        "AZZA3": "Azzas 2154",
        "CEAB3": "C&A",
        "YDUQ3": "YDUQS",
        "COGN3": "Cogna",
        "MGLU3": "Magazine Luiza",
    },
    "Comunicacao": {
        "VIVT3": "Telefonica Brasil",
        "TIMS3": "TIM",
        "DESK3": "Desktop",
        "BRIT3": "Brisanet",
    },
    "Energia": {
        "PETR4": "Petrobras",
        "PRIO3": "PRIO",
        "BRAV3": "Brava Energia",
        "RECV3": "PetroReconcavo",
        "VBBR3": "Vibra Energia",
        "UGPA3": "Ultrapar",
        "CSAN3": "Cosan",
    },
    "Consumo Nao Ciclico": {
        "ABEV3": "Ambev",
        "ASAI3": "Assai",
        "PCAR3": "Grupo Pao de Acucar",
        "JBSS3": "JBS",
        "BRFS3": "BRF",
        "MRFG3": "Marfrig",
        "MDIA3": "M. Dias Branco",
        "SLCE3": "SLC Agricola",
        "AGRO3": "BrasilAgro",
        "SMTO3": "Sao Martinho",
    },
    "Materiais Basicos": {
        "VALE3": "Vale",
        "CMIN3": "CSN Mineracao",
        "SUZB3": "Suzano",
        "KLBN11": "Klabin",
        "GGBR4": "Gerdau",
        "USIM5": "Usiminas",
        "CSNA3": "CSN",
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
    "Utilidade Publica": {
        "SBSP3": "Sabesp",
        "CSMG3": "Copasa",
        "SAPR11": "Sanepar",
        "ELET3": "Eletrobras",
        "EQTL3": "Equatorial",
        "CPFE3": "CPFL Energia",
        "EGIE3": "Engie Brasil",
        "TAEE11": "Taesa",
        "ENEV3": "Eneva",
        "CMIG4": "Cemig",
        "CPLE6": "Copel",
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
