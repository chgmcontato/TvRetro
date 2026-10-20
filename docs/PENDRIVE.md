# Jogos no armazenamento interno ou pendrive

**A configuração atual continua interna.** Nenhuma ROM/save foi movida nesta atualização. Enviar jogos pelo TvRetro continua gravando em `Games/SNES` ou `Games/PSX` da memória interna, mesmo se existir um USB conectado.

## Como usar um pendrive depois

1. Faça backup dos dados do pendrive no computador. Para continuar removendo e usando em outros equipamentos, mantenha-o como **armazenamento removível**. Não aceite “usar como armazenamento interno” na TV.
2. Verifique um formato legível pela TV. Na TCL testada, o pendrive de trabalho com Ventoy/exFAT foi identificado, mas o sistema declarou exFAT não suportado. Isso não prova defeito do pendrive. Não o formate sem salvar dados/decidir sobre o Ventoy. FAT32 costuma ser uma alternativa a testar e limita cada arquivo a menos de4GiB; o suporte real depende do modelo/firmware.
3. No computador, organize na raiz do pendrive:

```
Games/
  SNES/
    Nome do jogo.sfc
  PSX/
    Nome completo do jogo.chd
```

4. Ejete com segurança do computador e conecte à TV como removível. A aba Jogos lê `Games/SNES` e `Games/PSX` nos volumes USB montados e legíveis; se necessário, use Atualizar biblioteca.
5. Para uma futura migração, copie primeiro, verifique integridade e teste o jogo a partir do USB. Só depois considere apagar a cópia interna. Evite duplicatas na biblioteca enquanto houver as duas cópias; não altere nomes indiscriminadamente porque saves/histórico podem depender deles.
6. Encerre o jogo antes de ejetar o pendrive pelas configurações da TV. Não o remova durante leitura, jogo ou gravação de dados.

Saves e configurações do RetroArch permanecem nos caminhos internos já configurados. Ter as ROMs no pendrive libera espaço interno depois de uma migração validada, mas **não aumenta RAM** nem move automaticamente APKs. Capas online funcionam da mesma forma para arquivos internos e USB; o pendrive não substitui a conexão necessária para buscá-las.

Esta é uma orientação de uso futuro, não confirmação de teste de jogos no seu pendrive atual.
