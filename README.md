# Plugin: ajm-brp-automacao

Automação do fluxo jurídico da carteira **BRP** da **AJM Advogados**.

Empacota um conjunto de *skills* (instruções em linguagem natural que o Claude executa)
mais *assets* compartilhados, de forma que a equipe da AJM possa **manter e estender** a
automação editando arquivos `.md` — sem precisar mexer em código.

## Fluxo automatizado (Fase 1)

1. Chega um e-mail de **citação** do Banco BRP em uma caixa da AJM.
2. A skill `processar-citacao-brp` confere o **SQLite local** para não reprocessar e-mails.
3. A skill `processar-citacao-brp` **lê e interpreta** o e-mail e extrai os dados estruturados.
4. As skills de ação registram o caso no **SQLite**, criam a **pasta** do processo e lançam
   **audiência** e **prazo** na **agenda** com cores diferenciadas.
5. A skill `backup-brp` faz backup validado do SQLite para a pasta de rede da AJM.
6. A planilha `.xlsx` só é escrita quando alguém invoca manualmente `registrar-planilha-brp`,
   que lê o SQLite e aplica o mesmo processo de dedup/atualização controlada.

A elaboração assistida de defesas (Fase 2) fica na skill `gerar-defesa-brp`.

## Estrutura

```
ajm-brp-automacao/
├── .claude-plugin/plugin.json     # manifesto do plugin
├── skills/
│   ├── configurar-brp/            # assistente de instalação/configuração da máquina
│   ├── processar-citacao-brp/     # intake: lê o e-mail, extrai dados, orquestra
│   ├── database-brp/              # SQLite local: processos, e-mails processados e logs
│   ├── backup-brp/                # backup diário validado do SQLite para a rede AJM
│   ├── registrar-planilha-brp/    # manual: lê SQLite e registra na planilha
│   ├── criar-pasta-processo/      # cria a pasta no padrão do escritório
│   ├── agenda-brp/                # lança audiência (vermelho) e prazo (amarelo)
│   └── gerar-defesa-brp/          # Fase 2: rascunho de defesa
├── assets/
│   ├── tribunais-cnj.md           # mapa código CNJ → tribunal / UF / sistema
│   ├── nomenclatura-pastas.md     # padrão de nome das pastas (a confirmar com a AJM)
│   ├── schema-planilha.md         # colunas e vocabulário de status da planilha
│   └── teses/                     # base de teses (Fase 2)
```

## Pré-requisitos de integração

- **E-mail e agenda:** caixa Exchange Online (Microsoft 365) da AJM via Microsoft Graph.
- **Pasta dos processos:** acesso ao servidor/VPN onde ficam as pastas.
- **Banco local:** SQLite em `data/ajm-brp.sqlite3` ou no caminho definido em `config/brp.config.json`.
- **Backup:** pasta de rede da AJM acessível pela máquina do Daniel.
- **Planilha de controle:** escrita manual invocada a partir do SQLite, no padrão definido em `assets/schema-planilha.md`.

## Status

Em desenvolvimento — v0.3 adiciona SQLite local e backup diário. Veja cada `SKILL.md` para o estado atual.
