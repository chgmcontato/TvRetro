# TvRetro — TV Casa + Phone Pad

Launcher leve para Android TV, biblioteca SNES/PSX, monitor local e controle Bluetooth pelo celular. Projeto desenvolvido iterativamente com assistência de IA para uma TCL Android TV 11 e um Samsung com Android 16.

## Componentes

- `apps/tv-casa`: launcher Java Android 0.8; abas Aplicativos, Jogos e Monitorar; capas carregadas por visibilidade, leitura assíncrona da biblioteca e envio local temporário de ROMs.
- `apps/phone-pad`: controle Android Bluetooth HID 0.4. O pareamento e a compatibilidade dependem do celular/TV.
- `tools/controle-tv.py`: controle pelo notebook com página somente em localhost, captura manual e integração opcional scrcpy. Não instala um app permanente na TV.
- `docs/HISTORICO.md`: memória técnica da conversa e decisões; é um resumo editado, não transcrição integral.
- `docs/NOTEBOOK.md`: diferenças entre controlar a TV, espelhar a TV e transmitir o notebook.
- `docs/SEGURANCA.md`: limites, manutenção e auditoria.

## Compilar

JDK 17, Android SDK Platform 35 e Build Tools 35.0.0. Configure `JAVA_HOME`, `ANDROID_HOME`, `KEYSTORE` (fora do repositório) e `KEYSTORE_PASS` no ambiente e execute `sh apps/tv-casa/build.sh` ou `bash apps/phone-pad/build.sh`. APKs são gerados em `out/` ou `build/` do app correspondente. A senha não deve ser colocada no histórico do terminal. Preserve a chave original para atualizar uma instalação existente; outra chave exige desinstalação e pode perder dados.

A distribuição fonte não inclui fontes comerciais, wallpaper pessoal nem capas; usa fonte monoespaçada e fundo sólido sem eles. Assets opcionais estão descritos em `apps/tv-casa/assets/LEIA-ME.txt`. ROMs e BIOS nunca são incluídas. RetroArch e núcleos devem ser instalados/configurados separadamente. Os caminhos atuais dos núcleos são específicos do RetroArch ARM32; não há suporte universal a emuladores.

## Uso

Jogos em `Games/SNES` e `Games/PSX` no armazenamento compartilhado ou USB removível legível. SNES: SFC/SMC; PSX: CHD/PBP/CUE/M3U (BIN deve acompanhar o CUE). Biblioteca não extrai ZIP/RAR. O receptor temporário preserva 550 MiB livres: uma TV já abaixo desse limite pode recusar novos envios. Saves não devem ser apagados para limpar cache.

Para o notebook: `python3 tools/controle-tv.py --tv IP_DA_TV` (requer ADB autorizado e depuração de rede). Acrescente `--scrcpy /caminho/para/scrcpy` para imagem ao vivo. Não exponha ADB ou o receptor à internet. Veja docs/NOTEBOOK.md.

## Validação e limites

A versão 0.7 foi usada na TV alvo. Na 0.8: compilação local e testes HTTP automatizados do receptor; validações no aparelho estão registradas em docs/VALIDACAO.md. Não existe auditoria integral do firmware nem garantia de desempenho em outros modelos. PSX com BIOS emulada foi testado com um jogo; isso não equivale a compatibilidade completa.

## Origem

Base: [Ansub/tv-detox](https://github.com/Ansub/tv-detox), MIT. Veja LICENSE e NOTICE.md. O repositório não executa debloat automático nem remove pacotes de sistema.
