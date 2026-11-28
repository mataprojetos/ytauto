# Stickman: notas para o Claude (projeto SEPARADO do Whatifaholic)

Responde em português de Portugal. Os vídeos são em inglês (só texto curto no ecrã).
**As regras do Whatifaholic (CLAUDE.md da raiz) NÃO se aplicam aqui**, exceto não pôr credenciais no repositório.

## O que é
- Canal: **@ThePsychArena** (marca discreta no canto superior esquerdo, por cima das faixas).
- Canal de Shorts no estilo da trend "quem ganha?": bonecos simples (stickmen) de capuz que representam traços de personalidade
  (Motivation, Discipline, Obsession; às vezes Anger, Ego, Overthinking, Laziness) numa prova até só um vencer.
- Estilo visual livre de cópia direta: bonecos simples são um estilo comum; personagens, provas e títulos são nossos.

## Formato (decisão do dono)
- ~30 s, 1080×1920, **sem voz**. Só animação, texto curto no ecrã e música.
- **Drop da música aos ~17 s**, a coincidir com o momento decisivo.
- Estrutura: 0–2 s título "A vs B vs C" com a prova já a decorrer · 2–10 s alguém fraqueja · 10–16 s crise/tensão máxima ·
  ~17 s momento decisivo (drop) · 17–28 s consequência épica · 28–30 s frase-lição curta e corte seco.

## Estilo aprovado (EP #001 climb, v6)
- Fundo preto; 4 faixas com o nome a vermelho, % + barrinha na cor da personagem; percurso inteiro à vista
  (linha fina de ponta a ponta que anda por baixo de quem avança — "escada rolante"); meta só aparece nos últimos ~2 s.
- Bonecos néon, uma cor por personagem (Anger vermelho, Obsession roxo, Discipline ciano, Motivation laranja), muitas partículas.
- Obstáculos explicam quem pára; quem pára perde o movimento da linha. Vencedor chega ~2 s antes do fim.
- Pensamentos nascem a crescer da cabeça, ficam por cima e caem para trás para o chão.
- Pulsação ao BPM da música (`lib/beats.py` deteta BPM/drop/batidas); drop do vídeo aos 17,0 s.
  Música do dono em `music/` (não versionada); o render gera pré-visualização com música e indica o segundo de início.

## Produção
- **Tudo por código** (pycairo/numpy + ffmpeg). **Zero créditos do Higgsfield.**
- **Sem música no ficheiro final:** o dono junta o som (do autor que ele escolhe) na app do YouTube. O vídeo sai mudo
  ou só com efeitos sonoros mínimos, cronometrado para o drop cair aos 17 s. Indicar ao dono o segundo da música a usar.
- Nada de automatismos nem envio para o YouTube: o vídeo é entregue ao dono como ficheiro (pasta `stickman/out/`, não versionar mp4 grandes se não for preciso).
- Código partilhado em `stickman/lib/`, um script por vídeo em `stickman/videos/NNN_nome.py`.

## Entrega final (pedido do dono, 28/11/2026)
Sempre que um vídeo fica fechado e é hora de publicar, entregar SEMPRE, separados e prontos a copiar:
1. **Título** (personagens "A vs B vs C…: <prova>" + emoji + 2–3 hashtags).
2. **Descrição** (uma linha curta por personagem com o que lhe aconteceu, "Only one…", pergunta final "Which one are you? 👇", hashtags).
3. **Etiquetas** (separadas por vírgulas, incluir "ThePsychArena").
4. **Comentário para fixar** (reflexivo: uma ideia/lição curta sobre o que o vencedor mostra, tom pessoal; não listar as personagens).
Mais: vídeo sem música + pré-visualização com música, capa (`out/NNN_thumb.jpg`) e o segundo da música a usar na app.
Guardar o texto em `stickman/out/NNN_nome_post.md`. Exemplo: `out/001_climb_post.md`.
