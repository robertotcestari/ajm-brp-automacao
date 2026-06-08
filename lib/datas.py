"""Utilidades de data compartilhadas pela automação BRP.

A regra de prazo de defesa vive aqui, num único lugar, para a planilha
(`registrar-planilha-brp`) e a agenda (`agenda-brp`) calcularem exatamente a mesma data.
"""
from datetime import date, datetime, timedelta


def parse_data(texto):
    """Aceita 'DD/MM/AAAA', 'AAAA-MM-DD', 'DD/MM/AA', date/datetime (com ou sem hora).
    Devolve um date, ou None se não der para interpretar."""
    if texto is None:
        return None
    if isinstance(texto, datetime):
        return texto.date()
    if isinstance(texto, date):
        return texto
    s = str(texto).strip()
    if not s:
        return None
    # descarta a parte de hora, se houver ("2026-05-27T09:30" ou "27/05/2026 09:30")
    s = s.replace("T", " ").split()[0]
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def soma_dias_uteis(inicio, n):
    """Soma n dias ÚTEIS a partir de `inicio`, pulando apenas sábados e domingos.
    Feriados são DELIBERADAMENTE ignorados: contar menos dias dá um prazo mais cedo,
    portanto mais conservador (menos risco de perder a defesa)."""
    d = inicio
    restantes = n
    while restantes > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:  # 0=segunda ... 4=sexta
            restantes -= 1
    return d


# Quantidade padrão de dias úteis para o prazo de defesa (convenção conservadora da AJM).
DIAS_UTEIS_DEFESA = 13


def prazo_defesa(recebimento, dias_uteis=DIAS_UTEIS_DEFESA):
    """Data-limite (provisória) da defesa = recebimento + N dias úteis (sáb/dom pulados,
    feriados ignorados). Devolve date, ou None se a data de recebimento for inválida."""
    base = parse_data(recebimento)
    if base is None:
        return None
    return soma_dias_uteis(base, dias_uteis)


def fmt_br(d):
    """date -> 'DD/MM/AAAA'."""
    return d.strftime("%d/%m/%Y") if d else ""


def fmt_iso(d):
    """date -> 'AAAA-MM-DD'."""
    return d.isoformat() if d else ""
