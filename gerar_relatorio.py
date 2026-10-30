"""Gera relatorio.html a partir de vagas.json."""
import html
import json
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).parent
vagas = json.loads((PASTA / "vagas.json").read_text(encoding="utf-8"))
hoje = datetime.now().strftime("%Y-%m-%d")

GRUPOS = [
    ("Candidaturas enviadas", lambda v: v["status"] == "candidatado"),
    ("Precisam de você", lambda v: v["status"] == "pendente"),
    ("Para candidatar (nota ≥ 60)", lambda v: v["status"] == "nova" and v["nota"] >= 60),
    ("Talvez (nota 40–59)", lambda v: v["status"] == "nova" and 40 <= v["nota"] < 60),
]


def linha(v):
    e = html.escape
    nova = " <span class=tag>nova hoje</span>" if v["vista_em"] == hoje else ""
    obs = f"<div class=obs>{e(v['obs'])}</div>" if v.get("obs") else ""
    salario = f" · <b class=sal>{e(v['salario'])}</b>" if v.get("salario") else " · salário não informado"
    return (f"<tr><td class=nota>{v['nota']}</td><td><a href='{e(v['url'])}' target=_blank>{e(v['titulo'])}</a>{nova}"
            f"<div class=sub>{e(v['empresa'] or v['fonte'])} · {e(v['local'])} · publicada {e(v['publicada'])}{salario}</div>"
            f"<div class=sub>{e(' · '.join(v['motivos']))}</div>{obs}</td><td>{e(v['candidatura'])}</td></tr>")


secoes = []
for nome, filtro in GRUPOS:
    lista = sorted((v for v in vagas.values() if filtro(v)), key=lambda v: -v["nota"])
    if lista:
        secoes.append(f"<h2>{nome} <small>({len(lista)})</small></h2><table>"
                      + "".join(linha(v) for v in lista) + "</table>")

novas = sum(v["vista_em"] == hoje for v in vagas.values())
enviadas = sum(v["status"] == "candidatado" for v in vagas.values())
pagina = f"""<!doctype html><html lang=pt-br><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Relatório de vagas</title><style>
:root{{--bg:#fafaf8;--fg:#1d1d1b;--mut:#6b6b66;--line:#e4e3de;--acc:#1f6f5c;--tag:#e6f2ee}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--fg:#ecebe6;--mut:#9a9992;--line:#2c2c2a;--acc:#5fc2a6;--tag:#1f3530}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0 auto;max-width:960px;padding:24px 16px}}
h1{{margin:0}} h2{{margin-top:32px;font-size:18px}} small,.sub{{color:var(--mut);font-size:13px}}
.kpis{{display:flex;gap:24px;margin:16px 0;flex-wrap:wrap}} .kpis b{{font-size:24px;display:block}}
table{{width:100%;border-collapse:collapse}} td{{border-top:1px solid var(--line);padding:10px 8px;vertical-align:top}}
td.nota{{font-weight:700;color:var(--acc);width:40px}} a{{color:var(--fg);font-weight:600}}
.tag{{background:var(--tag);color:var(--acc);font-size:11px;padding:1px 6px;border-radius:8px;margin-left:6px}}
.obs{{font-size:13px;margin-top:4px}} .sal{{color:var(--acc)}}
</style></head><body><h1>Relatório de vagas</h1><div class=sub>{datetime.now():%d/%m/%Y %H:%M} · estágio, júnior e trainee · backend, engenharia de dados, QA</div>
<div class=kpis><div><b>{novas}</b>novas hoje</div><div><b>{enviadas}</b>candidaturas enviadas</div><div><b>{len(vagas)}</b>vagas no histórico</div></div>
{''.join(secoes)}</body></html>"""
(PASTA / "relatorio.html").write_text(pagina, encoding="utf-8")
print("relatorio.html gerado")
