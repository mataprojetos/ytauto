# Whatifaholic: notas para o Claude

Responde sempre em português de Portugal. O canal e os vídeos são em inglês.

## O projeto
- Canal YouTube Shorts **Whatifaholic** (@whatifaholics), id `UC8P0-pbFRXyDgu7iV6TMmTQ`.
- Formato comum: perguntas "What if…?" sobre ciência, dinheiro, tecnologia e IA, em animação.
- Finanças: só conteúdo educativo, nunca recomendações de investimento, sempre "not financial advice".
- Plano completo (documento): https://claude.ai/artifact/8GWwure2Kc1sery37j6A7K
- Painel (episódios, créditos, saldo, YouTube): https://claude.ai/artifact/SXpVwhH1JMhxAAfUkn3RYC. Atualizar: `python3 episodios/painel_dados.py --saldo <balance>`, carregar os 3 JSON de `episodios/painel/` como assets e apontar `datasets/<id>.source.url` para os novos (com `updated`).

## Fórmula de cada vídeo (aprovada pelo dono)
- Gancho com urgência + número + recompensa em 1–2 s (ex.: contagem "1.30 SECONDS LEFT" e a Lua estilhaça no zero).
- Gancho sonoro e visual: alarme de emergência de dois tons + bordas vermelhas a piscar até à recompensa (decisão do dono, 17/11/2026; é a exceção ao som discreto).
- Duração alvo: 40–55 s (~140–160 palavras de guião). Cortar o facto mais fraco antes de cortar uma boa piada.
- Loop aberto principal com selo no ecrã até à revelação; loops curtos a cada 8–10 s.
- Uma piada a cada ~15 s, cada uma com imagem própria; pergunta final "A ou B" para comentários.
- Sem espaços mortos: pausas da narração cortadas para ≤0,12 s e voz +10% (atempo, sem mudar o tom).
- Último frame igual ao primeiro (loop). Sem ecrã final.
- Estilo: ilustração plana em camadas (Higgsfield) + animação por código (pycairo). **Sem paleta fixa** (decisão do dono, 18/11/2026): as cores servem o tema de cada vídeo; o objetivo é só ser viciante (contraste forte, imagem que muda a cada 2–3 s, surpresa visual em cada piada).
- Movimento dentro das imagens em todas as cenas (pedido do dono, 18/11/2026), por código com `ep002/vivo.py` (0 créditos): partes recortadas por cor, olhos/expressões redesenhados, objetos a mexer de acordo com a narração. Pedir ilustrações com personagens grandes e fáceis de recortar (fundo contrastante).
- Legendas palavra a palavra, palavra atual em ciano, fora das zonas tapadas pelo YouTube.
- Som discreto: swish só nas mudanças de capítulo, pop leve nos números, ding nas piadas, música com ducking.
- Marca discreta "@whatifaholics" no canto superior esquerdo. Sem número de episódio no ecrã.
- Factos sempre verificados em fontes abertas; fontes na descrição de cada vídeo.
- Miniatura em cada vídeo (pedido do dono, 18/11/2026), feita por código com `thumbnail.py` (0 créditos) a partir de uma ilustração do episódio: sujeito em grande, 2–4 palavras enormes (amarelo/branco, contorno preto), etiqueta vermelha com número/urgência, tudo no quadrado central. Enviar com `yt_upload.py --thumbnail epXXX/publish/thumbnail.jpg` (ou `--set-thumbnail VIDEO_ID`). Testado a 18/11 no EP002: funciona com as permissões atuais. Nota: no feed de Shorts o vídeo arranca sozinho (conta o primeiro frame); a miniatura conta na pesquisa, na página do canal e nas sugestões.

## Ferramentas e custos
- Higgsfield (créditos: plano Ultra, 3 000/mês). Imagem `nano_banana_pro` ≈ 2 créditos; clip Seedance 28 (evitar).
- Voz: `elevenlabs_v4_turbo`, voz preset **"Bram"** `549ff70a-3ee7-4f04-a4d9-89a24fab7709` (~3 créditos/episódio; escolha do dono a 18/11/2026, a partir do EP002 v2). Antes era "Orion" `ed69c516-92d2-4b30-a967-617737a342e5`. Eleven v4 (não-turbo) com marcas de emoção soou a IA: não usar.
- Música: reutilizar `music/` (gerar uma faixa custa ~10 créditos).
- Meta: 11–15 créditos por episódio. **Limite rígido: 30 créditos por vídeo** (decisão do dono, 17/11/2026):
  - Registar o saldo do Higgsfield (`balance`) no início e verificar antes de cada geração; se a próxima geração passar dos 30, parar e perguntar ao dono.
  - Proibido gerar clips de vídeo no Higgsfield (Seedance ≈28). Animação só por código.
  - Imagens só com `nano_banana_pro`; no máximo 1 refação por imagem.
  - Música: reutilizar `music/`; faixa nova só com autorização do dono.
  - Voz: gerar uma vez, só com o guião fechado.
  - No fim: créditos reais em `episodios/registo.csv` e `episodios/EPxxx/relatorio.md`.
- YouTube Data API: quota de 10 000 unidades/dia; `research/yt_new_shorts_channels.py` controla a quota.

## Publicação
- `yt_upload.py`: privado por omissão; `--public` só com autorização explícita do dono.
- Credenciais em variáveis de ambiente (nunca no repositório): `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.
- Permissões da app OAuth: `youtube.upload`, `youtube.readonly`, `yt-analytics.readonly` (não pode apagar nem mudar a visibilidade).
- App OAuth "em produção" no projeto Google Cloud "Ptojeto YT"; página e política de privacidade em https://mataprojetos.github.io/whatifaholic-site/
- Episódio #001 v6 enviado como privado: https://www.youtube.com/shorts/mclRjhuB7eg (a v1 de 80 s, 5YPMC0g-DvY, é para apagar)

## Como se produz um episódio
- Sem palavras-chave nem automatismos: o dono pede sugestões de temas e decide-se em conversa (decisão do dono, 17/11/2026).
- Depois de acordado o tema e o guião, a produção pode correr numa sessão nova "Whatifaholic · EPxxx" (etiqueta `whatifaholic`), que envia como **privado**.
- No fim: link do vídeo privado + créditos gastos ao dono; atualizar registo e painel.

## Próximos passos (estado em 17/11/2026)
1. ✅ `--whoami` testado a 17/11/2026: canal Whatifaholic autorizado. O script usa `youtube.googleapis.com`, porque em `www.googleapis.com` o proxy injeta uma chave de API (`X-Goog-Api-Key`) e os pedidos OAuth dão 401.
2. ✅ Segredo temporário `youtube.googleapis.com` apagado (só resta a chave de API em `www.googleapis.com`, útil para pesquisa pública).
3. ✅ Decidido: produção arranca à mão, em conversa com o dono. Testado a 17/11: uma sessão nova criada pela sessão de controlo tem Higgsfield e credenciais do YouTube. Tarefas agendadas criadas pelo Claude não levam conectores (só pela interface do claude.ai).
4. ✅ #001 refeito (v6, 48 s, alarme no gancho, corais corrigidos): privado em https://www.youtube.com/shorts/mclRjhuB7eg. O dono apaga a v1 (5YPMC0g-DvY) no Studio e decide quando publicar.
5. Pendente: pack de efeitos sonoros da YouTube Audio Library para substituir os sons sintetizados.
6. Pendente: mudar o nome da app OAuth de "Claude" para "Whatifaholic Uploader" no Branding.
