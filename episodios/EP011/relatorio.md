# EP011 · What If You Fell Into Quicksand? 🏜️

- **Não listado v2** (pedido do dono, 27/11/2026): https://www.youtube.com/shorts/vzrbEYrz4rc (48,8 s; som do X novo). Para apagar no Studio: v1 wbBoqDaWXEY.
- Capa "DON'T MOVE" (texto centrado e compacto, cara visível por cima) aplicada com `thumbnails.set`. `yt_upload.py` ganhou a opção `--unlisted`.
- **Formato** (pedido do dono): tom com humor, guião do dono com a narração exata, sem alarme e **sem frase de marca** (exceção pedida para este vídeo). Fica abaixo de 60 s (Short).
- **Fim contínuo** (lição do EP010): a narração acaba em "Which means, the next time you…" e o vídeo começa em "…just stepped into quicksand." O "You" inicial da gravação foi cortado (0,185 s, `ep011/build/trim_start.py`), por isso no loop ouve-se uma frase só, sem palavra repetida. Último frame = frame 0 (câmara, afundamento e "SINKING" convergem para o início).
- **Base:** EP010 v2 / EP009 (maquete 2.5D com parallax). A mesma personagem (rapaz de capuz): as 5 ilustrações e a capa foram geradas com `ep009/anim/s1_queda_aviao.png` como referência.
- **Montagem:** `ep011/anim_ep011.py` · cortes de áudio `ep011/build/audio_cut.py` (pausas para 0,10 s, 9,3 s removidos, atempo 1,10) · palavras `ep011/build/words.json` (faster-whisper + texto exato do guião, 181/181) · camadas `ep011/build/layers11.py` (rembg isnet / u2net_human_seg + GrabCut: fundo, chão, personagem) · capa `ep011/thumb_ep011.py` → `thumbnails/ep011_thumb.jpg` · folha de controlo `ep011/folha_controlo_ep011.jpg` (frame 0, pop-up, último frame).

## Créditos (saldo real 699,68 → 682,68)
| Geração | Modelo | Créditos |
|---|---|---|
| 5 ilustrações (enterrado a afundar, amigo a puxar, parado à cintura, a flutuar de costas, a deslizar para fora) | nano_banana_pro | 10 |
| 1 refação (gancho: a 1.ª saiu a cair, não enterrado até aos joelhos; `ep011/build/q1_afundar_v1_rejeitada.png`) | nano_banana_pro | 2 |
| Narração (1 tentativa, guião fechado, stability 0,5) | elevenlabs_v4_turbo, voz Bram | 3 |
| Capa (rapaz enterrado até à cintura, em pânico) | nano_banana_pro | 2 |
| **Total** | | **17** |

Música reaproveitada (`music/track01_cosmic_ambient.mp3`, ducking). Efeitos sintetizados por código (14). Loudness −15,8 LUFS, pico −1,4 dBTP.

## Estrutura (tempos)
- 0 s gancho: enterrado até aos joelhos, a afundar devagar (a personagem desce e é recortada pela linha da areia), ondas e bolhas, "SINKING" com setas desde o frame 0.
- 2,7 s "pull your legs out": puxões, setas "PULL!", piada relatable "LEG DAY: SKIPPED".
- 6,0 s X vermelho; lupa com grãos de areia "SOLID" → água entra → "LIQUID"; "SINKING FASTER" (afunda mais depressa, quase até às coxas).
- 11,7 s "yell for help": balão "HELP!!".
- 12,9 s amigo a puxar (q2) → X; "GRIP" (areia agarra as pernas); cartão "1 FOOT = 🚗" com o carro a ser levantado + "= LIFTING A CAR".
- 21,6 s bandeira branca "FRIEND: GAVE UP"; piada relatable "ARM BATTERY" a descer até 3%.
- 24,2 s parado à cintura (q3): "STOP MOVING" ✓, "?" na viragem "weird", linha verde "STOPPED", "AT YOUR WAIST" ✓.
- 28,4 s balança SAND (2 blocos) vs YOU, "SAND 2× HEAVIER", "CAN'T SINK", setas para cima "YOU FLOAT".
- 33,4–35,9 s pop-up de subscrição no topo, logo a seguir a "You float in it."
- 33,3 s solução (q4): visto verde, "LEAN BACK" ✓ / "SPREAD ARMS" ✓ / "WIGGLE SLOWLY" ✓, piada "SUNDAY MODE: ON", gotas de água a voltar à areia "WATER IN = SAND LOOSENS".
- 40,2 s barra "LEGS FREE" → visto + "FREE!" (q5, a deslizar para fora).
- 43,9 s cena do gancho numa película a preto e branco, carimbo vermelho "THE MOVIES LIED" (impacto principal); "FIGHT IT = SINK".
- 47,2 s final: de volta ao gancho, converge para o frame 0.

## Áudio
14 efeitos: 2 sons de areia molhada (gancho e "sink even faster"), 2 sons de "resposta errada" nos X (v2: escolhidos pelo dono entre 4 da Epidemic Sound via Higgsfield, `lib/sfx/x_resposta_errada.mp3`; o trombone sintetizado da v1 era "horrível e chato"), 3 pops (carro, 2×, subscrição), batida no carro, 3 swishes (paragem, solução, cinema), 2 sons de "certo" (deitar-se, livre), brilho no "FREE!", impacto no carimbo. Sem dings, sem alarme.

## Fontes
- Bonn, D. et al. "Quicksand and the human body", Nature 434, 1079 (2005): areia movediça ~2× mais densa do que o corpo (não se afunda por completo, flutua-se); puxar um pé a 1 cm/s exige ~10⁶ N, comparável a levantar um carro.

## Notas / problemas
- O Higgsfield indica "nano_banana_2" nos trabalhos pedidos como `nano_banana_pro` (2 créditos por imagem, como sempre).
- A 5.ª ilustração (a deslizar para fora) não foi recortada em camadas (o poço ficava agarrado à personagem): só tem parallax fundo/chão e movimento de câmara.
- O loop começa em "just stepped…" (sem o "You" inicial), como pedido pelo dono; quem vê pela primeira vez ouve "Just stepped into quicksand." e lê o mesmo na legenda.
- A balança desenhada por código tinha um bonequinho no prato "YOU"; foi trocado por um bloco "YOU" e o vídeo voltou a ser renderizado (0 créditos). Ficou esclarecida com o dono a regra das personagens (coerência entre planos; várias personagens com papéis diferentes são bem-vindas), atualizada no CLAUDE.md.
- A capa saiu primeiro com o texto no topo (script antigo); corrigida antes do envio para o texto centrado, como manda a regra.
- O cartão "LEG DAY: SKIPPED" (4,7–6 s) e o "SUNDAY MODE" (35–37 s) tapam parte da cara do rapaz durante ~1 s.
