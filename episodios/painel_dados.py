"""Gera os ficheiros de dados do painel (episodios/painel/*.json) a partir do registo e do YouTube.

Uso: python3 episodios/painel_dados.py --saldo 1738.04 [--plano ultra]
O saldo do Higgsfield vem da ferramenta `balance` (MCP), por isso entra como argumento.
Depois, carregar os 3 ficheiros para o painel (ver CLAUDE.md).
"""
from __future__ import annotations

import argparse, csv, datetime as dt, json, os, pathlib, sys

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from yt_upload import API, auth_headers  # noqa: E402

AQUI = pathlib.Path(__file__).resolve().parent
OUT = AQUI / "painel"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saldo", type=float, required=True)
    ap.add_argument("--plano", default="ultra")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    agora = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    hoje = agora[:10]
    h = auth_headers()

    eps = list(csv.DictReader(open(AQUI / "registo.csv", encoding="utf-8")))
    ids = [e["video_id"] for e in eps if e["video_id"]]
    stats = {}
    if ids:
        r = requests.get(f"{API}/videos", params={"part": "statistics,status", "id": ",".join(ids)}, headers=h, timeout=30)
        r.raise_for_status()
        stats = {i["id"]: i for i in r.json().get("items", [])}
    ret = {}
    if ids:
        r = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", headers=h, timeout=30, params={
            "ids": "channel==MINE", "startDate": "2026-11-01", "endDate": hoje, "dimensions": "video",
            "metrics": "views,averageViewPercentage", "filters": "video==" + ",".join(ids)})
        if r.ok:
            ret = {row[0]: row[2] for row in r.json().get("rows", [])}
    rows = []
    for e in eps:
        s = stats.get(e["video_id"], {})
        st = s.get("statistics", {})
        rows.append({
            "episodio": e["episodio"], "data": e["data"], "titulo": e["titulo"],
            "link": f"https://www.youtube.com/shorts/{e['video_id']}" if e["video_id"] else None,
            "estado": {"private": "privado", "public": "público", "unlisted": "não listado"}.get(
                s.get("status", {}).get("privacyStatus", ""), e["estado"]),
            "creditos": float(e["creditos_higgsfield"]) if e["creditos_higgsfield"] else None,
            "duracao_s": round(float(e["duracao_s"])) if e["duracao_s"] else None,
            "visualizacoes": int(st.get("viewCount", 0)), "gostos": int(st.get("likeCount", 0)),
            "comentarios": int(st.get("commentCount", 0)),
            "retencao_pct": round(ret[e["video_id"]], 1) if e["video_id"] in ret else None,
        })
    json.dump(rows, open(OUT / "episodios.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    r = requests.get(f"{API}/channels", params={"part": "statistics", "mine": "true"}, headers=h, timeout=30)
    r.raise_for_status()
    cs = r.json()["items"][0]["statistics"]
    json.dump([{"atualizado": agora, "subscritores": int(cs.get("subscriberCount", 0)),
                "videos_publicos": int(cs.get("videoCount", 0)), "visualizacoes_canal": int(cs.get("viewCount", 0))}],
              open(OUT / "canal.json", "w", encoding="utf-8"), indent=1)

    p = OUT / "saldo.json"
    hist = json.load(open(p)) if p.exists() else []
    hist = [x for x in hist if x["data"] != hoje] + [{"data": hoje, "creditos": a.saldo, "plano": a.plano}]
    json.dump(sorted(hist, key=lambda x: x["data"]), open(p, "w"), indent=1)
    print("ok:", ", ".join(f.name for f in OUT.glob("*.json")))


if __name__ == "__main__":
    main()
