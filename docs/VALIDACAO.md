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
