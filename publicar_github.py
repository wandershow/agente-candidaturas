"""Publica no GitHub as mudanças nos arquivos versionados (scripts, README, prompt).
Antes de commitar, procura dados pessoais nos arquivos alterados e aborta se achar."""
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).parent
SENSIVEIS = {
    "telefone": re.compile(r"\(?\d{2}\)?\s?9\d{4}-?\d{4}"),
    "CPF": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    "e-mail": re.compile(r"[\w.+-]+@(gmail|hotmail|outlook|yahoo)\.com"),
    "pretensão salarial": re.compile(r"R\$\s?\d"),
}


def git(*args):
    r = subprocess.run(["git", *args], cwd=PASTA, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        sys.exit(f"git {' '.join(args)} falhou:\n{r.stderr}")
    return r.stdout


def main():
    mudancas = [l[3:].strip('"') for l in git("status", "--porcelain").splitlines()]
    if not mudancas:
        print("nada para publicar")
        return
    problemas = []
    for arq in mudancas:
        p = PASTA / arq
        if not p.is_file():
            continue
        texto = p.read_text(encoding="utf-8", errors="ignore")
        for nome, rx in SENSIVEIS.items():
            if rx.search(texto):
                problemas.append(f"{arq}: possível {nome}")
    if problemas:
        sys.exit("NÃO publicado, revise:\n" + "\n".join(problemas))

    mensagem = sys.argv[1] if len(sys.argv) > 1 else f"Atualização automática {datetime.now():%d/%m/%Y}"
    git("add", "-A")
    git("commit", "-m", mensagem + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    git("push")
    print("publicado:", ", ".join(mudancas))


if __name__ == "__main__":
    main()
