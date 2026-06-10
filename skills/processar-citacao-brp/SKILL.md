---
name: processar-citacao-brp
description: >-
  Lê e interpreta um e-mail de citação do Banco BRP (encaminhado pela equipe da AJM
  Advogados) e extrai os dados estruturados do processo: número CNJ, parte contrária,
  tribunal/UF, comarca, link e chave de acesso aos autos, data de recebimento e
  audiência quando houver. Em seguida orquestra o registro no SQLite local, a criação
  da pasta do processo e o lançamento de audiência/prazo na agenda. Não escreve na
  planilha automaticamente; a planilha é atualizada manualmente por registrar-planilha-brp,
  lendo os dados do SQLite. Use esta
  skill SEMPRE que aparecer um e-mail de citação da carteira BRP — assuntos no formato
  "Processo nº ... - NOME DA PARTE", mensagens que dizem "recebemos hoje, via DJE, a
  citação", ou qualquer pedido para "triar", "dar entrada" ou "processar" uma citação
  nova da BRP, mesmo que a pessoa não cite a planilha ou a pasta explicitamente.
---

# Processar citação BRP

Esta skill é o **ponto de entrada** do fluxo de triagem da carteira BRP. O e-mail de
citação é um *gatilho*: ele avisa que chegou um processo novo, mas a maior parte do dado
útil está no **assunto** e no **texto livre** escrito pelo contato do Banco BRP. O seu
trabalho é ler esse e-mail como um advogado leria — entendendo o conteúdo, não casando
padrões rígidos — e transformá-lo numa linha estruturada que alimenta o resto do fluxo.

Por que "ler como advogado" e não com regex: os e-mails chegam encaminhados de formas
diferentes (o "ENC:" do Outlook, o "Fwd: ... Enviado do meu iPhone"), com pontuação e
quebras variando, e a audiência às vezes aparece numa frase solta no meio do texto. Um
padrão fixo quebra nessas variações; a leitura compreensiva, não.

## Acompanhamento por TODO

Antes de iniciar uma rodada, chame a ferramenta de TODO do Claude para criar uma lista visível
dos passos. Mantenha exatamente um item como `in_progress`, marque cada etapa concluída e deixe
claro qual é o próximo passo. Para uma rodada normal, use esta sequência:

1. Buscar e-mails candidatos.
2. Verificar idempotência no SQLite.
3. Extrair dados do e-mail novo.
4. Registrar processo e e-mail no SQLite.
5. Criar ou reutilizar pasta do processo.
6. Lançar audiência/prazo na agenda.
7. Gravar log de auditoria e resumir pendências.

Se alguma etapa for pulada por configuração da instalação, marque como concluída com a razão
no resumo, não deixe o TODO ambíguo.

## Origem dos e-mails (execução agendada)

Em produção esta skill **não recebe um arquivo** — ela é disparada por uma **tarefa agendada**
(de hora em hora) que monitora a caixa da AJM via o conector **Microsoft 365**
(`outlook_email_search`). O fluxo de cada execução:

1. Buscar na caixa monitorada os e-mails de citação **recebidos desde a última execução**.
   Filtro: remetente do **Banco BRP** — domínio `@brp.com.br` (o contato é
   `kristian@brp.com.br`, com cópia para silvana@/anaheloisa@/sergio@brp.com.br) — e assunto no
   padrão "Processo nº ...". Em testes, os e-mails podem chegar reencaminhados (de um Gmail ou
   de outro advogado); nesse caso o remetente do envelope muda, mas o cabeçalho original do BRP
   continua no corpo — use-o para confirmar e para a data de recebimento.
2. Para cada e-mail, consultar `database-brp`:
   `python skills/database-brp/scripts/verificar_email.py --message-id "<id do Graph>"`.
3. Se o e-mail já estiver em `emails_processados`, pular por idempotência.
4. Se for novo, extrair os dados (seção abaixo).
5. **Não duplicar processo**: `database-brp` usa `numero_processo` como chave única e
   preserva dados já preenchidos.
6. Ao final, registrar o e-mail em `emails_processados` com status `processado`, `ignorado`,
   `erro`, `duplicado` ou `sem_numero_processo`.
7. Marcar o e-mail como tratado (categoria/flag) quando possível, como reforço.
8. **Não escrever na planilha nesta rodada.** A planilha só é atualizada quando alguém invocar
   manualmente `registrar-planilha-brp`, que lê do SQLite e grava no `.xlsx`.

O conector Microsoft 365 disponível é de **leitura/busca**. Escrever no calendário exige um
componente complementar (MCP próprio sobre a Microsoft Graph) — ver skill `agenda-brp`.

## Como o e-mail é, na prática

- O remetente original é o contato do **Banco BRP** (ex.: "Kristian Olaf Olsen - Banco BRP"),
  que escreve para uma lista de advogados da AJM. Alguém da AJM **reencaminha** para a caixa
  monitorada.
- O **assunto** quase sempre traz: `Processo nº <NÚMERO CNJ> - <NOME DA PARTE>`.
- O **corpo** costuma dizer algo como *"Recebemos hoje, via DJE, a citação do processo em
  referência."* e, **quando há**, acrescenta:
  - data e hora de **audiência** ("Foi designada audiência para o dia DD/MM/AAAA, às HH:MMh");
  - **link** de acesso aos autos e **chave do processo** (sistemas eproc);
  - instruções (ex.: audiência por Microsoft Teams).
- Os **anexos** normalmente são só a assinatura/logo do BRP — **a petição inicial não vem
  anexada**. Não conte com ela aqui.

## Campos a extrair

Produza um registro com estes campos (use exatamente estes nomes):

- `numero_processo` — número CNJ completo, do assunto.
- `parte_contraria` — nome da parte autora, do assunto (quem acionou o BRP).
- `tribunal_uf` — derive do número CNJ. Veja `assets/tribunais-cnj.md`.
- `link_autos` — URL de acesso, se o corpo trouxer; senão vazio.
- `chave` — chave do processo, se o corpo trouxer; senão vazio.
- `data_recebimento` — ver a regra crítica abaixo.
- `audiencia` — data/hora se o corpo informar; `verificar autos` se não informar; `não` só
  se o e-mail afirmar que não há audiência.
- `audiencia_obs` — detalhes úteis (ex.: "telepresencial via Microsoft Teams").
- `prazo_defesa` — quase nunca vem no e-mail → deixe `verificar autos`. **Não calcule à mão
  aqui**: o `agenda-brp` calcula sozinho um prazo *provisório*
  (`data_recebimento + 13 dias úteis`) — por isso a `data_recebimento` correta é tão crítica.
- `fonte_prazo` — `E-mail`, `Autos` ou `Provisório` (ver `assets/schema-planilha.md`).

### Regra crítica: data de recebimento

A `data_recebimento` é a data do **e-mail ORIGINAL do BRP**, não a data em que alguém
reencaminhou. Quando alguém da AJM encaminha dias depois, a data do topo da mensagem é a do
encaminhamento — ignore-a. Procure no corpo o cabeçalho do e-mail original ("Enviado:" /
"Data:") e a frase "Recebemos hoje, via DJE, a citação": a data desse envio original é a que
vale, porque é dela que corre o prazo. Errar aqui contamina o cálculo de prazo lá na frente.

### Princípio: nunca inventar

Se um dado não está no e-mail, o campo recebe `verificar autos` (ou fica vazio) — **nunca**
um valor estimado disfarçado de certo. Um campo honestamente vazio é seguro; um prazo errado
faz o escritório perder uma defesa. Prazo de defesa e audiência muitas vezes só existem nos
autos, e a integração com os tribunais está fora do escopo desta fase.

## Saída

Apresente o registro extraído de forma legível (tabela ou lista de `campo: valor`) e confirme
com a pessoa antes de disparar as ações — especialmente quando `audiencia` ou `prazo_defesa`
ficarem como `verificar autos`, para que a triagem humana saiba que precisa abrir os autos.

## Orquestração (próximos passos)

Depois de extrair e confirmar, encadeie as skills de ação:

1. `database-brp` — grava/atualiza o processo em `processos` e registra o e-mail em
   `emails_processados`.
2. `criar-pasta-processo` — cria a pasta no padrão do escritório
   (`assets/nomenclatura-pastas.md`) e devolve o caminho.
3. `agenda-brp` — lança na agenda BRP **até dois eventos**: a audiência (somente quando há
   data/hora confirmada — sem data, nenhum evento) e o **prazo de defesa**, cuja data é
   **calculada** (`data_recebimento + 13 dias úteis`, sáb/dom pulados, feriados ignorados) e
   entra como prazo **provisório** a confirmar nos autos.

Não chame `registrar-planilha-brp` durante o intake. Quando a equipe pedir para atualizar a
planilha, chame `registrar-planilha-brp`; ela deve ler o SQLite e escrever no `.xlsx` de forma
manual e controlada.

Se alguma ação não puder rodar (sem acesso ao servidor, à agenda etc.), registre o que
conseguiu e sinalize claramente o que ficou pendente, em vez de falhar em silêncio.

## Log de auditoria (obrigatório a cada e-mail)

Para que dê para **depurar no futuro** (ex.: "por que a automação não criou a pasta de X?"),
toda execução grava um log com os **dados completos**. Logo após processar cada e-mail —
mesmo quando o resultado for "pulado (duplicado)" ou houve falha numa ação — chame:

```
python scripts/registrar_log.py --registro '<json>'
```

O `<json>` deve juntar **três blocos**, para o log ser autoexplicativo:

- `email` — o e-mail **bruto**: `assunto`, `remetente`, `recebido_em`, `message_id` e um
  trecho (ou a íntegra) do `corpo`. É o que permite reconferir a extração depois.
- `extraido` — **todos** os campos extraídos (os da seção "Campos a extrair"), exatamente
  como foram para o SQLite.
- `acoes` — o que cada skill devolveu: `database` (processo/e-mail inserido/atualizado/pulado),
  `pasta` (caminho criado/reutilizado)
  e `agenda` (eventos lançados); e `observacoes` com
  qualquer pendência (ex.: "sem VPN, pasta não criada").

Onde grava: pasta **`LOGS/` na raiz do projeto** (sobreponível por `--logs-dir` ou pela
variável `BRP_LOGS_DIR`). Um arquivo por rodada — `AAAAMMDDThh-execucao.jsonl` — com **uma
linha JSON por e-mail**, então a rodada inteira (vários e-mails) fica no mesmo arquivo. O
script cria a pasta sozinho e só acrescenta um carimbo de tempo; **não inventa** nada.

O log é **best-effort**: se a gravação falhar, registre o aviso e siga — nunca deixe o log
travar a triagem. Mas trate a sua ausência como bug: o objetivo é que **toda** citação
processada deixe rastro.

## Exemplos reais (carteira BRP)

**Exemplo 1 — só número + parte (TJMA)**
Assunto: `Processo nº 0800680-38.2026.8.10.0049 - ALEXANDRE GLEISON SOUSA ANDRADE`
Corpo: "Recebemos hoje, via DJE, a citação..." (enviado em 27/05/2026). Sem link, sem chave,
sem audiência.
Extração:
- numero_processo: `0800680-38.2026.8.10.0049`
- parte_contraria: `ALEXANDRE GLEISON SOUSA ANDRADE`
- tribunal_uf: `TJMA / MA`  (J=8, TR=10)
- link_autos: — · chave: —
- data_recebimento: `27/05/2026`
- audiencia: `verificar autos` · prazo_defesa: `verificar autos` · fonte_prazo: —

**Exemplo 2 — com link e chave (TJSP / eproc)**
Assunto: `Processo nº 4002793-68.2026.8.26.0344 - VALTER JOSE CONEGLIAN`
Corpo: traz o link `eproc-consulta.tjsp.jus.br/...` e "a chave do processo 596492142726".
Extração:
- numero_processo: `4002793-68.2026.8.26.0344`
- parte_contraria: `VALTER JOSE CONEGLIAN`
- tribunal_uf: `TJSP / SP`  (J=8, TR=26)
- link_autos: `https://eproc-consulta.tjsp.jus.br/consulta_1g/...num_processo=40027936820268260344`
- chave: `596492142726`
- data_recebimento: `27/05/2026`
- audiencia: `verificar autos` · prazo_defesa: `verificar autos`

**Exemplo 3 — com audiência no corpo (TJPA, telepresencial)**
Assunto: `Processo nº 0854280-80.2026.8.14.0301 - FELIX NUNES DE ALMEIDA NETO`
Corpo: "Foi designada audiência para o dia 30/09/2026, às 9:30h" + instrução de audiência por
Microsoft Teams. Encaminhado pelo iPhone em 01/06, mas o e-mail original do BRP é de 27/05.
Extração:
- numero_processo: `0854280-80.2026.8.14.0301`
- parte_contraria: `FELIX NUNES DE ALMEIDA NETO`
- tribunal_uf: `TJPA / PA`  (J=8, TR=14)
- link_autos: — · chave: —
- data_recebimento: `27/05/2026`  ← data do e-mail original, NÃO a do encaminhamento (01/06)
- audiencia: `30/09/2026 09:30` · audiencia_obs: `telepresencial via Microsoft Teams (solicitar até o dia anterior)`
- prazo_defesa: `verificar autos` · fonte_prazo: `E-mail` (para a audiência)
