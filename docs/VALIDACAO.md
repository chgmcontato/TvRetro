# Histórico de validação

Este documento é cronológico. As pendências de cada etapa descrevem o que ainda não havia sido testado naquele momento. O resultado mais recente está na seção final, de validação em aparelho; não interpretar uma validação parcial como cobertura completa.

## Entrega 0.8

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
- **Na etapa inicial, não validado em TV real.** A execução posterior limitada está registrada na seção final. O comportamento de `pm disable-user`, `cmd package` e dos nomes de pacote varia entre fabricantes e versões do Android. Tratar a primeira execução em cada modelo como experimental.

## 0.9.1 — etapa automatizada do receptor e debloat

- `test_transfer.py`: cenários HTTP anteriores e novos POSTs de 8 MiB rejeitados com 409, 413 e 507; linhas de status 200/403/409; erro interno 500 sem caminho ou detalhe da exceção no corpo; atividade a cada segundo mantém a sessão e 2 segundos sem atividade fecham o socket no Harness. O caso 409 reproduziu BrokenPipeError antes da correção.
- `test_transfer_status.py`: 12 cenários JVM de statusFor, incluindo timeout, interrupção, argumentos inválidos, falta de espaço direta/causal e falhas internas. Receptor e testes compilados com JDK 17, source/target 1.8; isso não valida APIs Android.
- `test_catalog.py`: matcher passou. `test_tray_install.py`: 2 testes passaram. `test_debloat.py`: 12 testes com ADB simulado passaram, sem executar debloat na TV.
- Não testados: compilação/instalação do APK, interface e callbacks no Android real, sessão real de 10/60 minutos, upload real na TV, debloat em TV real. O timeout curto testa o rastreamento de atividade pelo Harness; o agendamento Android foi revisado apenas em código.

## Correções após teste de carga — 2026-10-20

- Regressões reproduzidas antes da correção: nomes com múltiplas quebras de linha retornaram 200; cabeçalho individual acima de 8 KiB retornou 500. Após a correção, `test_transfer_validation.py` passou seus 3 testes: nomes recusados com 400 sem arquivo criado, cabeçalho excessivo com 400 e espera de cabeçalho encerrada com 408. `test_transfer_status.py` passou 13 cenários, incluindo ProtocolException como erro 400.
- `test_platform_compat.py`: teste JVM do adaptador real de permissões com doubles para API 21/22/23/35 passou. Verifica permissão concedida/negada e evita chamadas de API 23 em versões antigas. Não é execução no Android. Consulta diária de Wi-Fi fica indisponível na API 21/22; rede e taxa atual usam o caminho legado.
- Todos os testes anteriores passaram novamente: receptor HTTP, catálogo, instalador de bandeja (2) e debloat simulado (12). Classes Java do launcher compiladas com JDK 17, source/target 1.8, android.jar 35 e stubs de lambdas. Nenhum APK foi gerado ou assinado.
- `test_transfer_stress.py` passou: 500 GETs, 80 uploads de 64 KiB com integridade, upload sintético de 64 MiB por streaming/SHA-256 com heap de 64 MiB, concorrência e recuperação da trava, 30 interrupções sem arquivo parcial/final, nomes inválidos, recuperação após 3,3 s de descarte, 80 entradas malformadas e saturação com 20 conexões. Arquivos são temporários; não acessa a TV nem usa ROMs. Métricas de /proc, quando disponíveis, são do JVM local, não da TV; aquecimento não permite concluir ausência de vazamentos.
- Não testados: APK completo/dex/assinatura, execução em TV/emulador (incluindo API 21), layouts/ciclo de vida Android, Bluetooth, jogos/RetroArch reais, fonte de capas real, sessões reais de 10/60 minutos, memória prolongada e debloat em TV real. O suporte mínimo continua exigindo validação em aparelho antigo.

## Validação em aparelho — 2026-10-20

### Compilação e atualização

- APK 0.9.1, código 15: compilação completa com JDK 17/SDK 35, geração de DEX, alinhamento e assinatura concluídos. O certificado SHA-256 foi comparado ao do APK instalado e era idêntico. Atualização com `adb install -r`, sem desinstalar; fonte e wallpaper pessoais preservados no build privado. Esses assets, chaves e APKs não fazem parte da distribuição fonte.
- TvRetro continuou como Home padrão. As abas Aplicativos, Jogos e Monitorar abriram; capas online, indicador de conexão/taxas e métricas locais ficaram visíveis. Foram feitas 24 trocas de abas em duas etapas, sem crash do launcher encontrado no buffer consultado. Isso não certifica ausência de falhas.

### Receptor na TV

- Página de envio: 200; token inválido: 403; três nomes com múltiplas quebras de linha: 400; linha de cabeçalho excessiva: 400; tentativa de envio abaixo da reserva de espaço: 507. Ao sair da tela, o receptor deixou de responder. Nenhum `.part` foi encontrado na biblioteca.
- O espaço disponível estava abaixo dos 550 MiB reservados. Portanto, **não houve envio completo bem-sucedido de um novo jogo na TV** nessa sessão. Os testes locais de envio/integridade e de carga continuam válidos dentro de seu próprio escopo, sem substituir essa pendência em aparelho.

### Jogos, controles e Play Store

- Um jogo SNES e um PSX iniciaram no RetroArch, com introduções observadas. Home retornou ao TvRetro. O emulador aberto para teste foi encerrado ao final; não houve teste prolongado de jogabilidade, saves ou compatibilidade de outros títulos.
- O usuário confirmou funcionamento dos controles físico e do S24 FE. A reconexão Bluetooth durante um jogo não foi repetida nesta sessão.
- A Play Store abriu inicialmente com mensagem genérica sobre Wi-Fi. O Android reportava conexão validada e os registros da loja indicavam `AuthFailureError`, exigindo novo login. Play Services e Google Services Framework estavam habilitados. Após o usuário concluir a autenticação diretamente na TV, a loja exibiu catálogo, recomendações e imagens, sem restaurar os apps removidos. A causa observada era autenticação; isso não permite atribuir toda mensagem semelhante a login. Instalação/compra de apps pela loja não foi testada.

### Memória, debloat e limites

- Durante o uso aquecido, o PSS reportado do launcher oscilou aproximadamente entre 63 e 72 MiB. A medição anterior, em outra condição de atividade/paginação, não serve como comparação direta de economia. Não foi demonstrado vazamento, mas a execução curta também não prova sua ausência.
- O script de debloat desativou somente `com.android.htmlviewer`, com confirmação e registro. O total de pacotes desativados passou de 23 para 24; a Home permaneceu TvRetro. Animações e protetor já estavam desligados. Reinício e desfazer não foram exercitados.
- Uma remoção personalizada posterior de seis componentes opcionais já desativados foi realizada fora do script, apenas para o usuário da TV. Não é parte do fluxo de debloat distribuído, não amplia sua lista de candidatos e não representa teste de desinstalação pelo script. Não houve ganho significativo de armazenamento, pois APKs do firmware permaneceram.
- **Ainda pendentes:** Android 5.x/API 21 real; sessões reais de 10/60 minutos; upload completo na TV; memória e jogabilidade prolongadas; reconexão Bluetooth durante jogo; reinício/restauração após debloat; demais candidatos/launchers/ajustes do script em aparelho. Não há certificação para outras TVs ou auditoria completa de firmware.

Os registros brutos, capturas e builds pessoais permanecem fora do Git. Não publicar dados de rede, conta, serial, tokens, chaves, ROMs, BIOS ou assets particulares ao compartilhar evidências.

## Controle do notebook — etapa 1 inspirada em menu bar

- Interface GTK dividida em Controle, Aplicativos e TV; inventário de apps e RAM/armazenamento sob demanda, seletor HDMI, comandos de reprodução e suspensão com confirmação. Implementação Android/ADB própria, sem código Swift ou assets do projeto de referência.
- `test_tray_backend.py`: 10 testes locais passaram, cobrindo endereço, componentes inválidos/metacaracteres, deduplicação/limite, argumentos fixos, timeout e parsers. `test_tray_install.py`: 2 testes passaram, incluindo preservação de configuração e instalação do novo módulo.
- Interface construída com GTK 3 instalado; troca de abas, renderização de apps com nomes longos e isolamento do teclado local foram conferidos. Preview offscreen usado para inspecionar o layout; essa verificação não equivale a testar comandos na TV. A inicialização normal não registrou traceback ou erro crítico no log consultado.
- Aplicativo do notebook atualizado por usuário e iniciado, mantendo configuração/typelib existentes. Backup dos arquivos anteriores em pasta privada ignorada pelo Git. Nenhum APK ou pacote da TV foi alterado nessa etapa.
- **Não validado na TCL nesta etapa:** a conexão ADB foi recusada. Abertura de apps, seletor HDMI, leitura real de métricas, reprodução e acordar/suspender precisam de teste em aparelho. Não confundir confirmação de envio ADB com confirmação de efeito do comando em cada firmware. Compatibilidade macOS/LG/Roku não foi implementada.
