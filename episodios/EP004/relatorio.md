# EP004 · What If GTA Happened in Space?

- **Vídeo:** 45,9 s, privado, com capa (`thumbnails/ep004_thumb.jpg`): https://www.youtube.com/shorts/p4CLvBy1eSY
- **Montagem:** `ep004/anim_ep004.py` (+ `ep004/neuro_lib.py`) · narração `ep004/audio/narration.wav` (Bram) · corte de pausas `ep004/build/cut_pauses.py` · palavras `ep004/build/words_ep004.json` (`build/transcribe.py`, faster-whisper small.en; tempos de "Five stars. Wanted… literally." corrigidos à mão pela energia do áudio) · capa `ep004/build/thumb.py` · `thumbnails.set` com espera pelo processamento `ep004/build/set_thumb.py` · folha de controlo `ep004/build/folha_controlo.jpg`
- Guião aprovado pelo dono, narração sem alterações.

## Créditos (20/11/2026)
| Geração | Modelo | Créditos |
|---|---|---|
| Astronauta de referência ao comando do foguetão | nano_banana_pro | 2 |
| 6 cenas com a 1.ª como referência (polícia a flutuar, foguetão atrás do caixote, rádio, bomba em Marte, Lua + satélite-radar, multa a chegar a casa) | nano_banana_pro | 12 |
| Capa (astronauta ao volante, polícia atrás) | nano_banana_pro | 2 |
| Narração (uma vez, guião fechado) | elevenlabs_v4_turbo, voz Bram | 2,40 |
| **Total** | | **18,40** (saldo 1 648,93 → 1 630,53) |

8 imagens no total, 0 refações. Música reutilizada (`music/track01_cosmic_ambient.mp3`). Motor de foguetão, alarme de dois tons, sirene genérica, estática, flash/obturador, pops, dings e swish sintetizados por código (ffmpeg).

## Direitos
Título menciona GTA; no vídeo e na capa nada do jogo (sem logótipo, personagens, arte, tipografia, mapas, música ou sons). Estrelas de procurado desenhadas por código (5 pontas simples), tipografia Inter Display. Descrição: "An imagined scenario, just for fun. Not affiliated with Rockstar Games."

## Fórmula aplicada
- 0 s: motor de foguetão + alarme de dois tons + bordas vermelhas a piscar; 5 estrelas acendem uma a uma em "Five stars. Wanted…", selo "WANTED"; no fim de "literally" (~4,0 s) as estrelas sobem e viram estrelas do céu (twinkle).
- Selo "THE TWIST · COMING UP" de ~4,6 s até "Then the twist" (32,6 s).
- Cenas: polícia a flutuar com sirenes azul/vermelha e "POLICE SPEED: 0.00010 KM/H", "ZERO GRAVITY", setas a rodar em "going nowhere"; holofote, NO ALLEYS / NO GARAGES riscados, seta "VERY OBVIOUS"; contador 0 → 28,000 KM/H com linhas de velocidade e carimbo "BAD IDEA"; estática no rádio, notas a desaparecer, "NO SOUND IN SPACE · 0 dB"; placa "GAS · LAST STOP", "NEAREST: MARS", placa "7 MONTHS · NEXT FUEL", medidor de combustível em E; Lua: "ESCAPED!" → "SPEED CAMERA", feixe vermelho e flash branco; multa "SPEEDING FINE · Location: The Moon · Send to: Mom" com carimbo "PAY NOW".
- Dings: "going nowhere", "very obvious spaceship", "Bad idea", "sing along", "bathroom", "your mom's house".
- Pop-up de subscrição (`lib/subscribe_popup.py`) logo a seguir a "your mom's house" (39,6–42,1 s, ~86 %); sobrepõe-se ao início da pergunta (sem pausa na narração).
- Pergunta A/B (A ROCKET / THE STATION) sobre o astronauta; último frame idêntico ao primeiro (diferença de píxeis 0 no render).
- Pausas ≤0,12 s e voz +10 % (atempo): narração 58,5 s → 44,9 s. Loudness −16,8 LUFS, pico −1,3 dBFS.

## Notas
- Capa aplicada só depois de `processingStatus = succeeded` (lição do EP003): `thumbnails.set` 200.
- Fontes na descrição: velocidade orbital ~28 000 km/h, viagem a Marte ~7 meses, som não se propaga no vácuo (NASA).
