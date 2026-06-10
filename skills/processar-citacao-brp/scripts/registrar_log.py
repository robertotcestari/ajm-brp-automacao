#!/usr/bin/env python3
"""
Grava um log de auditoria de cada e-mail de citação BRP processado pela automação.

Objetivo: deixar rastro completo para depurar no futuro — o que foi lido do e-mail,
o que a automação extraiu e o que cada ação (SQLite/pasta/agenda) devolveu.

- Cria a pasta de logs se não existir (padrão: LOGS/ na raiz do projeto/plugin).
- Agrupa por EXECUÇÃO: um arquivo por rodada (padrão = a hora corrente, casando com a
  tarefa agendada de hora em hora). Cada e-mail processado vira uma linha JSON (JSONL),
  então uma rodada que processa vários e-mails fica toda no mesmo arquivo.
- Nunca inventa: grava exatamente o que recebe, só acrescentando carimbo de tempo.

Uso:
  python registrar_log.py --registro '{...json com email/extraido/acoes...}'
  python registrar_log.py --registro-arquivo entrada.json
  # opcionais:
  #   --logs-dir "G:\\...\\LOGS"   (ou variável de ambiente BRP_LOGS_DIR)
  #   --run-id   "20260608T16"      (agrupa o arquivo da rodada)

Formato sugerido do registro (todos os campos são livres/opcionais — grave o que tiver):
  {
    "email": {                      # o e-mail BRUTO, como chegou
      "assunto": "...", "remetente": "...", "recebido_em": "...",
      "message_id": "...", "corpo": "...(trecho ou íntegra)..."
    },
    "extraido": { ...campos de processar-citacao-brp (numero_processo, etc.)... },
    "acoes": {                      # o que cada skill devolveu
      "database": "processo/e-mail inserido/atualizado/pulado",
      "pasta": "G:\\...\\<Parte> - <numero>",
      "agenda": ["audiencia ...", "prazo ..."]
    },
    "observacoes": "qualquer coisa útil p/ depurar"
  }
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def raiz_projeto():
    # skills/processar-citacao-brp/scripts/registrar_log.py -> sobe 3 níveis até a raiz
    return Path(__file__).resolve().parents[3]


def logs_dir_padrao():
    env = os.environ.get("BRP_LOGS_DIR")
    if env:
        return Path(env)
    return raiz_projeto() / "LOGS"


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--registro", help="JSON do registro (string)")
    g.add_argument("--registro-arquivo", help="arquivo .json com o registro")
    ap.add_argument("--logs-dir", default=None, help="pasta de logs (sobrepõe o padrão)")
    ap.add_argument("--run-id", default=None,
                    help="identificador da rodada (padrão: AAAAMMDDThh = hora corrente)")
    args = ap.parse_args()

    try:
        if args.registro:
            registro = json.loads(args.registro)
        else:
            registro = json.loads(Path(args.registro_arquivo).read_text(encoding="utf-8"))
    except Exception as e:
        sys.exit(f"Registro JSON inválido: {e}")

    agora = datetime.now()
    run_id = args.run_id or agora.strftime("%Y%m%dT%H")
    logs_dir = Path(args.logs_dir) if args.logs_dir else logs_dir_padrao()

    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        sys.exit(f"Não consegui criar a pasta de logs {logs_dir}: {e}")

    entrada = {
        "registrado_em": agora.isoformat(timespec="seconds"),
        "run_id": run_id,
        **registro,
    }

    arquivo = logs_dir / f"{run_id}-execucao.jsonl"
    try:
        with arquivo.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    except Exception as e:
        sys.exit(f"Não consegui gravar o log em {arquivo}: {e}")

    # resumo curto p/ o orquestrador
    extraido = registro.get("extraido") or {}
    proc = extraido.get("numero_processo") or registro.get("numero_processo") or "?"
    print(json.dumps({"acao": "log_gravado", "arquivo": str(arquivo),
                      "processo": proc, "run_id": run_id}, ensure_ascii=False))


if __name__ == "__main__":
    main()
