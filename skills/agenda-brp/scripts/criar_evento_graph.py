#!/usr/bin/env python3
"""
Cria um evento no calendário "BRP" (Exchange Online) via Microsoft Graph.

Tipos:
- audiencia : evento com hora, categoria "Audiência BRP" (vermelho). SÓ é criado com
              data/hora real — sem isso o script recusa (não usa o dia da execução).
- prazo     : evento de dia inteiro, categoria "Prazo BRP" (amarelo). A data pode vir pronta
              em --inicio OU ser calculada de --recebimento (+13 dias úteis, sáb/dom pulados,
              feriados ignorados); nesse caso o evento é marcado como PROVISÓRIO.
- verificar : evento de dia inteiro "Verificar prazo nos autos", categoria "Verificar BRP"
              (laranja). Fallback raro: só quando nem a data de recebimento é conhecida.

Autenticação: client credentials (app registration). Variáveis de ambiente:
  GRAPH_TENANT_ID, GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET, BRP_MAILBOX

Use --simular para ver o que seria criado SEM chamar a rede (útil antes do registro de app).
Só usa biblioteca padrão (urllib) — não precisa instalar nada.

Uso:
  python criar_evento_graph.py --tipo audiencia --numero "..." --parte "..." \
      --inicio "2026-09-30T09:30:00" --obs "telepresencial via Teams"
  python criar_evento_graph.py --tipo prazo --numero "..." --parte "..." --recebimento "27/05/2026"
  python criar_evento_graph.py --tipo prazo --numero "..." --parte "..." --inicio "2026-06-15"
  python criar_evento_graph.py --tipo verificar --numero "..." --parte "..." --inicio "2026-06-02"
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# Cálculo de prazo compartilhado (lib/ na raiz do plugin)
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import datas  # noqa: E402

TZ = "E. South America Standard Time"  # horário de Brasília (ajuste se necessário)
GRAPH = "https://graph.microsoft.com/v1.0"

# Propriedade estendida usada como "carimbo" de idempotência no próprio evento.
# Guardamos uma chave estável (tipo+processo) para reencontrar o evento em execuções
# futuras e atualizá-lo em vez de criar uma cópia. O GUID é fixo e arbitrário (namespace
# da automação BRP); não mude depois de eventos já terem sido gravados com ele.
BRP_PROP_GUID = "6F3B1A2C-9D4E-4B7A-8C1F-0A2B3C4D5E6F"
BRP_PROP_NAME = "brpKey"
BRP_PROP_ID = f"String {{{BRP_PROP_GUID}}} Name {BRP_PROP_NAME}"

# nome da categoria -> cor pré-definida do Outlook (preset0=vermelho, preset3=amarelo,
# preset1=laranja). Ajuste se a AJM preferir outra convenção.
CATEGORIAS = {
    "audiencia": ("Audiência BRP", "preset0"),
    "prazo": ("Prazo BRP", "preset3"),
    "verificar": ("Verificar BRP", "preset1"),
}


def http(method, url, token=None, body=None, form=False):
    data, headers = None, {}
    if body is not None:
        if form:
            data = urllib.parse.urlencode(body).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            txt = r.read().decode()
            return json.loads(txt) if txt else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"Erro Graph {e.code} em {method} {url}: {e.read().decode()[:500]}")


def get_token():
    tenant = os.environ["GRAPH_TENANT_ID"]
    res = http("POST",
               f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
               body={
                   "client_id": os.environ["GRAPH_CLIENT_ID"],
                   "client_secret": os.environ["GRAPH_CLIENT_SECRET"],
                   "scope": "https://graph.microsoft.com/.default",
                   "grant_type": "client_credentials",
               }, form=True)
    return res["access_token"]


def garante_categoria(token, mailbox, nome, cor):
    existentes = http("GET", f"{GRAPH}/users/{mailbox}/outlook/masterCategories", token).get("value", [])
    if not any(c.get("displayName") == nome for c in existentes):
        http("POST", f"{GRAPH}/users/{mailbox}/outlook/masterCategories", token,
             body={"displayName": nome, "color": cor})


def acha_calendario(token, mailbox, nome, criar=False):
    cals = http("GET", f"{GRAPH}/users/{mailbox}/calendars?$select=id,name", token).get("value", [])
    for c in cals:
        if c.get("name") == nome:
            return c["id"]
    if criar:
        novo = http("POST", f"{GRAPH}/users/{mailbox}/calendars", token, body={"name": nome})
        return novo["id"]
    sys.exit(f"Calendário '{nome}' não encontrado na caixa {mailbox}. "
             "Rode uma vez com --criar-calendario para criá-lo, ou ajuste --calendario.")


def chave_idempotencia(tipo, numero):
    """Chave estável por processo+tipo: um processo tem no máximo uma audiência,
    um prazo e uma tarefa de verificação. A data NÃO entra na chave de propósito —
    se a audiência for remarcada, o evento existente é atualizado em vez de duplicado."""
    return f"{tipo}|{numero}"


def monta_evento(tipo, numero, parte, inicio, duracao_min, obs):
    nome_cat = CATEGORIAS[tipo][0]
    carimbo = [{"id": BRP_PROP_ID, "value": chave_idempotencia(tipo, numero)}]
    if tipo == "audiencia":
        ini = datetime.fromisoformat(inicio)
        fim = ini + timedelta(minutes=duracao_min)
        return {
            "subject": f"Audiência — {parte} ({numero})",
            "body": {"contentType": "text", "content": obs or f"Processo {numero}"},
            "start": {"dateTime": ini.isoformat(), "timeZone": TZ},
            "end": {"dateTime": fim.isoformat(), "timeZone": TZ},
            "categories": [nome_cat],
            "singleValueExtendedProperties": carimbo,
        }
    # prazo / verificar: dia inteiro
    dia = datetime.fromisoformat(inicio).date()
    assunto = (f"Prazo de defesa — {parte} ({numero})" if tipo == "prazo"
               else f"Verificar prazo nos autos — {numero}")
    return {
        "subject": assunto,
        "body": {"contentType": "text", "content": obs or f"Processo {numero} — {parte}"},
        "isAllDay": True,
        "start": {"dateTime": f"{dia}T00:00:00", "timeZone": TZ},
        "end": {"dateTime": f"{dia + timedelta(days=1)}T00:00:00", "timeZone": TZ},
        "categories": [nome_cat],
        "singleValueExtendedProperties": carimbo,
    }


# Prefixos de assunto por tipo — usados para reconhecer eventos legados (criados
# antes do carimbo de idempotência) e casá-los pelo número CNJ presente no assunto.
PREFIXO_ASSUNTO = {
    "audiencia": "Audiência",
    "prazo": "Prazo de defesa",
    "verificar": "Verificar prazo",
}

# Snapshot de (id, subject) por calendário, lido uma vez por execução para não
# baixar a lista inteira a cada processo no modo lote.
_SNAPSHOT = {}


def snapshot_eventos(token, mailbox, cal_id, refresca=False):
    if refresca or cal_id not in _SNAPSHOT:
        eventos = []
        url = (f"{GRAPH}/users/{mailbox}/calendars/{cal_id}/events"
               f"?$select=id,subject&$top=100")
        while url:
            r = http("GET", url, token)
            eventos.extend(r.get("value", []))
            url = r.get("@odata.nextLink")
        _SNAPSHOT[cal_id] = eventos
    return _SNAPSHOT[cal_id]


def eventos_correspondentes(token, mailbox, cal_id, tipo, numero):
    """Todas as cópias deste compromisso já no calendário (carimbadas ou legadas).
    Casa pelo número CNJ no assunto + prefixo do tipo — o CNJ é único por processo."""
    prefixo = PREFIXO_ASSUNTO[tipo]
    return [e["id"] for e in snapshot_eventos(token, mailbox, cal_id)
            if numero in e.get("subject", "") and e.get("subject", "").startswith(prefixo)]


def upsert_evento(token, mailbox, cal_id, tipo, numero, evento):
    """Idempotente: se não houver cópia, cria; se houver, atualiza uma e apaga as
    sobrando (consolida duplicatas de execuções anteriores). O corpo já carrega o
    carimbo brpKey, então o evento mantido fica marcado para as próximas rodadas.
    Devolve (acao, id): 'criado', 'atualizado' ou 'consolidado'."""
    existentes = eventos_correspondentes(token, mailbox, cal_id, tipo, numero)
    if not existentes:
        criado = http("POST", f"{GRAPH}/users/{mailbox}/calendars/{cal_id}/events",
                      token, body=evento)
        _SNAPSHOT.setdefault(cal_id, []).append(
            {"id": criado.get("id"), "subject": evento["subject"]})
        return "criado", criado.get("id")

    alvo = existentes[0]
    http("PATCH", f"{GRAPH}/users/{mailbox}/calendars/{cal_id}/events/{alvo}",
         token, body=evento)
    for extra in existentes[1:]:
        http("DELETE", f"{GRAPH}/users/{mailbox}/calendars/{cal_id}/events/{extra}",
             token)
    # Mantém o snapshot coerente: remove os apagados da lista em memória.
    if len(existentes) > 1:
        apagados = set(existentes[1:])
        _SNAPSHOT[cal_id] = [e for e in _SNAPSHOT[cal_id] if e["id"] not in apagados]
    return ("atualizado" if len(existentes) == 1 else "consolidado"), alvo


def resolve_inicio_obs(args):
    """Valida/resolve a data de início e a observação conforme o tipo. Encerra com
    mensagem clara quando faltar dado — NUNCA inventa uma data (ex.: cair para hoje)."""
    obs = args.obs
    if args.tipo == "audiencia":
        # Audiência só entra na agenda com data E hora confirmadas. Sem isso, não há
        # evento — não usar o dia da execução como placeholder.
        if not args.inicio:
            sys.exit("Audiência sem data/hora: não crie evento. "
                     "Só lance audiência quando a data/hora estiver confirmada.")
        try:
            dt = datetime.fromisoformat(args.inicio)
        except ValueError:
            sys.exit(f"--inicio inválido para audiência: {args.inicio!r}. "
                     "Esperado data-hora ISO (ex.: 2026-09-30T09:30:00).")
        if dt.hour == 0 and dt.minute == 0 and "T" not in args.inicio and " " not in args.inicio:
            sys.exit("Audiência exige hora confirmada (não apenas a data). "
                     "Sem hora, não crie o evento.")
        return args.inicio, obs

    if args.tipo == "prazo":
        # Prazo: usa --inicio se vier pronto; senão calcula a partir de --recebimento
        # (recebimento + N dias úteis, sáb/dom pulados, feriados ignorados).
        if args.inicio:
            return args.inicio, obs
        prazo = datas.prazo_defesa(args.recebimento, args.dias_uteis)
        if prazo is None:
            sys.exit("Prazo: informe --inicio (data pronta) ou --recebimento "
                     "(DD/MM/AAAA ou ISO) para calcular o prazo de defesa.")
        nota = (f"Prazo PROVISÓRIO: recebimento {datas.parse_data(args.recebimento):%d/%m/%Y} "
                f"+ {args.dias_uteis} dias úteis (sem feriados). Confirmar nos autos.")
        obs = f"{obs} — {nota}" if obs else nota
        return datas.fmt_iso(prazo), obs

    # verificar
    if not args.inicio:
        sys.exit("--inicio é obrigatório para o tipo 'verificar'.")
    return args.inicio, obs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tipo", required=True, choices=list(CATEGORIAS))
    ap.add_argument("--numero", required=True)
    ap.add_argument("--parte", default="")
    ap.add_argument("--inicio", default="",
                    help="ISO: data (prazo/verificar) ou data-hora (audiencia). "
                         "Para 'prazo' pode ser omitido se usar --recebimento.")
    ap.add_argument("--recebimento", default="",
                    help="Data de recebimento (DD/MM/AAAA ou ISO); usada para CALCULAR "
                         "o prazo de defesa quando --inicio não é dado.")
    ap.add_argument("--dias-uteis", type=int, default=datas.DIAS_UTEIS_DEFESA,
                    help=f"Dias úteis do prazo de defesa (padrão {datas.DIAS_UTEIS_DEFESA}).")
    ap.add_argument("--duracao-min", type=int, default=60)
    ap.add_argument("--calendario", default="BRP")
    ap.add_argument("--obs", default="")
    ap.add_argument("--criar-calendario", action="store_true", help="Cria o calendário se não existir")
    ap.add_argument("--simular", action="store_true")
    args = ap.parse_args()

    inicio, obs = resolve_inicio_obs(args)
    evento = monta_evento(args.tipo, args.numero, args.parte, inicio,
                          args.duracao_min, obs)

    if args.simular:
        print(json.dumps({"acao": "simulado", "calendario": args.calendario,
                          "categoria": CATEGORIAS[args.tipo],
                          "chave_idempotencia": chave_idempotencia(args.tipo, args.numero),
                          "evento": evento},
                         ensure_ascii=False, indent=2))
        return

    mailbox = os.environ.get("BRP_MAILBOX")
    if not mailbox:
        sys.exit("Defina BRP_MAILBOX (caixa que hospeda o calendário BRP).")
    token = get_token()
    nome_cat, cor = CATEGORIAS[args.tipo]
    garante_categoria(token, mailbox, nome_cat, cor)
    cal_id = acha_calendario(token, mailbox, args.calendario, criar=args.criar_calendario)
    acao, ev_id = upsert_evento(token, mailbox, cal_id, args.tipo, args.numero, evento)
    print(json.dumps({"acao": acao, "id": ev_id,
                      "assunto": evento["subject"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
