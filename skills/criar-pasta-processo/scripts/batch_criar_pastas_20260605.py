#!/usr/bin/env python3
"""Cria em lote as pastas dos 6 processos BRP recebidos em 05/06/2026."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from criar_pasta import formata_parte, sanitiza

BASE = r"G:\A.Digital\BRP"

PROCESSOS = [
    ("0802349-48.2026.8.14.0136", "ELIONAY SOUSA FERREIRA"),
    ("0879645-70.2025.8.20.5001", "LUCIANA RAYANE MARTINS CIPRIANO"),
    ("5016919-46.2026.8.21.0021", "LUIS PAULO TROMBETTA"),
    ("4004370-40.2026.8.26.0099", "WILLIAM DAVID DE OLIVEIRA SAVIELO"),
    ("1029453-09.2026.8.11.0041", "DANIEL ASSIS DE MORAES"),
    ("4005983-52.2026.8.26.0566", "MARIA DA PENHA DA SILVA CESCHI"),
]

criadas, reutilizadas, erros = [], [], []

for numero, parte in PROCESSOS:
    nome = f"{formata_parte(parte)} - {sanitiza(numero)}"
    destino = Path(BASE) / nome
    try:
        ja_existia = destino.exists()
        destino.mkdir(parents=True, exist_ok=True)
        for sub in ["01 - Citação", "02 - Petição inicial", "03 - Defesa"]:
            (destino / sub).mkdir(parents=True, exist_ok=True)
        if ja_existia:
            reutilizadas.append(str(destino))
        else:
            criadas.append(str(destino))
    except Exception as e:
        erros.append({"processo": numero, "erro": str(e)})

print(f"Criadas: {len(criadas)} | Ja existiam: {len(reutilizadas)} | Erros: {len(erros)}")
for p in criadas:
    print(f"  [+] {p}")
for p in reutilizadas:
    print(f"  [=] {p}")
for e in erros:
    print(f"  [!] {e['processo']}: {e['erro']}", file=sys.stderr)
