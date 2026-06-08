# Base de teses — carteira BRP

Esta pasta é a "biblioteca de defesa" que a skill `gerar-defesa-brp` consome. Cada arquivo é
**uma tese**, com tudo que o modelo precisa para reconhecer quando ela se aplica e para escrever
o trecho correspondente da contestação.

## Como funciona

1. A skill lê a **petição inicial** e identifica a causa de pedir e os pedidos do autor.
2. Compara com os **gatilhos** ("Quando se aplica") de cada tese e **seleciona** as aplicáveis.
3. Monta o rascunho usando os **fundamentos**, a **jurisprudência** e o **texto-modelo** das
   teses escolhidas, adaptando aos fatos do caso.

## Como preencher (AJM)

Cada arquivo tem seções com `(preencher com material da AJM)`. Cole o conteúdo dos modelos de
contestação e da base de jurisprudência que o escritório já usa. Quanto mais fiel ao padrão de
vocês, melhor o rascunho.

**Regra de ouro — jurisprudência:** só entra na base o que vocês colarem aqui. A skill é
instruída a **não inventar** julgados nem citações; ela usa apenas o que estiver nestes arquivos.
Isso evita o risco de citação falsa.

## Teses (ponto de partida da proposta)

- `01-juros-acima-bacen.md` — juros acima da taxa média BACEN
- `02-venda-casada-seguro.md` — venda casada de seguro
- `03-cdc.md` — aplicação do CDC
- `04-legitimidade-passiva-cessao.md` — legitimidade passiva (cessão de contrato)
- `05-dano-moral-repeticao-indebito.md` — dano moral / repetição de indébito

Para acrescentar uma tese nova, copie um arquivo existente como modelo e mantenha as mesmas seções.
