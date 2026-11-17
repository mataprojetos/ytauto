#!/usr/bin/env python3
"""Whatifaholic — upload de um Short para o YouTube (API Data v3, upload resumível).

Segurança por omissão:
  * o vídeo fica PRIVADO, a menos que passes --public explicitamente;
  * --dry-run valida tudo (ficheiro, formato Shorts, limites do YouTube) sem enviar nada;
  * --whoami mostra em que canal vai publicar (precisa de autorização OAuth), sem enviar nada.

Autenticação (por ordem):
  1. YT_ACCESS_TOKEN                            -> token de acesso (dura ~1 h)
  2. GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET + YT_REFRESH_TOKEN -> renova o token sozinho
  3. nada                                       -> assume que o ambiente (proxy) injeta o cabeçalho Authorization

Uso:
  python3 yt_upload.py --whoami
  python3 yt_upload.py --video ep001/whatifaholic_ep001_moon.mp4 --metadata ep001/publish/metadata.json --dry-run
  python3 yt_upload.py --video ... --metadata ...                 # privado
  python3 yt_upload.py --video ... --metadata ... --public        # só quando já revisto
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

import requests

HOST = os.environ.get("YT_API_HOST", "www.googleapis.com")  # youtube.googleapis.com também serve a API
API = f"https://{HOST}/youtube/v3"
UPLOAD = f"https://{HOST}/upload/youtube/v3/videos"
TOKEN_URL = "https://oauth2.googleapis.com/token"
CHUNK = 8 * 1024 * 1024  # múltiplo de 256 KiB, como exige o upload resumível


def auth_headers() -> dict:
    tok = os.environ.get("YT_ACCESS_TOKEN")
    cid, sec, rt = (os.environ.get(k) for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "YT_REFRESH_TOKEN"))
    if not tok and cid and sec and rt:
        r = requests.post(TOKEN_URL, data={"client_id": cid, "client_secret": sec, "refresh_token": rt,
                                           "grant_type": "refresh_token"}, timeout=30)
        r.raise_for_status()
        tok = r.json()["access_token"]
    return {"Authorization": f"Bearer {tok}"} if tok else {}


def ffprobe(path: str) -> dict:
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height:format=duration,size", "-of", "json", path])
    j = json.loads(out)
    return {"w": j["streams"][0]["width"], "h": j["streams"][0]["height"],
            "dur": float(j["format"]["duration"]), "size": int(j["format"]["size"])}


def validate(meta: dict, video: str) -> list[str]:
    errs = []
    sn, st = meta.get("snippet", {}), meta.get("status", {})
    title, desc, tags = sn.get("title", ""), sn.get("description", ""), sn.get("tags", [])
    if not title or len(title) > 100:
        errs.append(f"título inválido ({len(title)} caracteres; máx. 100)")
    if "<" in title + desc or ">" in title + desc:
        errs.append("título/descrição não podem conter < ou >")
    if len(desc.encode("utf-8")) > 5000:
        errs.append(f"descrição com {len(desc.encode('utf-8'))} bytes (máx. 5000)")
    tag_len = sum(len(t) + (2 if " " in t else 0) for t in tags) + max(0, len(tags) - 1)
    if tag_len > 500:
        errs.append(f"etiquetas com {tag_len} caracteres (máx. 500)")
    if st.get("selfDeclaredMadeForKids") is not False:
        errs.append("selfDeclaredMadeForKids tem de ser false (canal não é para crianças)")
    if not os.path.isfile(video):
        errs.append(f"ficheiro não encontrado: {video}")
    else:
        p = ffprobe(video)
        if p["w"] > p["h"]:
            errs.append(f"formato horizontal ({p['w']}x{p['h']}); um Short tem de ser vertical ou quadrado")
        if p["dur"] > 180:
            errs.append(f"duração {p['dur']:.0f}s; os Shorts vão até 180 s")
    return errs


def whoami() -> None:
    r = requests.get(f"{API}/channels", params={"part": "snippet,statistics", "mine": "true"},
                     headers=auth_headers(), timeout=30)
    if r.status_code != 200:
        sys.exit(f"HTTP {r.status_code}: {r.text[:400]}")
    items = r.json().get("items", [])
    if not items:
        sys.exit("A conta autorizada não tem canal.")
    c = items[0]
    print(f"Canal autorizado: {c['snippet']['title']} ({c['snippet'].get('customUrl', 'sem @')}) "
          f"· id {c['id']} · {c['statistics'].get('subscriberCount', '?')} subscritores")


def upload(video: str, meta: dict) -> dict:
    size = os.path.getsize(video)
    h = {**auth_headers(), "Content-Type": "application/json; charset=UTF-8",
         "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)}
    r = requests.post(UPLOAD, params={"uploadType": "resumable", "part": "snippet,status"},
                      headers=h, data=json.dumps(meta), timeout=60)
    if r.status_code != 200:
        sys.exit(f"Falha ao iniciar o upload: HTTP {r.status_code}: {r.text[:500]}")
    session = r.headers["Location"]
    sent = 0
    with open(video, "rb") as f:
        while sent < size:
            f.seek(sent)
            chunk = f.read(CHUNK)
            end = sent + len(chunk) - 1
            for attempt in range(6):
                try:
                    resp = requests.put(session, data=chunk, timeout=300, headers={
                        "Content-Length": str(len(chunk)), "Content-Range": f"bytes {sent}-{end}/{size}",
                        "Content-Type": "video/mp4"})
                except requests.RequestException:
                    resp = None
                if resp is not None and resp.status_code in (200, 201):
                    return resp.json()
                if resp is not None and resp.status_code == 308:
                    rng = resp.headers.get("Range")  # bytes=0-N
                    sent = int(rng.split("-")[1]) + 1 if rng else 0
                    break
                if resp is not None and resp.status_code not in (500, 502, 503, 504):
                    sys.exit(f"Upload falhou: HTTP {resp.status_code}: {resp.text[:500]}")
                time.sleep(2 ** attempt)
                q = requests.put(session, headers={"Content-Length": "0", "Content-Range": f"bytes */{size}"}, timeout=60)
                if q.status_code in (200, 201):
                    return q.json()
                if q.status_code == 308:
                    rng = q.headers.get("Range")
                    sent = int(rng.split("-")[1]) + 1 if rng else 0
                    break
            else:
                sys.exit("Upload falhou após várias tentativas.")
            print(f"  enviado {min(sent, size) / 1e6:.1f}/{size / 1e6:.1f} MB", file=sys.stderr)
    sys.exit("Upload terminou sem resposta final do YouTube.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video")
    ap.add_argument("--metadata")
    ap.add_argument("--public", action="store_true", help="publica logo (por omissão fica privado)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--whoami", action="store_true")
    ap.add_argument("--log", default="uploaded.json")
    a = ap.parse_args()

    if a.whoami:
        whoami(); return
    if not (a.video and a.metadata):
        ap.error("--video e --metadata são obrigatórios")
    meta = json.load(open(a.metadata, encoding="utf-8"))
    meta.setdefault("status", {})["privacyStatus"] = "public" if a.public else "private"
    errs = validate(meta, a.video)
    p = ffprobe(a.video) if os.path.isfile(a.video) else {}
    print(f"Vídeo: {a.video} · {p.get('w')}x{p.get('h')} · {p.get('dur', 0):.1f}s · {p.get('size', 0) / 1e6:.1f} MB")
    print(f"Título ({len(meta['snippet']['title'])}): {meta['snippet']['title']}")
    print(f"Visibilidade: {meta['status']['privacyStatus']} · categoria {meta['snippet'].get('categoryId')}"
          f" · IA sintética: {meta['status'].get('containsSyntheticMedia')}")
    if errs:
        sys.exit("ERROS:\n - " + "\n - ".join(errs))
    if a.dry_run:
        print("Validação OK (dry-run: nada foi enviado)."); return
    res = upload(a.video, meta)
    vid = res["id"]
    print(f"ENVIADO: https://www.youtube.com/shorts/{vid} (estado: {res['status'].get('privacyStatus')})")
    log = []
    if os.path.exists(a.log):
        log = json.load(open(a.log))
    log.append({"id": vid, "title": meta["snippet"]["title"], "privacy": res["status"].get("privacyStatus"),
                "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    json.dump(log, open(a.log, "w"), indent=2)


if __name__ == "__main__":
    main()
