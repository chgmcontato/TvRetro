# TvRetro — sua Android TV como console retrô (SNES e PlayStation)

O TvRetro é uma tela inicial (launcher) leve para Android TV. Ela mostra seus aplicativos do dia a dia (Netflix, YouTube etc.), uma biblioteca de jogos de SNES e PlayStation com capas baixadas automaticamente, um monitor de memória e rede, e uma tela para enviar jogos do celular ou do computador para a TV. Se a sua TV ainda está de fábrica, o projeto também traz uma **limpeza guiada e reversível** dos apps que você não usa.

É um projeto pessoal, feito aos poucos com ajuda de IA e testado em uma **TCL Android TV 11**. Em outras TVs pode funcionar ou não: leia a seção [Validação e limites](#validação-e-limites).

> **Aviso legal.** Este repositório **não contém nem indica ROMs ou BIOS**. Use apenas jogos que você tem direito de usar (por exemplo, backups de cartuchos e discos que você possui). Você é responsável pelo que instala na sua TV.

---

## Sumário

1. [O que vem no projeto](#o-que-vem-no-projeto)
2. [O que você precisa](#o-que-você-precisa)
3. [Antes de começar: 4 decisões](#antes-de-começar-4-decisões)
4. [Caminho A — instalar com ajuda do Claude ou do Codex](#caminho-a--instalar-com-ajuda-do-claude-ou-do-codex)
5. [Caminho B — instalar pelo Terminal ou CMD](#caminho-b--instalar-pelo-terminal-ou-cmd)
6. [Colocando seus jogos](#colocando-seus-jogos)
7. [Controles opcionais](#controles-opcionais)
8. [Problemas comuns](#problemas-comuns)
9. [Segurança](#segurança)
10. [Validação e limites](#validação-e-limites)
11. [Estrutura do repositório](#estrutura-do-repositório)
12. [Créditos e licença](#créditos-e-licença)

---

## O que vem no projeto

| Parte | O que faz | Onde fica |
|---|---|---|
| **TvRetro** (launcher da TV) | Abas Aplicativos, Jogos e Monitorar; capas online; envio de jogos pela rede | `apps/tv-casa` |
| **Phone Pad** (opcional) | Usa o celular Android como controle Bluetooth. Experimental | `apps/phone-pad` |
| **TvRetro Controle** (opcional) | Ícone na bandeja do notebook Linux para mandar setas, Home, Voltar e volume | `tools/tray` |
| **Limpeza da TV / debloat** (opcional, recomendada em TV de fábrica) | Desativa (não desinstala) apps dispensáveis, item a item, com registro e como desfazer | `tools/debloat` |

O jogo em si roda no **RetroArch**, que você instala separadamente. O TvRetro só organiza a biblioteca e abre o jogo no RetroArch.

## O que você precisa

- Uma **Android TV ou Google TV** (Android 5.0 ou mais novo; compatibilidade 5.x ainda não validada em aparelho) na mesma rede Wi-Fi/cabo do seu computador.
- Um **computador** (Linux, macOS ou Windows com WSL) para compilar e instalar.
- Um **celular** ou o próprio computador para enviar os jogos (opcional se você usar pendrive).
- Alguns GB livres na TV, ou um pendrive. TVs baratas têm pouco armazenamento: o receptor de jogos sempre deixa **550 MiB livres** e recusa envios que passem disso.
- Os seus próprios arquivos de jogo (ROMs) nos formatos listados em [Colocando seus jogos](#colocando-seus-jogos).

Não é preciso saber programar. Você só vai copiar e colar comandos, ou deixar uma IA fazer isso por você (Caminho A).

---

## Antes de começar: 4 decisões

Responda estas quatro perguntas antes de qualquer passo. As três primeiras definem o que será compilado dentro do app; a quarta define se a TV será limpa.

### 1. Fundo da tela inicial: genérico ou uma imagem sua?

- **Genérico:** não faça nada. Sem imagem, o app usa um fundo sólido escuro e fonte monoespaçada.
- **Imagem sua:** prepare um arquivo **JPG**, de preferência em 1920×1080 e leve (idealmente abaixo de 1 MB, porque ele vai dentro do APK). Ele deve ficar em:

  `apps/tv-casa/assets/backgrounds/home.jpg`

  A pasta `backgrounds` não existe ainda; você a cria no passo da personalização. O arquivo fica só no seu computador (o `.gitignore` impede de ir para o GitHub).

### 2. Quais aplicativos você usa no dia a dia?

A aba **Aplicativos** mostra a lista que está em `apps/tv-casa/apps.txt`, **um nome de pacote por linha**. A lista que vem de exemplo:

```text
com.crunchyroll.crunchyroid
com.google.android.youtube.tv
com.disney.disneyplus
com.wbd.stream
com.netflix.ninja
com.amazon.amazonvideo.livingroom
```

Esses são, respectivamente: Crunchyroll, YouTube, Disney+, Max, Netflix e Prime Video. Para os **seus** apps:

1. Instale os apps na TV normalmente pela loja.
2. Com a TV conectada ao computador por ADB (passo 6 do Caminho B), liste os pacotes instalados por você:
   - Linux/macOS/WSL: `adb shell pm list packages -3`
   - Para procurar um app pelo nome: `adb shell pm list packages | grep -i nome`
   - No CMD do Windows (sem WSL): `adb shell pm list packages | findstr /i nome`
3. O nome depois de `package:` é o que vai no `apps.txt`.

### 3. Você vai usar pendrive para as ROMs?

- **Não (memória interna):** os jogos ficam em `Games/SNES` e `Games/PSX` na memória interna da TV. É o jeito mais simples; o envio pelo celular grava aqui.
- **Sim (pendrive):**
  - Mantenha o pendrive como **armazenamento removível**. **Não** aceite "usar como armazenamento interno" na TV.
  - Formato: **FAT32** é a aposta mais segura (cada arquivo precisa ter menos de 4 GiB). Na TCL testada, um pendrive **exFAT** foi reconhecido mas o sistema declarou exFAT não suportado.
  - Estrutura na raiz do pendrive: `Games/SNES/` e `Games/PSX/`.
  - Atenção: o envio pela tela "Enviar jogos" **continua gravando na memória interna**, mesmo com pendrive conectado. Com pendrive, copie os arquivos pelo computador.
  - Faça backup do que já existe no pendrive antes de formatar qualquer coisa.
  - O pendrive libera espaço de armazenamento, mas **não aumenta a memória RAM** da TV.

### 4. Quer limpar a TV (debloat)?

- **Sim (recomendado para TV de fábrica):** depois de instalar o TvRetro, o script `tools/debloat/tvretro-debloat.sh` desativa apps dispensáveis de uma **lista curta e conservadora**, **um por vez, perguntando antes**. Nada é desinstalado, tudo fica registrado e dá para desfazer. Apps de sistema essenciais, Google Play, teclado, Bluetooth, entradas HDMI e os seus apps nunca são oferecidos. Detalhes em [docs/DEBLOAT.md](docs/DEBLOAT.md).
- **Não:** pule o passo 9 do Caminho B. A TV continua como está.

Mesmo escolhendo "sim", apps do fabricante (TCL, Philips, Hisense etc.) **não** são desativados sozinhos: ficam num relatório para você revisar.

---

## Caminho A — instalar com ajuda do Claude ou do Codex

Neste caminho, um assistente de IA com acesso ao seu computador executa os comandos do Caminho B por você, pedindo confirmação a cada passo. Você pode usar o **Claude Code** (na aba Code do app do Claude para computador, ou no terminal) ou o **Codex**. Siga a instalação oficial da ferramenta escolhida e abra uma **pasta vazia** nela (por exemplo, `TvRetro-meu`).

> **Atenção:** o chat comum do Claude (site e app de celular) roda nos servidores da Anthropic e **não enxerga a sua TV**. É preciso uma ferramenta que rode no seu computador, como as acima.

### O que a IA não consegue fazer por você

Estes passos são sempre seus, na TV:

1. Ativar as **Opções do desenvolvedor** e a **depuração por rede/USB** (veja o passo 5 do Caminho B).
2. Dizer o **IP da TV** (Configurações → Rede).
3. **Aceitar o pop-up** "Permitir depuração?" que aparece na TV.
4. Escolher o **TvRetro como tela inicial** quando a TV perguntar.
5. Digitar **a senha da sua chave de assinatura** (a IA nunca deve pedir nem ver essa senha).

### Prompt para colar

Preencha os campos entre colchetes e cole na ferramenta:

```text
Quero instalar o TvRetro (https://github.com/chgmcontato/TvRetro) na minha Android TV, passo a passo, neste computador. Clone o repositório, leia o README.md e siga o "Caminho B".

Minhas respostas:
1) Fundo da tela inicial: [GENÉRICO (fundo sólido) | IMAGEM MINHA: caminho do arquivo, ex.: C:\Users\eu\Pictures\fundo.jpg]
2) Apps que uso no dia a dia na TV: [ex.: Netflix, YouTube, Disney+, Prime Video]
3) Vou usar pendrive para as ROMs? [SIM (formato atual: FAT32 / exFAT / não sei) | NÃO, vou usar a memória interna]
4) Limpar a TV (debloat) depois de instalar? [SIM, com confirmação item a item | NÃO]
5) Sistema do computador: [Windows (WSL) | Linux | macOS]
6) IP da TV: [ex.: 192.168.1.50 | não sei, me ensine onde ver]

Regras:
- Se alguma resposta estiver vazia, pergunte uma por vez antes de agir.
- Antes de cada comando que instale programas, grave arquivos fora da pasta do projeto ou use o adb, explique em uma frase e peça minha confirmação.
- Depois que a TV estiver conectada por adb, descubra os nomes de pacote dos meus apps (adb shell pm list packages -3, filtrando por nome) e edite apps/tv-casa/apps.txt, um pacote por linha. Mostre o arquivo final antes de compilar.
- Se escolhi imagem: copie para apps/tv-casa/assets/backgrounds/home.jpg (converta para JPG, de preferência 1920x1080 e leve). Se escolhi genérico: não crie esse arquivo.
- Crie a chave de assinatura FORA do repositório. Eu digito a senha no terminal. Nunca peça, mostre, repita ou grave a senha no chat, em arquivos ou no histórico. Se a ferramenta não deixar eu digitar, me dê o comando para eu rodar sozinho.
- Os passos na TV (opções do desenvolvedor, depuração por rede, autorizar o computador, escolher TvRetro como Home) são meus: diga exatamente o que apertar e espere eu confirmar.
- Não baixe, procure nem sugira ROMs ou BIOS. Use o adb apenas para connect, devices, install, push, shell pm list packages e uninstall do TvRetro. Não remova nem desative nenhum app da TV.
- Se eu usar pendrive: não formate nem apague nada. Apenas explique a estrutura Games/SNES e Games/PSX e o formato.
- Se eu escolhi limpar a TV: só depois que o TvRetro for a tela inicial padrão, rode `tools/debloat/tvretro-debloat.sh --tv IP --dry-run` e me explique em português simples o que cada app da lista faz. Depois rode sem `--dry-run`, e use `--launchers` e `--tuning` só se eu aceitar. Não use outros comandos de remoção.
- Regras da limpeza: desative, nunca desinstale (`pm disable-user --user 0`); peça minha confirmação antes de CADA mudança; nunca desative Google Play, Google Play Services, Configurações, System UI, apps de configuração inicial, teclado, Bluetooth, entradas HDMI nem o sintonizador/framework de TV; na dúvida, deixe ligado. Apps do fabricante (relatório tv-revisar-*.txt): explique um por um e só desative os que eu aprovar, acrescentando-os em tools/debloat/lists/pessoal.txt.
- Mantenha o registro tv-changes-*.txt e me diga como desfazer (`--undo`). Depois da última mudança, espere 30 s, reinicie a TV uma vez e confirme comigo que Home, Wi-Fi, Bluetooth, HDMI, teclado e meus apps funcionam antes de dizer que terminou.
- No fim, resuma o que foi instalado, o que foi desativado e como enviar meus jogos.
```

### Dicas ao usar IA

- Leia o comando antes de aprovar. Se algo parecer estranho (apagar pastas, `sudo` sem motivo, baixar de sites desconhecidos), recuse e pergunte por quê.
- Se a IA travar, volte ao Caminho B e continue do ponto onde parou.
- A IA pode errar nomes de pacotes de apps: confirme com `adb shell pm list packages`.

---

## Caminho B — instalar pelo Terminal ou CMD

Testado pelo autor em **Linux** (Zorin/Ubuntu). O roteiro para macOS segue o que o script `build.sh` prevê, mas **não foi validado**. No **Windows**, o script de compilação (`build.sh`) precisa de um shell POSIX: use o **WSL** (Ubuntu) para tudo, ou compile no WSL e use o `adb` do Windows no CMD. Esse caminho no Windows também **não foi validado** pelo autor.

### 1. Instale as ferramentas no computador

**Ubuntu, Zorin, Debian (ou Ubuntu dentro do WSL):**

```bash
sudo apt update
sudo apt install git openjdk-17-jdk zip unzip adb
```

**macOS (Homebrew):**

```bash
brew install git openjdk@17 android-platform-tools
brew install --cask android-commandlinetools
```

**Windows:** abra o PowerShell como administrador, rode `wsl --install -d Ubuntu`, reinicie se pedido, abra o Ubuntu e siga os comandos de Ubuntu acima.

Confirme as versões:

```bash
java -version      # deve mostrar 17
adb version
```

### 2. Instale o Android SDK (plataforma 35 e build-tools 35.0.0)

Baixe as "Command line tools only" em <https://developer.android.com/studio#command-line-tools-only>.

Linux/WSL:

```bash
mkdir -p "$HOME/Android/Sdk/cmdline-tools"
unzip commandlinetools-linux-*.zip -d "$HOME/Android/Sdk/cmdline-tools"
mv "$HOME/Android/Sdk/cmdline-tools/cmdline-tools" "$HOME/Android/Sdk/cmdline-tools/latest"
export ANDROID_HOME="$HOME/Android/Sdk"
yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --licenses
"$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" "platforms;android-35" "build-tools;35.0.0"
```

macOS:

```bash
sdkmanager "platforms;android-35" "build-tools;35.0.0"
```

Defina `JAVA_HOME` se o script reclamar (Linux: `export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64`).

### 3. Baixe o projeto e personalize

```bash
git clone https://github.com/chgmcontato/TvRetro.git
cd TvRetro
```

- **Seus apps:** edite `apps/tv-casa/apps.txt` (um pacote por linha). Você pode deixar a lista de exemplo agora e ajustá-la depois de conectar a TV; basta recompilar.
- **Seu fundo (se escolheu imagem):**

  ```bash
  mkdir -p apps/tv-casa/assets/backgrounds
  cp /caminho/da/sua/imagem.jpg apps/tv-casa/assets/backgrounds/home.jpg
  ```

  Se escolheu fundo genérico, pule.
- Fontes (opcional): `apps/tv-casa/assets/fonts/Courier_New.ttf` e `Courier_New_Bold.ttf`. Sem elas, usa fonte monoespaçada.

### 4. Crie sua chave de assinatura (uma vez só)

O Android só aceita APK assinado. **Guarde essa chave**: para atualizar o app depois, é preciso usar a mesma chave. Com outra chave, você terá que desinstalar o app antes (e pode perder dados dele).

```bash
keytool -genkeypair -v -keystore "$HOME/tvretro-chave.jks" -alias tvretro -keyalg RSA -keysize 2048 -validity 10000
```

Ele pergunta uma senha e seus dados; invente uma senha forte e anote em lugar seguro. **Nunca** coloque a chave dentro da pasta do projeto nem a envie ao GitHub.

### 5. Prepare a TV

1. Na TV: **Configurações → Preferências do dispositivo → Sobre** e aperte **Versão/Build** 7 vezes. Isso libera as **Opções do desenvolvedor**.
2. Em **Opções do desenvolvedor**, ligue **Depuração USB** e, se existir, **Depuração por rede/Wi-Fi**. Os nomes mudam conforme o fabricante.
3. Anote o **IP da TV** em Configurações → Rede.

### 6. Compile e instale o TvRetro

A senha é digitada sem aparecer na tela e não fica no histórico:

```bash
export KEYSTORE="$HOME/tvretro-chave.jks"
read -rs KEYSTORE_PASS && export KEYSTORE_PASS
sh apps/tv-casa/build.sh
```

O APK sai em `apps/tv-casa/out/tvhome.apk`. Agora conecte na TV (troque pelo IP real):

```bash
adb connect 192.168.1.50:5555
```

Aparece na TV um pop-up pedindo para **permitir a depuração**: aceite (marque "Sempre permitir"). Depois:

```bash
adb devices                                   # a TV deve aparecer como "device"
adb install -r apps/tv-casa/out/tvhome.apk
```

Se você ainda precisa descobrir os pacotes dos seus apps, faça agora `adb shell pm list packages -3`, ajuste o `apps.txt`, rode o `build.sh` de novo e reinstale com `adb install -r`.

### 7. Instale o RetroArch e os núcleos na TV

O TvRetro abre o jogo no **RetroArch 32 bits** (pacote `com.retroarch.ra32`); os caminhos dos núcleos são específicos dessa versão.

1. Instale o **RetroArch (32 bits)** pela loja de apps da TV ou pelo site oficial.
2. Abra o RetroArch **uma vez**, para ele criar suas pastas e o arquivo `retroarch.cfg`.
3. No RetroArch: **Carregar núcleo → Baixar um núcleo** e baixe:
   - **Nintendo - SNES / SFC (Snes9x)**
   - **Sony - PlayStation (PCSX ReARMed)**
4. A BIOS do PlayStation **não é fornecida**. O PCSX ReARMed tem BIOS emulada, mas a compatibilidade é limitada (testado com um jogo). Se quiser mais compatibilidade, use a BIOS do seu próprio console.

### 8. Defina o TvRetro como tela inicial

Aperte o botão **Home** do controle. O Android pergunta qual launcher usar: escolha **TvRetro** e **Sempre**. Se não perguntar, procure em Configurações → Apps → Apps padrão (o caminho muda por modelo).

Na primeira vez, o app pede permissão de armazenamento (ao enviar jogos). **Localização** e **acesso de uso** são opcionais; recuse se não quiser o painel de consumo de rede Wi-Fi.

### 9. Limpeza da TV (debloat), opcional

Pule se você respondeu "não" na decisão 4. O TvRetro precisa ser a tela inicial padrão (passo 8) e a TV conectada por ADB. No Windows, rode no WSL.

```bash
# só olhar, sem alterar nada
tools/debloat/tvretro-debloat.sh --tv 192.168.1.50 --dry-run

# limpeza guiada: pergunta item a item (s = sim, Enter = não, a = todos os próximos, q = sair)
tools/debloat/tvretro-debloat.sh --tv 192.168.1.50

# opcional: também a tela inicial original da TV e animações/protetor de tela
tools/debloat/tvretro-debloat.sh --tv 192.168.1.50 --launchers --tuning
```

O script **desativa, não desinstala**, só oferece uma lista curta de apps dispensáveis, nunca toca em apps protegidos nem nos seus (`apps.txt`), grava um registro `tv-changes-*.txt` e, no fim, espera 15 s e oferece reiniciar a TV. Depois do reinício, confira a Home, o Wi-Fi, o Bluetooth, as entradas HDMI, o teclado e seus apps.

Apps do fabricante não são tocados: veja o relatório `tv-revisar-*.txt` e o guia [docs/DEBLOAT.md](docs/DEBLOAT.md).

Para desfazer tudo:

```bash
tools/debloat/tvretro-debloat.sh --tv 192.168.1.50 --undo tv-changes-AAAAMMDD-HHMMSS.txt
```

> Foi testado com um `adb` simulado, **não em uma TV real**. Trate a primeira execução como experimental.

### 10. Atualizar ou desinstalar

```bash
adb install -r apps/tv-casa/out/tvhome.apk    # atualizar, com a MESMA chave
adb uninstall com.carlos.tvcasa               # desinstalar o TvRetro
```

Se `INSTALL_FAILED_UPDATE_INCOMPATIBLE` aparecer, a chave é outra: desinstale primeiro.

---

## Colocando seus jogos

Os jogos devem estar em `Games/SNES` e `Games/PSX`, na memória interna ou na raiz de um pendrive.

| Console | Formatos aceitos |
|---|---|
| SNES | `.sfc`, `.smc` |
| PlayStation | `.chd`, `.pbp`, `.cue` (com os `.bin` ao lado), `.m3u` |

ZIP e RAR **não são extraídos**: extraia antes. Para PlayStation, prefira CHD.

**Nomes completos ajudam nas capas.** Use o formato do catálogo Libretro, por exemplo `Super Mario Kart (USA).sfc` ou `Castlevania - Symphony of the Night.chd`. Nomes genéricos ou abreviados mostram um cartão com o nome, e o jogo abre do mesmo jeito.

### Sem pendrive: enviar pela rede

1. Na TV, abra **TvRetro → Jogos → Enviar jogos → Iniciar recebimento**.
2. A TV mostra um endereço temporário do tipo `http://192.168.x.x:porta/código`. Abra-o no navegador do celular ou do computador (mesma rede).
3. Escolha **SNES** ou **PSX**, selecione os arquivos e envie. Mantenha a tela da TV aberta.
4. Arquivos que já existem **não são substituídos**. O limite é de 2 GiB por arquivo, e a sessão encerra após **10 minutos sem atividade**, ao sair da tela ou após o teto absoluto de 60 minutos. Cada upload tem prazo máximo de 8 minutos.
5. Volte à biblioteca ou toque em **Atualizar biblioteca**.

### Sem pendrive: copiar pelo computador (ADB)

```bash
adb push "Super Mario Kart (USA).sfc" /storage/emulated/0/Games/SNES/
adb push "Meu Jogo.chd" /storage/emulated/0/Games/PSX/
```

### Com pendrive

1. Faça backup do pendrive. Formate em **FAT32** só se tiver certeza do que está nele.
2. Crie `Games/SNES` e `Games/PSX` na raiz e copie os jogos pelo computador.
3. Ejete com segurança e espete na TV. Abra **Jogos → Atualizar biblioteca**.
4. Antes de ejetar na TV, feche o jogo. Não remova o pendrive durante leitura ou gravação.
5. Saves e configurações do RetroArch continuam na memória interna. Não apague saves para "limpar espaço".

---

## Controles opcionais

- **Phone Pad (celular como controle Bluetooth, experimental):** `export KEYSTORE=... KEYSTORE_PASS=...` e `bash apps/phone-pad/build.sh`. O APK sai em `apps/phone-pad/build/phone-pad.apk` e exige Android 9 ou mais novo no celular. O pareamento depende do celular e da TV.
- **Ícone de bandeja no notebook (Linux):** veja [docs/NOTEBOOK.md](docs/NOTEBOOK.md). Em resumo: `sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 adb` e `/usr/bin/python3 tools/tray/install-user.py --tv IP_DA_TV --autostart`. Não instala nada na TV; usa o ADB já autorizado.

---

## Problemas comuns

| Sintoma | O que fazer |
|---|---|
| `adb connect` não conecta | Confirme que TV e computador estão na mesma rede, que a depuração por rede está ligada e o IP está certo. Algumas TVs só aceitam ADB depois de plugar um cabo USB uma vez. |
| `adb devices` mostra `unauthorized` | Aceite o pop-up na TV. Se não aparecer, revogue as autorizações em Opções do desenvolvedor e conecte de novo. |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | O APK foi assinado com outra chave. Desinstale (`adb uninstall com.carlos.tvcasa`) e instale de novo. |
| O script diz "Android SDK not found" | Defina `ANDROID_HOME` e instale `platforms;android-35` e `build-tools;35.0.0`. |
| "Defina KEYSTORE" | Rode os `export` do passo 6 na mesma janela do terminal. |
| O jogo não abre | Confira se o RetroArch 32 bits está instalado, se foi aberto uma vez e se o núcleo SNES/PSX foi baixado. |
| Não aparecem jogos | Verifique a pasta (`Games/SNES`, `Games/PSX`), a extensão e toque em **Atualizar biblioteca**. Em pendrive, confira o formato (FAT32). |
| Envio recusado por espaço | A TV reserva 550 MiB livres. Libere espaço ou use pendrive. |
| "Já existe um arquivo com esse nome" | O receptor nunca substitui. Renomeie ou apague o arquivo antigo. |
| Capas não aparecem | As capas vêm da internet (Libretro). Use nomes completos e confira a conexão. Sem capa, o jogo ainda abre. |
| O app de TV some da Home | Aperte Home e escolha TvRetro de novo como padrão. |
| A TV abre a tela inicial original em vez do TvRetro | Defina o TvRetro como padrão (passo 8) e rode a limpeza com `--launchers`. |
| Depois da limpeza algo parou de funcionar | `tools/debloat/tvretro-debloat.sh --tv IP --undo tv-changes-*.txt`, ou `adb shell pm enable PACOTE`. |
| Uma atualização reativou apps desativados | Rode o script de novo; ele ignora o que já está desativado. |
| O botão do YouTube do controle parou | Pode ocorrer ao desativar a tela inicial original em alguns Google TV. Reative-a com `--undo`. |
| O script diz que não achou os pacotes ou o adb | Confira `adb devices`, a conexão e passe `--tv IP_DA_TV`. |

---

## Segurança

- O **ADB por rede** deixa a TV controlável por quem estiver na mesma rede e tiver autorização. **Desligue a depuração por rede** quando terminar de instalar e de configurar. Nunca exponha o ADB à internet.
- O envio de jogos usa **HTTP sem criptografia**, com endereço e token temporários (128 bits). Use só em rede doméstica confiável, não compartilhe o endereço e **não encaminhe portas** do roteador.
- O receptor só grava em `Games/SNES` ou `Games/PSX`, só aceita as extensões listadas e nunca sobrescreve arquivos.
- A limpeza (debloat) só **desativa** pacotes, com confirmação e registro, e protege apps essenciais, mas mexer em apps de sistema tem risco. Veja [docs/DEBLOAT.md](docs/DEBLOAT.md).
- Chave de assinatura, senha, IP da TV e configurações pessoais **nunca** devem ir para o Git. Os registros `tv-changes-*.txt` e `tv-revisar-*.txt` também ficam fora do Git.
- Mantenha o sistema da TV atualizado: o firmware e os apps fechados do fabricante não foram auditados.

Detalhes em [docs/SEGURANCA.md](docs/SEGURANCA.md).

---

## Validação e limites

- A versão 0.7 foi usada na TV alvo. Nas versões 0.8, 0.8.1 e 0.9: compilação local, testes HTTP automatizados do receptor e validações no aparelho registradas em [docs/VALIDACAO.md](docs/VALIDACAO.md).
- Não existe auditoria completa do firmware nem garantia de desempenho em outros modelos.
- PlayStation com BIOS emulada foi testado com **um** jogo; isso não equivale a compatibilidade completa.
- Os caminhos dos núcleos são os do **RetroArch ARM32**; não há suporte universal a outros emuladores.
- O launcher usa `targetSdk 28` (dívida técnica documentada): migrar exige rever permissões e acesso aos jogos.
- A lista de jogos ainda não recicla views para bibliotecas enormes.
- Windows e macOS não foram validados pelo autor.
- O script de limpeza foi testado com `adb` simulado, não em TV real. Os nomes de pacote variam entre fabricantes e versões; a lista é curta de propósito.

---

## Estrutura do repositório

```text
apps/tv-casa      launcher TvRetro 0.9.1 (apps.txt, assets/, build.sh)
apps/phone-pad    controle Bluetooth HID 0.4 (experimental)
tools/tray        TvRetro Controle (bandeja do notebook Linux)
tools/debloat     limpeza guiada e reversível (script e listas de pacotes)
tools/controle-tv.py   controle web legado, só para referência
tests             testes do receptor, do catálogo de capas, do instalador e do debloat
docs              NOTEBOOK, CAPAS-E-REDE, PENDRIVE, SEGURANCA, VALIDACAO, DEBLOAT, HISTORICO
```

Rodar os testes (precisa de JDK 17 com `javac`):

```bash
python3 tests/test_transfer.py
python3 tests/test_catalog.py
python3 tests/test_transfer_status.py
python3 tests/test_transfer_validation.py
python3 tests/test_platform_compat.py
python3 tests/test_tray_install.py
python3 tests/test_debloat.py     # não precisa de JDK nem de TV
python3 tests/test_transfer_stress.py  # carga sintética opcional; sem TV/ROMs
```

Mais detalhes: [capas e consumo de rede](docs/CAPAS-E-REDE.md) e [uso de pendrive](docs/PENDRIVE.md).

---

## Créditos e licença

- Base: [Ansub/tv-detox](https://github.com/Ansub/tv-detox), licença MIT. Veja `LICENSE` e `NOTICE.md`.
- Capas: [Libretro Thumbnails](https://docs.libretro.com/guides/roms-playlists-thumbnails/).
- Emulação: [RetroArch](https://www.retroarch.com/) e seus núcleos, instalados e configurados por você.
- O debloat é opcional, interativo e reversível: nunca desinstala pacotes de sistema, apenas os desativa com a sua confirmação. Ideias de segurança inspiradas no `install.sh`/`undo.sh` do tv-detox.
- Licença: MIT. Projeto desenvolvido de forma iterativa com assistência de IA; `docs/HISTORICO.md` é um resumo editado das decisões, não uma transcrição.
