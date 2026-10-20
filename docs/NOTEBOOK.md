# TvRetro Controle — aplicativo de bandeja

O controle principal do notebook agora é um aplicativo GTK nativo, sem navegador, captura de imagem ou espelhamento. O menu da bandeja permite abrir a janela, enviar Home/Voltar/volume e sair.

## Instalação por usuário no Linux

Dependências: Python 3 do sistema, PyGObject/GTK 3, Ayatana AppIndicator e Android Platform Tools (ADB). Em sistemas Ubuntu/Zorin que precisarem dos pacotes:

```
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 adb
```

Depois, na pasta do repositório:

```
/usr/bin/python3 tools/tray/install-user.py --tv IP_DA_TV --autostart
```

A opção `--autostart` inicia apenas o ícone ao entrar no computador. Sem essa opção, inicie pelo menu de aplicativos. `--adb-port PORTA` permite usar outro servidor ADB local. A instalação atual do notebook usa o servidor já existente; o IP e essa porta ficam apenas no arquivo particular `~/.config/tvretro/config.json`, nunca no Git.

O instalador preserva a configuração existente em uma atualização. Caso a biblioteca Ayatana já exista mas falte o typelib, `--typelib PASTA` permite copiar o typelib de um pacote oficial para a pasta local do app; não se deve redistribuir esse binário no repositório. No notebook alvo isso evitou instalar pacotes de sistema com sudo.

## Uso

- Procure **TvRetro Controle** no menu de aplicativos.
- Clique no ícone da TV na bandeja → **Abrir controle**. Clique do meio também pode abrir, conforme o painel.
- Na janela: setas e Enter navegam; Esc/Backspace enviam Voltar. Há botões para Home, reprodução e volume.
- Fechar a janela mantém o ícone. **Sair** no menu da bandeja encerra o aplicativo.
- Em **Configurações**, altere o IPv4 da TV, salve/reconecte e escolha iniciar na bandeja ao entrar no computador.
- O aplicativo não monitora teclado globalmente, não consulta a TV periodicamente e não inicia captura/streaming. A conexão ocorre ao enviar o primeiro comando ou reconectar. Comandos são serializados sem fila acumulada.

A TV precisa estar na mesma rede, com ADB de rede habilitado e computador autorizado. Ele não liga uma TV completamente desligada e não faz pareamento Bluetooth. Se a conexão cair, confira o endereço/depuração e tente novamente. O suporte depende das políticas de depuração do firmware.

## Arquivos locais e remoção

Aplicativo: `~/.local/share/tvretro/`. Atalho: `~/.local/share/applications/tvretro-controle.desktop`. Inicialização: `~/.config/autostart/tvretro-controle.desktop`. Configuração particular: `~/.config/tvretro/config.json`.

Para parar, use **Sair**. Para desativar a inicialização automática, desmarque a opção nas configurações e salve. Para desinstalar, encerre o aplicativo e remova somente esses arquivos/pastas, preservando a configuração se quiser reutilizá-la. Não remova a pasta geral `~/.config` nem `~/.local/share`. Nenhum APK é instalado na TV pelo instalador do controle.

## Transmissão de tela e controle antigo

O controle web antigo em `tools/controle-tv.py` é legado e não faz parte do aplicativo de bandeja. O scrcpy não é dependência do novo app.

Para mostrar o notebook na TV, HDMI continua sendo uma opção separada. Google Cast estava desativado e não foi reativado nesta entrega. No Linux/Wayland não se deve garantir transmissão de tela inteira sem testar. [Documentação do Google](https://support.google.com/chrome/answer/3228332).

## Controle ampliado — etapa 1

A interface agora tem três abas, com as mesmas dependências GTK 3:

- **Controle:** direcional, Home/Voltar, Menu, volume/mudo, reprodução/pausa, anterior/próximo, avançar/retroceder e Informações. As teclas de mídia dependem do app em primeiro plano. Na aba Controle, setas/Enter/Esc enviam comandos à TV; nas outras abas e na configuração, o teclado navega pela interface local.
- **Aplicativos:** **Carregar apps da TV** consulta activities de TV e de launcher, remove duplicatas e mostra no máximo 100 pacotes. Clique para abrir. Nomes conhecidos recebem rótulos; os demais aparecem pelo pacote, sem baixar ícones ou puxar APKs da TV. A lista é refeita somente quando solicitada e não é salva em arquivo.
- **TV:** atalho para o seletor de entradas HDMI, configurações do Android, RAM/armazenamento sob demanda, acordar a tela e suspender com confirmação. HDMI abre o seletor da TV; não seleciona automaticamente uma porta. Acordar exige rede e ADB respondendo, e não substitui Wake-on-LAN. Se o firmware recusar uma função, o controle informa indisponibilidade.

Não há coleta de histórico de uso, captura de tela, servidor de mídia ou consulta periódica. A leitura de RAM é `MemAvailable`, não uma soma do consumo de processos; os valores são da última consulta manual. Comandos continuam serializados, com tempo limite e sem fila acumulada. Fechar mantém a bandeja; Sair encerra. Atualize com o mesmo instalador para preservar a configuração e o autostart existentes.

### Referência e próximas etapas

A organização de funções foi inspirada no [TVmenubar-MacOS](https://github.com/gabrielgreco1/TVmenubar-MacOS). Esse projeto usa Swift/macOS e protocolos LG webOS/Roku. A implementação aqui é própria para GTK/Linux e Android TV via ADB: não é um port binário nem promete compatibilidade com os protocolos LG/Roku. Nenhum código Swift, logo ou recurso de marca do projeto foi copiado.

Etapas futuras, sujeitas a teste na TCL: seleção direta de portas HDMI e identificação do app atual; teclado/touchpad; descoberta local e Wake-on-LAN se o firmware permitir. Uso histórico, ajustes de imagem e envio de mídia exigem desenho e validação próprios. Espelhamento permanece fora do escopo solicitado. Essas funções não estão implementadas nesta etapa.

Testes locais sem TV:

```bash
python3 tests/test_tray_backend.py
python3 tests/test_tray_install.py
```

O backend testa validação de endereços/componentes, montagem de argumentos, parsers, limites e falhas, sem acessar configuração privada, GUI ou rede. Testes simulados não comprovam funcionamento de cada comando em todos os firmwares.
