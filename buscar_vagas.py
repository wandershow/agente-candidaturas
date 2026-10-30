"""Busca vagas de estágio/júnior/trainee em backend, engenharia de dados e QA,
pontua contra o perfil-base e salva em vagas.json (acumulando histórico)."""
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PASTA = Path(__file__).parent
ARQUIVO = PASTA / "vagas.json"
UA = {"User-Agent": "Mozilla/5.0 (buscador-de-vagas pessoal)"}

TERMOS_GUPY = [
    "estagio backend", "estagio desenvolvimento", "estagio python", "estagio java",
    "estagio dados", "estagio engenharia de dados", "estagio qa", "estagio testes",
    "estagio ti", "estagio inteligencia artificial", "estagio software",
    "desenvolvedor junior", "desenvolvedor backend", "desenvolvedor python",
    "desenvolvedor java", "python junior", "java junior", "backend junior",
    "engenheiro de dados", "engenharia de dados", "qa junior", "analista de testes",
    "analista qa", "trainee tecnologia", "trainee ti", "trainee dados",
]

NIVEL = re.compile(r"\b(estagi\w*|junior|jr\.?|trainee|aprendiz\w*|nivel i|i)\b")
NIVEL_RUIM = re.compile(r"\b(pleno|senior|sr\.?|especialista|lider|tech lead|coordenador|gerente|ii|iii|nivel medio|ensino medio|tecnico em)\b")
TRILHAS = {
    "backend": r"back[- ]?end|desenvolvedor|developer|programador|software|python|java\b|api",
    "dados": r"engenh\w* de dados|data engineer|\betl\b|pipeline|dados",
    "qa": r"\bqa\b|qualidade de software|testes?\b|tester|quality",
}
CIDADES_PERTO = {"rio grande", "pelotas", "sao jose do norte", "capao do leao", "santa vitoria do palmar"}
TI_GERAL = re.compile(r"\bti\b|tecnologia|intelig\w* artificial|\bia\b|desenvolvimento( e aplicacoes| de integracoes| de software|\s*$|\s*-)")
FORA = re.compile(r"front[- ]?end|mobile|android|\bios\b|\.net|c#|php|ruby|delphi|sap\b|suporte|help ?desk|service ?desk|infraestrutura|pre[- ]?vendas?|comercial|vendas|marketing|contab|juridic|rh\b|design")
STACK = ["python", "sql", "aws", "java", "linux", "git", "docker", "pytest", "playwright",
         "postgres", "mysql", "spark", "etl", "s3", "lambda", "api", "poo", "orientacao a objetos",
         "selenium", "automacao", "fastapi"]
FALTA = ["react", "angular", "vue", "kotlin", "golang", "kubernetes", "c++", "scala", "node"]
IA = re.compile(r"intelig\w* artificial|\bia\b|\bai\b|\bllm|machine learning|genai|agentes?\b|openai|chatgpt|claude|n8n")
BONUS = re.compile(r"ingles|english|transicao de carreira|atendimento|cliente|primeiro emprego|sem experiencia")


def norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode()
    return t.lower()


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def buscar_gupy():
    vagas = {}
    for termo in TERMOS_GUPY:
        url = "https://portal.gupy.io/api/job-search/jobs?" + urllib.parse.urlencode(
            {"jobName": termo, "limit": 100, "offset": 0})
        try:
            dados = get_json(url).get("data", [])
        except Exception as e:
            print(f"[gupy] falha em '{termo}': {e}", file=sys.stderr)
            continue
        for v in dados:
            vagas[f"gupy-{v['id']}"] = {
                "id": f"gupy-{v['id']}",
                "fonte": "Gupy",
                "titulo": v["name"].strip(),
                "empresa": v.get("careerPageName", ""),
                "local": "Remoto" if v.get("workplaceType") == "remote"
                         else f"{v.get('city', '')}/{v.get('state', '')} ({v.get('workplaceType', '')})",
                "modelo": v.get("workplaceType", ""),
                "estado": v.get("state", ""),
                "cidade": v.get("city", ""),
                "publicada": (v.get("publishedDate") or "")[:10],
                "prazo": (v.get("applicationDeadline") or "")[:10],
                "url": v["jobUrl"].split("?")[0],
                "descricao": v.get("description", ""),
                "candidatura": "plataforma (Gupy)",
            }
        time.sleep(0.5)
    return vagas


def buscar_github(repo="backend-br/vagas"):
    vagas = {}
    for label in ["Júnior", "Estagiário"]:
        url = f"https://api.github.com/repos/{repo}/issues?" + urllib.parse.urlencode(
            {"state": "open", "labels": label, "per_page": 100})
        try:
            dados = get_json(url)
        except Exception as e:
            print(f"[github] falha em {label}: {e}", file=sys.stderr)
            continue
        for i in dados:
            labels = [l["name"] for l in i["labels"]]
            corpo = i.get("body") or ""
            emails = sorted(set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", corpo)))
            remoto = "Remoto" in labels
            vagas[f"gh-{i['number']}"] = {
                "id": f"gh-{repo}-{i['number']}",
                "fonte": f"GitHub {repo}",
                "titulo": i["title"].strip(),
                "empresa": "",
                "local": "Remoto" if remoto else ("Híbrido" if "Híbrido" in labels else "ver vaga"),
                "modelo": "remote" if remoto else "",
                "estado": "", "cidade": "",
                "publicada": i["created_at"][:10],
                "prazo": "",
                "url": i["html_url"],
                "descricao": corpo + " " + " ".join(labels),
                "candidatura": f"e-mail ({', '.join(emails)})" if emails else "ver instruções na vaga",
                "emails": emails,
            }
    return vagas


def pontuar(v):
    titulo = norm(v["titulo"])
    texto = titulo + " " + norm(v["descricao"])
    motivos = []
    if NIVEL_RUIM.search(titulo) or not (NIVEL.search(titulo) or re.search(r"\b(estagi\w*|junior|trainee)\b", texto[:600])):
        return None, ["nível fora do alvo"]
    if FORA.search(titulo):
        return None, ["área fora do alvo"]
    trilhas = [t for t, rx in TRILHAS.items() if re.search(rx, titulo)]
    generica = False
    if not trilhas and TI_GERAL.search(titulo):
        # título genérico ("Estágio em TI"): aceita se a descrição fala das trilhas
        trilhas = [t for t, rx in TRILHAS.items() if re.search(rx, texto)]
        generica = True
    if not trilhas:
        return None, ["título não é de backend/dados/QA"]
    # local: remoto em qualquer lugar; presencial/híbrido só perto de Rio Grande
    no_rs = norm(v["cidade"]) in CIDADES_PERTO
    if v["modelo"] in ("on-site", "hybrid") and not no_rs:
        return None, [f"presencial longe ({v['local']})"]

    nota = 20 + (10 if generica else 20)  # nível ok + trilha ok (genérica vale menos)
    motivos.append(("TI geral, cita: " if generica else "trilha: ") + ", ".join(trilhas))
    achou = [s for s in STACK if re.search(r"\b" + re.escape(s) + r"\b", texto)]
    nota += min(40, len(achou) * 8)
    if achou:
        motivos.append("stack: " + ", ".join(achou))
    if v["modelo"] == "remote" or v["local"] == "Remoto":
        nota += 20; motivos.append("remoto")
    elif no_rs:
        nota += 20; motivos.append(f"RS: {v['cidade']}")
    falta = [s for s in FALTA if re.search(r"\b" + re.escape(s) + r"\b", texto)]
    nota -= 10 * len(falta)
    if falta:
        motivos.append("pede: " + ", ".join(falta))
    if IA.search(texto):
        nota += 5; motivos.append("usa IA")
    if BONUS.search(texto):
        nota += 10; motivos.append("valoriza inglês/atendimento/transição")
    try:
        dias = (datetime.now(timezone.utc).date() - datetime.fromisoformat(v["publicada"]).date()).days
        if dias <= 7:
            nota += 10; motivos.append(f"publicada há {dias}d")
        elif dias > 45:
            nota -= 15; motivos.append(f"antiga ({dias}d)")
    except ValueError:
        pass
    return max(0, min(100, nota)), motivos


def main():
    hist = json.loads(ARQUIVO.read_text(encoding="utf-8")) if ARQUIVO.exists() else {}
    hoje = datetime.now().strftime("%Y-%m-%d")
    novas = {**buscar_gupy(), **buscar_github()}
    descartes = {}
    for vid, v in novas.items():
        nota, motivos = pontuar(v)
        if nota is None:
            descartes[motivos[0]] = descartes.get(motivos[0], 0) + 1
            continue
        v["descricao"] = v["descricao"][:1500]
        v["nota"], v["motivos"] = nota, motivos
        if v["id"] in hist:
            v["status"] = hist[v["id"]].get("status", "nova")
            v["vista_em"] = hist[v["id"]].get("vista_em", hoje)
        else:
            v["status"], v["vista_em"] = "nova", hoje
        hist[v["id"]] = v
    ARQUIVO.write_text(json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8")
    aprovadas = [v for v in hist.values() if v["vista_em"] == hoje]
    print(f"brutas: {len(novas)} | aproveitadas hoje: {len(aprovadas)} | descartes: {descartes}")


if __name__ == "__main__":
    main()
