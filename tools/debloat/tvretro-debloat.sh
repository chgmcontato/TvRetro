#!/usr/bin/env bash
# TvRetro Debloat: desativa (nunca desinstala) apps dispensáveis de uma Android TV,
# com confirmação item a item, registro de tudo e comando para desfazer.
# Veja docs/DEBLOAT.md. Ideias de segurança inspiradas no install.sh/undo.sh do Ansub/tv-detox (MIT).
set -u -o pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
ADB="${ADB:-adb}"
APPS_FILE="${APPS_FILE:-$REPO/apps/tv-casa/apps.txt}"
TVRETRO_PKG=com.carlos.tvcasa
TVRETRO_HOME="$TVRETRO_PKG/com.ansub.tvhome.MainActivity"
TV_LIST=/data/local/tmp/tvretro-disabled.txt
WAIT="${WAIT:-15}"
PESSOAL_FILE="${PESSOAL_FILE:-$HERE/lists/pessoal.txt}"
STAMP="$(date +%Y%m%d-%H%M%S)"

TV=""; SERIAL=""; DRY=0; DO_LAUNCHERS=0; DO_TUNING=0; UNDO=""; UNDO_SET=0; LOG=""
QUIT=0; ALL_YES=0; CHANGED=0

say() { printf '%s\n' "$*"; }
err() { printf '%s\n' "$*" >&2; }

usage() {
  cat <<'EOF'
Uso: tools/debloat/tvretro-debloat.sh [opções]

  --tv IP[:PORTA]   TV a usar (padrão da porta: 5555). Sem isso, usa o único aparelho
                    já conectado ao adb.
  --dry-run         só mostra o que faria; não altera nada na TV.
  --launchers       também oferece desativar a tela inicial ORIGINAL da TV
                    (só se o TvRetro já for a tela inicial padrão).
  --tuning          também oferece desligar animações e protetor de tela.
  --undo [ARQUIVO]  desfaz: reativa o que o ARQUIVO de registro (tv-changes-*.txt)
                    lista; sem ARQUIVO, reativa o que está na lista guardada na TV.
  -h, --help        esta ajuda.

Nada é desinstalado. Cada item pede confirmação: s = sim, Enter = não,
a = sim para todos os próximos desta etapa, q = parar.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --tv) [ $# -ge 2 ] || { err "--tv precisa de um valor"; exit 2; }; TV="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    --launchers) DO_LAUNCHERS=1; shift ;;
    --tuning) DO_TUNING=1; shift ;;
    --undo) UNDO_SET=1; shift
            if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then UNDO="$1"; shift; fi ;;
    -h|--help) usage; exit 0 ;;
    *) err "Opção desconhecida: $1"; usage >&2; exit 2 ;;
  esac
done
case "$TV" in ''|*[!A-Za-z0-9._:-]*) [ -z "$TV" ] || { err "Valor inválido para --tv."; exit 2; } ;; esac

# ---------- adb ----------
tv() { "$ADB" -s "$SERIAL" shell "$@" </dev/null 2>&1 | tr -d '\r'; }
list_pkgs() { tv pm list packages "$@" | sed -n 's/^package://p'; }
has_line() { printf '%s\n' "$1" | grep -Fxq -- "$2"; }

connect() {
  command -v "$ADB" >/dev/null 2>&1 || {
    err "adb não encontrado. Instale o Android Platform Tools (veja o README, passo 1)."; exit 1; }
  if [ -n "$TV" ]; then
    case "$TV" in
      *.*.*.*:*|*[!0-9.]*) ;;
      *.*.*.*) TV="$TV:5555" ;;
    esac
    case "$TV" in *:*) "$ADB" connect "$TV" >/dev/null 2>&1 || true ;; esac
    SERIAL="$TV"
  else
    local devs n
    devs="$("$ADB" devices | awk 'NR>1 && $2=="device"{print $1}')"
    n="$(printf '%s\n' "$devs" | grep -c .)"
    [ "$n" = 1 ] || { err "Use --tv IP_DA_TV (encontrei $n aparelho(s) conectado(s))."; exit 1; }
    SERIAL="$devs"
  fi
  local state
  state="$("$ADB" -s "$SERIAL" get-state 2>&1 || true)"
  case "$state" in
    device) ;;
    *unauthorized*) err "A TV está pedindo 'Permitir depuração?'. Aceite na TV (marque 'Sempre') e rode de novo."; exit 1 ;;
    *) err "Não consegui falar com $SERIAL. Confira se a TV está ligada, na mesma rede e com a depuração ligada."; exit 1 ;;
  esac
}

# ---------- perguntas ----------
confirm() {
  [ "$DRY" = 1 ] && return 0
  [ "$ALL_YES" = 1 ] && return 0
  local a
  printf '%s [s/N/a=todos os próximos/q=sair] ' "$1" >&2
  IFS= read -r a || a=q
  case "$(printf '%s' "$a" | tr 'A-Z' 'a-z')" in
    s|sim|y|yes) return 0 ;;
    a|todos) ALL_YES=1; return 0 ;;
    q|sair) QUIT=1; return 1 ;;
    *) return 1 ;;
  esac
}

# ---------- registro ----------
ensure_log() {
  [ -n "$LOG" ] || LOG="tv-changes-$STAMP.txt"
  if [ ! -f "$LOG" ]; then
    printf '# TvRetro debloat %s | serial %s | modelo %s\n' "$STAMP" "$SERIAL" "${MODEL:-?}" > "$LOG"
  fi
}

disable_pkg() { # pacote descrição
  local p="$1" d="$2"
  if [ "$DRY" = 1 ]; then say "   [simulação] desativaria $p"; return 0; fi
  ensure_log
  if ! tv "echo $p >> $TV_LIST" >/dev/null; then
    err "   Mantive $p ligado: não consegui gravar a lista de desfazer na TV."; return 1
  fi
  printf 'OFF\t%s\t%s\n' "$p" "$d" >> "$LOG"
  tv "pm disable-user --user 0 $p" >/dev/null
  if tv "pm list packages -d $p" | grep -Fxq "package:$p"; then
    say "   desativado: $p"; CHANGED=$((CHANGED + 1)); OFFLIST="$OFFLIST"$'\n'"$p"
  else
    err "   Não consegui desativar $p (nada foi alterado)."; return 1
  fi
}

enable_pkg() {
  tv "pm enable $1" >/dev/null || true
  if tv "pm list packages -d $1" | grep -Fxq "package:$1"; then
    err "   Não consegui reativar $1."; return 1
  fi
  say "   reativado: $1"
}

put_setting() { # namespace chave valor
  local ns="$1" key="$2" val="$3" old
  if [ "$DRY" = 1 ]; then say "   [simulação] settings put $ns $key $val"; return 0; fi
  ensure_log
  old="$(tv settings get "$ns" "$key" | tail -1)"; [ -n "$old" ] || old=null
  printf 'SET\t%s\t%s\t%s\n' "$ns" "$key" "$old" >> "$LOG"
  tv "settings put $ns $key $val" >/dev/null
  if [ "$(tv settings get "$ns" "$key" | tail -1)" = "$val" ]; then
    say "   ajustado: $ns $key = $val (antes: $old)"; CHANGED=$((CHANGED + 1))
  else
    err "   Não consegui ajustar $ns $key."
  fi
}

# ---------- classificação ----------
glob_match_file() { # pacote arquivo
  local p="$1" f="$2" g
  [ -f "$f" ] || return 1
  while IFS= read -r g || [ -n "$g" ]; do
    g="${g//[[:space:]]/}"
    case "$g" in ''|'#'*) continue ;; esac
    case "$p" in $g) return 0 ;; esac
  done < "$f"
  return 1
}
is_protected() {
  glob_match_file "$1" "$HERE/lists/protegidos.txt" && return 0
  glob_match_file "$1" "$HERE/lists/launchers.txt" && return 0
  has_line "$HOME_PKGS" "$1" && return 0
  return 1
}
is_keep() { has_line "$KEEP" "$1"; }
is_installed() { has_line "$ALL" "$1"; }
is_off() { has_line "$OFFLIST" "$1"; }

load_keep() {
  KEEP="$TVRETRO_PKG"$'\n'"com.retroarch.ra32"$'\n'"com.carlos.padtest"$'\n'"com.android.vending"
  if [ -f "$APPS_FILE" ]; then
    KEEP="$KEEP"$'\n'"$(grep -v '^[[:space:]]*#' "$APPS_FILE" | tr -d ' \t\r' | grep -v '^$' || true)"
  else
    err "Aviso: não achei $APPS_FILE; seus apps não estão protegidos por essa lista."
  fi
}

# ---------- etapas ----------
step_candidates() {
  say; say "== 1. Apps dispensáveis conhecidos (lista curta e conservadora) =="
  ALL_YES=0
  local files=("$HERE/lists/candidatos.txt") f found=0 pkg flag desc
  [ -f "$PESSOAL_FILE" ] && files+=("$PESSOAL_FILE")
  for f in "${files[@]}"; do
    while IFS='|' read -r pkg flag desc <&3 || [ -n "$pkg" ]; do
      pkg="${pkg//[[:space:]]/}"
      case "$pkg" in ''|'#'*) continue ;; esac
      [ "$QUIT" = 1 ] && break 2
      is_installed "$pkg" || continue
      if is_off "$pkg"; then say "   (já desativado) $pkg"; continue; fi
      if is_keep "$pkg"; then say "   (mantido: está na sua lista de apps) $pkg"; continue; fi
      if is_protected "$pkg"; then say "   (protegido, nunca será mexido) $pkg"; continue; fi
      if [ "${flag//[[:space:]]/}" = home ] && [ "$HOME_IS_TVRETRO" != 1 ]; then
        say "   (adiado: só depois do TvRetro ser a tela inicial) $pkg"; continue
      fi
      found=$((found + 1))
      say; say " $pkg"; say "   $desc"
      if confirm "   Desativar?"; then disable_pkg "$pkg" "$desc" || true; fi
    done 3< "$f"
  done
  [ "$found" = 0 ] && say "   Nada novo da lista curta para desativar nesta TV."
  return 0
}

step_launchers() {
  say; say "== 2. Tela inicial original da TV =="
  if [ "$HOME_IS_TVRETRO" != 1 ]; then
    say "   Pulei: o TvRetro ainda não é a tela inicial padrão."
    say "   Aperte Home na TV, escolha TvRetro e 'Sempre', e rode de novo com --launchers."
    return 0
  fi
  ALL_YES=0
  local p flags
  while IFS= read -r p <&3 || [ -n "$p" ]; do
    p="${p//[[:space:]]/}"
    case "$p" in ''|'#'*) continue ;; esac
    [ "$QUIT" = 1 ] && break
    is_installed "$p" || continue
    if is_off "$p"; then say "   (já desativada) $p"; continue; fi
    flags="$(tv dumpsys package "$p" | sed -n '/pkgFlags=\[/{p;q;}')"
    if [ -z "$flags" ]; then say "   Mantive $p: não consegui ler as propriedades dele."; continue; fi
    case "$flags" in *PERSISTENT*) say "   Mantive $p: o sistema o mantém sempre em execução."; continue ;; esac
    say; say " $p"; say "   Tela inicial original. Desativá-la evita que ela volte a abrir no lugar do TvRetro."
    if confirm "   Desativar?"; then
      disable_pkg "$p" "tela inicial original" || continue
      if [ "$DRY" != 1 ] && [ "$(home_component | sed 's|/.*||')" != "$TVRETRO_PKG" ]; then
        err "   A Home deixou de abrir o TvRetro. Reativando $p por segurança."
        enable_pkg "$p" || true
        tv "cmd package set-home-activity $TVRETRO_HOME" >/dev/null || true
      fi
    fi
  done 3< "$HERE/lists/launchers.txt"
}

step_tuning() {
  say; say "== 3. Ajustes de desempenho =="
  ALL_YES=0
  if confirm " Desligar as animações do sistema (a navegação fica mais ágil)?"; then
    put_setting global window_animation_scale 0
    put_setting global transition_animation_scale 0
    put_setting global animator_duration_scale 0
  fi
  [ "$QUIT" = 1 ] && return 0
  if confirm " Desligar o protetor de tela?"; then
    put_setting secure screensaver_enabled 0
  fi
  say "   Suspensão automática: ajuste pelo menu da TV (o nome muda por modelo; procure por"
  say "   'Economia de energia' ou 'Desligar após'). Eu não mexo nisso por script."
}

report_review() {
  local out="tv-revisar-$STAMP.txt" p path n=0 lines
  lines="$(tv pm list packages -s -f | sed -n 's/^package://p')"
  : > "$out"
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    p="${line##*=}"; path="${line%=*}"
    case "$p" in com.google.*|com.android.*|android|android.*|org.chromium.*) continue ;; esac
    is_protected "$p" && continue
    is_keep "$p" && continue
    printf '%s\t%s\n' "$p" "$path" >> "$out"; n=$((n + 1))
  done <<EOF
$lines
EOF
  say; say "== Relatório =="
  say "   $n app(s) de sistema de outras empresas (fabricante etc.) para você REVISAR."
  say "   Eu não desativo esses sozinho: alguns são essenciais. Lista em: $out"
  say "   Dica: cole essa lista no Claude/Codex (Caminho A do README) e peça para explicar cada um,"
  say "   ou pesquise o nome do pacote. Depois acrescente os que você decidir em"
  say "   tools/debloat/lists/pessoal.txt (modelo em pessoal.txt.exemplo) e rode de novo."
}

home_component() { tv cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME | tail -1; }
home_pkgs() {
  { tv cmd package query-activities --brief -a android.intent.action.MAIN -c android.intent.category.HOME \
      | grep / | sed 's|/.*||; s/^ *//'
    home_component | sed 's|/.*||'; } | sort -u | grep -v '^$' || true
}

do_undo() {
  say "== Desfazendo =="
  local kind a b c fails=0 seen=""
  if [ -n "$UNDO" ]; then
    [ -f "$UNDO" ] || { err "Arquivo não encontrado: $UNDO"; exit 1; }
    while IFS=$'\t' read -r kind a b c <&3 || [ -n "$kind" ]; do
      case "$kind" in
        OFF) enable_pkg "$a" || fails=1 ;;
        SET) if [ "$c" = null ]; then tv "settings delete $a $b" >/dev/null || true
             else tv "settings put $a $b $c" >/dev/null || true; fi
             say "   restaurado: $a $b" ;;
      esac
    done 3< "$UNDO"
  else
    local list
    list="$(tv "if [ -e $TV_LIST ]; then cat $TV_LIST; fi" | grep -v '^$' | sort -u || true)"
    [ -n "$list" ] || { say "   Nada na lista guardada na TV."; return 0; }
    while IFS= read -r a; do enable_pkg "$a" || fails=1; done <<EOF
$list
EOF
    say "   Obs.: ajustes de animação/protetor só voltam com o arquivo de registro (--undo ARQUIVO)."
  fi
  if [ "$fails" = 0 ] && [ -z "$UNDO" ]; then tv "rm -f $TV_LIST" >/dev/null || true; fi
  say "   Concluído. Se algo ainda estranhar, reinicie a TV."
  return "$fails"
}

# ---------- principal ----------
connect
if [ "$UNDO_SET" = 1 ]; then do_undo; exit $?; fi

MODEL="$(tv getprop ro.product.model | tail -1)"
BRAND="$(tv getprop ro.product.brand | tail -1)"
ANDROID="$(tv getprop ro.build.version.release | tail -1)"
ALL="$(list_pkgs)"
[ -n "$ALL" ] || { err "Não consegui listar os pacotes da TV."; exit 1; }
OFFLIST="$(list_pkgs -d)"
HOME_PKGS="$(home_pkgs)"
HOME_IS_TVRETRO=0
[ "$(home_component | sed 's|/.*||')" = "$TVRETRO_PKG" ] && HOME_IS_TVRETRO=1
load_keep

say "TV: $BRAND $MODEL (Android $ANDROID) | tela inicial: $(home_component)"
say "Pacotes instalados: $(printf '%s\n' "$ALL" | grep -c .) | já desativados: $(printf '%s\n' "$OFFLIST" | grep -c .)"
printf '%s\n' "$(tv pm list packages -f)" > "tv-pacotes-antes-$STAMP.txt"
say "Foto da lista de pacotes antes de qualquer mudança: tv-pacotes-antes-$STAMP.txt"
[ "$DRY" = 1 ] && say "MODO SIMULAÇÃO: nada será alterado na TV."
[ "$HOME_IS_TVRETRO" = 1 ] || say "Aviso: o TvRetro ainda não é a tela inicial padrão; itens que dependem disso ficam para depois."

if [ "$DRY" != 1 ]; then
  say
  say "Regras: nada é desinstalado, só desativado; cada item pede confirmação; tudo fica registrado"
  say "para desfazer; apps de sistema essenciais, Google Play, teclado, Bluetooth e entradas HDMI"
  say "nunca são oferecidos. Mesmo assim, mexer em apps de sistema tem risco. Faça por sua conta."
  confirm "Continuar?" || { say "Nada foi alterado."; exit 0; }
fi

step_candidates
[ "$DO_LAUNCHERS" = 1 ] && [ "$QUIT" = 0 ] && step_launchers
[ "$DO_TUNING" = 1 ] && [ "$QUIT" = 0 ] && step_tuning
report_review

if [ "$DRY" != 1 ] && [ "$CHANGED" -gt 0 ]; then
  say; say "O Android grava as mudanças alguns segundos depois. Aguardando ${WAIT}s antes de continuar…"
  sleep "$WAIT"
  [ "$HOME_IS_TVRETRO" = 1 ] && { tv "cmd package set-home-activity $TVRETRO_HOME" >/dev/null || true; }
  say
  say "Alterações: $CHANGED. Registro: $LOG"
  say "Para desfazer tudo:  tools/debloat/tvretro-debloat.sh --tv ${TV:-IP_DA_TV} --undo $LOG"
  ALL_YES=0
  if confirm "Reiniciar a TV agora para conferir que ela liga normalmente?"; then
    "$ADB" -s "$SERIAL" reboot || true
    say "Reiniciando. Quando voltar, confira a Home, os apps e o Wi-Fi. Se algo falhar, rode o comando de desfazer acima."
  else
    say "Reinicie a TV uma vez (Configurações → Reiniciar, ou tire da tomada por 10 s) e confira que liga normalmente."
  fi
elif [ "$DRY" != 1 ]; then
  say; say "Nenhuma alteração foi feita."
fi
