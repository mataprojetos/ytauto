# EP007 · What If Earth Had Rings Like Saturn?

- **Privado:** https://www.youtube.com/shorts/CXKyU9wS_hc (34,2 s) · capa aplicada e confirmada (personalizada + versão vertical do feed de Shorts)
- **Montagem:** `ep007/anim_ep007.py` · cortes de áudio `ep007/build/audio_cut.py` · palavras `ep007/build/words.json` (faster-whisper, 105/105 palavras) · limpeza das imagens `ep007/build/fix_images.py` · capa `ep007/thumb_ep007.py` → `thumbnails/ep007_thumb.jpg` · folha de controlo `ep007/folha_controlo_ep007.jpg` (frame 0, pop-up 23,4/24,3 s, último frame)
- Guião aprovado pelo dono, narração sem alterações. Sem pedido de comentário.

## Créditos (23/11/2026, saldo real 1 596,50 → 1 582,70)
| Geração | Modelo | Créditos |
|---|---|---|
| 4 ilustrações: rua europeia com arco (frame 0), noite clara sobre casas, praia no equador, pôr do sol com anéis de gelo (referências de estilo: `ep001/anim/sky_city.png` e `ep003/anim/orbit.png`) | nano_banana_pro | 8 |
| Refação do equador (a v1 trazia o astronauta da referência do EP003) — saiu pior, não usada | nano_banana_pro | 2 |
| Imagem da capa (rapaz em choque + arco sobre a rua) | nano_banana_pro | 2 |
| Narração (1 tentativa, guião fechado, stability 0,5) | elevenlabs_v4_turbo, voz Bram | 1,8 |
| **Total** | | **13,8** |

Música reaproveitada (`music/track01_cosmic_ambient.mp3`, com ducking). Swish, whoosh, pop, ding, brilho e boom sintetizados por código; som da frase de marca `lib/sfx/scratch_head.wav` e assinatura visual `lib/brand_scratch.py`.

## Estrutura (tempos)
Gancho 0 s: o arco gigante já está no frame 0, brilho + boom suave; câmara sobe da rua para o céu em "Look up" e aproxima-se do arco; "EARTH HAS RINGS" 0,6 s · pin "EUROPE" 3,3 s · frase de marca 6,9 s (mão a coçar + som) · noite 8,4 s: medidor "DARKNESS" que nunca enche, piada "SLEEP SCHEDULE: CANCELLED" (12 s) · equador 12,5 s: a câmara sobe da praia, linha prateada a brilhar com "THE RINGS", piada "EQUATOR PEOPLE: 'WHAT RINGS?'" (16,4 s) · inverno 17,1 s: globo por código, sombra dos anéis a cobrir o hemisfério norte, pin "YOU", "COLDER DAYS / LONGER NIGHTS", piada "HEATING BILL: x3", neve · pôr do sol 22,2 s: piada do chat de família cheio de fotos do pôr do sol · pop-up de subscrição 23,0–25,6 s (67 %, antes de "But wait") · selo "THE STRANGEST PART · COMING UP" 25,8–30,5 s · Terra do Ordovícico com anel, "IT WAS REAL" 28,8 s, "466 MILLION YEARS AGO" 30,5 s (boom) · "Which means, one day…": Terra de hoje com anel fantasma, a câmara mergulha e nos últimos 0,5 s a rua do frame 0 abre-se (último frame = frame 0 a menos de 1 frame de movimento das partículas; diferença média 0,6/255).

Câmara sempre em movimento em todas as ilustrações (zoom e pan lentos) + partículas em três camadas de velocidade (parallax).

## Áudio
Pausas cortadas por energia (silêncios abaixo de −38 dB do pico encurtados para 0,11 s, 3,8 s removidos) e atempo 1,10. Loudness −15,3 LUFS.

## Fontes
- Tomkins, Martin & Cawood (2024), "Evidence suggesting that earth had a ring in the Ordovician", Earth and Planetary Science Letters 646, 118991: https://doi.org/10.1016/j.epsl.2024.118991

## Notas / problemas
- O Higgsfield devolve os trabalhos `nano_banana_pro` com o rótulo `nano_banana_2`; custo de 2 créditos cada, como cotado.
- Com duas referências, a imagem do equador copiou o astronauta do EP003. A refação (só com a referência da cidade) saiu com dia/noite misturados e prédios da referência, por isso usei a v1 e apaguei o astronauta por código (céu reconstruído; v1 original em `ep007/anim/equator_v1_astronauta.png`). Próxima vez: referência de estilo sem personagens.
- A imagem da capa tinha um terceiro braço a apontar; apagado por código (`anim/thumb_bg_clean.png`).
- Sem alarme nem bordas vermelhas no gancho: o tema pede deslumbramento e o dono pediu impacto pelo arco no frame 0.
- O cenário (sombra no inverno, noites claras) é especulativo/simplificado; a descrição diz-o.
