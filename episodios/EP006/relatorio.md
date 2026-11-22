# EP006 · What If You Fell Into a Black Hole?

**Teste só código** (pedido do dono): animação, capa e sons feitos 100 % por código (pycairo + numpy/ffmpeg), sem imagens geradas no Higgsfield. Tom imersivo, calmo, na primeira pessoa.

- **Privado:** https://www.youtube.com/shorts/QoJLgJB3rzs (38,7 s) · capa aplicada e confirmada (versão vertical do feed de Shorts)
- **Montagem:** `ep006/anim_ep006.py` · cortes de áudio `ep006/build/audio_cut.py` · capa `ep006/thumb_ep006.py` → `thumbnails/ep006_thumb.jpg` · folha de controlo `ep006/folha_controlo_ep006.jpg` (inclui frame 0 e último frame)

## Créditos (22/11/2026, saldo real 1 626,25 → 1 624,30)
| Geração | Modelo | Créditos |
|---|---|---|
| Narração (1 tentativa, guião aprovado, stability 0,6) | elevenlabs_v4_turbo, voz Bram | 1,95 |
| **Total** | | **1,95** |

Zero imagens geradas. Música reaproveitada (`music/track01_cosmic_ambient.mp3`, com passa-baixo). Grave ambiente, swish, whoosh, pop, tiques, boom e brilho sintetizados por código; som da frase de marca `lib/sfx/scratch_head.wav`; assinatura visual `lib/brand_scratch.py` (reutilizados do EP005).

## Estrutura (tempos)
Gancho 0–4,3 s (já a cair: buraco negro a crescer, estrelas a deslizar e curvar, disco a rodar, HUD do capacete "DISTANCE TO THE EDGE" a contar até 0 na borda) · "4,000,000× heavier than the Sun" com o Sol minúsculo · frase de marca 7,6 s · lente: estrelas a curvar, anel de Einstein · anel de fogo 11,8 s · "Turn your head": pan de câmara → nuca do astronauta dentro do anel ("THAT'S YOU") · raio de luz a dar a volta (360°) · relógios YOU (normal) vs EARTH (ponteiros a voar, YEAR 2026→…) · borda 24,2 s: a escuridão enche o ecrã, "EVENT HORIZON" passa, silêncio súbito no grave e na música · pop-up de subscrição 25,6 s (sobre o escuro, sem tapar o anel) · selo "WHAT'S INSIDE · COMING UP" 27,8–30,5 s · revelação: todas as linhas/setas curvam para o centro, "NO WAY BACK" 34,6 s, raio de luz que tenta sair e volta, "NOT EVEN LIGHT" 36 s · "Which means, right now…": a escuridão do centro enche o ecrã e nos últimos 0,42 s encolhe até à sombra do frame 0 (último frame = abertura em t = −1/30 s, movimento contínuo). Sem pedido de comentário (pedido do dono).

## Áudio
Atempo 1,06 (mais calmo do que o habitual +10 %, como o dono permitiu). Pausas por pontuação, cortes só em silêncio com palavras protegidas (método do EP005): fim de frase ~0,27 s, reticências ~0,34 s, vírgula ~0,17 s. Verificado pelo Whisper: 123/123 palavras.

## Fontes
- NASA, black holes (Sgr A* ≈ 4 milhões de massas solares; horizonte de eventos): https://science.nasa.gov/universe/black-holes/
- Event Horizon Telescope, imagem de Sgr A*: https://eventhorizontelescope.org/blog/astronomers-reveal-first-image-black-hole-heart-our-galaxy

## Notas / problemas
- O Whisper (com initial_prompt) saltou os primeiros 7,7 s; sem prompt e sem condicionamento transcreveu tudo (`build/align2.py`).
- `yt_upload.py` dava falso erro na capa de vídeos privados: o `i.ytimg.com/.../sardefault.jpg` público dá 404 enquanto o vídeo é privado. Agora verifica o URL assinado `shortsAspectRatio` da API (confirmado: imagem 1080×1920 = a nossa capa).
- `registo.csv` deste ramo não tinha EP002–EP004 (estão noutros ramos): linhas repostas a partir do painel; `painel_dados.py` aceita durações decimais.
- Física simplificada: "years flying by" vale para relógios longe do buraco negro vs o teu, perto do horizonte; a descrição fala em dilatação gravitacional do tempo.
