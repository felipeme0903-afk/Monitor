# Monitor B3

Aplicativo Streamlit que monitora ações brasileiras organizadas nos 11 setores
GICS, além de índices globais, juros, commodities e câmbio. Todos os dados vêm
do Yahoo Finance e da API SGS do Banco Central. Não há chamada a modelos de IA:
o pipeline é determinístico e não exige nenhuma chave de API.

## Estado atual: Etapa 1 de 5

| Etapa | Escopo | Situação |
|-------|--------|----------|
| 1 | `universe.py`, `data.py`, barra lateral e Aba 3 (screener) | Concluída |
| 2 | `metrics.py` completo e Aba 4 (raio-X individual) | Pendente |
| 3 | Aba 5 (fundamentos) com cache em disco | Pendente |
| 4 | Abas 1 e 2 e KPIs do topo | Pendente |
| 5 | `theme.py`, revisão de erros e README final | Pendente |

## Como rodar localmente

Requer Python 3.11 ou superior.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

No Linux ou macOS, troque a ativação por `source .venv/bin/activate`.

O app abre em `http://localhost:8501`. O primeiro carregamento baixa dez anos de
cotações do setor selecionado e leva algum tempo. As execuções seguintes usam
cache.

## Deploy no Streamlit Community Cloud

1. Faça push deste repositório para o GitHub.
2. Em share.streamlit.io, escolha New app e aponte para este repositório.
3. Arquivo principal: `app.py`. Versão do Python: 3.11.
4. Nenhum segredo precisa ser configurado.

## Organização do código

| Arquivo | Responsabilidade |
|---------|------------------|
| `universe.py` | Dicionário de setores, tickers, ativos macro e códigos do Banco Central |
| `data.py` | Download em lote, cache de sessão e cache em disco dos demonstrativos |
| `metrics.py` | Cálculo de retorno, volatilidade, beta, múltiplos e rentabilidade |
| `app.py` | Interface, barra lateral e abas |

## Premissas de cálculo

- **Base anual**: 252 dias úteis. A volatilidade é o desvio padrão amostral
  (`ddof=1`) dos retornos logarítmicos diários multiplicado pela raiz de 252.
- **Série de preço**: `Adj Close` para retorno, volatilidade, beta e drawdown.
  `Close` para P/L, P/VP e Dividend Yield.
- **Retorno do período**: `P_0` é o último fechamento em ou antes da data
  inicial. Para YTD isso equivale ao último pregão do ano anterior.
- **Beta**: padrão de 104 observações semanais (2 anos), com fechamento na
  sexta-feira. A opção diária usa 504 observações. O benchmark padrão é o
  Ibovespa.
- **Distância de 52 semanas**: calculada sobre os últimos 252 pregões.
- **Dividend Yield LTM**: soma dos proventos nos 365 dias anteriores à data de
  referência, dividida pelo `Close` naquela data.
- **P/L e EV/EBITDA**: lucro e EBITDA somados dos quatro últimos trimestres
  reportados. Quando o Yahoo não publica quatro trimestres, o cálculo cai para o
  demonstrativo anual mais recente.
- **ROE**: lucro líquido LTM dividido pela média do patrimônio líquido entre o
  primeiro e o último dos quatro trimestres da janela.

## Fontes de dados

| Dado | Fonte |
|------|-------|
| Cotações e proventos | `yfinance.download` com `auto_adjust=False` e `actions=True` |
| Demonstrativos trimestrais e anuais | `yfinance.Ticker.quarterly_income_stmt`, `quarterly_balance_sheet`, `income_stmt`, `balance_sheet` |
| Market Cap atual | `yfinance.Ticker.fast_info` |
| Selic meta e CDI | API SGS do Banco Central, séries 432 e 12 |

Todo ticker da B3 recebe o sufixo `.SA` na consulta ao Yahoo e é exibido sem
ele. Juros brasileiros não existem no Yahoo Finance e vêm do Banco Central.

## Tratamento de erros

Ticker sem dados, balanço ausente, coluna inexistente e divisão por zero
resultam em `NaN`, exibido como `n/d`. Nenhuma dessas situações derruba o app.
Os tickers que falharam aparecem agrupados num único aviso ao pé da tabela.

## Cache

- Cotações: `st.cache_data(ttl=3600)`, na memória da sessão.
- Demonstrativos: arquivos Parquet em `data/`, válidos por 24 horas.

O botão Atualizar dados na barra lateral limpa os dois níveis.

## Aviso

Este projeto não constitui recomendação de investimento. Os dados do Yahoo
Finance podem conter atrasos e inconsistências.
