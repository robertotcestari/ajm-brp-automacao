# Plugin: ajm-brp-automacao

Automação do fluxo jurídico da carteira **BRP** da **AJM Advogados**.

Empacota um conjunto de *skills* (instruções em linguagem natural que o Claude executa)
mais *assets* compartilhados, de forma que a equipe da AJM possa **manter e estender** a
automação editando arquivos `.md` — sem precisar mexer em código.

## Fluxo automatizado (Fase 1)

1. Chega um e-mail de **citação** do Banco BRP em uma caixa da AJM.
2. A skill `processar-citacao-brp` **lê e interpreta** o e-mail e extrai os dados estruturados.
3. As skills de ação registram o caso na **planilha**, criam a **pasta** do processo e lançam
   **audiência** e **prazo** na **agenda** com cores diferenciadas.

A elaboração assistida de defesas (Fase 2) fica na skill `gerar-defesa-brp`.

## Estrutura

```
ajm-brp-automacao/
├── .claude-plugin/plugin.json     # manifesto do plugin
├── skills/
│   ├── configurar-brp/            # assistente de instalação/configuração da máquina
│   ├── processar-citacao-brp/     # intake: lê o e-mail, extrai dados, orquestra
│   ├── registrar-planilha-brp/    # grava a linha na planilha de controle
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
- **Planilha de controle:** arquivo `.xlsx` no padrão definido em `assets/schema-planilha.md`.

## Status

Em desenvolvimento — Fase 1 em construção. Veja cada `SKILL.md` para o estado atual.
