---
name: agenda-brp
description: >-
  Lança no calendário "BRP" do escritório AJM Advogados (Exchange Online via Microsoft Graph)
  os compromissos de um processo: a audiência (categoria/cor vermelha) e o prazo de defesa
  (categoria/cor amarela), além de uma tarefa de "verificar prazo nos autos" quando o prazo
  ainda não é conhecido. Use depois de processar-citacao-brp para garantir que audiências e
  prazos da carteira BRP apareçam na agenda compartilhada com cores diferenciadas.
---

# Agenda BRP



Lança audiências e prazos no calendário compartilhado "BRP". É a peça que ataca diretamente o
incidente que motivou o projeto — a audiência que passou despercebida. Por isso o cuidado
central aqui é: **só lançar data em que se tem certeza**, e, quando não se tem, lançar uma
*tarefa de verificação* em vez de uma data falsa.

## Pré-requisito: registro de app no Azure AD

O conector Microsoft 365 padrão só lê. Para **escrever** eventos usamos a Microsoft Graph com
um registro de aplicativo (app registration) próprio. O passo a passo para o administrador
está em `references/azure-app-registration.md`. Sem essas credenciais, a skill roda em modo
simulação (mostra o evento que criaria, sem gravar).

As credenciais ficam em variáveis de ambiente na máquina onde a automação roda:
`GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET`, e `BRP_MAILBOX` (a caixa que
hospeda o calendário compartilhado).

## O que lançar

A partir do registro da citação:

- **Audiência** — se `audiencia` tiver data/hora: evento no horário, categoria `Audiência BRP`
  (cor vermelha). Inclua no corpo a `audiencia_obs` (ex.: "telepresencial via Teams") e o
  número do processo.
- **Prazo de defesa** — se `prazo_defesa` for uma data conhecida: evento de dia inteiro,
  categoria `Prazo BRP` (cor amarela). Se for `verificar autos`, **não invente data**: crie
  um evento/tarefa de dia inteiro hoje (ou no dia seguinte) intitulado
  "Verificar prazo nos autos — <processo>", para a triagem humana abrir os autos e confirmar.

## Como executar

Use `scripts/criar_evento_graph.py`. Ele cuida da autenticação (client credentials), garante
que a categoria exista com a cor certa e cria o evento no calendário "BRP". O modo `--simular`
imprime o que seria criado sem chamar a rede — use enquanto o registro de app não estiver
pronto.

```
# Audiência (com data/hora)
python scripts/criar_evento_graph.py --tipo audiencia \
  --numero "0854280-80.2026.8.14.0301" --parte "FELIX NUNES DE ALMEIDA NETO" \
  --inicio "2026-09-30T09:30:00" --obs "telepresencial via Teams"

# Prazo conhecido (dia inteiro)
python scripts/criar_evento_graph.py --tipo prazo \
  --numero "..." --parte "..." --inicio "2026-06-20"

# Prazo desconhecido → tarefa de verificação
python scripts/criar_evento_graph.py --tipo verificar \
  --numero "..." --parte "..." --inicio "2026-06-02"
```

Depois de lançar, não há campo dedicado de "evento criado" na planilha; registre o sucesso/
falha no retorno para a orquestração. Se a Graph recusar (token, permissão, calendário não
encontrado), **relate** — não siga como se tivesse lançado.

## Cores

No Outlook, a cor vem de **categorias nomeadas** com cor pré-definida no nível da caixa
(masterCategories). O script garante que `Audiência BRP` (vermelho) e `Prazo BRP` (amarelo)
existam antes de criar o evento. Ajuste os nomes/cores no topo do script se a AJM preferir
outra convenção.
