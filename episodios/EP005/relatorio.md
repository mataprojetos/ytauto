# EP005 · What If You Got $1 Every Time You Blinked?

**Teste só código** (pedido do dono): animação, capa e efeitos sonoros feitos 100 % por código (pycairo + numpy/ffmpeg), sem imagens geradas no Higgsfield.

- **Vídeo:** 38,3 s, privado: https://www.youtube.com/shorts/yZtfk_Y9ydQ (capa aplicada com `thumbnails.set`)
- **Montagem:** `ep005/anim_ep005.py` · capa `ep005/thumb_ep005.py` → `thumbnails/ep005_thumb.jpg` · folha de controlo `ep005/folha_controlo_ep005.jpg`
- **Áudio:** `ep005/build/audio_prep.py` + `audio_cut2.py` (pausas ≤0,12 s, tosse sintetizada com pausa cómica ~0,4 s entre "of…" e "black pepper", atempo 1.1)

## Créditos (21/11/2026)
| Geração | Modelo | Créditos |
|---|---|---|
| Narração (1 tentativa) | elevenlabs_v4_turbo, voz Bram | 2,25 |
| Imagens | — (só código) | 0 |
| **Total** | | **2,25** (saldo 1 630,53 → 1 628,28) |

Música reaproveitada (`music/track01_cosmic_ambient.mp3`). Alarme, ka-ching, tosse, swish, pop, ding e som da frase de marca sintetizados por código.

## Novo em `lib/` (reutilizável)
- `lib/brand_sfx.py` + `lib/sfx/scratch_head.wav`: **som fixo da frase de marca** (três arranhadelas + "tok"), mais `cough.wav` e `kaching.wav`.
- `lib/brand_scratch.py`: **assinatura visual da frase de marca** (cabeça com mão a coçar + "?"), cores por parâmetro.

## Estrutura (tempos)
Gancho 0–2,9 s (olho a piscar, "$1 PER BLINK", contador $3 ao ~0,8 s, alarme + bordas vermelhas até $3) · 15/min · frase de marca 4,9 s · $900/h + sofá · RENT PAID ✓ · $14,400 à noite · reunião de segunda (piada) · selo "YEAR TOTAL · COMING UP" 16,8–31,3 s · cama "0 $/h" · despertador de gravata (piada) · pop-up de subscrição 23,5 s (61 %, logo após "boss", para não atropelar o número final) · espirros + pimenteiro, tosse, "BLACK PEPPER", "FREE MONEY" · calendário 1→365 e $5,256,000 com confetes (31,3 s) · "BLINK OR SNEEZE? ONE WORD." · loop (último frame = primeiro).

## Fontes
- Taxa média de piscar ~15/min (13–20 conforme estudo/atividade): Healthline; PMC9899223 (média ~16/min).
- Olhos fecham por reflexo ao espirrar: Live Science.

## Notas do teste
- Ritmo: mudança visual a cada ~1–2 s conseguida só com formas vetoriais; o render completo leva ~2 min no contentor.
- Limitações: personagens simples (estilo plano/ícone), menos "wow" que ilustrações geradas; a capa é vetorial.
- Pop-up a 61 % e não a 70–75 %: a zona dos 70–75 % é a piada da pimenta e o número final (escolha dada pelo dono).
- O Whisper juntou "black" à tosse e "Free money": tempos corrigidos à mão no script.
