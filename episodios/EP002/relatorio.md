# EP002 · What If AI Took Your Job Tomorrow?

- **Vídeo:** 51 s, privado: https://www.youtube.com/shorts/Iysk_pswcVg
- **Montagem:** `ep002/anim_ep002.py` (base: `ep001/anim_ep001_v6.py`) · `ep002/neuro_lib.py` (cópia sem recursos da Lua)
- **Narração:** `ep002/audio/narration.wav` (pausas ≤0,12 s, atempo 1,1) · palavras `ep002/build/words_ep002.json` (openai-whisper base.en)
- **Imagens:** `ep002/anim/` — office_empty, robot_desk (referência do robô), meeting, jobs_city, pizza, park, band, robot_quits
- Cenário imaginado, sem fontes científicas (nota "This is an imagined scenario, just for fun." na descrição).

## Créditos (17/11/2026)
| Geração | Modelo | Créditos |
|---|---|---|
| 8 ilustrações (sem refações) | nano_banana_pro | 16,00 |
| Narração (uma vez) | elevenlabs_v4_turbo, voz Orion | 2,70 |
| 3 amostras de voz (Orion, Marcus, Gideon) em elevenlabs_v4, rejeitadas | elevenlabs_v4 | 2,76 |
| **Total** | | **21,46** (saldo 1 729,19 → 1 707,73) |

Música reaproveitada de `music/`; alarme, swish, pop, ding e boom sintetizados por código.

## Estrutura
- Gancho: contador 24:00:00 LEFT a acelerar até zero em "hired", alarme de dois tons + bordas vermelhas; corte para o robô na cadeira.
- Relógio "HOUR 1/3/8/12/24" fixo no topo com barra do dia; selo "THE TWIST · COMING UP" até "here's the twist".
- Piadas com ding: with itself, zero personality, in electricity, unfortunately, and quits.
- Pergunta final A (AN AI) ou B (ANNOYING COWORKER). Último frame = primeiro (escritório vazio + 24:00:00 LEFT).

## Notas
- O faster-whisper não descarregou o modelo (limite do Hugging Face); usou-se o openai-whisper.
- Algumas imagens vêm com faixas escuras decorativas em cima e em baixo (o relógio e as legendas ficam por cima delas).
- Teste de voz mais intensa (Eleven v4, estabilidade 0,3, marcas de emoção): o dono achou que todas soavam a IA. Fica a voz Orion em elevenlabs_v4_turbo; o vídeo enviado não muda. Amostras em `ep002/audio/amostras/`.
