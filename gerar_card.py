#!/usr/bin/env python3
"""Gera o card 'Dado do dia' da IPPI (1080x1350) a partir de um JSON.

Uso:
  python3 gerar_card.py post.json saida.png
  python3 gerar_card.py --demo   # gera os 4 exemplos em ./exemplos/

JSON esperado:
{
  "pilar": "politica" | "saude" | "educacao" | "institucional",
  "selo": "POLÍTICA · PIAUÍ",            # texto curto no topo (opcional)
  "numero": "72,4%",                      # número em destaque
  "manchete": "...",                      # até ~12 palavras
  "contexto": "...",                      # 1 a 2 frases
  "fonte": "TSE, eleitorado de set/2026", # rodapé
  "comparacao": {"rotulo": "Brasil", "valor": "68,1%"}   # opcional
}
"""
import json, sys, os, html
from pathlib import Path

PILARES = {
    "politica":      {"cor": "#3B82F6", "nome": "POLÍTICA"},
    "saude":         {"cor": "#22C55E", "nome": "SAÚDE"},
    "educacao":      {"cor": "#F5C400", "nome": "EDUCAÇÃO"},
    "institucional": {"cor": "#F5C400", "nome": "IPPI"},
}

TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<style>
  :root{ --navy:#14243A; --navy2:#0E1A2E; --gold:#F5C400; --pilar:__COR__; }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{width:1080px;height:1350px}
  body{font-family:'Inter',sans-serif;color:#fff;
       background:radial-gradient(1200px 900px at 15% 10%, #1B3052 0%, var(--navy) 45%, var(--navy2) 100%);
       position:relative;overflow:hidden}
  .grid{position:absolute;inset:0;background-image:
        linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);
        background-size:90px 90px;}
  .barra{position:absolute;left:0;top:0;width:18px;height:100%;background:var(--pilar)}
  .wrap{position:absolute;left:96px;right:84px;top:84px;bottom:84px;display:flex;flex-direction:column}
  .selo{display:inline-flex;align-items:center;gap:14px;font-size:30px;font-weight:700;letter-spacing:.12em;color:var(--pilar)}
  .selo::before{content:"";width:16px;height:16px;background:var(--pilar);border-radius:3px}
  .tag{margin-left:auto;font-size:26px;font-weight:600;color:rgba(255,255,255,.55);letter-spacing:.08em}
  .topo{display:flex;align-items:center}
  .numero{margin-top:120px;font-family:'Inter Display','Inter',sans-serif;font-weight:800;
          font-size:__NUMSIZE__px;line-height:.95;letter-spacing:-.03em;color:var(--gold)}
  .manchete{margin-top:44px;font-size:62px;font-weight:700;line-height:1.12;letter-spacing:-.015em;max-width:880px}
  .contexto{margin-top:36px;font-size:34px;line-height:1.4;color:rgba(255,255,255,.82);max-width:860px;font-weight:400}
  .comp{margin-top:40px;display:inline-flex;align-items:center;gap:18px;padding:18px 28px;
        border:2px solid rgba(255,255,255,.18);border-radius:16px;font-size:30px;width:max-content}
  .comp b{color:var(--gold);font-size:36px}
  .rodape{margin-top:auto;display:flex;align-items:flex-end;justify-content:space-between;
          border-top:2px solid rgba(255,255,255,.14);padding-top:34px}
  .fonte{font-size:26px;line-height:1.35;color:rgba(255,255,255,.7);max-width:620px}
  .fonte b{color:#fff;font-weight:600}
  .logo{display:flex;align-items:center;gap:14px}
  .logo .canto{width:34px;height:34px;border-left:12px solid var(--gold);border-top:12px solid var(--gold)}
  .logo span{font-family:'Inter Display','Inter',sans-serif;font-weight:800;font-size:60px;letter-spacing:.02em}
  .logo small{display:block;font-size:20px;font-weight:500;letter-spacing:.14em;color:rgba(255,255,255,.6);margin-top:-6px}
</style></head><body>
<div class="grid"></div><div class="barra"></div>
<div class="wrap">
  <div class="topo"><div class="selo">__SELO__</div><div class="tag">DADO DO DIA</div></div>
  <div class="numero">__NUMERO__</div>
  <div class="manchete">__MANCHETE__</div>
  <div class="contexto">__CONTEXTO__</div>
  __COMP__
  <div class="rodape">
    <div class="fonte"><b>Fonte:</b> __FONTE__</div>
    <div class="logo"><div class="canto"></div><div><span>IPPI</span><small>PESQUISAS E CONSULTORIAS</small></div></div>
  </div>
</div></body></html>"""


def montar_html(p: dict) -> str:
    pil = PILARES[p.get("pilar", "institucional")]
    numero = p.get("numero", "")
    numsize = 230 if len(numero) <= 5 else (180 if len(numero) <= 8 else 130)
    comp = ""
    if p.get("comparacao"):
        c = p["comparacao"]
        comp = f'<div class="comp">{html.escape(c["rotulo"])}: <b>{html.escape(c["valor"])}</b></div>'
    return (TEMPLATE
            .replace("__COR__", pil["cor"])
            .replace("__SELO__", html.escape(p.get("selo") or pil["nome"]))
            .replace("__NUMSIZE__", str(numsize))
            .replace("__NUMERO__", html.escape(numero))
            .replace("__MANCHETE__", html.escape(p["manchete"]))
            .replace("__CONTEXTO__", html.escape(p.get("contexto", "")))
            .replace("__COMP__", comp)
            .replace("__FONTE__", html.escape(p.get("fonte", ""))))


def renderizar(p: dict, saida: str):
    from playwright.sync_api import sync_playwright
    html_str = montar_html(p)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        pg.set_content(html_str)
        pg.wait_for_timeout(150)
        pg.screenshot(path=saida, full_page=False)
        b.close()
    return saida


DEMO = [
    {"pilar": "politica", "selo": "POLÍTICA · PIAUÍ", "numero": "2,63 mi",
     "manchete": "Piauí chega a 2,63 milhões de eleitores aptos para 2026",
     "contexto": "Crescimento de 3,1% em relação a 2022. Teresina concentra 22% do eleitorado do estado.",
     "fonte": "TSE, Estatísticas do Eleitorado, set/2026",
     "comparacao": {"rotulo": "Eleitores em Teresina", "valor": "578 mil"}},
    {"pilar": "saude", "selo": "SAÚDE · MARANHÃO", "numero": "9,8%",
     "manchete": "Quase 1 em cada 10 bebês nasce com baixo peso no Maranhão",
     "contexto": "Proporção de nascidos vivos com menos de 2.500 g em 2024. A média brasileira é 8,6%.",
     "fonte": "DataSUS/SINASC, nascidos vivos 2024",
     "comparacao": {"rotulo": "Brasil", "valor": "8,6%"}},
    {"pilar": "educacao", "selo": "EDUCAÇÃO · PIAUÍ", "numero": "5,1",
     "manchete": "IDEB do ensino médio do Piauí fica acima da média nacional",
     "contexto": "Resultado de 2023 na rede estadual. Em 2019 o índice era 4,6 — avanço de 0,5 ponto em quatro anos.",
     "fonte": "INEP, IDEB 2023 — rede estadual",
     "comparacao": {"rotulo": "Brasil", "valor": "4,3"}},
    {"pilar": "institucional", "selo": "IPPI · BASTIDORES", "numero": "50",
     "manchete": "Como escolhemos os 50 municípios de uma pesquisa estadual",
     "contexto": "A amostra segue o peso de cada região no eleitorado, com cotas por sexo, idade, renda e escolaridade.",
     "fonte": "IPPI Pesquisas, metodologia registrada no PesqEle"},
]

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        out = Path(__file__).parent / "exemplos"; out.mkdir(exist_ok=True)
        for i, p in enumerate(DEMO, 1):
            f = out / f"{i}_{p['pilar']}.png"
            renderizar(p, str(f)); print("ok", f)
    else:
        p = json.load(open(sys.argv[1], encoding="utf-8"))
        print(renderizar(p, sys.argv[2]))
