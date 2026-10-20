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
