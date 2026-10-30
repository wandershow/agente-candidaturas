"""Uso: python marcar.py <id> <status> [observação]  (status: candidatado | pendente | descartada)"""
import json, sys
from datetime import datetime
from pathlib import Path
p = Path(__file__).parent / "vagas.json"
h = json.loads(p.read_text(encoding="utf-8"))
vid, status = sys.argv[1], sys.argv[2]
h[vid]["status"] = status
h[vid]["atualizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M")
if len(sys.argv) > 3:
    h[vid]["obs"] = sys.argv[3]
p.write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding="utf-8")
print(vid, "->", status)
