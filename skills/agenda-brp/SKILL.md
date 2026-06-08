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

A partir do registro da citação, **até dois eventos por processo**:

- **Audiência** (categoria `Audiência BRP`, vermelha) — **somente** quando há data/hora de
  audiência confirmada. Se `audiencia` for `verificar autos`, `não` ou vazio, **não crie
  evento de audiência nenhum** — nunca use o dia da execução como data placeholder. O script
  recusa audiência sem data/hora justamente para evitar esse lixo na agenda. Inclua no corpo a
  `audiencia_obs` (ex.: "telepresencial via Teams") e o número do processo.
- **Prazo de defesa** (categoria `Prazo BRP`, amarela) — evento de dia inteiro na data-limite.
  Essa data é **calculada automaticamente**: `data_recebimento + 13 dias úteis`, pulando apenas
  sábados e domingos (feriados ignorados de propósito — um prazo mais cedo é mais conservador,
  menos risco de perder a defesa). É um prazo **PROVISÓRIO**: o corpo do evento avisa para
  confirmar nos autos. Passe `--recebimento` e o script faz a conta (mesma regra da planilha,
  em `lib/datas.py`). Só caia para a tarefa `verificar` ("Verificar prazo nos autos") se **nem
  a data de recebimento** for conhecida.

## Como executar

Use `scripts/criar_evento_graph.py`. Ele cuida da autenticação (client credentials), garante
que a categoria exista com a cor certa e cria o evento no calendário "BRP". O modo `--simular`
imprime o que seria criado sem chamar a rede — use enquanto o registro de app não estiver
pronto.

```
# Audiência — SÓ com data/hora confirmada (sem data, não rode: o script recusa)
python scripts/criar_evento_graph.py --tipo audiencia \
  --numero "0854280-80.2026.8.14.0301" --parte "FELIX NUNES DE ALMEIDA NETO" \
  --inicio "2026-09-30T09:30:00" --obs "telepresencial via Teams"

# Prazo de defesa — CALCULADO a partir do recebimento (recebimento + 13 dias úteis)
python scripts/criar_evento_graph.py --tipo prazo \
  --numero "..." --parte "..." --recebimento "27/05/2026"

# (Opcional) prazo com data já pronta, em vez de calcular:
python scripts/criar_evento_graph.py --tipo prazo --numero "..." --inicio "2026-06-15"

# Fallback raro — sem nem a data de recebimento, só uma tarefa de verificação:
python scripts/criar_evento_graph.py --tipo verificar \
  --numero "..." --parte "..." --inicio "2026-06-02"
```

Depois de lançar, não há campo dedicado de "evento criado" na planilha; registre o sucesso/
falha no retorno para a orquestração. Se a Graph recusar (token, permissão, calendário não
encontrado), **relate** — não siga como se tivesse lançado.

## Idempotência (não duplicar eventos)

Rodar a rotina mais de uma vez para o mesmo processo **não cria cópias**. Cada processo tem no
máximo uma audiência, um prazo e uma tarefa de verificação; a chave é `tipo|número CNJ`
(a data **não** entra na chave de propósito). O script faz *upsert*:

- **não existe** ainda → cria o evento;
- **já existe** → atualiza o existente (ex.: audiência remarcada passa a refletir a nova hora);
- **existe em duplicidade** (cópias de execuções antigas, antes desta correção) → mantém uma e
  **apaga as sobrando**, consolidando.

O evento mantido recebe um carimbo numa propriedade estendida (`brpKey`), e o casamento também
reconhece eventos legados pelo número CNJ no assunto — então a primeira rodada após a correção
já limpa as duplicatas que ficaram para trás. O retorno traz `acao`: `criado`, `atualizado` ou
`consolidado`.

## Cores

No Outlook, a cor vem de **categorias nomeadas** com cor pré-definida no nível da caixa
(masterCategories). O script garante que `Audiência BRP` (vermelho) e `Prazo BRP` (amarelo)
existam antes de criar o evento. Ajuste os nomes/cores no topo do script se a AJM preferir
outra convenção.
