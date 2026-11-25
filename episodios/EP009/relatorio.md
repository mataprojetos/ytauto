# EP009 · What If You Fell Out of a Plane Without a Parachute?

- **Privado (v3):** https://www.youtube.com/shorts/Lcj71XgslJw (48,2 s), capa aplicada e confirmada (personalizada + versão vertical do feed de Shorts)
- **Formato livre** (pedido do dono): até ~60 s, sem alarme no gancho, tom com humor. Guião do dono, narração sem alterações.
- **Montagem:** `ep009/anim_ep009.py` (base do EP008) · cortes de áudio `ep009/build/audio_cut.py` (silêncios encurtados para 0,10 s, 7,2 s removidos, atempo 1,10) · palavras `ep009/build/words.json` (faster-whisper + texto exato do guião, `build/fix_words.py`, 171/171) · profundidade `ep009/build/depth.py` · capa `ep009/thumb_ep009.py` → `thumbnails/ep009_thumb.jpg` · folha de controlo `ep009/folha_controlo_ep009.jpg` (frame 0, pop-up, último frame)

## Créditos (saldo real 882,20 → 879,35 nesta sessão)
| Geração | Modelo | Créditos |
|---|---|---|
| 3 ilustrações-chave aprovadas (avião, estrela, piloto na neve), sessão anterior | nano_banana_pro | ~6 |
| Narração (1 tentativa, guião fechado, stability 0,5) | elevenlabs_v4_turbo, voz Bram | 2,85 |
| Capa | — (ilustração s1 + texto por código) | 0 |
| **Total** | | **~8,85** |

Sem refações. Música reaproveitada (`music/track01_cosmic_ambient.mp3`, com ducking). Efeitos sintetizados por código.

## Estrutura (tempos)
- 0 s gancho: s1 já em queda (câmara a tremer/rodar, parallax 2.5D), cronómetro 3:00.00 a descer desde o frame 0, "NO PARACHUTE" (1,5 s).
- 5,3 s código: altímetro "10 KM", termómetro "-50°C" com geada nos cantos, barra "AIR" a esvaziar; o boneco desmaia (pálpebras, "Zzz"), cartão "BEST NAP OF YOUR LIFE"; acorda com "!" e o altímetro desce.
- 13,9 s s2 com parallax: velocímetro fixa em "200 KM/H", "TOP SPEED", estrela tracejada à volta do boneco + "STARFISH MODE", setas "AIR PUSHES BACK".
- 20,7 s menu "PICK YOUR LANDING": água com X desenhado → cimento (fissuras) + "SPLASH? MORE LIKE CRUNCH"; neve, árvores, colina fofa com vistos + "LIKE YOUR BED ON A MONDAY MORNING"; "IMPOSSIBLE?".
- 28,2 s s3: "1944", "18,000 FT FALL", "PINE TREES" / "DEEP SNOW", "DAMAGE: 1 SPRAINED LEG".
- 35,4 s frase de marca (`lib/brand_scratch.py` + `lib/sfx/scratch_head.wav`).
- 36,8–39,4 s pop-up de subscrição no topo (logo depois da frase de marca, sobre o início da cena de 1972).
- 36,8 s código: "1972", régua de altitude a subir até 10,160 M, Everest como referência, "HIGHER THAN EVEREST", "SHE SURVIVED", troféu "WORLD RECORD" (boom + brilho). Sem acidente nem destroços.
- 44,6 s de volta à s1 com a lista "FALL PLAN" a marcar; em "…if you…" a câmara volta continuamente à do frame 0 e o cronómetro reaparece em 3:00.00 (último frame = frame 0, diferença 0 no render de teste).

## v3 (25/11/2026, pedido do dono)
O dono apagou a v2 (CmjneUs37Xg): personagens sem coerência (boneco desenhado por código, outro rapaz na estrela, piloto) e "uma pessoa por cima de uma imagem". Agora o rapaz do avião (s1) aparece do início ao fim, sempre dentro das ilustrações:
- 5 ilustrações novas nano_banana_pro com a s1 como referência: `anim/v3_frio.png` (a tremer a 10 km), `v3_sono.png` (a dormir no ar; dissolve frio → sono → frio), `v3_estrela.png` (estrela-do-mar sobre montanhas), `v3_escolha.png` (visto de cima a escolher: lago, neve, pinheiros, colina), `v3_pensa.png` (a cair com um balão de pensamento vazio).
- Menu de aterragem desenhado em cima da própria paisagem (marcas nos sítios; o lago da ilustração passa a cimento por máscara).
- 1944 (ilustração s3 do piloto) e 1972 (régua de altitude, Everest, troféu) aparecem dentro do balão de pensamento do rapaz (escolha do dono). Frase de marca com as cores do rapaz.
- Pop-up de subscrição por baixo do rapaz (o balão ocupa o topo). Sem dings (regra do canal).
- Créditos v3: 10 (5 imagens; 3 tentativas falharam no servidor e não foram cobradas). Saldo 879,35 → 869,35. **Total do episódio: ~18,85.**

## v2 (25/11/2026, pedido do dono)
O dono apagou a v1 (L0KWjrkJWWk): o som de fundo afastava as pessoas. Tirado o vento contínuo e baixada a música (0,2 → 0,12, com ducking); efeitos e imagem iguais. Capa com o texto ao centro (como no EP007). Sem créditos extra.

## Áudio (v1)
Vento contínuo do princípio ao fim, com volume/brilho a seguir a velocidade (baixa no desmaio, máximo nos 200 km/h, quase calado na neve e em 1972, volta no fim para ligar ao loop). 14 efeitos: vento, 4 swishes (capítulos), 3 dings baixos nas piadas (pedido do guião), 3 pops (200 · 1944 · toque da subscrição), frase de marca, boom + brilho no recorde. Loudness −15,8 LUFS, pico −1,4 dBTP.

## Fontes
- Nicholas Alkemade (1944): ~18,000 ft para pinheiros e neve, entorse na perna.
- Vesna Vulović (1972): 10 160 m, Guinness World Records (maior queda sobrevivida sem paraquedas).
- Velocidade terminal em posição de estrela ~200 km/h; ~−50 °C a 10 km (atmosfera padrão).

## Notas / problemas
- O CLAUDE.md do main (24/11) diz "sem ding nas piadas"; o guião deste episódio pedia ding em 3 piadas: ficaram, mas com volume baixo (0,13).
- A frase de marca ficou aos 35 s (posição do guião do dono), não nos 3–8 s da regra geral.
- O boneco da cena de código (5–14 s) é desenhado em pycairo, inspirado no da s1; a s2 tem um boneco com outra roupa (ilustração aprovada assim).
