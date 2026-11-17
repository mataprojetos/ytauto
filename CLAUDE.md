# Whatifaholic: notas para o Claude

Responde sempre em português de Portugal. O canal e os vídeos são em inglês.

## O projeto
- Canal YouTube Shorts **Whatifaholic** (@whatifaholics), id `UC8P0-pbFRXyDgu7iV6TMmTQ`.
- Formato comum: perguntas "What if…?" sobre ciência, dinheiro, tecnologia e IA, em animação.
- Finanças: só conteúdo educativo, nunca recomendações de investimento, sempre "not financial advice".
- Plano completo (documento): https://claude.ai/artifact/8GWwure2Kc1sery37j6A7K

## Fórmula de cada vídeo (aprovada pelo dono)
- Gancho com urgência + número + recompensa em 1–2 s (ex.: contagem "1.30 SECONDS LEFT" e a Lua estilhaça no zero).
- Loop aberto principal com selo no ecrã até à revelação; loops curtos a cada 8–10 s.
- Uma piada a cada ~15 s, cada uma com imagem própria; pergunta final "A ou B" para comentários.
- Sem espaços mortos: pausas da narração cortadas para ≤0,12 s e voz +10% (atempo, sem mudar o tom).
- Último frame igual ao primeiro (loop). Sem ecrã final.
- Estilo: ilustração plana em camadas (Higgsfield) + animação por código (pycairo); paleta azul-noite e ciano.
- Legendas palavra a palavra, palavra atual em ciano, fora das zonas tapadas pelo YouTube.
- Som discreto: swish só nas mudanças de capítulo, pop leve nos números, ding nas piadas, música com ducking.
- Marca discreta "@whatifaholics" no canto superior esquerdo. Sem número de episódio no ecrã.
- Factos sempre verificados em fontes abertas; fontes na descrição de cada vídeo.

## Ferramentas e custos
- Higgsfield (créditos: plano Ultra, 3 000/mês). Imagem `nano_banana_pro` ≈ 2 créditos; clip Seedance 28 (evitar).
- Voz: `elevenlabs_v4_turbo`, voz preset "Orion" `ed69c516-92d2-4b30-a967-617737a342e5` (~3 créditos/episódio).
- Música: reutilizar `music/` (gerar uma faixa custa ~10 créditos).
- Meta: 11–15 créditos por episódio.
- YouTube Data API: quota de 10 000 unidades/dia; `research/yt_new_shorts_channels.py` controla a quota.

## Publicação
- `yt_upload.py`: privado por omissão; `--public` só com autorização explícita do dono.
- Credenciais em variáveis de ambiente (nunca no repositório): `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.
- Permissões da app OAuth: `youtube.upload`, `youtube.readonly`, `yt-analytics.readonly` (não pode apagar nem mudar a visibilidade).
- App OAuth "em produção" no projeto Google Cloud "Ptojeto YT"; página e política de privacidade em https://mataprojetos.github.io/whatifaholic-site/
- Episódio #001 já enviado como privado: https://www.youtube.com/shorts/5YPMC0g-DvY

## Próximos passos (estado em 17/11/2026)
1. ✅ `--whoami` testado a 17/11/2026: canal Whatifaholic autorizado. O script usa `youtube.googleapis.com`, porque em `www.googleapis.com` o proxy injeta uma chave de API (`X-Goog-Api-Key`) e os pedidos OAuth dão 401.
2. ✅ Segredo temporário `youtube.googleapis.com` apagado (só resta a chave de API em `www.googleapis.com`, útil para pesquisa pública).
3. Decidir onde corre a produção diária (tarefa agendada com sessão nova, GitHub Actions ou computador do dono) e testar se a sessão agendada consegue usar o Higgsfield.
4. Pendente: frase "No Moon, no signal" no #001 é uma simplificação (a temperatura e a duração do dia também contam).
5. Pendente: pack de efeitos sonoros da YouTube Audio Library para substituir os sons sintetizados.
6. Pendente: mudar o nome da app OAuth de "Claude" para "Whatifaholic Uploader" no Branding.
