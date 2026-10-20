# Notebook e TV

São direções diferentes:

## Controlar e ver a TV no notebook

Execute `python3 tools/controle-tv.py --tv IP_DA_TV`. Requer Python 3 e Android Platform Tools (ADB). Na TV, depuração de rede ativa e computador autorizado. A página abre em 127.0.0.1 com porta/token aleatórios. Setas/Enter/Escape, Home, volume, play e captura manual. Não recebe comandos arbitrários nem abre um serviço HTTP na TV. Feche com Ctrl+C no terminal; o controle fica indisponível depois disso.

Para vídeo ao vivo, instale o [scrcpy do projeto oficial](https://github.com/Genymobile/scrcpy/blob/master/doc/linux.md) e passe `--scrcpy /caminho/scrcpy`. O modo preparado usa 1024 pixels, 15 fps, 2 Mbps e sem áudio para reduzir o custo na TV. Setas/Enter navegam; Alt+Home envia Home no scrcpy. Conteúdo protegido de streaming pode ficar preto. Não confundir isso com defeito da home.

O scrcpy usa um servidor temporário pelo ADB durante a sessão; não é um APK permanente. Para máxima leveza, use só os botões do controle local, sem espelhamento ou atualização contínua de imagem. ADB é necessário enquanto usar essas funções; não será desligado automaticamente.

## Mostrar o notebook na TV

**HDMI:** conecta o notebook à entrada HDMI da TCL e seleciona HDMI 1/2. No Zorin, Configurações → Monitores → espelhar ou estender. Não usa RAM para emular outro receptor Android e é a opção mais previsível para tela inteira/baixa latência. Depende do cabo/porta do notebook.

**Google Cast:** receptor `com.google.android.apps.mediashell` estava desativado na TV alvo e foi mantido assim. O Chrome oferece Transmitir, salvar e compartilhar → Transmitir; selecione a TV na mesma rede. A documentação atual do Google descreve transmissão de tela inteira em Mac/Windows/Chromebook; no Linux/Wayland não garantir tela inteira nem áudio. Transmitir uma aba é o primeiro teste indicado quando houver Chrome instalado. Não foi instalado navegador nem realizada sessão Cast no notebook nesta entrega.

Reativação opcional, somente após decidir usar Cast:

```
adb -s IP_DA_TV:5555 shell pm enable --user 0 com.google.android.apps.mediashell
```

Desfazer essa reativação (caso ele estivesse desativado antes):

```
adb -s IP_DA_TV:5555 shell pm disable-user --user 0 com.google.android.apps.mediashell
```

Não se deve remover Google Cast para usar scrcpy, e scrcpy não transmite o desktop do notebook para a TV.

Fonte: [Google: transmissão pelo Chrome](https://support.google.com/chrome/answer/3228332).
