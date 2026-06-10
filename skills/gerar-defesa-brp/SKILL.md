---
name: gerar-defesa-brp
description: >-
  Gera um RASCUNHO de contestação para um processo da carteira BRP da AJM Advogados a partir da
  petição inicial (PDF na pasta do processo) e da base de teses do escritório. Seleciona
  automaticamente as teses aplicáveis, monta a minuta em .docx na estrutura do escritório, com um
  bloco de "teses aplicadas e justificativa" e um alerta de confiança, e atualiza o status no
  SQLite. Use quando houver uma petição inicial baixada na pasta de um processo BRP e for
  preciso produzir um rascunho de defesa, ou quando pedirem para "gerar/elaborar a contestação/defesa".
---

# Gerar rascunho de defesa BRP (Fase 2)

Produz um **rascunho** de contestação. A peça final é sempre do advogado — esta skill entrega um
ponto de partida sólido, transparente e rápido de revisar. Por isso, duas obsessões guiam tudo:
**transparência** (deixar claro o que foi usado e por quê) e **fidelidade às fontes** (não inventar
nada jurídico).

## Quando roda

Começa quando a **petição inicial** já está na pasta do processo (subpasta de petição), baixada
dos autos pelo advogado. A skill não busca a petição nos tribunais — isso é manual.

## Regras inegociáveis

- **Nunca protocolar.** Esta skill só gera rascunho; quem revisa e protocola é o advogado.
- **Nunca inventar jurisprudência ou citação.** Use **apenas** o que está em `assets/teses/`. Se
  uma tese não tem julgado colado na base, escreva o argumento sem citação e sinalize a lacuna.
  Citação falsa é o pior erro possível aqui.
- **Não afirmar fato que não está na petição.** Os fatos do caso saem do PDF; o resto da base é
  argumento jurídico, não fato.

## Passo a passo

### 1. Ler a petição inicial
Use a skill `pdf` para extrair o texto do PDF na pasta do processo. Identifique e resuma:
- partes (autor e quem é acionado), contrato/operação, valores;
- **causa de pedir** (o que o autor alega) e **pedidos** (o que ele requer).

### 2. Selecionar as teses (automático)
Compare a causa de pedir e os pedidos com os gatilhos ("Quando se aplica") de cada arquivo em
`assets/teses/`. Selecione todas as teses que se encaixam. Para cada tese considerada, registre
**por que** aplicou ou descartou.

### 3. Avaliar a confiança
Classifique o caso:
- **Rotina** — a petição casa claramente com teses conhecidas (o típico da carteira BRP).
- **Atenção** — algo foge do padrão: pedido incomum, tese que encaixa só em parte, fato que não
  bate com nenhuma tese, ou petição confusa/ilegível. Liste o que gerou dúvida.

### 4. Montar o rascunho (.docx)
Use a skill `docx` para gerar a minuta na estrutura do escritório (preliminares, mérito, pedidos),
combinando o texto-modelo das teses selecionadas com os fatos do caso. **No topo do documento**,
inclua um bloco de revisão:

```
RASCUNHO PARA REVISÃO — não protocolar sem revisão de advogado
Nível: Rotina | Atenção
Teses aplicadas: <lista> — justificativa: <por quê>
Teses descartadas: <lista> — motivo: <por quê>
Pontos de atenção: <lacunas, dúvidas, citações faltando>
```

Salve o `.docx` na subpasta de defesa do processo (`03 - Defesa`), com nome claro
(ex.: `Contestação (rascunho) - <Parte> - <Número>.docx`).

### 5. Atualizar o SQLite
Via `database-brp`: `status_minuta = Rascunho gerado` e `teses_aplicaveis` com a lista das teses
usadas. Não escreva automaticamente na planilha; se a equipe pedir atualização do `.xlsx`, rode
`registrar-planilha-brp` manualmente depois, lendo do SQLite.

### 6. Entregar para revisão
Avise que o rascunho está pronto, destacando o **Nível** e os **pontos de atenção**. Em casos
"Atenção", peça revisão mais cuidadosa da seleção de teses. Nunca dê a defesa por finalizada.

## Validação (fase de calibração)
Nos primeiros 5 a 10 casos, compare o rascunho com a contestação real que o escritório escreveria
e ajuste os arquivos de `assets/teses/` (gatilhos, texto-modelo) até o rascunho ficar próximo do
padrão da AJM. O aprendizado vai para a base de teses, não para código.
