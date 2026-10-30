"""Uso: python marcar.py <id> <status> [observação] [--salario="R$ X.XXX,XX"]
status: candidatado | pendente | descartada (use "-" para manter o status atual)"""
import json, sys
from datetime import datetime
from pathlib import Path
p = Path(__file__).parent / "vagas.json"
h = json.loads(p.read_text(encoding="utf-8"))
args = [a for a in sys.argv[1:] if not a.startswith("--salario=")]
salario = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--salario=")), None)
vid, status = args[0], args[1]
if status != "-":
    h[vid]["status"] = status
h[vid]["atualizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M")
if len(args) > 2:
    h[vid]["obs"] = args[2]
if salario:
    h[vid]["salario"] = salario
p.write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding="utf-8")
print(vid, "->", h[vid]["status"], f"| salário: {salario}" if salario else "")
