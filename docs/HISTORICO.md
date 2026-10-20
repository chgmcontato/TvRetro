# Memória técnica do desenvolvimento

Este documento resume a conversa autorizada para registro do projeto. Informações de rede, número de série, dados de conta, diretórios pessoais, chaves, logs privados e conteúdo de jogos foram excluídos. Não é uma exportação literal das mensagens.

1. Debloat inicial baseado no tv-detox. Preservar Play Store, teclado, Bluetooth e HDMI; manter reversibilidade e não remover pacotes desconhecidos por palpite.
2. TV Casa como launcher próprio: seis streamings, atalhos HDMI/ajustes, foco amarelo, relógio com segundos, tipografia monoespaçada e fundo pessoal opcional.
3. Phone Pad: Bluetooth HID no Android 16; direcionais, botões SNES, ícone próprio. TV não encontrava celular na busca, mas pareamento iniciado pelo celular funcionou.
4. Reconexão depois de alternar para WhatsApp: TV podia continuar informando conexão sem jogo responder. RetroArch configurado com `android_input_disconnect_workaround = "true"`; reconexão foi validada pelo usuário.
5. Biblioteca de jogos: oito títulos SNES e um PSX fornecidos pelo usuário, capas locais e navegação horizontal. Conteúdo não faz parte deste repositório.
6. PSX: PCSX ReARMed ARM32, CHD para reduzir armazenamento. Teste com BIOS emulada por escolha do usuário; compatibilidade menor, sem baixar BIOS de terceiros.
7. Abertura de outro jogo: RetroArch pode encerrar ao receber outro conteúdo. Ponte de abertura com retry limitado foi usada para contornar esse comportamento; precisa continuar sob teste, não remover sem regressão.
8. Transferência: receptor HTTP temporário com URL aleatória, encerramento ao sair/depois de 10 min, streaming em blocos, sem sobrescrita e validação de nomes/extensões. Reserva passou de 200 para 550 MiB na 0.8.
9. Limpeza anterior removeu apps opcionais e testes identificados, com backups locais. Jogos e saves preservados. Não houve remoção indiscriminada de essenciais.
10. USB: pendrive de trabalho com Ventoy/exFAT não foi montado pela TCL; log declarou filesystem não suportado. Manter como removível e não formatar/adotar como interno sem decisão explícita. Próximo passo é testar armazenamento compatível e só depois mover conteúdo com verificação de integridade.
11. Monitorar 0.7: RAM disponível/total, armazenamento, rede, tráfego global e consumo diário Wi-Fi mediante acesso de uso. SSID exige permissão/localização no Android. O botão RAM não promete ganho e não encerra emulador/sistema.
12. Auditoria: patch do firmware antigo, ADB ativo, poucos recursos físicos. Nenhum grande lixo identificado nas pastas acessíveis. Cache do Android não é automaticamente desperdício.
13. Versão 0.8: biblioteca varrida em worker, capas decodificadas sob demanda com descarte fora da tela, fonte opcional, limites adicionais no receptor e guarda de ciclo de vida no monitor. Parte das melhorias da auditoria continua como roadmap.
14. GitHub: repositório privado solicitado. Somente código e documentação sanitizada; sem assets particulares, ROMs, BIOS ou chaves. Controle do notebook separado do launcher para não manter serviço permanente extra na TV.

## Próximas decisões

- USB compatível e migração com hash, preservando saves internos.
- Controle físico para jogos.
- Verificar atualização oficial da TCL; nunca usar firmware de outro modelo.
- Google Cast estava desativado. Decidir reativação após avaliar custo de memória e navegador do notebook. HDMI é a opção direta para tela inteira no Linux.
- Alexa: integração ainda não implementada; não prometer controle de voz só por instalar o launcher.

15. Nome da home alterado de TV Casa para **TvRetro**, versão 0.8.1, mantendo pacote/assinatura e configurações. Controle do notebook convertido em **TvRetro Controle** nativo de bandeja, sem espelhamento, sem consultas periódicas e com inicialização automática opcional.

16. Versão0.9: indicador fixo de conexão/taxas em todas as telas do TvRetro, retirada das nove capas incorporadas e busca online genérica pelo catálogo Libretro. romsgames.net retornou403. Imagens somente em RAM; fallback por nome mantém o jogo acessível sem internet. Jogos continuam internos; uso futuro de pendrive documentado, sem migração.
