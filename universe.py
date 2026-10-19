"""Universo de ativos do Monitor B3.

Tickers da B3 sao guardados sem sufixo. O sufixo .SA exigido pelo Yahoo
Finance e adicionado apenas na hora da consulta, por `para_yahoo`.
"""

from __future__ import annotations

SUFIXO_B3 = ".SA"

# {setor da B3: {ticker: nome de exibicao}}
# Classificacao setorial da B3. Os BDRs (final 32-35) dao exposicao
# internacional ao setor, mas nao sao acoes locais.
SETORES: dict[str, dict[str, str]] = {
    "Bens Industriais": {
        "WEGE3": "WEG",
        "EMBJ3": "Embraer (ex-EMBR3)",
        "MOTV3": "Motiva (ex-CCRO3)",
        "RAIL3": "Rumo",
        "POMO4": "Marcopolo",
        "RAPT4": "Randoncorp",
        "TUPY3": "Tupy",
        "ECOR3": "EcoRodovias",
        "GEOO34": "GE Aerospace (BDR)",
        "HONB34": "Honeywell (BDR)",
    },
    "Consumo Ciclico": {
        "RENT3": "Localiza",
        "LREN3": "Lojas Renner",
        "MGLU3": "Magazine Luiza",
        "AZZA3": "Azzas 2154",
        "CYRE3": "Cyrela",
        "MRVE3": "MRV",
        "CURY3": "Cury",
        "DIRR3": "Direcional",
        "SMFT3": "Smart Fit",
        "VIVA3": "Vivara",
        "AMZO34": "Amazon (BDR)",
        "MCDC34": "McDonald's (BDR)",
    },
    "Consumo Nao Ciclico": {
        "ABEV3": "Ambev",
        "JBSS32": "JBS N.V. (DR, ex-JBSS3)",
        # BRF e Marfrig se fundiram: MBRF3 e o unico ticker sobrevivente.
        "MBRF3": "MBRF (ex-BRFS3 e MRFG3)",
        "ASAI3": "Assai",
        "NATU3": "Natura",
        "MDIA3": "M. Dias Branco",
        "CAML3": "Camil",
        "BEEF3": "Minerva",
        "GMAT3": "Grupo Mateus",
        "COCA34": "Coca-Cola (BDR)",
        "WALM34": "Walmart (BDR)",
        "PGCO34": "Procter & Gamble (BDR)",
    },
    "Financeiro": {
        "ITUB4": "Itau Unibanco",
        "BBDC4": "Bradesco",
        "BBAS3": "Banco do Brasil",
        "SANB11": "Santander Brasil",
        "BPAC11": "BTG Pactual",
        "B3SA3": "B3",
        "ITSA4": "Itausa",
        "BBSE3": "BB Seguridade",
        "CXSE3": "Caixa Seguridade",
        "PSSA3": "Porto Seguro",
        "ROXO34": "Nu Holdings (BDR, ex-NUBR33)",
        # A B3 classifica shoppings em Financeiro > Exploracao de Imoveis.
        "ALOS3": "Allos",
        "JPMC34": "JPMorgan (BDR)",
        "VISA34": "Visa (BDR)",
    },
    "Materiais Basicos": {
        "VALE3": "Vale",
        "SUZB3": "Suzano",
        "KLBN11": "Klabin",
        "GGBR4": "Gerdau",
        "CSNA3": "CSN",
        "CMIN3": "CSN Mineracao",
        "USIM5": "Usiminas",
        "BRKM5": "Braskem",
        "BRAP4": "Bradespar",
    },
    "Petroleo, Gas e Biocombustiveis": {
        "PETR4": "Petrobras",
        "PRIO3": "PRIO",
        "VBBR3": "Vibra Energia",
        "UGPA3": "Ultrapar",
        "BRAV3": "Brava Energia",
        "RECV3": "PetroReconcavo",
        "CSAN3": "Cosan",
        "RAIZ4": "Raizen",
        "EXXO34": "Exxon Mobil (BDR)",
        "CHVX34": "Chevron (BDR)",
    },
    "Saude": {
        "RDOR3": "Rede D'Or",
        "HAPV3": "Hapvida",
        "RADL3": "RD Saude",
        "FLRY3": "Fleury",
        "HYPE3": "Hypera Pharma",
        "ODPV3": "OdontoPrev",
        "MATD3": "Mater Dei",
        "JNJB34": "Johnson & Johnson (BDR)",
        "PFIZ34": "Pfizer (BDR)",
    },
    "Tecnologia da Informacao": {
        "TOTS3": "Totvs",
        "LWSA3": "Locaweb",
        "INTB3": "Intelbras",
        "POSI3": "Positivo Tecnologia",
        "AAPL34": "Apple (BDR)",
        "MSFT34": "Microsoft (BDR)",
        "GOGL35": "Alphabet (BDR)",
        "NVDC34": "Nvidia (BDR)",
        "M1TA34": "Meta Platforms (BDR)",
    },
    "Telecomunicacoes": {
        "VIVT3": "Telefonica Brasil (Vivo)",
        "TIMS3": "TIM",
        "BRST3": "Brisanet (ex-BRIT3)",
        "FIQE3": "Unifique",
    },
    "Utilidade Publica": {
        "AXIA3": "Axia Energia (ex-Eletrobras, ex-ELET3)",
        "EQTL3": "Equatorial",
        "SBSP3": "Sabesp",
        "CMIG4": "Cemig",
        "CPLE3": "Copel (ex-CPLE6)",
        "CPFE3": "CPFL Energia",
        "EGIE3": "Engie Brasil",
        "ENEV3": "Eneva",
        "NEOE3": "Neoenergia",
        "TAEE11": "Taesa",
        "ISAE4": "ISA Energia (ex-TRPL4)",
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
