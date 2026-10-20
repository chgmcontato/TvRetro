# Segurança e recursos

A auditoria local foi de leitura e não certifica ausência de todas as falhas. Firmware e apps fechados não foram auditados internamente. Resumo sem dados particulares:

- TV Android 11 com aproximadamente 918 MiB de RAM e 2,73 GiB em /data. Memória disponível varia; não confundir MemFree com MemAvailable nem somar RSS como memória exclusiva.
- Patch declarado pelo aparelho: março de 2025 na auditoria de outubro de 2026. Verificar atualização oficial é prioritário.
- SELinux Enforcing, Verified Boot green e criptografia reportados. ADB autenticado, mas aberto pela rede. Desligar após manutenção quando não precisar do controle via ADB.
- As portas de controle remoto Android TV e Netflix não são prova de invasão. Não remover serviços por porta sem identificar proprietário/protocolo.
- HTTP de envio é local, temporário e sem criptografia. Token 128 bits na 0.8. Limite de cabeçalhos de 32 KiB, prazo de cabeçalho, timeout de leitura e prazo de upload. Não foi migrado para HTTPS. Não use em rede pública e não encaminhe portas.
- Receptor não baixa arquivos nem sobrescreve existentes; reserva 550 MiB. Uma morte abrupta do processo pode deixar .part; remoção automática pós-crash não implementada.
- targetSdk 28 do launcher é dívida técnica: migração exige rever permissões e acesso aos jogos. Não basta elevar o número. Localização/uso são opcionais e amplos no Android; revogue se dispensáveis.
- Launcher principal precisa ser exportado como HOME. Activities de transferência/ponte de emulação são internas. Backup do launcher desativado.
- Nenhuma chave de assinatura, senha real, token de acesso ou configuração de rede deve entrar no Git. Builds exigem keystore externo e senha pelo ambiente.
- Não use encerramentos automáticos periódicos nem apague saves para recuperar RAM. Não remova componentes essenciais TCL/Google por consumo isolado.

## Roadmap pendente

A lista ainda mantém views simples para todos os arquivos, embora somente capas visíveis sejam decodificadas: para bibliotecas enormes, virtualizar também as views. Métricas de armazenamento do monitor ainda são consultadas a cada 2 s; reduzir frequência e retirar I/O da interface em uma próxima versão. O retry do RetroArch precisa de regressão antes de qualquer mudança. Testes longos de memória e novos jogos ainda são necessários.

Referências: [Android: memória](https://developer.android.com/topic/performance/memory-overview), [ADB](https://developer.android.com/tools/adb), [scrcpy oficial](https://github.com/Genymobile/scrcpy).

## Controle de bandeja
O aplicativo GTK não abre portas HTTP nem captura vídeo/áudio. Usa ADB já autorizado sob demanda e comandos fixos por argumentos, sem shell local e sem interpolar comandos do usuário. IPv4/portas são validados; configuração fica no usuário com modo0600. O ícone ocioso não consulta a TV. ADB continua necessário: o novo controle não elimina a exposição da depuração de rede. Bibliotecas/typelib de terceiros não são versionados.

## Capas0.9
HTTPS somente para thumbnails.libretro.com, sem redirecionamento/ROM upload; catálogo/arquivos/dimensões limitados e worker único. Não há cache de imagens em disco. Nomes ambíguos não geram associação automática arbitrária. Veja docs/CAPAS-E-REDE.md.

## Debloat (opcional)
`tools/debloat/tvretro-debloat.sh` só desativa pacotes (`pm disable-user --user 0`), nunca desinstala; pede confirmação item a item, respeita uma lista de pacotes protegidos e a lista de apps do usuário, registra tudo e permite desfazer. Pacotes de fabricantes não entram sozinhos: vão para um relatório de revisão. Veja docs/DEBLOAT.md.

## Receptor 0.9.1

A sessão encerra ao sair da tela, após 10 minutos sem atividade (verificação a cada 10 segundos) ou após 60 minutos absolutos. Conexões aceitas e leituras do corpo renovam a atividade. O limite de 8 minutos por upload permanece. Os callbacks são cancelados ao encerrar.

POSTs rejeitados com corpo pendente recebem a resposta antes de shutdownOutput e descarte limitado a 16 MiB ou 3 segundos. GETs não passam pelo descarte. Arquivos parciais, trava de envio e sockets são liberados no finally. Erros internos ficam apenas no observer; o cliente recebe mensagens fixas e status HTTP apropriados.

## Validação após carga

A verificação do nome cobre caracteres de controle mesmo quando há múltiplas quebras de linha; rejeita antes de criar qualquer arquivo. Uma linha de cabeçalho excessiva é erro de protocolo (400), e prazo de leitura excedido é timeout (408); falhas de armazenamento continuam separadas. O mapeamento não transforma genericamente todas as IOExceptions em erros do cliente.
