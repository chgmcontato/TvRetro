# Limpeza (debloat) da TV

Uma Android TV de fábrica vem com apps do fabricante e do Google que a maioria das pessoas não usa, ocupam memória e mostram sugestões e anúncios. O script `tools/debloat/tvretro-debloat.sh` ajuda a desativá-los com segurança. Ele é opcional e roda **depois** de instalar o TvRetro.

> **Risco.** Mexer em apps de sistema pode deixar a TV instável. O script foi desenhado para ser conservador e reversível, mas não existe garantia para todos os modelos. Foi testado com um `adb` simulado (`tests/test_debloat.py`) e **ainda não foi validado em uma TV real**. Faça por sua conta e risco.

## O que o script faz e não faz

- **Desativa, nunca desinstala.** Usa `pm disable-user --user 0`. O app continua na TV e volta com `pm enable`.
- **Pergunta antes de cada mudança.** Respostas: `s` (sim), Enter (não), `a` (sim para todos os próximos da etapa), `q` (parar).
- **Só oferece uma lista curta e conservadora** (`lists/candidatos.txt`): Google TV/Play Filmes, Play Games, YouTube Music para TV, recomendações da tela inicial original, easter egg e serviços de impressão. O que não estiver instalado é ignorado.
- **Nunca mexe no que está protegido** (`lists/protegidos.txt`): Android System UI, Configurações, Google Play e serviços do Google, teclado, Bluetooth, HDMI e entradas da TV, sintonizador, configuração inicial, fornecedores de chip (MediaTek, Amlogic, Realtek etc.). Esses padrões valem até para o que você acrescentar no `pessoal.txt`.
- **Nunca mexe nos seus apps**: tudo o que está em `apps/tv-casa/apps.txt`, o próprio TvRetro, o RetroArch e a Google Play.
- **Não adivinha apps do fabricante.** Nomes como `com.tcl.*` ou `com.hisense.*` podem ser essenciais. Eles vão para um relatório (`tv-revisar-*.txt`) para você revisar, e você decide.
- **Registra tudo** em `tv-changes-AAAAMMDD-HHMMSS.txt` (no computador) e em `/data/local/tmp/tvretro-disabled.txt` (na TV), com o valor antigo de cada ajuste.
- **Guarda uma foto dos pacotes** antes de qualquer mudança (`tv-pacotes-antes-*.txt`).
- **Espera 15 s** no fim, porque o Android grava o estado dos pacotes alguns segundos depois, e oferece reiniciar a TV para conferir que ela liga normalmente.

## Como usar

Pré-requisito: TvRetro instalado e definido como tela inicial padrão, TV conectada por ADB (README, passos 5 a 8). No Windows, rode tudo dentro do WSL.

```bash
# 1) Só olhar: não altera nada
tools/debloat/tvretro-debloat.sh --tv 192.168.1.50 --dry-run

# 2) Limpeza guiada (pergunta item a item)
tools/debloat/tvretro-debloat.sh --tv 192.168.1.50

# 3) Também a tela inicial original e ajustes de desempenho
tools/debloat/tvretro-debloat.sh --tv 192.168.1.50 --launchers --tuning
```

| Opção | O que faz |
|---|---|
| `--tv IP[:PORTA]` | TV a usar (porta padrão 5555). Sem ela, usa o único aparelho já conectado. |
| `--dry-run` | Simula. Só mostra o que faria e gera os relatórios. |
| `--launchers` | Oferece desativar a tela inicial **original** da TV, para ela parar de abrir no lugar do TvRetro. Só roda se o TvRetro já for a tela inicial padrão, pula apps que o sistema mantém sempre em execução e reativa tudo sozinho se a Home deixar de abrir o TvRetro. |
| `--tuning` | Oferece desligar animações e protetor de tela. A suspensão automática você ajusta no menu da TV. |
| `--undo [ARQUIVO]` | Desfaz. Com o arquivo `tv-changes-*.txt`, reativa os apps e restaura os ajustes. Sem arquivo, reativa os apps listados na TV. |

Se o arquivo não tiver permissão de execução: `bash tools/debloat/tvretro-debloat.sh ...`.

## Depois da limpeza

1. Espere os 15 s do script e **reinicie a TV** (o script oferece).
2. Confira: Home abre o TvRetro, Wi-Fi, Bluetooth, entradas HDMI, teclado, Google Play e seus apps de streaming.
3. Se algo falhar: `tools/debloat/tvretro-debloat.sh --tv IP --undo tv-changes-....txt`.

## Desfazer manualmente

```bash
adb shell pm list packages -d              # lista o que está desativado
adb shell pm enable com.exemplo.pacote     # reativa um app
```

## Apps do fabricante (TCL, Philips, Hisense, Xiaomi...)

1. Rode o script normalmente. Ele gera `tv-revisar-*.txt` com os apps de sistema de outras empresas.
2. Cole essa lista no Claude Code ou no Codex (Caminho A do README) e peça para explicar, um por um, o que cada app faz e se é seguro desativar. Ou pesquise o nome do pacote.
3. Copie `tools/debloat/lists/pessoal.txt.exemplo` para `pessoal.txt` e acrescente só os que você decidiu desativar, no formato `pacote|-|descrição`. Rode o script de novo: ele continua perguntando item a item e continua respeitando a lista de protegidos.
4. Na dúvida, deixe ligado.

## Efeitos colaterais conhecidos (de projetos parecidos)

- Em alguns Google TV, desativar a tela inicial original pode fazer o botão do YouTube do controle parar de funcionar.
- Em alguns Chromecast/Google TV, desativar a Home original pode atrapalhar a transmissão (cast). O pacote do receptor de cast (`com.google.android.apps.mediashell`) é protegido, mas teste.
- Atualizações do sistema podem reativar apps. Rode o script de novo (ele ignora o que já está desativado).
- Em alguns firmwares o comando `pm disable-user` é recusado; nesse caso nada foi alterado.

## Se a TV não ligar direito

1. Espere alguns minutos e reinicie tirando da tomada por 10 s.
2. Se ainda der para conectar por ADB: `tools/debloat/tvretro-debloat.sh --tv IP --undo ARQUIVO` (ou `adb shell pm enable PACOTE`).
3. Último recurso: restauração de fábrica pelo menu de recuperação da TV. Isso apaga tudo (apps, jogos, saves); consulte o manual do fabricante.

## Testes

```bash
python3 tests/test_debloat.py
```

Usam um `adb` falso (`tests/fake-adb.sh`): verificam que nada é alterado em `--dry-run` ou em EOF, que protegidos e apps do usuário nunca são tocados, que só o que foi confirmado é desativado, que `--undo` restaura tudo e que a rede de segurança das telas iniciais funciona. Eles **não** substituem um teste em TV real.

## Créditos

A ideia de desativar em vez de desinstalar, o cuidado com telas iniciais (`PERSISTENT`), a espera de 15 s e a lista de desfazer vêm do [Ansub/tv-detox](https://github.com/Ansub/tv-detox) (MIT). As listas e o script deste repositório são independentes.
