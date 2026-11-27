# Stickman: notas para o Claude (projeto SEPARADO do Whatifaholic)

Responde em português de Portugal. Os vídeos são em inglês (só texto curto no ecrã).
**As regras do Whatifaholic (CLAUDE.md da raiz) NÃO se aplicam aqui**, exceto não pôr credenciais no repositório.

## O que é
- Canal de Shorts no estilo da trend "quem ganha?": bonecos simples (stickmen) de capuz que representam traços de personalidade
  (Motivation, Discipline, Obsession; às vezes Anger, Ego, Overthinking, Laziness) numa prova até só um vencer.
- Estilo visual livre de cópia direta: bonecos simples são um estilo comum; personagens, provas e títulos são nossos.

## Formato (decisão do dono)
- ~30 s, 1080×1920, **sem voz**. Só animação, texto curto no ecrã e música.
- **Drop da música aos ~17 s**, a coincidir com o momento decisivo.
- Estrutura: 0–2 s título "A vs B vs C" com a prova já a decorrer · 2–10 s alguém fraqueja · 10–16 s crise/tensão máxima ·
  ~17 s momento decisivo (drop) · 17–28 s consequência épica · 28–30 s frase-lição curta e corte seco.

## Produção
- **Tudo por código** (pycairo/numpy + ffmpeg). **Zero créditos do Higgsfield.**
- **Sem música no ficheiro final:** o dono junta o som (do autor que ele escolhe) na app do YouTube. O vídeo sai mudo
  ou só com efeitos sonoros mínimos, cronometrado para o drop cair aos 17 s. Indicar ao dono o segundo da música a usar.
- Nada de automatismos nem envio para o YouTube: o vídeo é entregue ao dono como ficheiro (pasta `stickman/out/`, não versionar mp4 grandes se não for preciso).
- Código partilhado em `stickman/lib/`, um script por vídeo em `stickman/videos/NNN_nome.py`.
