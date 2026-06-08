#!/usr/bin/env python3
"""Remove eventos DUPLICADOS do calendário "BRP" (resíduo das rodadas antigas, antes de a
criação virar idempotente).

Varre o calendário inteiro, agrupa os eventos por compromisso — chave (tipo, número CNJ)
inferida do assunto — e, em cada grupo com mais de uma cópia, mantém UMA e apaga as demais.
A cópia mantida é, na ordem de preferência:
  1) a que já tem o carimbo brpKey (criada pela versão idempotente), senão
  2) a mais antiga (createdDateTime).

Por padrão roda em SIMULAÇÃO (só lista o que faria). Use --aplicar para apagar de verdade.

  python dedup_agenda.py            # relatório, não apaga nada
  python dedup_agenda.py --aplicar  # apaga as duplicatas
"""
import argparse
import os
import re
import sys
import urllib.parse
from pathlib import Path

# Carrega credenciais do graph.env (mesmo esquema do batch)
ENV_FILE = Path(__file__).parents[3] / "config" / "graph.env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, str(Path(__file__).parent))
from criar_evento_graph import (get_token, acha_calendario, http, GRAPH,
                                 PREFIXO_ASSUNTO, BRP_PROP_ID)

MAILBOX = os.environ.get("BRP_MAILBOX", "ajmadvogados@ajmadvogados.com.br")
CALENDARIO = os.environ.get("BRP_CALENDARIO", "BRP")

CNJ_RE = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
# prefixo do assunto -> tipo
TIPO_POR_PREFIXO = {v: k for k, v in PREFIXO_ASSUNTO.items()}


def lista_eventos(token, cal_id):
    """Todos os eventos do calendário, com carimbo brpKey expandido e data de criação."""
    eventos = []
    qs = urllib.parse.urlencode({
        "$select": "id,subject,createdDateTime",
        "$expand": f"singleValueExtendedProperties($filter=id eq '{BRP_PROP_ID}')",
        "$top": "100",
    }, quote_via=urllib.parse.quote)
    url = f"{GRAPH}/users/{MAILBOX}/calendars/{cal_id}/events?{qs}"
    while url:
        r = http("GET", url, token)
        eventos.extend(r.get("value", []))
        url = r.get("@odata.nextLink")
    return eventos


def chave_do_evento(ev):
    """(tipo, numero) inferido do assunto, ou None se não for um evento padrão da BRP."""
    assunto = ev.get("subject", "") or ""
    cnj = CNJ_RE.search(assunto)
    if not cnj:
        return None
    for prefixo, tipo in TIPO_POR_PREFIXO.items():
        if assunto.startswith(prefixo):
            return (tipo, cnj.group(0))
    return None


def tem_carimbo(ev):
    return bool(ev.get("singleValueExtendedProperties"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true",
                    help="Apaga de verdade (sem isto, apenas simula/relata)")
    args = ap.parse_args()

    token = get_token()
    cal_id = acha_calendario(token, MAILBOX, CALENDARIO)
    eventos = lista_eventos(token, cal_id)

    grupos = {}
    ignorados = 0
    for ev in eventos:
        chave = chave_do_evento(ev)
        if chave is None:
            ignorados += 1
            continue
        grupos.setdefault(chave, []).append(ev)

    a_apagar = []
    print(f"Calendario '{CALENDARIO}': {len(eventos)} eventos "
          f"({ignorados} fora do padrao BRP, ignorados).\n")
    for (tipo, numero), evs in sorted(grupos.items()):
        if len(evs) <= 1:
            continue
        # mantem: carimbado primeiro, depois o mais antigo
        evs.sort(key=lambda e: (not tem_carimbo(e), e.get("createdDateTime", "")))
        manter, sobra = evs[0], evs[1:]
        marca = "carimbado" if tem_carimbo(manter) else "mais antigo"
        print(f"[{tipo}] {numero}: {len(evs)} copias -> mantem 1 ({marca}), apaga {len(sobra)}")
        print(f"    keep: {manter.get('subject','')[:70]}")
        a_apagar.extend(sobra)

    print(f"\nResumo: {len(a_apagar)} eventos duplicados "
          f"em {sum(1 for e in grupos.values() if len(e) > 1)} compromissos.")

    if not a_apagar:
        print("Nada a apagar.")
        return
    if not args.aplicar:
        print("\n(SIMULACAO) Rode com --aplicar para apagar.")
        return

    print("\nApagando...")
    apagados, erros = 0, 0
    for ev in a_apagar:
        try:
            http("DELETE", f"{GRAPH}/users/{MAILBOX}/calendars/{cal_id}/events/{ev['id']}", token)
            apagados += 1
        except SystemExit as e:
            print(f"  [!] erro ao apagar {ev.get('subject','')[:50]}: {e}", file=sys.stderr)
            erros += 1
    print(f"Apagados: {apagados}, erros: {erros}")


if __name__ == "__main__":
    main()
