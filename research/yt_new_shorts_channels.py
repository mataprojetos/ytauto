#!/usr/bin/env python3
"""
Encontra canais do YouTube novos (1.º vídeo há <= N dias) e com bom desempenho,
focados em Shorts, em EN / ES / DE / FR.

Pipeline:
  1. search.list (100 u/pedido): vídeos curtos dos últimos N dias, order=viewCount,
     por idioma (relevanceLanguage) e região (regionCode), vários termos.
  2. channels.list (1 u / 50 canais): subscritores, n.º de vídeos, playlist de uploads.
  3. playlistItems.list (1 u / 50 vídeos): percorre a playlist de uploads; descarta o
     canal logo que encontra um vídeo publicado antes do limite (saída antecipada).
  4. videos.list (1 u / 50 vídeos): duração, visualizações, idioma do áudio.
  5. Métricas, ordenação por visualizações/dia, relatório Markdown + CSV + JSON.

Autenticação: por omissão NÃO envia a chave (o proxy do ambiente injeta o cabeçalho
X-Goog-Api-Key). Fora desse ambiente, defina YT_API_KEY.

Quota: um contador interno nunca deixa passar o teto (--max-units, por omissão 9500)
e um registo diário (quota_ledger.json, dia do Pacífico, como a Google) soma as
execuções do mesmo dia para não ultrapassar 10 000 unidades.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

API = "https://www.googleapis.com/youtube/v3"
DAILY_QUOTA = 10_000
COST = {"search": 100, "channels": 1, "playlistItems": 1, "videos": 1}

LANGS = {
    "en": {"regions": ["US", "GB"],
           "terms": ["#shorts", "funny", "satisfying", "facts", "challenge", "life hacks"]},
    "es": {"regions": ["ES", "MX"],
           "terms": ["#shorts", "humor", "curiosidades", "recetas", "retos", "datos curiosos"]},
    "de": {"regions": ["DE", "AT"],
           "terms": ["#shorts", "lustig", "fakten", "rezepte", "challenge", "lifehacks"]},
    "fr": {"regions": ["FR", "CA"],
           "terms": ["#shorts", "drôle", "astuces", "recette", "défi", "le saviez-vous"]},
}


# --------------------------------------------------------------------------- quota
class QuotaExhausted(Exception):
    pass


class Quota:
    """Contador de unidades com teto rígido e registo diário persistente."""

    def __init__(self, max_units: int, ledger_path: str):
        self.ledger_path = ledger_path
        self.day = dt.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
        self.prior = self._load().get(self.day, 0)
        self.used = 0
        # nunca passar o limite diário, contando execuções anteriores do mesmo dia
        self.cap = min(max_units, DAILY_QUOTA - self.prior)

    def _load(self) -> dict:
        try:
            with open(self.ledger_path) as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def save(self):
        data = self._load()
        data[self.day] = self.prior + self.used
        with open(self.ledger_path, "w") as f:
            json.dump(data, f, indent=2)

    @property
    def left(self) -> int:
        return self.cap - self.used

    def can(self, units: int) -> bool:
        return self.used + units <= self.cap

    def spend(self, units: int):
        if not self.can(units):
            raise QuotaExhausted(f"teto atingido ({self.used}/{self.cap})")
        self.used += units


# --------------------------------------------------------------------------- HTTP
class YT:
    def __init__(self, quota: Quota):
        self.quota = quota
        self.key = os.environ.get("YT_API_KEY")  # opcional: o proxy injeta a chave

    def get(self, endpoint: str, **params) -> dict:
        self.quota.spend(COST[endpoint])  # conta antes de pedir (pedidos falhados também gastam)
        params = {k: v for k, v in params.items() if v is not None}
        url = f"{API}/{endpoint}?{urllib.parse.urlencode(params)}"
        headers = {"Accept": "application/json"}
        if self.key:
            headers["X-Goog-Api-Key"] = self.key
        for attempt in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")
                reason = ""
                try:
                    reason = json.loads(body)["error"]["errors"][0].get("reason", "")
                except Exception:
                    pass
                if reason in ("quotaExceeded", "dailyLimitExceeded"):
                    raise QuotaExhausted("a Google indica quota diária esgotada")
                if e.code in (500, 502, 503, 504) and attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"HTTP {e.code} em {endpoint}: {body[:300]}") from None
            except urllib.error.URLError:
                if attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                raise
        raise RuntimeError("falhou após várias tentativas")


# --------------------------------------------------------------------------- utils
def parse_ts(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


_DUR = re.compile(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def iso_seconds(d: str) -> int:
    m = _DUR.fullmatch(d or "")
    if not m:
        return 0
    dd, h, mi, s = (int(x or 0) for x in m.groups())
    return dd * 86400 + h * 3600 + mi * 60 + s


def chunks(seq, n=50):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def is_short_url(video_id: str) -> bool | None:
    """Confirma Short via youtube.com/shorts/ID (200 = Short, redirect = não). 0 unidades."""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    opener = urllib.request.build_opener(NoRedirect)
    try:
        req = urllib.request.Request(f"https://www.youtube.com/shorts/{video_id}", method="HEAD",
                                     headers={"User-Agent": "Mozilla/5.0"})
        with opener.open(req, timeout=15) as r:
            return r.status == 200
    except urllib.error.HTTPError as e:
        return False if e.code in (301, 302, 303, 307, 308) else None
    except Exception:
        return None


# --------------------------------------------------------------------------- pipeline
def search_phase(yt: YT, cutoff: dt.datetime, langs: list[str], budget: int, pages: int) -> dict:
    """Devolve {channelId: {"hits": set((lang, region, term)), "title": str}}."""
    plan = [(lang, region, term)
            for lang in langs
            for region in LANGS[lang]["regions"]
            for term in LANGS[lang]["terms"]]
    max_calls = budget // COST["search"]
    print(f"[pesquisa] {len(plan)} combinações × {pages} pág. — orçamento {budget} u "
          f"({max_calls} pedidos)", file=sys.stderr)
    # intercalar por idioma para que um orçamento curto fique equilibrado
    plan.sort(key=lambda x: (LANGS[x[0]]["terms"].index(x[2]), LANGS[x[0]]["regions"].index(x[1]), x[0]))

    found: dict[str, dict] = {}
    calls = 0
    for lang, region, term in plan:
        token = None
        for _ in range(pages):
            if calls >= max_calls:
                break
            data = yt.get("search", part="snippet", type="video", videoDuration="short",
                          order="viewCount", publishedAfter=cutoff.strftime("%Y-%m-%dT%H:%M:%SZ"),
                          relevanceLanguage=lang, regionCode=region, q=term,
                          maxResults=50, pageToken=token)
            calls += 1
            for it in data.get("items", []):
                sn = it["snippet"]
                ch = found.setdefault(sn["channelId"], {"hits": set(), "title": sn["channelTitle"]})
                ch["hits"].add((lang, region, term))
            token = data.get("nextPageToken")
            if not token:
                break
    print(f"[pesquisa] {calls} pedidos, {len(found)} canais únicos", file=sys.stderr)
    return found


def channels_phase(yt: YT, ids: list[str]) -> dict:
    out = {}
    for batch in chunks(ids):
        data = yt.get("channels", part="snippet,statistics,contentDetails", id=",".join(batch),
                      maxResults=50)
        for it in data.get("items", []):
            out[it["id"]] = it
    return out


def uploads_phase(yt: YT, channel: dict, cutoff: dt.datetime, max_pages: int):
    """Lista os uploads. Devolve (video_ids, first_published) ou None se o canal for
    mais antigo que o limite (ou demasiado grande)."""
    pl = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, oldest, token = [], None, None
    for _ in range(max_pages):
        data = yt.get("playlistItems", part="contentDetails", playlistId=pl, maxResults=50,
                      pageToken=token)
        for it in data.get("items", []):
            cd = it["contentDetails"]
            ts = cd.get("videoPublishedAt")
            if not ts:  # privado/eliminado
                continue
            t = parse_ts(ts)
            if t < cutoff:
                return None  # saída antecipada: há um vídeo antigo
            ids.append(cd["videoId"])
            oldest = t if oldest is None or t < oldest else oldest
        token = data.get("nextPageToken")
        if not token:
            return (ids, oldest) if ids else None
    return None  # mais vídeos do que max_pages*50: não percorrido por inteiro


def videos_phase(yt: YT, ids: list[str]) -> list[dict]:
    out = []
    for batch in chunks(ids):
        data = yt.get("videos", part="snippet,contentDetails,statistics", id=",".join(batch),
                      maxResults=50)
        out.extend(data.get("items", []))
    return out


def metrics(channel: dict, videos: list[dict], first: dt.datetime, now: dt.datetime,
            short_max_s: int, verify: bool) -> dict:
    rows = []
    for v in videos:
        secs = iso_seconds(v["contentDetails"].get("duration", ""))
        live = v["snippet"].get("liveBroadcastContent", "none") != "none"
        short = (0 < secs <= short_max_s) and not live
        rows.append({
            "id": v["id"], "title": v["snippet"]["title"], "secs": secs, "short": short,
            "views": int(v.get("statistics", {}).get("viewCount", 0)),
            "lang": (v["snippet"].get("defaultAudioLanguage") or v["snippet"].get("defaultLanguage") or "")[:2].lower(),
        })
    if verify:  # confirma os candidatos a Short pelo URL /shorts/ (sem custo de quota)
        for r in rows:
            if r["short"]:
                ok = is_short_url(r["id"])
                if ok is False:
                    r["short"] = False
    views = [r["views"] for r in rows]
    total = sum(views)
    days = max((now - first).total_seconds() / 86400, 1.0)
    top = max(rows, key=lambda r: r["views"])
    langs = [r["lang"] for r in rows if r["lang"]]
    main_lang = max(set(langs), key=langs.count) if langs else ""
    st = channel.get("statistics", {})
    return {
        "channel_id": channel["id"],
        "title": channel["snippet"]["title"],
        "url": f"https://www.youtube.com/channel/{channel['id']}",
        "country": channel["snippet"].get("country", ""),
        "audio_lang": main_lang,
        "first_video": first.date().isoformat(),
        "days_active": round(days, 1),
        "n_videos": len(rows),
        "shorts_pct": round(100 * sum(r["short"] for r in rows) / len(rows), 1),
        "total_views": total,
        "views_per_day": round(total / days),
        "avg_views": round(statistics.mean(views)),
        "median_views": round(statistics.median(views)),
        "subscribers": None if st.get("hiddenSubscriberCount") else int(st.get("subscriberCount", 0)),
        "top_video_title": top["title"],
        "top_video_views": top["views"],
        "top_video_url": f"https://www.youtube.com/shorts/{top['id']}" if top["short"]
                         else f"https://www.youtube.com/watch?v={top['id']}",
    }


# --------------------------------------------------------------------------- report
def fmt(n) -> str:
    if n is None:
        return "oculto"
    n = float(n)
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if abs(n) >= div:
            return f"{n / div:.1f}{suf}"
    return f"{n:.0f}"


def write_report(results: list[dict], path_base: str, meta: dict):
    with open(path_base + ".json", "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "channels": results}, f, ensure_ascii=False, indent=2)
    if results:
        with open(path_base + ".csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            w.writeheader()
            w.writerows(results)

    L = [f"# Canais novos focados em Shorts — {meta['generated']}", "",
         f"- Janela: 1.º vídeo há ≤ {meta['days']} dias (desde {meta['cutoff']})",
         f"- Filtros: Shorts ≥ {meta['min_shorts_pct']}%, ≥ {fmt(meta['min_views_per_day'])} visualizações/dia",
         f"- Quota usada nesta execução: {meta['units_used']} unidades "
         f"(hoje, no total: {meta['units_today']}/{DAILY_QUOTA})",
         f"- Canais encontrados na pesquisa: {meta['candidates']} · com 1.º vídeo na janela: "
         f"{meta['new_channels']} · no relatório: {len(results)}", ""]
    for lang in meta["langs"]:
        sub = [r for r in results if lang in r["search_langs"]]
        L += [f"## {lang.upper()} ({', '.join(LANGS[lang]['regions'])}) — {len(sub)} canais", ""]
        if not sub:
            L += ["_Nenhum canal passou os filtros._", ""]
            continue
        L += ["| # | Canal | 1.º vídeo | Vídeos | % Shorts | Vis./dia | Média | Mediana | Subs | Vídeo de topo |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for i, r in enumerate(sub, 1):
            title = r["title"].replace("|", "/")
            top = r["top_video_title"].replace("|", "/")[:45]
            L.append(f"| {i} | [{title}]({r['url']}) | {r['first_video']} ({r['days_active']:.0f} d) | "
                     f"{r['n_videos']} | {r['shorts_pct']:.0f}% | **{fmt(r['views_per_day'])}** | "
                     f"{fmt(r['avg_views'])} | {fmt(r['median_views'])} | {fmt(r['subscribers'])} | "
                     f"[{top}]({r['top_video_url']}) ({fmt(r['top_video_views'])}) |")
        L.append("")
    L += ["---", "Notas: Short = duração ≤ "
          f"{meta['short_max_s']} s e não é live" + (" (confirmado pelo URL /shorts/)" if meta["verify"] else "")
          + ". Um canal pode aparecer em vários idiomas se surgiu em várias pesquisas. "
            "A playlist de uploads só inclui vídeos públicos."]
    with open(path_base + ".md", "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=21)
    ap.add_argument("--langs", default="en,es,de,fr")
    ap.add_argument("--max-units", type=int, default=9500, help="teto rígido desta execução")
    ap.add_argument("--search-budget", type=int, default=4800, help="unidades para search.list")
    ap.add_argument("--pages", type=int, default=1, help="páginas de 50 por pesquisa")
    ap.add_argument("--max-channel-videos", type=int, default=300,
                    help="ignora canais com mais vídeos do que isto (poupança de quota)")
    ap.add_argument("--min-shorts-pct", type=float, default=50)
    ap.add_argument("--min-views-per-day", type=float, default=1000)
    ap.add_argument("--short-max-seconds", type=int, default=180)
    ap.add_argument("--verify-shorts", action="store_true",
                    help="confirma Shorts via youtube.com/shorts/ID (sem quota, mais lento)")
    ap.add_argument("--out", default="relatorio_canais_shorts")
    ap.add_argument("--ledger", default="quota_ledger.json")
    a = ap.parse_args()

    langs = [l.strip() for l in a.langs.split(",") if l.strip() in LANGS]
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=a.days)
    quota = Quota(a.max_units, a.ledger)
    yt = YT(quota)
    print(f"[quota] já usado hoje (registo): {quota.prior} · teto desta execução: {quota.cap}",
          file=sys.stderr)
    if quota.cap <= 0:
        sys.exit("Sem quota disponível hoje.")

    results, new_channels, found = [], 0, {}
    try:
        # teste de ligação (1 unidade)
        yt.get("videos", part="id", id="dQw4w9WgXcQ")
        print("[ok] ligação à API", file=sys.stderr)

        found = search_phase(yt, cutoff, langs, min(a.search_budget, quota.left - 200), a.pages)
        chans = channels_phase(yt, list(found))

        # pré-filtro barato: canais grandes demais não podem ser percorridos com quota razoável;
        # ordenar por menos vídeos primeiro (mais baratos e mais prováveis de serem novos)
        cands = [c for c in chans.values()
                 if 0 < int(c["statistics"].get("videoCount", 0)) <= a.max_channel_videos]
        cands.sort(key=lambda c: int(c["statistics"]["videoCount"]))
        print(f"[canais] {len(cands)} candidatos (≤ {a.max_channel_videos} vídeos)", file=sys.stderr)

        max_pages = -(-a.max_channel_videos // 50)
        for i, ch in enumerate(cands, 1):
            need = -(-int(ch["statistics"]["videoCount"]) // 50) * 2 + 1  # uploads + videos
            if not quota.can(need):
                print(f"[quota] a parar na fase de canais ({i - 1}/{len(cands)} vistos)", file=sys.stderr)
                break
            up = uploads_phase(yt, ch, cutoff, max_pages)
            if not up:
                continue
            ids, first = up
            new_channels += 1
            vids = videos_phase(yt, ids)
            if not vids:
                continue
            m = metrics(ch, vids, first, now, a.short_max_seconds, a.verify_shorts)
            m["search_langs"] = sorted({h[0] for h in found[ch["id"]]["hits"]})
            m["search_regions"] = sorted({h[1] for h in found[ch["id"]]["hits"]})
            m["search_terms"] = sorted({h[2] for h in found[ch["id"]]["hits"]})
            if m["shorts_pct"] >= a.min_shorts_pct and m["views_per_day"] >= a.min_views_per_day:
                results.append(m)
                print(f"  + {m['title'][:40]:40} {fmt(m['views_per_day']):>7}/dia "
                      f"{m['shorts_pct']:.0f}% Shorts", file=sys.stderr)
    except QuotaExhausted as e:
        print(f"[quota] {e} — a gerar relatório com o que já foi recolhido", file=sys.stderr)
    finally:
        quota.save()

    results.sort(key=lambda r: r["views_per_day"], reverse=True)
    for r in results:
        for k in ("search_langs", "search_regions", "search_terms"):
            r[k] = ",".join(r[k])
    meta = {
        "generated": now.strftime("%Y-%m-%d %H:%M UTC"), "days": a.days,
        "cutoff": cutoff.date().isoformat(), "langs": langs,
        "min_shorts_pct": a.min_shorts_pct, "min_views_per_day": a.min_views_per_day,
        "short_max_s": a.short_max_seconds, "verify": a.verify_shorts,
        "units_used": quota.used, "units_today": quota.prior + quota.used,
        "candidates": len(found), "new_channels": new_channels,
    }
    write_report(results, a.out, meta)
    print(f"\n[fim] {len(results)} canais · {quota.used} unidades usadas "
          f"(hoje: {quota.prior + quota.used}/{DAILY_QUOTA}) · {a.out}.md/.csv/.json", file=sys.stderr)


if __name__ == "__main__":
    main()
