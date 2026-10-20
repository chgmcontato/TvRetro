# Validação da entrega 0.8

- Compilação JDK 17 + Android 35: versão pessoal e árvore fonte sem assets particulares, ambas concluídas.
- Assinatura da versão pessoal compatível com a instalação anterior; instalação por atualização concluída na TCL Android TV 11. Dados e jogos preservados.
- Biblioteca com nove jogos: capas visíveis no início e no fim, rolagem e foco por direcional até o último título. Decodificação por visibilidade e varredura em worker; as views ainda não são recicladas.
- Receptor JVM: envio SNES e PSX, token inválido, pré-checagem, duplicidade sem sobrescrita, tentativa de sair da pasta, formato negado, origem diferente, arquivo vazio, interrupção sem .part, reserva de espaço, limite de cabeçalhos e tamanho do token. `python3 tests/test_transfer.py` compila o receptor e executa os testes em pasta temporária. Nenhum teste envolve ROM comercial.
- Controle do notebook: Python compilado, página local abriu, botão Home recebeu sucesso, captura de tela válida exibida. Firmware TCL escreve um prefixo textual antes do PNG; o controle trata isso procurando a assinatura PNG.
- scrcpy oficial 5.0.1 Linux x86_64: SHA256 verificado contra digest da release na API GitHub. TV reconhecida, gravação de cinco segundos concluída. Janela Wayland com renderização por software também foi iniciada em teste de três segundos; log confirmou textura 1024×576 e término normal. Não prometer teste de todos os atalhos/joystick.
- Google Cast não reativado; sessão de transmissão notebook → TV não realizada. ADB mantido porque é necessário para o controle do notebook.
- Não houve teste prolongado de consumo de memória, regressão completa de todos os jogos/streamings ou auditoria interna do firmware. Não atribuir economia fixa de RAM às mudanças.
- Pendrive não formatado, conectado nem migrado nesta etapa. Saves e ROMs não apagados.

## Regressões a repetir após mudanças futuras

Trocar entre dois jogos, sair e voltar pelo Home, reconectar Phone Pad após outro app no celular, retornar do menu de permissões, conectar/desconectar USB com biblioteca aberta e encerrar transferência no meio de um arquivo. Alguns desses cenários foram validados em versões anteriores; isso não substitui testar novamente após alterar sua implementação.

## Entrega 0.8.1 e controle de bandeja

- Nome instalado da home: TvRetro; pacote preservado, versionCode13. Atualização com mesma assinatura, sem desinstalar nem mudar a home padrão.
- Python do aplicativo/instalador compilado sem erro; arquivos desktop validados. Indicador registrado pelo StatusNotifierWatcher do Zorin; ações da aplicação publicadas na sessão e instância única verificada pela ativação do aplicativo existente.
- Comando Home enviado pela ação real do app; estado retornou “Conectado à TV • pronto para usar”. Não se afirma teste manual de todos os botões.
- Instalado somente no usuário. Bibliotecas GTK/Ayatana já existiam; typelib ausente obtido de pacote oficial Ubuntu, sem instalar novos pacotes de sistema. Configuração privada fora do Git; atalho de inicialização contém somente caminho local, sem IP.
- Fechar mantém a aplicação por desenho de ciclo de vida; Sair encerra. Não há timer de polling, servidor HTTP ou execução de scrcpy no novo aplicativo.
- Testes do receptor JVM continuaram passando após a mudança de nome. Nenhum jogo/save foi movido ou apagado nesta entrega.

## Entrega 0.9 — capas online e cabeçalho

- Fonte pessoal e fonte sanitizada sem assets particulares compiladas. APK sem pasta de capas: aproximadamente457KiB, contra cerca de3,1MiB na0.8.1. Mesma assinatura, pacote e home padrão.
- Cabeçalho verificado visualmente em Aplicativos, Jogos, Monitorar e Enviar jogos. Exibe conexão e taxas da TV inteira em KiB/s; aparece também por implementação na breve ponte de abertura de jogo, sem sobrepor o RetroArch.
- Capas de Castlevania, Chrono Trigger, Donkey Kong Country e Bomberman2 apareceram na TCL pela internet, sem PNGs incorporados. Demais títulos foram resolvidos contra o catálogo real; carregamento de imagens ocorre sob demanda. O primeiro protótipo buscava todo o índice; o final tenta primeiro a URL do título/região para reduzir tráfego e alocações.
- Matcher JVM determinístico: regiões/tags/Gold Cartridge, título ambíguo, ausente, URL encoding e rejeição de caminhos; testes em tests/test_catalog.py. Receptor HTTP mantém os testes anteriores passando. Lookup adicional de Crash Bandicoot e Tekken3 confirmou que a busca não depende dos nove jogos da instalação alvo.
- Fallback sem imagem é parte da implementação; Wi-Fi da TV não foi desativado para simular indisponibilidade. Não se afirma teste completo de todas as falhas de rede ou catálogo.
- Nove ROMs e saves mantidos no armazenamento interno; thumbnails públicos já vazios. Sem formatação ou migração de USB. No teste após retirar as imagens do APK, aproximadamente539MiB livres.
- Não foi feito teste longo de emulação/desempenho. Catálogo online e correspondência por nome podem mudar ou não incluir um título; isso não impede abrir a ROM.

## Debloat guiado (tools/debloat)

- Testes automatizados com `adb` simulado (`python3 tests/test_debloat.py`, 12 cenários): simulação sem alterar nada, protegidos e apps do usuário intocados, só o confirmado é desativado, desfazer pelo registro e pela lista da TV, telas iniciais condicionadas ao TvRetro, apps persistentes preservados e reativação automática quando a Home deixa de abrir o TvRetro.
- **Não validado em TV real.** O comportamento de `pm disable-user`, `cmd package` e dos nomes de pacote varia entre fabricantes e versões do Android. Tratar a primeira execução em cada modelo como experimental.
