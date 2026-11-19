# EP003 · What If You Farted in a Spacesuit?

- **Vídeo (v3):** 46,3 s, privado: https://www.youtube.com/shorts/UcEvUvZZkNI
- **Apagar no Studio:** v1 https://www.youtube.com/shorts/nyv9yK3VSX0 (estação clara) e v2 https://www.youtube.com/shorts/u2zB5B1jGM4 (fundo azul, com sirene)
- **Montagem:** `ep003/anim_ep003.py` (+ `ep003/neuro_lib.py`) · narração `ep003/audio/narration.wav` · palavras `ep003/build/words_ep003.json` · folha de controlo `ep003/build/folha_controlo.jpg`
- Guião aprovado pelo dono, narração sem alterações.

## Créditos (19/11/2026)
| Geração | Modelo | Créditos |
|---|---|---|
| Astronauta de referência (fora da estação, Terra atrás) | nano_banana_pro | 2 |
| Close do capacete, interior do capacete, órbita, interior da estação (com a 1.ª como referência) | nano_banana_pro | 8 |
| Refação do interior da estação, escuro com janela estrelada (indicação do dono) | nano_banana_pro | 2 |
| v3: as 5 imagens refeitas com fundo de espaço preto, mesma composição (pedido do dono; 2.ª refação da estação autorizada) | nano_banana_pro | 10 |
| Narração (uma vez, guião fechado) | elevenlabs_v4_turbo, voz Orion | 2,55 |
| **Total** | | **24,55** (saldo 1 678,03 → 1 653,48) |

1 refação (estação: o dono pediu espaço escuro com estrelas em todas as cenas; a v1 clara ficou em `ep003/anim/station_v1_claro.png`). Música reutilizada (`music/track01_cosmic_ambient.mp3`). Peido, alarme, toc, faísca, pssh, swish, pop e ding sintetizados por código (ffmpeg).

## Fórmula aplicada
- 0 s: "pffrrt" sintetizado (`build/fart_synth.py`, 0,85 s, sem sirene nem bordas vermelhas na v3); a narração só entra a seguir (0,95 s). Painel "SUIT ALERT · AIR QUALITY" e medidor "SMELL LEVEL" até 100 % no fim de "spacesuit." (~2,6 s): "MAX!", flash verde e a nuvem rebenta à volta do capacete.
- Selo "THE SCARY PART · COMING UP" de ~4,7 s até "Now the scary part" (23 s).
- Nuvem verde com cara (código) em todas as cenas; cartão On Earth / In Space; luvas a bater no vidro com "toc"; propulsão "+1 cm" e caracol com bateria fraca a ultrapassar; HYDROGEN/METHANE com chamas desenhadas; faísca apagada por uma luva; filtros de carvão a sugar a nuvem; barra "Removing smell…" (100 % → 97 %, "Time left: forever").
- Pop-up de subscrição (`lib/subscribe_popup.py`) logo a seguir a "Very… slowly" (38,5–41 s).
- Pergunta A/B na estação; último frame idêntico ao primeiro (diferença de píxeis 0).
- Pausas ≤0,12 s e voz +10 % (atempo). Loudness −14,9 LUFS.

## Notas
- O pop-up sobrepõe-se ao início da pergunta (a narração não tem pausa entre "Very… slowly" e "Would you rather").
- As pausas cómicas de "Slowly. Very… slowly." ficaram curtas por causa da regra das pausas; a barra de download compensa no ecrã.
- Fontes na descrição: investigação da NASA sobre flatulência na era Apollo; carvão ativado nos fatos (NASA).

## Versões
- v1 → v2: estação refeita com interior escuro (indicação do dono via sessão de controlo).
- v2 → v3 (dono viu o vídeo): fundo ainda azul → as 5 imagens refeitas com espaço preto (versões antigas em `ep003/anim/*_azul.png`); sirene retirada; "pffrrt" mais nítido e narração depois dele.
