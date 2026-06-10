---
name: configurar-brp
description: >-
  Assistente de configuração/instalação do plugin de automação BRP da AJM Advogados. Conduz
  interativamente a preparação de uma máquina: verifica pré-requisitos, garante o conector
  Microsoft 365, pergunta os dados específicos da instalação (caixa monitorada, caminho da
  planilha, base das pastas, calendário, credenciais do Azure), grava os arquivos de
  configuração, inicializa o SQLite local, roda uma verificação e oferece criar a tarefa agendada. Use SEMPRE que alguém
  for "instalar", "configurar", "inicializar" ou "preparar" a automação BRP numa máquina (a do
  Daniel ou outra), ou quando pedirem para "reconfigurar"/"trocar" algum dado da automação.
---

# Configurar BRP (assistente de instalação)

Esta skill prepara uma máquina para rodar a automação BRP. Ela é conversacional: faz perguntas,
confirma cada resposta e **grava a configuração** nos arquivos que as demais skills leem. O
objetivo é que a própria equipe da AJM consiga instalar/reconfigurar sem depender de ninguém —
por isso, explique cada passo em linguagem simples e nunca siga adiante com um dado em dúvida.

É **re-executável**: rodar de novo serve para reconfigurar (trocar a caixa, o caminho da
planilha, renovar o segredo etc.). Sempre leia a config atual antes e mostre o que vai mudar.

## Acompanhamento por TODO

Antes de começar, chame a ferramenta de TODO do Claude para criar uma lista visível da
instalação. Mantenha exatamente um item como `in_progress`, atualize a lista a cada avanço e
use os nomes dos passos abaixo para a pessoa saber onde está e aonde vai chegar:

1. Checar pré-requisitos.
2. Validar conector Microsoft 365.
3. Coletar caminhos e credenciais.
4. Gravar configuração local.
5. Inicializar e validar SQLite.
6. Testar backup.
7. Testar planilha, pasta e calendário.
8. Configurar tarefas agendadas.
9. Resumir instalação e pendências.

Se uma etapa depender de ação humana ou permissão externa, deixe o TODO nessa etapa até a
decisão ficar clara; não avance fingindo que a configuração foi validada.

## O que esta skill grava

- `config/brp.config.json` — dados da máquina (caminho da planilha, base das pastas, nome do
  calendário, caixa monitorada, filtro de remetente, caminho do SQLite e pasta de backup).
  Modelo em `config/brp.config.example.json`.
- `config/graph.env` — credenciais do Microsoft Graph + `BRP_MAILBOX` (contém **segredo**;
  protegido pelo `.gitignore`, nunca exibir o valor de volta nem comitar).

## Passo 0 — Pré-requisitos

Confirme (rode as checagens e relate o que faltar, com como resolver):

- **Python 3**: `python --version` (ou `python3`).
- **openpyxl**: `python -c "import openpyxl"` — se faltar, `pip install openpyxl`.
- **Acesso ao drive/servidor** onde ficam a planilha e as pastas (ex.: `G:`).
- **Acesso à pasta de backup** da rede AJM.
- **Cowork** instalado e logado, e **internet** disponível.

## Passo 1 — Conector Microsoft 365

A automação lê as citações por este conector. Verifique se ele está conectado tentando uma
busca simples (ex.: `outlook_email_search` por assunto "Processo nº"). 

- Se **não** estiver conectado, acione o card de conexão (sugira o conector Microsoft 365) e
  peça para a pessoa entrar **com a caixa que recebe as citações do BRP**. Lembre que as
  citações chegam nas caixas dos advogados — o ideal é uma **caixa compartilhada**
  (`citacoes-brp@…`) ou **acesso delegado** à caixa que recebe.
- Confirme com a pessoa **qual caixa** será monitorada e registre em `brp_mailbox` /
  `brp_sender_filter`.

## Passo 2 — Coletar os dados da instalação

Pergunte (uma coisa de cada vez, com o padrão atual como sugestão):

1. **Caminho da planilha** de controle (ex.: `G:\A.Digital\BRP\Defesas BRP.xlsx`).
2. **Caminho do SQLite local** (padrão `data\ajm-brp.sqlite3`; em produção, uma pasta local do Daniel).
3. **Pasta de backup** na rede AJM (ex.: `G:\A.Digital\BRP\Backups\sqlite`).
4. **Base das pastas** dos processos (padrão `G:\A.Digital\BRP`).
5. **Nome do calendário** (padrão `BRP`) e a **caixa do calendário** (`brp_mailbox`).
6. **Filtro de remetente** das citações (padrão `@brp.com.br`).
7. **Credenciais do Azure** (do app "Automacao BRP"): `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`,
   `GRAPH_CLIENT_SECRET`. Oriente a colar o **Valor** do segredo (não o ID). Não repita o
   segredo de volta na conversa.

Grave as respostas: paths/caixa/filtro em `config/brp.config.json`; credenciais + `BRP_MAILBOX`
em `config/graph.env`. Se um arquivo já existir, atualize só o que mudou e preserve o resto.

## Passo 3 — Verificação (dry-run)

Confirme que tudo conversa, sem efeitos colaterais permanentes:

1. **Leitura**: buscar pelo conector a citação mais recente do BRP e rodar `processar-citacao-brp`
   sobre ela — mostrar os campos extraídos.
2. **SQLite**: rodar `database-brp` com `init_db.py`; se houver planilha existente, importar com
   `importar_planilha.py`; depois inserir um processo de teste e registrar um e-mail de teste;
   confirmar `integrity_check = ok`.
3. **Backup**: rodar `backup-brp` uma vez e confirmar arquivo `.sqlite3` + `.sha256` na pasta da rede.
4. **Planilha manual**: rodar `registrar-planilha-brp` lendo o processo de teste do SQLite e
   escrevendo numa **cópia** da planilha (não na original); conferir que insere/atualiza sem
   duplicar.
5. **Pasta**: rodar `criar-pasta-processo` em modo `--simular` e mostrar o caminho.
6. **Calendário**: criar um **evento de teste** no calendário (via `agenda-brp`) e pedir para a
   pessoa conferir no Outlook; orientar a apagar depois. Use `--criar-calendario` se for a
   primeira vez.

Relate o resultado de cada item. Se algum falhar (token, 403, VPN, calendário), explique a causa
provável e o que ajustar — não dê a instalação por concluída.

## Passo 4 — Tarefa agendada (oferecer)

Pergunte se a pessoa quer ativar a execução automática **de hora em hora** da skill
`processar-citacao-brp`. Se sim, crie a tarefa agendada e lembre que a **máquina precisa ficar
ligada** com o Cowork aberto. Se preferir, deixe para ativar depois — a configuração já fica pronta.

Configure também uma tarefa diária para:

```bash
python skills/backup-brp/scripts/backup_sqlite.py
```

Use um horário em que a pasta de rede esteja montada.

## Encerramento

Mostre um resumo do que ficou configurado (sem o segredo) e os próximos passos. Lembre dos dois
pontos de segurança: **renovar o segredo** se ele tiver sido exposto, e aplicar a **Application
Access Policy** para o app só acessar a caixa do BRP (ver
`skills/agenda-brp/references/azure-app-registration.md`).
