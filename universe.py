"""Universo de ativos do Monitor B3.

Tickers da B3 sao guardados sem sufixo. O sufixo .SA exigido pelo Yahoo
Finance e adicionado apenas na hora da consulta, por `para_yahoo`.
"""

from __future__ import annotations

SUFIXO_B3 = ".SA"

# {setor: {subsetor: {ticker: nome de exibicao}}}
# Classificacao propria por atividade-fim, em dois niveis. So acoes locais:
# BDRs ficaram de fora porque o Yahoo nao entrega multiplos confiaveis para
# eles. Sairam por falta de cotacoes no Yahoo: NEOE3, NGRD3, ODPV3, JBSS3
# (JBS so negocia como BDR, JBSS32), ELET3 (hoje AXIA3) e BRIT3 (hoje BRST3).
SETORES: dict[str, dict[str, dict[str, str]]] = {
    "Financeiro e Imobiliario": {
        "Bancos": {
            "ITUB4": "Itau Unibanco",
            "BBDC4": "Bradesco",
            "BBAS3": "Banco do Brasil",
            "SANB11": "Santander Brasil",
            "BPAC11": "BTG Pactual",
            "BRSR6": "Banrisul",
        },
        "Seguros e resseguros": {
            "BBSE3": "BB Seguridade",
            "CXSE3": "Caixa Seguridade",
            "PSSA3": "Porto Seguro",
            "IRBR3": "IRB(Re)",
        },
        "Holdings de participacoes": {
            "ITSA4": "Itausa",
            "BRAP4": "Bradespar",
            "CSAN3": "Cosan",
        },
        "Shopping centers": {
            "ALOS3": "Allos",
            "MULT3": "Multiplan",
        },
        "Incorporacao residencial": {
            "CYRE3": "Cyrela",
            "MRVE3": "MRV",
            "CURY3": "Cury",
            "DIRR3": "Direcional",
        },
    },
    "Varejo e Servicos ao Consumidor": {
        "Varejo de moda e joias": {
            "LREN3": "Lojas Renner",
            "AZZA3": "Azzas 2154",
            "CEAB3": "C&A",
            "VIVA3": "Vivara",
        },
        "Varejo de eletronicos e e-commerce": {
            "MGLU3": "Magazine Luiza",
        },
        "Varejo alimentar (atacarejo)": {
            "ASAI3": "Assai",
            "GMAT3": "Grupo Mateus",
        },
        "Locacao de veiculos e maquinas": {
            "RENT3": "Localiza",
            "VAMO3": "Vamos",
        },
        "Educacao": {
            "YDUQ3": "YDUQS",
        },
        "Academias": {
            "SMFT3": "Smart Fit",
        },
        "Servicos terceirizados (facilities)": {
            "GGPS3": "Grupo GPS",
        },
    },
    "Alimentos, Bebidas e Agronegocio": {
        "Alimentos e bebidas": {
            "ABEV3": "Ambev",
            "MDIA3": "M. Dias Branco",
            "CAML3": "Camil",
        },
        "Proteina animal (frigorificos)": {
            # BRF e Marfrig se fundiram: MBRF3 e o unico ticker sobrevivente.
            "MBRF3": "MBRF (ex-BRFS3 e MRFG3)",
            "BEEF3": "Minerva",
        },
        "Graos e insumos agricolas": {
            "SLCE3": "SLC Agricola",
            "TTEN3": "3tentos",
        },
        "Acucar e etanol": {
            "SMTO3": "Sao Martinho",
            "JALL3": "Jalles Machado",
            "RAIZ4": "Raizen",
        },
        "Higiene pessoal e beleza": {
            "NATU3": "Natura",
        },
    },
    "Petroleo e Gas": {
        "Exploracao e producao": {
            "PETR4": "Petrobras",
            "PRIO3": "PRIO",
            "BRAV3": "Brava Energia",
            "RECV3": "PetroReconcavo",
        },
        "Distribuicao de combustiveis e gas": {
            "VBBR3": "Vibra Energia",
            "UGPA3": "Ultrapar",
            "PASS3": "Compass",
        },
    },
    "Materiais Basicos": {
        "Mineracao": {
            "VALE3": "Vale",
            "CMIN3": "CSN Mineracao",
        },
        "Siderurgia": {
            "GGBR4": "Gerdau",
            "CSNA3": "CSN",
            "USIM5": "Usiminas",
        },
        "Papel e celulose": {
            "SUZB3": "Suzano",
            "KLBN11": "Klabin",
        },
        "Petroquimica": {
            "BRKM5": "Braskem",
        },
    },
    "Industria e Infraestrutura de Transporte": {
        "Maquinas, veiculos e componentes": {
            "WEGE3": "WEG",
            "EMBJ3": "Embraer (ex-EMBR3)",
            "POMO4": "Marcopolo",
            "RAPT4": "Randoncorp",
            "TUPY3": "Tupy",
        },
        "Concessoes de rodovias e ferrovias": {
            "MOTV3": "Motiva (ex-CCRO3)",
            "ECOR3": "EcoRodovias",
            "RAIL3": "Rumo",
        },
    },
    "Saude": {
        "Hospitais e medicina diagnostica": {
            "RDOR3": "Rede D'Or",
            "MATD3": "Mater Dei",
            "FLRY3": "Fleury",
        },
        "Planos de saude": {
            "HAPV3": "Hapvida",
        },
        "Industria farmaceutica": {
            "HYPE3": "Hypera Pharma",
            "BLAU3": "Blau Farmaceutica",
        },
        "Farmacias": {
            "RADL3": "RD Saude",
            "PGMN3": "Pague Menos",
        },
    },
    "Tecnologia e Telecomunicacoes": {
        "Software e plataformas digitais": {
            "TOTS3": "Totvs",
            "LWSA3": "Locaweb",
            "BMOB3": "Bemobi",
            "CASH3": "Meliuz",
        },
        "Hardware e equipamentos": {
            "INTB3": "Intelbras",
            "POSI3": "Positivo Tecnologia",
            "PDTC3": "Padtec",
            "ALLD3": "Allied Tecnologia",
        },
        "Operadoras de telecomunicacoes": {
            "VIVT3": "Telefonica Brasil (Vivo)",
            "TIMS3": "TIM",
            "BRST3": "Brisanet (ex-BRIT3)",
            "FIQE3": "Unifique",
        },
    },
    "Energia Eletrica e Saneamento": {
        "Geracao de energia": {
            "AXIA3": "Axia Energia (ex-Eletrobras, ex-ELET3)",
            "EGIE3": "Engie Brasil",
            "ENEV3": "Eneva",
        },
        "Distribuicao e energia integrada": {
            "EQTL3": "Equatorial",
            "CMIG4": "Cemig",
            "CPLE3": "Copel (ex-CPLE6)",
            "CPFE3": "CPFL Energia",
        },
        "Transmissao de energia": {
            "TAEE11": "Taesa",
            "ISAE4": "ISA Energia (ex-TRPL4)",
        },
        "Saneamento": {
            "SBSP3": "Sabesp",
        },
    },
}

# Em bancos e seguradoras, "divida" e captacao e nao ha EBITDA nem receita
# operacional comparavel. Nesses subsetores o app mostra n/d em EV/EBITDA,
# Market Equity/Debt, Divida liquida/EBITDA e margens.
SUBSETORES_FINANCEIROS = {"Bancos", "Seguros e resseguros"}

# Subsetores com menos acoes que isto recebem aviso de amostra pequena.
AMOSTRA_MINIMA = 3

# Units negociam um pacote de acoes. O balanco informa acoes, nao units, entao
# o market cap calculado divide o total de acoes por este fator.
ACOES_POR_UNIT: dict[str, int] = {
    "SANB11": 2,  # 1 ON + 1 PN
    "BPAC11": 3,  # 1 ON + 2 PNA
    "KLBN11": 5,  # 1 ON + 4 PN
    "TAEE11": 3,  # 1 ON + 2 PN
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


def subsetores(setor: str) -> list[str]:
    return list(SETORES.get(setor, {}).keys())


def tickers_do_setor(setor: str) -> list[str]:
    return [t for grupo in SETORES.get(setor, {}).values() for t in grupo]


def tickers_do_subsetor(setor: str, subsetor: str) -> list[str]:
    return list(SETORES.get(setor, {}).get(subsetor, {}).keys())


def acoes_por_unit(ticker: str) -> int:
    return ACOES_POR_UNIT.get(de_yahoo(ticker), 1)


def todos_tickers_b3() -> list[str]:
    return list(_INDICE_B3)


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


def subsetor_de(ticker: str) -> str:
    limpo = de_yahoo(ticker)
    return _SUBSETOR_DE.get(limpo, "")


def eh_financeira(ticker: str) -> bool:
    """Bancos e seguradoras: metricas de divida, EBITDA e margem nao se aplicam."""
    return subsetor_de(ticker) in SUBSETORES_FINANCEIROS


# {ticker: (setor, nome)} e {ticker: subsetor}, construidos na importacao.
_INDICE_B3: dict[str, tuple[str, str]] = {
    ticker: (setor, nome)
    for setor, grupos in SETORES.items()
    for tickers in grupos.values()
    for ticker, nome in tickers.items()
}
_SUBSETOR_DE: dict[str, str] = {
    ticker: subsetor
    for grupos in SETORES.values()
    for subsetor, tickers in grupos.items()
    for ticker in tickers
}
