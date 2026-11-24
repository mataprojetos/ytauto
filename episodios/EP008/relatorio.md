# EP008 · What If You Jumped Into a Hole Through the Earth?

- **Privado (v2, som limpo):** https://www.youtube.com/shorts/wsYw5ghP6eA (39,2 s)
- **Apagar no Studio:** v1 https://www.youtube.com/shorts/n1jCVaDkhkw
- **v2:** capa aplicada e confirmada (personalizada + versão vertical do feed de Shorts)
- **Montagem:** `ep008/anim_ep008.py` (base do EP007) · cortes de áudio `ep008/build/audio_cut.py` · palavras `ep008/build/words.json` (faster-whisper + pontuação do guião, `build/fix_words.py`, 130/130 palavras) · recorte do boneco `ep008/build/sprite.py` · oceano sem boneco `ep008/build/ocean_clean.py` · profundidade `ep008/build/depth.py` · capa `ep008/thumb_ep008.py` → `thumbnails/ep008_thumb.jpg` · folha de controlo `ep008/folha_controlo_ep008.jpg` (frame 0, pop-up, último frame)
- Guião aprovado pelo dono, narração sem alterações. Sem pedido de comentário. Loop de frase "Which means, right now…" → "You just jumped…".

## Créditos (24/11/2026, saldo real 1 126,45 → 1 114,20)
| Geração | Modelo | Créditos |
|---|---|---|
| Narração (1 tentativa, guião fechado, stability 0,5) | elevenlabs_v4_turbo, voz Bram | ~2,25 |
| 4 ilustrações: quintal americano visto de cima com o poço (frame 0), Terra em corte com o túnel, boneco sem peso no núcleo, saída no Índico (referência de estilo: `ep007/anim/city.png`, só estilo) | nano_banana_pro | 8 |
| Imagem da capa (boneco a cair no túnel, núcleo ao fundo) | nano_banana_pro | 2 |
| **Total** | | **12,25** |

Sem refações. Música reaproveitada (`music/track01_cosmic_ambient.mp3`, com ducking). Alarme de dois tons, swish, whoosh, pop, ding, brilho e boom sintetizados por código; som da frase de marca `lib/sfx/scratch_head.wav` e assinatura visual `lib/brand_scratch.py`.

## Estrutura (tempos)
- 0 s gancho: quintal visto de cima, o boneco já a cair no poço (frame 0); alarme de dois tons + bordas vermelhas até 2,9 s; "12,742 KM · STRAIGHT DOWN" (0,25 s); a câmara mergulha atrás do boneco (o boneco é recortado da ilustração e animado: encolhe, roda e escurece).
- 2,9 s Terra em corte: a câmara começa à boca do túnel e afasta-se; piada "THAT 'MISSED A STAIR' FEELING…"; "NO BOTTOM" (5,9 s).
- 6,3 s frase de marca (mão a coçar a cabeça + som).
- 7,8 s "MAGIC TUNNEL" com brilhos, chips "NO AIR" / "NO HEAT" riscados.
- 10,7 s a câmara desce ao núcleo: termómetro + "5,000°C · INNER CORE".
- 13,6 s túnel em perspetiva por código (anéis de rocha a passar, linhas de velocidade), velocímetro a subir até "28,000 KM/H" (17,1 s, flash + boom), mini-mapa da Terra com o ponto a descer, "CENTER OF THE EARTH".
- 19,1 s boneco sem peso no núcleo (ilustração), piada "YOUR PHONE: 'NO SIGNAL'", "WEIGHTLESS".
- 21,0 s esquema: o boneco passa o centro e as setas da gravidade invertem-se (dourado → vermelho), "GRAVITY FLIPS", "PULLING YOU BACK".
- 23,4–26,0 s pop-up de subscrição (antes de "But wait").
- 24,2 s túnel a abrandar, velocímetro a descer; piada "LIKE THE LAST HOUR BEFORE THE WEEKEND".
- 26,0 s globo a girar com "?"; selo "WHERE YOU END UP · COMING UP" de "wait" (26,2 s) até à revelação (31,4 s).
- 27,9 s globo: pin USA, linha através da Terra, relógio "42 MIN", rotação até ao antípoda.
- 31,4 s revelação: Índico, "INDIAN OCEAN · SW OF AUSTRALIA" (boom), temporizador "1 s".
- 34,8 s vaivém pelo túnel com contador "TRIP #n" → "FOREVER ∞"; piada "LIKE HITTING SNOOZE".
- 37,8 s "Which means, right now…": o boneco volta a cair no buraco do oceano e nos últimos 0,5 s o quintal do frame 0 abre-se (último frame = frame 0, diferença 0/255 no render de teste).

Câmara sempre em movimento (parallax 2.5D por profundidade nas 4 ilustrações, zooms, pans).

## Áudio
**v2 (pedido do dono, 24/11/2026):** o início estava confuso e os efeitos repetitivos cansavam. Tirados o alarme de dois tons e as bordas vermelhas do gancho; efeitos reduzidos de ~40 para 13: um whoosh suave no início, 3 swishes (só nas grandes mudanças), frase de marca, um vento contínuo e grave durante a queda (em vez de whooshes repetidos), 3 pops (5,000 · 28,000 · toque da subscrição) + 1 no relógio de 42 min, whoosh antes de "But wait", boom + brilho só na revelação do Índico e whoosh de saída para o loop. Sem dings nas piadas. Volumes mais baixos.

Pausas cortadas por energia (silêncios abaixo de −36 dB do pico encurtados para 0,08 s, 9,0 s removidos) e atempo 1,10. Duração 39,2 s.

## Fontes
- Física clássica do "gravity tunnel" (Terra uniforme, sem ar): ~42 min de queda, ~7,9 km/s no centro.
- Núcleo interno acima de 5 000 °C (USGS / NASA).
- Antípoda dos EUA: oceano Índico, a sudoeste da Austrália.

## Notas / problemas
- O Higgsfield devolve os trabalhos `nano_banana_pro` com o rótulo `nano_banana_2` (como no EP007).
- O boneco do frame 0 foi recortado da própria ilustração (fundo do poço quase preto) para poder ser animado; o poço ficou limpo por preenchimento. No oceano, o boneco desenhado foi apagado só na versão usada no mergulho final.
- Pausas mais curtas do que no EP007 (0,08 s) para ficar abaixo dos 40 s sem mexer no guião.
