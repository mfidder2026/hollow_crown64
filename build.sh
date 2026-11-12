#!/bin/zsh
# build.sh — bouwt Hollow Crown: kamers/costumes -> scripts -> assembleren -> D64.
# Stopt bij de eerste fout, met het bestand en de regel.
#
#   ./build.sh               gewone build:    build/hollowcrown.prg, build/hollowcrown.d64
#   ./build.sh --autotest    testbuild:       build/autotest/... (leest invoer van een invoerband)
#   ./build.sh --vice        daarna starten in VICE
#   ./build.sh --clean       eerst build/ leegmaken
#
# ---- instellingen: alle paden naar gereedschap staan hier (en in tools/vicetest.py) -------------
JAVA="${JAVA:-/opt/homebrew/opt/openjdk/bin/java}"          # JDK 17+; /usr/bin/java is een stub
VICE_BIN="${VICE_BIN:-/Applications/vice-arm64-gtk3-3.10/bin}" # VICE 3.10: x64sc en c1541
PYTHON="${PYTHON:-python3}"
# -------------------------------------------------------------------------------------------------

set -u
ROOT="${0:A:h}"
cd "$ROOT"
KICKASS="$ROOT/tools/KickAss.jar"
CHECKER="$ROOT/tools/c64_ka_syntax_checker.py"
HOOFD="src/main.asm"
NAAM="hollowcrown"
SCHIJFNAAM="hollow crown,hc"

AUTOTEST=0; START_VICE=0; CLEAN=0
for a in "$@"; do
  case "$a" in
    --autotest) AUTOTEST=1 ;;
    --vice)     START_VICE=1 ;;
    --clean)    CLEAN=1 ;;
    -h|--help)  sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) print -u2 "[build] onbekende optie: $a"; exit 2 ;;
  esac
done

stap() { print "[build] == $*" }
fout() { print -u2 "[build] FOUT: $*"; exit 1 }

(( CLEAN )) && rm -rf build
if (( AUTOTEST )); then UIT="$ROOT/build/autotest"; else UIT="$ROOT/build"; fi
mkdir -p "$UIT"

# ---- gereedschap controleren ----
"$JAVA" -version >/dev/null 2>&1 || fout "Java werkt niet: $JAVA (zet JAVA=/pad/naar/java)"
[[ -f "$KICKASS" ]] || fout "Kick Assembler ontbreekt: $KICKASS"
[[ -x "$VICE_BIN/c1541" ]] || fout "c1541 niet gevonden in $VICE_BIN (zet VICE_BIN)"
command -v "$PYTHON" >/dev/null || fout "Python niet gevonden: $PYTHON"

# ---- 1. kamers en costumes ----
stap "1/4 kamers en costumes"
if [[ tools/sprites_hc.py -nt src/sprites_hc.asm ]]; then
  "$PYTHON" tools/sprites_hc.py || fout "tools/sprites_hc.py"
else
  print "[build]   src/sprites_hc.asm is bij"
fi
mkdir -p build/gen
"$PYTHON" tools/kamer.py data/kamers.txt build/gen || fout "tools/kamer.py (data/kamers.txt)"
"$PYTHON" tools/lettertype.py build/gen || fout "tools/lettertype.py"
"$PYTHON" tools/costume.py build/gen || fout "tools/costume.py"

# ---- 2. scripts compileren (na de kamers: de compiler controleert de loopvakken op het plaatje) ----
stap "2/4 scripts"
if [[ -f tools/scriptc.py ]]; then
  mkdir -p build/gen
  EXTRA_SCRIPTS=()
  (( AUTOTEST )) && EXTRA_SCRIPTS=(tests/scripts)      # proefscripts alleen in de testbuild
  "$PYTHON" tools/scriptc.py scripts build/gen ${EXTRA_SCRIPTS[@]} || fout "scriptcompiler (zie hierboven)"
else
  print "[build]   nog geen tools/scriptc.py (hoofdstuk 4): overgeslagen"
fi

# ---- 3. assembleren ----
stap "3/4 assembleren${AUTOTEST:+}$( (( AUTOTEST )) && print ' (AUTOTEST)')"
for f in src/*.asm; do
  uit=$("$PYTHON" "$CHECKER" "$f" 2>&1)
  if ! print -r -- "$uit" | grep -qE 'Summary: 0 error'; then
    print -r -- "$uit" | grep -E 'ERROR|error' | head -5
    fout "syntaxcheck van $f"
  fi
done
DEFINES=()
(( AUTOTEST )) && DEFINES=(-define AUTOTEST)
LOG="$UIT/kickass.log"
"$JAVA" -jar "$KICKASS" "$HOOFD" -odir "$UIT" -symbolfiledir "$UIT" -vicesymbols -showmem \
        ${DEFINES[@]} > "$LOG" 2>&1
RC=$?
if (( RC != 0 )); then
  # Kick Assembler: "Error: <melding>" en daaronder "at line N, column C in <bestand>"
  melding=$(grep -m1 -E '^Error:' "$LOG" | sed 's/^Error: //')
  plek=$(grep -m1 -E '^at line [0-9]+, column [0-9]+ in ' "$LOG")
  if [[ -n "$plek" ]]; then
    regel=$(print -r -- "$plek" | sed -E 's/^at line ([0-9]+).*/\1/')
    bestand=$(print -r -- "$plek" | sed -E 's/^at line [0-9]+, column [0-9]+ in //')
    [[ -f "$bestand" ]] || bestand="src/${bestand:t}"
    print -u2 "[build] $bestand:$regel: $melding"
    [[ -f "$bestand" ]] && print -u2 "[build]   $regel | $(sed -n "${regel}p" "$bestand")"
  else
    grep -vE '^//' "$LOG" | tail -15 >&2
  fi
  fout "assembleren mislukt (volledig log: ${LOG#$ROOT/})"
fi
if grep -q 'ERROR IN ASSERTION' "$LOG"; then
  grep 'ERROR IN ASSERTION' "$LOG" >&2
  fout "een .assert is mislukt (Kick Assembler zelf gaat dan gewoon door)"
fi
grep -E '^[[:space:]]+\*?\$[0-9a-f]{4}-\$[0-9a-f]{4} ' "$LOG" | grep -v ' Basic End' | sed 's/^ */[build]   /'
[[ -f "$UIT/$NAAM.prg" ]] || fout "geen $NAAM.prg gemaakt"
mv -f "$UIT/main.vs" "$UIT/$NAAM.vs"; mv -f "$UIT/main.sym" "$UIT/$NAAM.sym"   # symbolen voor VICE en vicetest.py

# ---- 4. diskette ----
stap "4/4 diskette"
D64="$UIT/$NAAM.d64"
rm -f "$D64"
"$VICE_BIN/c1541" -format "$SCHIJFNAAM" d64 "$D64" -write "$UIT/$NAAM.prg" "$NAAM" >/dev/null 2>"$UIT/c1541.log" \
  || { cat "$UIT/c1541.log" >&2; fout "c1541"; }
[[ -f "$D64" ]] || fout "geen D64 gemaakt"
"$VICE_BIN/c1541" -attach "$D64" -list 2>/dev/null | grep -E '^[0-9]+ ' | sed 's/^/[build]   /'

print "[build] OK: ${D64#$ROOT/}"

if (( START_VICE )); then
  # Eigen procesgroep: bin/x64sc start op macOS een kindproces; zo stop je later alleen deze VICE.
  perl -e 'setpgrp(0,0); exec @ARGV' "$VICE_BIN/x64sc" -pal -autostart "$D64" >/dev/null 2>&1 &!
  print "[build] VICE gestart: cursor met joystick 2 of de pijltjestoetsen (CRSR), vuur = spatie of linker Control"
fi
