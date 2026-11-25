# EP010 · What If YOU Had to Stop an Asteroid? ☄️

- **Privado (v2):** https://www.youtube.com/shorts/yRKvGPcnUmA (67,2 s), capa aplicada com `thumbnails.set`. A v1 (I_kDWqBwOYo) é para apagar no Studio.
- **Formato livre** (pedido do dono): ~65 s, tom com humor, sem alarme. Guião do dono, narração sem alterações; a última frase ("Which means, next time an asteroid is heading for Earth…") liga à primeira (loop de frase; último frame = frame 0).
- **Base:** EP009 (estilo maquete, parallax 2.5D por profundidade). A mesma personagem (rapaz de capuz): as 7 ilustrações foram geradas com `ep009/anim/s1_queda_aviao.png` como referência.
- **Montagem:** `ep010/anim_ep010.py` · cortes de áudio `ep010/build/audio_cut.py` (silêncios para 0,10 s, 8,9 s removidos, atempo 1,10) · palavras `ep010/build/words.json` (faster-whisper + texto exato do guião, 232/232) · profundidade `ep010/build/depth.py` · capa `ep010/thumb_ep010.py` → `thumbnails/ep010_thumb.jpg` · folha de controlo `ep010/folha_controlo_ep010.jpg` (frame 0, os "genius", pop-up, último frame)

## v2 (25/11/2026, pedido do dono: "não tem profundidade nenhuma, tudo em 2D")
O dono escolheu resolver só por código (0 créditos). Cada ilustração passa a ser uma maquete em 3 camadas recortadas (`ep010/build/layers.py`: saliência rembg isnet + GrabCut guiado por zonas da personagem):
fundo (espaço, desfocado e mais escuro), objetos (asteroide, Terra, nave, foguetes) e personagem. A câmara está sempre a mexer (deriva contínua + movimentos de cada cena) e cada camada desloca-se e aproxima-se conforme a distância; cada camada projeta sombra suave na de trás; brilhos desfocados em primeiro plano. Quando o rapaz está em cima de um objeto (foguetes, pintar, Terra), ele e o objeto mexem-se juntos (sem costuras). O loop mantém-se (a deriva converge para a do frame 0).

## Créditos (saldo real 869,35 → 851,45)
| Geração | Modelo | Créditos |
|---|---|---|
| 6 ilustrações (pânico, pose de génio, foguetes, pintar, impacto da nave, alívio) | nano_banana_pro | 12 |
| Narração (1 tentativa, guião fechado, stability 0,5) | elevenlabs_v4_turbo, voz Bram | 3,9 |
| Capa v2 (rapaz a carregar no botão nuclear, asteroide em chamas) | nano_banana_pro | 2 |
| **Total** | | **17,9** |

Sem refações. Música reaproveitada (`music/track01_cosmic_ambient.mp3`, ducking; mais baixa na viragem). Efeitos sintetizados por código.

## Estrutura (tempos)
- 0 s gancho: a1 (asteroide em chamas, rapaz em pânico), "STOP IT." desde o frame 0, câmara sempre em movimento, brasas.
- Cada "And you, being a genius…" (3,8 · 13,4 · 23,8 · 35,0 s): a mesma ilustração a2 (dedo na cabeça), o mesmo enquadramento, a mesma faísca de ideia e o mesmo "ding" de ideia; carimbo "PLAN A/B/C/D". Durante cada plano, etiqueta "PLAN X · …" no topo, que leva X quando falha.
- Plano A: míssil "NUKE" → explosão → "1,000 ROCKS" a vir contra a câmara + "STILL COMING" (a1, cara de pânico).
- Plano B: a3 com setas de impulso → X; "spinning like a washing machine": o asteroide (com o rapaz e os foguetes) a girar dentro da porta de uma máquina de lavar ("SPIN 1400", "WASHING MACHINE MODE"); grande plano da cara de desilusão (a1) + X + "GOES NOWHERE".
- Plano C: a4 com raios de sol a empurrar, "IT WORKS…" com barra "OFF COURSE: 0.0001%", calendário "50 YEARS" com relógio → X; cara + "NO TIME".
- Plano D: esquema por código sobre a2 (asteroide, nave, ondas "GRAVITY", lupa "TINY") → X; cara + "DECADES".
- 44,2 s viragem: zoom lento na cara (a2), fundo escuro, música baixa, "PUSH HARDER" riscado → "PUSH EARLIER".
- 47,9 s plano E: a5 (nave pequena a bater), carimbo "PLAN E" com visto verde, "YEARS BEFORE IMPACT".
- 51,5 s a6 (rapaz aliviado sobre a Terra): trajetória vermelha para a Terra vs. verde a desviar desde o "TINY NUDGE", "THOUSANDS OF KM", "MISSED!".
- 56,5 s revelação: "2022", "NASA · DART", etiqueta na nave, "ORBIT CHANGED" → "−32 MIN" (impacto principal). Sem logótipos da NASA (nave estilizada).
- 63,3 s frase de marca (`lib/brand_scratch.py` + `lib/sfx/scratch_head.wav`, cores do rapaz).
- 64,8–66,8 s pop-up de subscrição (logo a seguir à frase de marca), sobre a cena final.
- 64,8 s final: de volta a a1, a câmara converge para a do frame 0 e o "STOP IT." reaparece no fim (último frame = frame 0; só a legenda muda).

## Áudio
19 efeitos (mais do que os ~15 da regra, porque o guião pedia o mesmo som de ideia nos 4 "genius" e um som de falhanço em cada X): 4 dings de ideia, 4 sons de falhanço, explosão baixa (nuke), 3 swishes (máquina de lavar, viragem, plano E), 4 pops (1,000 · 50 · 2022 · subscrição), batida suave no embate da nave, boom + brilho em "−32 MIN", frase de marca. Sem som ambiente contínuo. Loudness −15,6 LUFS, pico −1,4 dBTP.

## Capa
v1 (a2 + "PLAN A FAILED") rejeitada pelo dono durante a produção ("tem de ser mais impactante e o texto não puxa"). v2: ilustração própria (rapaz de olhos esbugalhados a carregar num botão nuclear vermelho, asteroide gigante em chamas atrás, Terra em baixo) + "DON'T NUKE IT!" (branco/amarelo com contorno).

## Fontes
- NASA DART (26/09/2022): embate em Dimorphos; órbita à volta de Didymos encurtada ~32 min (11 h 55 → 11 h 23).
- Efeito Yarkovsky (empurrão térmico da luz solar; muda com a refletividade da superfície).
- Trator gravitacional: Lu & Love, Nature 438, 177 (2005).

## Notas / problemas
- O Higgsfield indica "nano_banana_2" como modelo nos trabalhos pedidos como `nano_banana_pro` (preço de 2 créditos por imagem, como sempre).
- Duração 67,2 s (o dono pediu ~65 s; a regra geral do canal é 30–40 s).
- Frase de marca aos 63 s (posição do guião do dono), não nos 3–8 s da regra geral.
- O pedido de "cara de desilusão" foi feito com grandes planos da cara de pânico da a1 (sem gerar mais imagens).
