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
    ("Abaixo do corte (nota < 40)", lambda v: v["status"] == "nova" and v["nota"] < 40),
    ("Descartadas", lambda v: v["status"] in ("descartada", "antiga")),
]
RECOLHIDOS = {"Descartadas"}  # seções longas que abrem só ao clicar
SEM_SELETOR = {"Descartadas"}  # seções onde não faz sentido marcar decisão

# Seletor de decisão por vaga: grava no banco do Artifact (coleção "decisoes",
# doc = id da vaga). O agente lê essas decisões no início de cada execução
# (aplicar_decisoes.py) e atualiza o vagas.json.
OPCOES = [("", "Decidir…"), ("candidatado", "Já me candidatei"),
          ("expirada", "Expirada"), ("sem_interesse", "Sem interesse")]


def seletor(v):
    e = html.escape
    ops = "".join(f"<option value='{k}'>{t}</option>" for k, t in OPCOES)
    return (f"<label class=dec><span class=vh>Decisão sobre {e(v['titulo'])}</span>"
            f"<select data-id='{e(v['id'])}' disabled>{ops}</select></label>")


def linha(v, com_seletor=True):
    e = html.escape
    nova = " <span class=tag>nova hoje</span>" if v["vista_em"] == hoje else ""
    feita = v["status"] == "candidatado"
    if feita:
        nova += " <span class=tag>✓ candidatura feita</span>"
    obs = f"<div class=obs>{e(v['obs'])}</div>" if v.get("obs") else ""
    salario = f" · <b class=sal>{e(v['salario'])}</b>" if v.get("salario") else " · salário não informado"
    dec = seletor(v) if com_seletor and not feita else ""  # já enviada: não há o que decidir
    return (f"<tr data-id='{e(v['id'])}'><td class=nota>{v['nota']}</td><td><a href='{e(v['url'])}' target=_blank>{e(v['titulo'])}</a>{nova}"
            f"<div class=sub>{e(v['empresa'] or v['fonte'])} · {e(v['local'])} · publicada {e(v['publicada'])}{salario}</div>"
            f"<div class=sub>{e(' · '.join(v['motivos']))}</div>{obs}<div class=decmsg></div></td><td>{e(v['candidatura'])}{dec}</td></tr>")


secoes = []
for nome, filtro in GRUPOS:
    lista = sorted((v for v in vagas.values() if filtro(v)), key=lambda v: -v["nota"])
    if not lista:
        continue
    tabela = "<table>" + "".join(linha(v, nome not in SEM_SELETOR) for v in lista) + "</table>"
    if nome in RECOLHIDOS:
        secoes.append(f"<details><summary><h2>{nome} <small>({len(lista)})</small></h2></summary>{tabela}</details>")
    else:
        secoes.append(f"<h2>{nome} <small>({len(lista)})</small></h2>{tabela}")

SCRIPT = r"""
const ROTULO = {candidatado: "Você marcou: já se candidatou", expirada: "Você marcou: expirada — sai da lista na próxima execução",
  sem_interesse: "Você marcou: sem interesse — sai da lista na próxima execução"};
const aviso = document.getElementById("aviso");
const selects = [...document.querySelectorAll("select[data-id]")];
function mostrar(id, dec) {
  const tr = document.querySelector(`tr[data-id="${CSS.escape(id)}"]`);
  if (!tr) return;
  tr.classList.toggle("fora", dec === "expirada" || dec === "sem_interesse");
  tr.querySelector(".decmsg").textContent = ROTULO[dec] || "";
  const s = tr.querySelector("select"); if (s) s.value = dec || "";
}
(async () => {
  const db = await claude.use("db");
  if (!db) { aviso.textContent = "As decisões só podem ser marcadas com você logado no claude.ai."; return; }
  const user = await claude.use("user");
  const podeEditar = user ? await user.canEdit() : true;
  const col = db.collection("decisoes");
  const timer = setTimeout(() => { aviso.textContent = "Não consegui carregar as decisões salvas ainda."; }, 10000);
  col.onSnapshot(snap => {
    if (!snap.metadata.fromCache) clearTimeout(timer);
    snap.docChanges().forEach(c => mostrar(c.doc.id, c.type === "removed" ? "" : c.doc.data().decisao));
  }, () => { clearTimeout(timer); aviso.textContent = "Não consegui carregar as decisões salvas."; });
  if (!podeEditar) { aviso.textContent = "Só o dono do relatório pode marcar decisões."; return; }
  selects.forEach(s => {
    s.disabled = false;
    s.addEventListener("change", async () => {
      const id = s.dataset.id, dec = s.value;
      s.disabled = true;
      try {
        if (dec) await col.doc(id).set({decisao: dec, em: new Date().toISOString()});
        else await col.doc(id).delete();
        mostrar(id, dec);
      } catch (e) {
        s.closest("tr").querySelector(".decmsg").textContent = "Não salvou, tente de novo.";
      } finally { s.disabled = false; }
    });
  });
})();
"""

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
summary{{cursor:pointer}} summary h2{{display:inline}}
td:last-child{{width:170px}} .dec{{display:block;margin-top:8px}}
.dec select{{width:100%;font:inherit;font-size:13px;padding:4px 6px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)}}
.dec select:disabled{{opacity:.5}} .decmsg{{font-size:13px;color:var(--acc);margin-top:4px}}
tr.fora td{{opacity:.45}} tr.fora td:last-child{{opacity:1}}
.vh{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}}
#aviso{{font-size:13px;color:var(--mut);margin:8px 0}}
@media (max-width:600px){{tr{{display:grid;grid-template-columns:40px 1fr}} td:last-child{{grid-column:2;width:auto;border-top:0;padding-top:0}}}}
</style></head><body><h1>Relatório de vagas</h1><div class=sub>{datetime.now():%d/%m/%Y %H:%M} · estágio, júnior e trainee · backend, engenharia de dados, QA</div>
<div class=kpis><div><b>{novas}</b>novas hoje</div><div><b>{enviadas}</b>candidaturas enviadas</div><div><b>{len(vagas)}</b>vagas no histórico</div></div>
<div id=aviso>Use o seletor de cada vaga para dizer se já se candidatou, se expirou ou se não tem interesse. O agente aplica isso na próxima execução.</div>
{''.join(secoes)}<script>{SCRIPT}</script></body></html>"""
(PASTA / "relatorio.html").write_text(pagina, encoding="utf-8")
print("relatorio.html gerado")
