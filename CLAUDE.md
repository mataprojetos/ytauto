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
- Gancho **sem alarme e sem bordas vermelhas a piscar** (decisão do dono, 24/11/2026: deixavam o início confuso e aumentavam o scroll). O impacto vem da imagem, do número e da voz; no máximo um whoosh ou impacto suave.
- Duração alvo: 30–40 s (~100–120 palavras de guião; decisão do dono a 21/11/2026, para subir a % vista). Cortar o facto mais fraco antes de cortar uma boa piada.
- Loop aberto principal com selo no ecrã até à revelação; loops curtos a cada 8–10 s.
- Uma piada a cada ~10–15 s, cada uma com visual próprio. **Piadas relatable sempre que der** (pedido do dono): situações do dia a dia da maioria das pessoas (chefe, segunda-feira, renda, despertador, reuniões chatas, chat de família, bateria do telemóvel), ligadas ao tema; evitar piadas de nicho.
- Sem espaços mortos: pausas da narração cortadas para ≤0,12 s e voz +10% (atempo, sem mudar o tom).
- Último frame igual ao primeiro (loop). Sem ecrã final.
- Estilo: ilustração plana e/ou animação só por código (pycairo). **Sem paleta fixa nem cor de marca** (decisão do dono, 21/11/2026): cada vídeo usa as cores que o tema pedir; não forçar azul/ciano.
- **Personagens coerentes entre planos** (decisão do dono, 25/11/2026, esclarecida a 27/11/2026): cada personagem mantém o mesmo aspeto em todas as cenas (gerar as ilustrações com a primeira como referência no nano_banana_pro); nunca trocar a personagem a meio de uma ação nem pôr um boneco desenhado por código no lugar dela. **Várias personagens com papéis diferentes a interagir no vídeo são bem-vindas** (ex.: o amigo que puxa no EP011). Gráficos e números por código podem ir por cima.
- Legendas palavra a palavra, palavra atual destacada numa cor de contraste que combine com o vídeo, fora das zonas tapadas pelo YouTube.
- **Som limpo e poucos efeitos** (decisão do dono, 24/11/2026: efeitos repetitivos cansam): ~10–15 efeitos por vídeo, volumes baixos. Swish só em 2–3 mudanças grandes; pop leve só nos 3–4 números principais; **sem ding nas piadas**; nada de repetir o mesmo som em série (numa queda, nem vários whooshes nem vento contínuo); impacto forte só na revelação principal. Frase de marca com o seu som; música baixa com ducking. **Sem som ambiente contínuo por baixo da voz** (vento, ruído, drones; decisão do dono, 25/11/2026: o som de fundo do EP009 afastava as pessoas). Referência: EP008 v2 (`ep008/anim_ep008.py`, função `mix`).
- **Pop-up de subscrição em todos os vídeos** (aprovado pelo dono): cápsula "🔔 SUBSCRIBE · for more what ifs" (cores livres) logo após a revelação principal (~70–75%), ~2,5 s, toque animado → "SUBSCRIBED ✓", pop leve; fora das zonas do YouTube e sem tapar o essencial da cena. Código de referência: `lib/subscribe_popup.py`.
- **Capa (thumbnail) em todos os vídeos** (pedido do dono): imagem própria, não precisa de ser um frame do vídeo, feita para ser irresistível de clicar (expressão forte, cor de destaque, 2–4 palavras grandes com contorno, fundo do tema). **Texto da capa sempre centrado no meio da imagem** (vertical e horizontal; pedido repetido do dono, EP009 e EP010), nunca no topo. **Texto compacto** (no máximo ~60% da largura, letras ~140–150 px numa capa 1080×1920) para caber no recorte da visualização do Short (pedido do dono, EP010). 1 imagem nano_banana_pro 9:16 (~2 créditos) + texto por código, JPG < 2 MB em `thumbnails/epXXX_thumb.jpg`; aplicar logo após o envio privado com `thumbnails.set` em `youtube.googleapis.com` (funciona com a permissão `youtube.upload`).
- Marca discreta "@whatifaholics" no canto superior esquerdo. Sem número de episódio em nada do que é público (ecrã, título, descrição, etiquetas): é irrelevante para quem vê. EPxxx só nos ficheiros internos.
- **Frase de marca em todos os vídeos:** "That one made me scratch my head." (escolha do dono). **Obrigatória cedo, no desenvolvimento (~3–8 s, logo a seguir ao gancho)**; pode repetir-se na viragem. Sempre com a mesma assinatura visual curta (mão a coçar a cabeça) e o mesmo som curto.
- **Final com gatilhos até ao último segundo** (pedido do dono, 21/11/2026): guardar a maior revelação/número para os últimos ~5 s, anunciada antes com um loop aberto ("wait until you see…"); nada de abrandar no fim.
- **Pedido de comentário: opcional** (decisão do dono, 22/11/2026): só quando o dono quiser ou o tipo de vídeo pedir. Quando houver, original e curtíssimo (≤6 palavras), colado à revelação final; nunca o genérico "Tell me below". Alternativa preferida para fechar: frase final incompleta que o início do vídeo completa (loop de frase, ex.: "Which means, right now…" → "You're falling into a black hole.").
- Factos sempre verificados em fontes abertas; fontes na descrição de cada vídeo.

## Ferramentas e custos
- Higgsfield (créditos: plano Ultra, 3 000/mês). Imagem `nano_banana_pro` ≈ 2 créditos; clip Seedance 28 (evitar).
- Voz: `elevenlabs_v4_turbo`, voz preset **"Bram"** `549ff70a-3ee7-4f04-a4d9-89a24fab7709` (~3 créditos/episódio; escolha do dono, a voz do vídeo do capacete). **Não usar "Orion"** (`ed69c516-…`), a voz antiga. Eleven v4 (não-turbo) com marcas de emoção soou a IA: não usar.
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
