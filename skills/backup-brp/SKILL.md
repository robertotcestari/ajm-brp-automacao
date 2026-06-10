---
name: backup-brp
description: >-
  Faz backup validado do SQLite local da automação BRP para a pasta de rede da AJM.
  Use para backup manual, configuração do backup diário no computador do Daniel e
  auditoria dos arquivos gerados.
---

# Backup BRP

Esta skill protege o SQLite local da automação BRP. O banco fica no computador do Daniel;
a pasta da rede da AJM recebe uma cópia diária validada.

## Configuração

Defina em `config/brp.config.json`:

```json
{
  "sqlite_path": "C:\\AJM\\BRP\\data\\ajm-brp.sqlite3",
  "backup_dir": "G:\\A.Digital\\BRP\\Backups\\sqlite",
  "backup_retention_days": 90
}
```

Use o caminho real da pasta de rede no computador do Daniel. Se a unidade `G:` depender de
VPN ou mapeamento manual, o backup diário deve rodar em um horário em que essa pasta esteja
montada.

## Backup manual

```bash
python skills/backup-brp/scripts/backup_sqlite.py
```

O script:

- valida o banco origem com `PRAGMA integrity_check`;
- cria a cópia usando a API de backup do SQLite, evitando cópia inconsistente;
- valida o arquivo copiado;
- grava `.sha256` ao lado do backup;
- registra o backup na tabela `backups_sqlite`;
- remove backups antigos conforme `backup_retention_days`.

## Nome dos arquivos

Padrão:

```text
ajm-brp-sqlite-YYYYMMDD-HHMMSS.sqlite3
ajm-brp-sqlite-YYYYMMDD-HHMMSS.sqlite3.sha256
```

## Backup diário

No Windows, configurar pelo Agendador de Tarefas:

- Programa: `python`
- Argumentos: `skills/backup-brp/scripts/backup_sqlite.py`
- Iniciar em: pasta raiz do plugin `ajm-brp-automacao`
- Horário sugerido: fim do expediente, depois da triagem do dia.

Depois de configurar, rode manualmente uma vez e confirme:

- `integrity_check = ok`;
- arquivo `.sqlite3` criado na pasta da rede;
- arquivo `.sha256` criado ao lado;
- tamanho do arquivo maior que zero.
