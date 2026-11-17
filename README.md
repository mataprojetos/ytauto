# Whatifaholic: fábrica de Shorts

Canal de YouTube Shorts **Whatifaholic** (@whatifaholics): perguntas "What if…?" sobre ciência, dinheiro, tecnologia e IA, explicadas em animação, com factos verificados e humor.

## Estrutura

| Pasta / ficheiro | O que é |
| --- | --- |
| `research/yt_new_shorts_channels.py` | Pesquisa de canais novos de Shorts com bom desempenho (YouTube Data API, respeita a quota de 10 000 unidades/dia) |
| `research/relatorio_canais_shorts.*` | Relatório da pesquisa (32 canais, 16/11/2026) |
| `ep001/neuro_lib.py` | Biblioteca de desenho partilhada: camadas, Terra, Lua, texto, brilho (pycairo) |
| `ep001/anim_ep001_v5.py` | Montagem do episódio #001: cenas presas às frases da narração, transições, legendas, som |
| `ep001/script_v3.txt` | Guião (fórmula de retenção: loops abertos, piadas, pergunta final, loop) |
| `ep001/audio/narration_v4.wav` | Narração final (pausas cortadas, +10% de velocidade, gancho da contagem) |
| `ep001/build/words_v4.json` | Tempos de cada palavra (faster-whisper), usados para sincronizar cenas e legendas |
| `ep001/anim/*.png` | Ilustrações do estilo animado |
| `ep001/publish/metadata.json` | Título, descrição (com fontes), etiquetas e definições do upload |
| `ep001/whatifaholic_ep001_moon_v6.mp4` | Vídeo final do episódio #001, v6 (1080×1920, 48 s, alarme no gancho), montado por `ep001/anim_ep001_v6.py` |
| `ep001/whatifaholic_ep001_moon.mp4` | Versão antiga de 80 s (v5), só como referência |
| `yt_upload.py` | Upload para o YouTube (resumível, privado por omissão, `--dry-run`, `--whoami`) |
| `music/` | Biblioteca de música reutilizável |
| `branding/` | Fotos de perfil e banner do canal |
| `assets_legacy/` | Imagens do estilo fotográfico antigo (não usado) |

## Requisitos do sistema

- Python 3.11+ e `pip install -r requirements.txt`
- `ffmpeg` com `libass` (legendas)
- Tipo de letra **Inter / Inter Display** instalado

## Montar o episódio

```bash
python3 ep001/anim_ep001_v5.py
```

## Publicar

O script lê as credenciais de variáveis de ambiente. **Nunca as escrevas em ficheiros deste repositório.**

| Variável | Para quê |
| --- | --- |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `YT_REFRESH_TOKEN` | Autorização OAuth duradoura (renova o token sozinho) |
| `YT_ACCESS_TOKEN` | Alternativa temporária (1 hora) |
| `YT_API_HOST` | Opcional: `youtube.googleapis.com` em vez de `www.googleapis.com` |

```bash
python3 yt_upload.py --whoami
python3 yt_upload.py --video ep001/whatifaholic_ep001_moon.mp4 --metadata ep001/publish/metadata.json --dry-run
python3 yt_upload.py --video ep001/whatifaholic_ep001_moon.mp4 --metadata ep001/publish/metadata.json
```

O vídeo fica **privado** a menos que se passe `--public`.
