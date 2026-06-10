---
name: database-brp
description: >-
  Inicializa, consulta e atualiza o SQLite local da automação BRP da AJM.
  Use para criar o banco no computador do Daniel, registrar processos, registrar
  e-mails já processados e checar idempotência antes de reprocessar mensagens.
---

# Database BRP

Esta skill mantém a memória local da automação BRP em SQLite. A partir da v0.3, o banco
local passa a ser o registro operacional principal; a planilha pode continuar existindo
como exportação/compatibilidade, mas o intake deve consultar o SQLite antes de agir.

## Acompanhamento por TODO

Quando a operação envolver mais de uma ação (instalar, migrar planilha, registrar processo e
e-mail, ou auditar duplicidade), chame a ferramenta de TODO do Claude antes de rodar os scripts.
Mantenha exatamente um item como `in_progress` e atualize a lista a cada script concluído.

Para instalação/migração, use:

1. Confirmar caminho do SQLite.
2. Inicializar ou migrar schema.
3. Importar planilha existente, se houver.
4. Registrar processo de teste.
5. Registrar e verificar e-mail de teste.
6. Confirmar `PRAGMA integrity_check`.

Para uma consulta rápida de idempotência, não precisa abrir TODO se houver apenas um comando.

## Arquivo do banco

O caminho padrão é `data/ajm-brp.sqlite3` dentro do plugin. Em produção, no computador do
Daniel, prefira configurar `sqlite_path` em `config/brp.config.json`.

Exemplo:

```json
{
  "sqlite_path": "C:\\AJM\\BRP\\data\\ajm-brp.sqlite3"
}
```

## Inicializar

Rode uma vez durante a instalação e sempre que houver atualização de schema:

```bash
python skills/database-brp/scripts/init_db.py
```

O script cria/migra o banco e valida `PRAGMA integrity_check`.

## Registrar processo

Use o mesmo JSON produzido por `processar-citacao-brp`:

```bash
python skills/database-brp/scripts/upsert_processo.py --registro '<json>'
```

Regras:

- `numero_processo` é chave única.
- Se o processo não existir, insere com padrões (`Novo`, `Pendente`, `Não iniciada`).
- Se já existir, preenche somente campos vazios, preservando edições humanas.
- A exceção é `prazo_defesa = verificar autos`, que pode ser promovido para uma data real.

## Importar planilha existente

Para migrar a planilha atual para SQLite:

```bash
python skills/database-brp/scripts/importar_planilha.py --planilha "<caminho.xlsx>"
```

O importador reconhece os cabeçalhos atuais da AJM, faz upsert por `numero_processo` e pula
linhas sem número de processo.

## Registrar e-mail processado

Depois de processar ou decidir ignorar uma mensagem, registre:

```bash
python skills/database-brp/scripts/registrar_email.py --registro '<json>'
```

Campos esperados:

```json
{
  "message_id": "...",
  "internet_message_id": "...",
  "assunto": "...",
  "remetente": "...",
  "destinatarios": "...",
  "recebido_em": "...",
  "numero_processo": "...",
  "status": "processado",
  "raw_ref": "graph://...",
  "payload_json": {}
}
```

Status recomendados: `processado`, `ignorado`, `erro`, `duplicado`, `sem_numero_processo`.

## Checar idempotência

Antes de processar um e-mail:

```bash
python skills/database-brp/scripts/verificar_email.py --message-id "<id do Graph>"
```

Se `processado = true`, não processe de novo; registre no resumo da execução que o e-mail
foi pulado por idempotência.
