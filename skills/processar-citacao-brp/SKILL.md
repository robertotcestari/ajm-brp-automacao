---
name: processar-citacao-brp
description: >-
  Lê e interpreta apenas o e-mail ORIGINAL de citação do Banco BRP e extrai os dados
  estruturados do processo: número CNJ, parte contrária, tribunal/UF, comarca, link e chave de
  acesso aos autos, data de recebimento e audiência quando houver. Respostas, encaminhamentos e
  mensagens derivadas do e-mail original devem ser ignoradas. Em seguida orquestra o registro no
  SQLite local, a atualização da planilha exclusiva do Claude, a criação da pasta do processo e o
  lançamento de audiência/prazo na agenda. A planilha original da AJM não é tocada. Use esta
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

Regra crítica: **processe só o e-mail original da BRP**. Respostas (`Re:`, `RES:`),
encaminhamentos (`Fwd:`, `FW:`, `ENC:`) e qualquer mensagem com cabeçalhos
`In-Reply-To`/`References` não devem gerar novo processo, nova planilha, nova pasta ou novo
evento. Elas podem citar o mesmo processo, mas são conversa derivada; se o original já entrou,
não há novo intake.

## Acompanhamento por TODO

Antes de iniciar uma rodada, chame a ferramenta de TODO do Claude para criar uma lista visível
dos passos. Mantenha exatamente um item como `in_progress`, marque cada etapa concluída e deixe
claro qual é o próximo passo. Para uma rodada normal, use esta sequência:

1. Buscar e-mails candidatos.
2. Separar e-mails originais de respostas/encaminhamentos.
3. Verificar idempotência no SQLite.
4. Extrair dados do e-mail original novo.
5. Registrar processo e e-mail no SQLite.
6. Registrar/atualizar a planilha exclusiva do Claude.
7. Criar ou reutilizar pasta do processo.
8. Lançar audiência/prazo na agenda.
9. Gravar log de auditoria e resumir pendências.

Se alguma etapa for pulada por configuração da instalação, marque como concluída com a razão
no resumo, não deixe o TODO ambíguo.

## Origem dos e-mails (execução agendada)

Em produção esta skill **não recebe um arquivo** — ela é disparada por uma **tarefa agendada**
(de hora em hora) que monitora a caixa da AJM via o conector **Microsoft 365**
(`outlook_email_search`). O fluxo de cada execução:

1. Buscar na caixa monitorada os e-mails de citação **recebidos desde a última execução**.
   Filtro primário: remetente do **Banco BRP** — domínio `@brp.com.br` (o contato é
   `kristian@brp.com.br`, com cópia para silvana@/anaheloisa@/sergio@brp.com.br) — e assunto no
   padrão "Processo nº ...".
2. Antes de extrair dados, classificar a mensagem:
   - **Original processável:** mensagem enviada pelo domínio `@brp.com.br`, assunto de citação
     sem prefixo de resposta/encaminhamento, e sem cabeçalhos `In-Reply-To`/`References`.
   - **Resposta/derivada:** qualquer mensagem com prefixo `Re:`, `RES:`, `Fwd:`, `FW:`, `ENC:`,
     ou cabeçalhos `In-Reply-To`/`References`.
   - **Encaminhamento:** envelope de outro remetente com corpo contendo o e-mail original da BRP.
     Não processe como novo intake. Registre como `ignorado` se for útil para auditoria.
3. Para cada mensagem original, consultar `database-brp` com todos os identificadores disponíveis:
   `python skills/database-brp/scripts/verificar_email.py --message-id "<id do Graph>" --internet-message-id "<Message-ID>"`.
   Para respostas, passe também cada id de `References`/`In-Reply-To` como
   `--reference-message-id "<Message-ID referenciado>"`.
4. Se a própria mensagem ou qualquer referência dela já estiver em `emails_processados`, pular
   por idempotência. Isso evita reprocessar uma resposta de advogado ao e-mail original da BRP.
5. Se a mensagem for resposta/encaminhamento/derivada, **não extraia dados do processo** e não
   acione nenhuma etapa de processo, planilha, pasta ou agenda. Registre apenas o e-mail como
   `ignorado` em `emails_processados`, com `raw_ref` apontando para o motivo (`resposta`,
   `encaminhamento`, `referencia_original_processada`, etc.).
6. Se for e-mail original novo, extrair os dados (seção abaixo).
7. **Não duplicar processo**: `database-brp` usa `numero_processo` como chave única e
   preserva dados já preenchidos.
8. Após gravar o processo no SQLite, chamar `registrar-planilha-brp` para atualizar a planilha
   exclusiva do Claude a partir do SQLite. Use o escopo do processo atual:
   `python skills/registrar-planilha-brp/scripts/registrar_do_sqlite.py --numero "<CNJ>"`.
   Não use a planilha original da AJM como destino.
9. Ao final, registrar o e-mail original em `emails_processados` com status `processado`,
   `ignorado`, `erro`, `duplicado` ou `sem_numero_processo`.
10. Marcar o e-mail como tratado (categoria/flag) quando possível, como reforço.

O conector Microsoft 365 disponível é de **leitura/busca**. Escrever no calendário exige um
componente complementar (MCP próprio sobre a Microsoft Graph) — ver skill `agenda-brp`.

## Como o e-mail é, na prática

- O remetente original é o contato do **Banco BRP** (ex.: "Kristian Olaf Olsen - Banco BRP"),
  que escreve para uma lista de advogados da AJM.
- O **assunto** quase sempre traz: `Processo nº <NÚMERO CNJ> - <NOME DA PARTE>`.
- O **corpo** costuma dizer algo como *"Recebemos hoje, via DJE, a citação do processo em
  referência."* e, **quando há**, acrescenta:
  - data e hora de **audiência** ("Foi designada audiência para o dia DD/MM/AAAA, às HH:MMh");
  - **link** de acesso aos autos e **chave do processo** (sistemas eproc);
  - instruções (ex.: audiência por Microsoft Teams).
- Os **anexos** normalmente são só a assinatura/logo do BRP — **a petição inicial não vem
  anexada**. Não conte com ela aqui.

## O que não processar

Não processe como citação nova:

- respostas de advogados, do BRP ou de terceiros ao e-mail original;
- encaminhamentos do e-mail original para outra pessoa/caixa;
- mensagens com assunto começando por `Re:`, `RES:`, `Fwd:`, `FW:` ou `ENC:`;
- mensagens com cabeçalhos `In-Reply-To` ou `References`;
- qualquer e-mail cujo `References`/`In-Reply-To` aponte para um `internet_message_id` já
  gravado em `emails_processados`.

Para esses casos, o output deve ser um resumo curto: `ignorado`, motivo, `message_id`,
`internet_message_id` e, se houver, o `message_id` original referenciado. Não crie/atualize
processo, planilha, pasta ou agenda.

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

A `data_recebimento` é a data do **e-mail original do BRP**. Como respostas e encaminhamentos
não são processados, não use datas de mensagens derivadas. A frase "Recebemos hoje, via DJE, a
citação" se refere à data desse envio original; errar aqui contamina o cálculo de prazo lá na
frente.

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
2. `registrar-planilha-brp` — lê o processo do SQLite e registra/atualiza a planilha exclusiva
   do Claude (`planilha_claude_path`). Nunca escreva na planilha original da AJM.
3. `criar-pasta-processo` — cria a pasta no padrão do escritório
   (`assets/nomenclatura-pastas.md`) e devolve o caminho.
4. `agenda-brp` — lança na agenda BRP **até dois eventos**: a audiência (somente quando há
   data/hora confirmada — sem data, nenhum evento) e o **prazo de defesa**, cuja data é
   **calculada** (`data_recebimento + 13 dias úteis`, sáb/dom pulados, feriados ignorados) e
   entra como prazo **provisório** a confirmar nos autos.

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
  trecho (ou a íntegra) do `corpo`; inclua também `internet_message_id`, `in_reply_to` e
  `references` quando disponíveis. É o que permite reconferir a extração depois.
- `extraido` — **todos** os campos extraídos (os da seção "Campos a extrair"), exatamente
  como foram para o SQLite.
- `acoes` — o que cada skill devolveu: `database` (processo/e-mail inserido/atualizado/pulado),
  `planilha_claude` (inserido/atualizado/sem alteração), `pasta` (caminho criado/reutilizado)
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
Microsoft Teams. O e-mail original do BRP é de 27/05.
Extração:
- numero_processo: `0854280-80.2026.8.14.0301`
- parte_contraria: `FELIX NUNES DE ALMEIDA NETO`
- tribunal_uf: `TJPA / PA`  (J=8, TR=14)
- link_autos: — · chave: —
- data_recebimento: `27/05/2026`  ← data do e-mail original
- audiencia: `30/09/2026 09:30` · audiencia_obs: `telepresencial via Microsoft Teams (solicitar até o dia anterior)`
- prazo_defesa: `verificar autos` · fonte_prazo: `E-mail` (para a audiência)
