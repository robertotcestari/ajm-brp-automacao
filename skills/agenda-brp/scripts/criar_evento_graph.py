#!/usr/bin/env python3
"""
Cria um evento no calendário "BRP" (Exchange Online) via Microsoft Graph.

Tipos:
- audiencia : evento com hora, categoria "Audiência BRP" (vermelho)
- prazo     : evento de dia inteiro, categoria "Prazo BRP" (amarelo)
- verificar : evento de dia inteiro "Verificar prazo nos autos", categoria "Verificar BRP" (laranja)

Autenticação: client credentials (app registration). Variáveis de ambiente:
  GRAPH_TENANT_ID, GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET, BRP_MAILBOX

Use --simular para ver o que seria criado SEM chamar a rede (útil antes do registro de app).
Só usa biblioteca padrão (urllib) — não precisa instalar nada.

Uso:
  python criar_evento_graph.py --tipo audiencia --numero "..." --parte "..." \
      --inicio "2026-09-30T09:30:00" --obs "telepresencial via Teams"
  python criar_evento_graph.py --tipo prazo --numero "..." --parte "..." --inicio "2026-06-20"
  python criar_evento_graph.py --tipo verificar --numero "..." --parte "..." --inicio "2026-06-02"
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

TZ = "E. South America Standard Time"  # horário de Brasília (ajuste se necessário)
GRAPH = "https://graph.microsoft.com/v1.0"

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


def monta_evento(tipo, numero, parte, inicio, duracao_min, obs):
    nome_cat = CATEGORIAS[tipo][0]
    if tipo == "audiencia":
        ini = datetime.fromisoformat(inicio)
        fim = ini + timedelta(minutes=duracao_min)
        return {
            "subject": f"Audiência — {parte} ({numero})",
            "body": {"contentType": "text", "content": obs or f"Processo {numero}"},
            "start": {"dateTime": ini.isoformat(), "timeZone": TZ},
            "end": {"dateTime": fim.isoformat(), "timeZone": TZ},
            "categories": [nome_cat],
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
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tipo", required=True, choices=list(CATEGORIAS))
    ap.add_argument("--numero", required=True)
    ap.add_argument("--parte", default="")
    ap.add_argument("--inicio", required=True, help="ISO: data (prazo/verificar) ou data-hora (audiencia)")
    ap.add_argument("--duracao-min", type=int, default=60)
    ap.add_argument("--calendario", default="BRP")
    ap.add_argument("--obs", default="")
    ap.add_argument("--criar-calendario", action="store_true", help="Cria o calendário se não existir")
    ap.add_argument("--simular", action="store_true")
    args = ap.parse_args()

    evento = monta_evento(args.tipo, args.numero, args.parte, args.inicio,
                          args.duracao_min, args.obs)

    if args.simular:
        print(json.dumps({"acao": "simulado", "calendario": args.calendario,
                          "categoria": CATEGORIAS[args.tipo], "evento": evento},
                         ensure_ascii=False, indent=2))
        return

    mailbox = os.environ.get("BRP_MAILBOX")
    if not mailbox:
        sys.exit("Defina BRP_MAILBOX (caixa que hospeda o calendário BRP).")
    token = get_token()
    nome_cat, cor = CATEGORIAS[args.tipo]
    garante_categoria(token, mailbox, nome_cat, cor)
    cal_id = acha_calendario(token, mailbox, args.calendario, criar=args.criar_calendario)
    criado = http("POST", f"{GRAPH}/users/{mailbox}/calendars/{cal_id}/events", token, body=evento)
    print(json.dumps({"acao": "criado", "id": criado.get("id"),
                      "assunto": evento["subject"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
