---
name: registrar-planilha-brp
description: >-
  MANUAL. Lê os processos salvos no SQLite local da automação BRP e registra/atualiza uma
  planilha exclusiva do Claude/automação, separada da planilha original da AJM. Usa o mesmo
  processo de dedup pelo número CNJ e preservação de células já preenchidas. Não use
  automaticamente depois de processar-citacao-brp; invoque somente quando alguém pedir para
  atualizar a planilha do Claude.
---

# Registrar na planilha de controle BRP

Esta skill é **manual** e não faz parte do intake automático. Na v0.3, a memória operacional é
o SQLite (`database-brp`); quando a equipe quiser atualizar a visão em planilha, esta skill lê
do SQLite e escreve em um `.xlsx` exclusivo do Claude/automação.

A automação **não toca na planilha original da AJM**. O destino deve ser um arquivo separado,
por padrão:

```text
G:\A.Digital\BRP\Defesas BRP - Claude.xlsx
```

Se esse arquivo ainda não existir, o script cria uma nova planilha com o schema esperado.

## Acompanhamento por TODO

Antes de registrar a planilha, chame a ferramenta de TODO do Claude para deixar claro o escopo:

1. Confirmar banco SQLite origem.
2. Confirmar planilha `.xlsx` destino exclusiva do Claude.
3. Ler processo(s) do SQLite.
4. Aplicar dedup/atualização na planilha do Claude.
5. Salvar planilha do Claude e resumir inseridos/atualizados/sem alteração.

## Princípios

- **Não duplicar.** Antes de inserir, procure o `numero_processo` na coluna "Nº do Processo".
  Se já existe, atualize a linha existente (preenchendo campos que estavam vazios) em vez de
  criar outra. É o filtro de segurança que torna a execução horária idempotente — rodar duas
  vezes não bagunça a planilha.
- **Não inventar.** Campo sem informação recebe `verificar autos` ou fica vazio, nunca um
  palpite. Ver o porquê em `assets/schema-planilha.md`.
- **Prazo de defesa calculado (provisório).** A única exceção ao "não inventar" é o prazo:
  quando há `data_recebimento` e o prazo não foi informado, o script calcula
  `recebimento + 13 dias úteis` (sáb/dom pulados, feriados ignorados — propositalmente
  conservador) e grava essa data com `Fonte do prazo = Provisório`. Não é um palpite disfarçado
  de certo: fica explicitamente marcado como provisório, para a triagem confirmar nos autos.
  A regra mora em `lib/datas.py` (a mesma usada pela agenda).
- **Preservar o que a equipe já preencheu.** Se um advogado já pôs o prazo ou o responsável à
  mão, não sobrescreva — só o placeholder `verificar autos` é promovido à data calculada.

## Como executar

Use o script `scripts/registrar_do_sqlite.py`, que lê o SQLite e usa o mesmo processo de
`append_to_planilha.py`: dedup, mapeamento de colunas e preservação de valores já preenchidos.

```
# um processo específico
python scripts/registrar_do_sqlite.py --numero "<CNJ>" --planilha "<caminho.xlsx>"

# todos os processos do SQLite
python scripts/registrar_do_sqlite.py --todos --planilha "<caminho.xlsx>"
```

Se `--planilha` não for informado, o script usa `planilha_claude_path` de
`config/brp.config.json`. O script exige `--numero` ou `--todos` para evitar escrita ampla
acidental. Não use o caminho da planilha original da AJM como destino.

Se o caminho da planilha do Claude não estiver acessível (sem VPN, arquivo aberto/bloqueado), **não
falhe em silêncio**: relate o que tentou e o processo que seria gravado, para a triagem
humana resolver.

## Exemplo

Registro no SQLite (do Exemplo 3, TJPA):

```json
{
  "numero_processo": "0854280-80.2026.8.14.0301",
  "parte_contraria": "FELIX NUNES DE ALMEIDA NETO",
  "tribunal_uf": "TJPA / PA",
  "comarca_origem": "0301 (a confirmar)",
  "data_recebimento": "27/05/2026",
  "audiencia": "30/09/2026 09:30",
  "audiencia_obs": "telepresencial via Microsoft Teams",
  "prazo_defesa": "verificar autos",
  "fonte_prazo": "E-mail"
}
```

Resultado esperado: como o número ainda não está na planilha do Claude, insere uma nova linha; se já
existir, preenche apenas campos vazios e preserva as edições humanas.
