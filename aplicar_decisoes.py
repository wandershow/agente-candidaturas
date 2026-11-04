"""Aplica no vagas.json as decisões que o Wanderson marcou no relatório.

Uso: python aplicar_decisoes.py <pasta>
<pasta> contém um JSON por vaga (nome = id da vaga), exportado da coleção
"decisoes" do banco do Artifact. Cada documento tem {"decisao", "em"}:
  candidatado   -> status candidatado
  expirada      -> status descartada (sai da lista)
  sem_interesse -> status descartada (sai da lista)
É idempotente: uma decisão já aplicada (mesmo "em") não é reaplicada.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).parent
REGRAS = {
    "candidatado": ("candidatado", "Você marcou no relatório que já se candidatou"),
    "expirada": ("descartada", "Expirada (marcado por você no relatório)"),
    "sem_interesse": ("descartada", "Sem interesse (marcado por você no relatório)"),
}


def corpo(d):
    """Aceita o documento puro ou embrulhado ({"data": {...}})."""
    if isinstance(d, dict) and "decisao" not in d and isinstance(d.get("data"), dict):
        return d["data"]
    return d


def main(pasta):
    arq = PASTA / "vagas.json"
    vagas = json.loads(arq.read_text(encoding="utf-8"))
    aplicadas, ignoradas = [], []
    for f in sorted(Path(pasta).rglob("*.json")):
        vid, doc = f.stem, corpo(json.loads(f.read_text(encoding="utf-8")))
        regra = REGRAS.get(doc.get("decisao"))
        if vid not in vagas or not regra:
            ignoradas.append(vid)
            continue
        v = vagas[vid]
        if v.get("decisao_aplicada") == doc.get("em"):
            continue
        status, obs = regra
        quando = (doc.get("em") or "")[:10]
        v["status"] = status
        v["obs"] = f"{obs} em {quando}." + (f" Antes: {v['obs']}" if v.get("obs") else "")
        v["decisao_aplicada"] = doc.get("em")
        v["atualizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        aplicadas.append(f"{vid} -> {status} ({doc['decisao']})")
    arq.write_text(json.dumps(vagas, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(aplicadas)} decisão(ões) aplicada(s)")
    for a in aplicadas:
        print(" ", a)
    if ignoradas:
        print("ignoradas (id desconhecido ou decisão inválida):", ", ".join(ignoradas))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "decisoes")
