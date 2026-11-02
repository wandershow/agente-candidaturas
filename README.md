# Agente de Candidaturas

Agente de IA que, todo dia, busca vagas de **estágio, júnior e trainee** em TI, pontua cada uma contra o meu perfil, se candidata às que fazem sentido e gera um relatório do dia.

Construí este projeto para a minha própria busca por emprego na transição de carreira para TI (backend, engenharia de dados, QA, IA e cloud).

## Como funciona

```
 08:00  rotina agendada (Claude Code)
   │
   ├─ buscar_vagas.py ──► API pública da Gupy (26 termos)
   │                      Issues do GitHub backend-br/vagas (rótulos Júnior/Estagiário)
   │        │
   │        ▼
   │   filtro + nota 0–100 ──► vagas.json (histórico, sem duplicar)
   │
   ├─ agente (navegador) ──► lê a vaga, responde perguntas, escreve apresentação
   │                         personalizada e envia (Gupy / LinkedIn)
   │                         casos sensíveis viram "pendente" para decisão humana
   │
   ├─ marcar.py ──────────► atualiza status: candidatado | pendente | descartada
   │
   └─ gerar_relatorio.py ─► relatorio.html (enviadas, pendentes, para candidatar, talvez)
```

### Pontuação (`buscar_vagas.py`)
- **Descarta** vagas com inscrições encerradas, por nível (pleno, sênior, especialista), por área fora do alvo (suporte, vendas, frontend, mobile…) e vagas presenciais longe da minha cidade.
- **Soma pontos** por stack compatível (Python, SQL, AWS, Java, Docker, pytest, Playwright…), trilha-alvo (backend, dados, QA, IA ou cloud), trabalho remoto, uso de IA, vaga recente e vagas que valorizam inglês, atendimento ao cliente ou transição de carreira.
- **Tira pontos** por tecnologias exigidas que ainda não domino.

### O agente (`agente/rotina-diaria.md`)
É o prompt da tarefa agendada no Claude Code, que roda todo dia. Ele:
- usa os scripts acima para buscar e registrar as vagas;
- abre cada vaga no navegador, confere se ela encaixa de verdade e preenche o formulário com respostas honestas, baseadas em `respostas-padrao.md`;
- escreve uma apresentação diferente para cada vaga, citando os projetos mais relevantes;
- **não age sozinho** em CAPTCHA, criação de conta, senhas, consentimentos extras, vagas afirmativas ou requisitos de experiência que eu não tenho: nesses casos a vaga fica **pendente** para eu decidir;
- limita as candidaturas no LinkedIn a poucas por dia.

## Estrutura

| Arquivo | O que faz |
|---|---|
| `buscar_vagas.py` | Coleta (Gupy + GitHub), filtra, pontua e salva em `vagas.json` |
| `marcar.py` | `python marcar.py <id> <status> "<obs>"` |
| `gerar_relatorio.py` | Gera `relatorio.html` (tema claro/escuro, responsivo) |
| `publicar_github.py` | Commit + push das melhorias, abortando se achar dado pessoal |
| `agente/rotina-diaria.md` | Prompt do agente agendado |
| `exemplos/` | Modelos de `perfil-base.md` e `respostas-padrao.md` |

Os arquivos com dados pessoais e o histórico de candidaturas (`perfil-base.md`, `respostas-padrao.md`, `vagas.json`, `relatorio.html`) estão no `.gitignore`.

## Rodando

Só biblioteca padrão do Python 3.10+.

```bash
cp exemplos/perfil-base.exemplo.md perfil-base.md
cp exemplos/respostas-padrao.exemplo.md respostas-padrao.md
python buscar_vagas.py
python gerar_relatorio.py
```

Para a parte de candidaturas, crie uma tarefa agendada no Claude Code (desktop) com o conteúdo de `agente/rotina-diaria.md` e deixe Gupy/LinkedIn logados no navegador do app.

## Tecnologias
Python (urllib, re, json, unicodedata) · API REST · GitHub API · HTML/CSS · Claude Code (agente com navegador e tarefas agendadas)

---
Wanderson Fonseca da Silva · [github.com/wandershow](https://github.com/wandershow) · [linkedin.com/in/wandershow](https://linkedin.com/in/wandershow)
