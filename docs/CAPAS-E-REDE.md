# Capas online e indicador de rede — 0.9

O cabeçalho fixo fica no canto superior direito das abas Aplicativos, Jogos e Monitorar, na tela de envio e na breve tela de abertura de jogo. Menus do Android, Netflix e RetroArch são aplicativos externos e não recebem uma sobreposição do TvRetro.

Ao lado do ícone há taxas de recebimento/envio em **KiB/s**, amostradas a cada 2 segundos enquanto a tela está ativa. São os bytes de todas as interfaces da TV, incluindo tráfego local (como ADB), e não apenas o TvRetro, nem um teste da velocidade contratada. O painel Monitorar continua oferecendo o consumo diário Wi-Fi quando o Android permite acesso de uso. O cabeçalho não exige essa permissão nem localização.

## Capas automáticas

A biblioteca não depende mais de uma lista fixa de nove jogos nem de imagens incorporadas ao APK. O TvRetro usa o **Libretro Thumbnails** para SNES e PlayStation. Primeiro tenta a URL do título/região derivados do nome; se não houver essa imagem, consulta o catálogo para normalizar o título. Baixa somente as capas visíveis.

O romsgames.net foi avaliado como sugestão, mas retornou HTTP403 à consulta automatizada; não foi implementado scraping nem contorno de bloqueio. A fonte usada tem estrutura documentada para capas: [Libretro](https://docs.libretro.com/guides/roms-playlists-thumbnails/).

- Use nomes completos: `Super Mario Kart (USA).sfc`, `Donkey Kong Country (USA).smc` ou `Castlevania - Symphony of the Night.chd`.
- Tags como região, revisão e `[!]` são normalizadas; versões regionais são priorizadas quando reconhecidas.
- Para nomes genéricos/ambíguos ou ausentes no catálogo, aparece um cartão com o nome. Não se escolhe arbitrariamente entre jogos diferentes.
- O primeiro carregamento pode demorar quando for preciso consultar o índice completo do console. Nomes convencionais tentam a capa diretamente, evitando baixar esse índice. A interface e a abertura do jogo não esperam pela capa.
- Sem internet, as capas que ainda estiverem na memória podem aparecer. Depois de liberar memória/reiniciar, o cartão com o nome continua abrindo o jogo normalmente; novas tentativas têm intervalo para evitar requisições contínuas.
- Nenhuma ROM, save ou conteúdo do arquivo de jogo é enviado. São baixados um índice público e a imagem do título correspondente.

## Limites de memória e armazenamento

Imagens em cache **somente em RAM**, com LRU de 3 MiB; sem arquivos de capa em disco. Imagens de cards fora da tela são liberadas; ao sair da home/receber pressão de memória, o cache é descartado. Catálogos de nomes ficam em RAM durante a vida do processo. Views ainda não são totalmente recicladas para bibliotecas enormes.

Downloads usam HTTPS para um único host, sem seguir redirecionamentos, com prazos e limites: catálogo de até 4 MiB e 16 mil entradas, imagem de até 2 MiB e dimensões de até4096px, decodificada com amostragem/RGB565. Há uma fila limitada e apenas um worker de capas. Não há senha de serviço ou chave de API.

A remoção das imagens antigas se restringiu às capas do aplicativo. O wallpaper pessoal, ícones da interface, logos de outros aplicativos, ROMs e saves são preservados. Na instalação alvo, as pastas públicas de thumbnails já estavam vazias; não houve limpeza genérica de imagens do Android.

## Metadados opcionais

Um build pessoal pode incluir `assets/cover-hints.properties` para preservar associações anteriores de arquivos com nomes abreviados:

```
PSX/ArquivoAbreviado.chd=Titulo Completo do Catalogo
```

Isso contém apenas texto, não a imagem. O arquivo é ignorado pelo Git e não acompanha a distribuição fonte. O build pessoal preserva uma associação anterior desse tipo. Novos usuários com títulos completos não precisam disso. Correspondência por hash de ROM não é implementada; hacks/traduções/títulos desconhecidos podem ficar sem capa.
