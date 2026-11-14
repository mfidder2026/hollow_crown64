#!/bin/zsh
# build.sh — bouwt Hollow Crown: kamers/costumes -> scripts -> assembleren -> D64.
# Stopt bij de eerste fout, met het bestand en de regel.
#
#   ./build.sh               gewone build:    build/hollowcrown.prg, build/hollowcrown.d64
#   ./build.sh --autotest    testbuild:       build/autotest/... (leest invoer van een invoerband)
#   ./build.sh --vice        daarna starten in VICE
#   ./build.sh --clean       eerst build/ leegmaken
#   ./build.sh --geen-crt    zonder de cartridge (build/hollowcrown.crt: alles in één bestand, src/cartridge.asm)
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

AUTOTEST=0; START_VICE=0; CLEAN=0; CRT=1; TESTTAAL=nl
for a in "$@"; do
  case "$a" in
    --autotest) AUTOTEST=1 ;;
    --vice)     START_VICE=1 ;;
    --clean)    CLEAN=1 ;;
    --geen-crt) CRT=0 ;;
    --taal=*)   TESTTAAL=${a#--taal=} ;;      # de testbuild: de cartridge in deze taal (voor schermafbeeldingen)
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
"$PYTHON" tools/logo.py build/gen || fout "tools/logo.py"
"$PYTHON" tools/thema.py build/gen || fout "tools/thema.py"
"$PYTHON" tools/baas.py build/gen || fout "tools/baas.py"

# ---- 2. scripts compileren (na de kamers: de compiler controleert de loopvakken op het plaatje) ----
stap "2/4 scripts"
if [[ -f tools/scriptc.py ]]; then
  mkdir -p build/gen
  EXTRA_SCRIPTS=()
  (( AUTOTEST )) && EXTRA_SCRIPTS=(tests/scripts)      # proefscripts alleen in de testbuild
  "$PYTHON" tools/taal.py maak nl build/gen/taal/nl >/dev/null || fout "tools/taal.py (nl)"
  cp build/gen/taal/nl/teksten.asm build/gen/teksten.asm          # de vaste teksten (src/teksten_nl.asm), als .byte
  HC_SUFFIX=S "$PYTHON" tools/scriptc.py scripts build/gen ${EXTRA_SCRIPTS[@]} || fout "scriptcompiler (zie hierboven)"
  mkdir -p "$UIT"
  cp build/gen/spel.json "$UIT/spel.json"     # eigen kopie per build: de testbuild heeft extra (proef)vlaggen, en een
                                              # gewone build tussendoor mag de nummers van de tests niet veranderen
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
rm -f "$UIT"/scr_*.prg                       # (geen oude scriptbestanden van kamers die er niet meer zijn)
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
# De kamers staan op drie diskettes (data/kamers.txt: schijf=1/2/3/alle). Diskette 1: het spel en de kamers van
# schijf 1; diskette 2 en 3: de rest. Een kamer = het plaatje (<kamer>) en zijn scripts (<kamer>.s, als hij scripts heeft).
D64_2="$UIT/${NAAM}_2.d64"
D64_3="$UIT/${NAAM}_3.d64"
rm -f "$D64_2" "$D64_3"
# tools/d64.py zet de sectoren van elk bestand 3 sectoren uit elkaar (gemeten het snelst met de snellader).
for schijf in 1 2 3; do
  BESTANDEN=()
  (( schijf == 1 )) && BESTANDEN+=("$UIT/$NAAM.prg:$NAAM")
  for kamer in $("$PYTHON" tools/kamer.py --schijf $schijf data/kamers.txt); do
    [[ -f "build/gen/kamer_$kamer.prg" ]] && BESTANDEN+=("build/gen/kamer_$kamer.prg:$kamer")
    [[ -f "$UIT/scr_$kamer.prg" ]] && BESTANDEN+=("$UIT/scr_$kamer.prg:$kamer.s")
  done
  if (( schijf == 1 )); then
    "$PYTHON" tools/d64.py "$D64" "$SCHIJFNAAM" ${BESTANDEN[@]} || fout "tools/d64.py"
  else
    "$PYTHON" tools/d64.py "$UIT/${NAAM}_$schijf.d64" "${SCHIJFNAAM%%,*} $schijf,${SCHIJFNAAM##*,}" ${BESTANDEN[@]} \
      || fout "tools/d64.py (diskette $schijf)"
  fi
done
[[ -f "$D64" && -f "$D64_2" && -f "$D64_3" ]] || fout "geen D64 gemaakt"
# Voor de 1571: twee dubbelzijdige diskettes (D71), elk zoveel als twee 1541-diskettes: build/hollowcrown_1-2.d71
# (het spel en de kamers van schijf 1 en 2) en build/hollowcrown_3.d71 (schijf 3). Vraagt het spel om diskette 3,
# dan gaat de tweede D71 erin. c1541 maakt ze (tools/d64.py kent alleen D64).
for paar in "1-2:1 2" "3:3"; do
  label=${paar%%:*}
  D71="$UIT/${NAAM}_$label.d71"
  rm -f "$D71"
  C1541_ARGS=(-format "${SCHIJFNAAM%%,*} $label,${SCHIJFNAAM##*,}" d71 "$D71")
  [[ $label == 1-2 ]] && C1541_ARGS+=(-write "$UIT/$NAAM.prg" "$NAAM")
  GEZIEN=" "
  for schijf in ${=paar##*:}; do
    for kamer in $("$PYTHON" tools/kamer.py --schijf $schijf data/kamers.txt); do
      [[ "$GEZIEN" == *" $kamer "* ]] && continue                  # (schijf=alle: maar één keer)
      GEZIEN+="$kamer "
      [[ -f "build/gen/kamer_$kamer.prg" ]] && C1541_ARGS+=(-write "build/gen/kamer_$kamer.prg" "$kamer")
      [[ -f "$UIT/scr_$kamer.prg" ]] && C1541_ARGS+=(-write "$UIT/scr_$kamer.prg" "$kamer.s")
    done
  done
  "$VICE_BIN/c1541" ${C1541_ARGS[@]} >/dev/null 2>&1 || fout "c1541 ($D71)"
  [[ -f "$D71" ]] || fout "geen $D71 gemaakt"
  print "[build]   ${D71#$ROOT/}: $("$VICE_BIN/c1541" -attach "$D71" -list 2>/dev/null | grep -cE '^[0-9]+ ') bestanden, $("$VICE_BIN/c1541" -attach "$D71" -list 2>/dev/null | grep -i 'blocks free')"
done
rm -f "$UIT/$NAAM.d71"

# ---- 5. de cartridge: alles in één bestand (build/hollowcrown.crt, een EasyFlash van 1 MB), met een taalmenu ----
# Per taal (nl, en, de, fr; een taal is er als tools/taal/<taal>.json bestaat): vertaalde scripts en vaste teksten
# (tools/taal.py), de compiler, en het programma (-define CRT: laden uit de cartridge, src/cartridge.asm) in
# build/crt/<taal>/. De plaatjes zijn voor alle talen gelijk. De testbuild: alleen Nederlands, zonder taalmenu.
if (( CRT )); then
  stap "5/5 cartridge"
  CRT_ARGS=()
  TALEN=(nl)
  (( AUTOTEST )) && TALEN=($TESTTAAL)
  if (( ! AUTOTEST )); then
    for t in en de fr; do [[ -f tools/taal/$t.json ]] && TALEN+=($t); done
  fi
  typeset -A ACHTER=(nl S en E de D fr F)
  for taal in $TALEN; do
    TD="$UIT/crt/$taal"
    mkdir -p "$TD"
    if [[ $taal != nl ]]; then
      "$PYTHON" tools/taal.py maak $taal build/gen/taal/$taal >/dev/null || fout "tools/taal.py ($taal)"
      cp build/gen/taal/$taal/teksten.asm build/gen/teksten.asm
      HC_TAAL=$taal HC_SUFFIX=${ACHTER[$taal]} "$PYTHON" tools/scriptc.py build/gen/taal/$taal/scripts build/gen ${EXTRA_SCRIPTS[@]} \
        > "$TD/scriptc.log" 2>&1 || { tail -5 "$TD/scriptc.log" >&2; fout "scriptcompiler ($taal)"; }
    else
      HC_SUFFIX=S "$PYTHON" tools/scriptc.py scripts build/gen ${EXTRA_SCRIPTS[@]} > "$TD/scriptc.log" 2>&1 \
        || fout "scriptcompiler (nl)"
    fi
    CRT_DEFINES=(-define CRT)
    (( AUTOTEST )) && CRT_DEFINES+=(-define AUTOTEST)
    "$JAVA" -jar "$KICKASS" "$HOOFD" -odir "$TD" -symbolfiledir "$TD" -vicesymbols ${CRT_DEFINES[@]} \
      > "$TD/kickass.log" 2>&1 || { tail -20 "$TD/kickass.log" >&2; fout "assembleren (cartridge, $taal)"; }
    grep -q 'ERROR IN ASSERTION' "$TD/kickass.log" && { grep 'ERROR IN ASSERTION' "$TD/kickass.log" >&2; fout "een .assert (cartridge, $taal)"; }
    mv -f "$TD/main.vs" "$TD/$NAAM.vs"; mv -f "$TD/main.sym" "$TD/$NAAM.sym"
    CRT_START=$(grep -E '^\.label start=\$' "$TD/$NAAM.sym" | head -1 | sed 's/.*=\$//')
    [[ -n "$CRT_START" ]] || fout "cartridge ($taal): geen label start"
    CRT_ARGS+=("TAAL=$taal:$TD/$NAAM.prg:$CRT_START")
    for kamer in $("$PYTHON" tools/kamer.py --schijf 1 data/kamers.txt) $("$PYTHON" tools/kamer.py --schijf 2 data/kamers.txt) \
                 $("$PYTHON" tools/kamer.py --schijf 3 data/kamers.txt); do
      [[ -f "$TD/scr_$kamer.prg" && " ${CRT_ARGS[*]} " != *" $TD/scr_$kamer.prg:"* ]] \
        && CRT_ARGS+=("$TD/scr_$kamer.prg:$kamer.${ACHTER[$taal]}")
    done
    print "[build]   cartridge: $taal"
  done
  # terug naar het Nederlands in build/gen (de D64-build hierboven en de tests gebruiken die)
  cp build/gen/taal/nl/teksten.asm build/gen/teksten.asm
  [[ ${#TALEN} -gt 1 ]] && { HC_SUFFIX=S "$PYTHON" tools/scriptc.py scripts build/gen ${EXTRA_SCRIPTS[@]} >/dev/null || fout "scriptcompiler (nl, terug)"; }
  GEZIEN=" "
  for schijf in 1 2 3; do
    for kamer in $("$PYTHON" tools/kamer.py --schijf $schijf data/kamers.txt); do
      [[ "$GEZIEN" == *" $kamer "* ]] && continue
      GEZIEN+="$kamer "
      [[ -f "build/gen/kamer_$kamer.prg" ]] && CRT_ARGS+=("build/gen/kamer_$kamer.prg:$kamer")
    done
  done
  AUTOTAAL=0
  typeset -A TAALNR=(nl 1 en 2 de 3 fr 4)
  (( AUTOTEST )) && AUTOTAAL=${TAALNR[$TESTTAAL]}
  if (( ! AUTOTEST )); then                    # het taalmenu: het aardmannetje met de vlaggen (src/taalmenu.asm)
    "$PYTHON" tools/teken_taalmenu.py build/gen | sed 's/^/[build]   /' || fout "tools/teken_taalmenu.py"
    "$JAVA" -jar "$KICKASS" src/taalmenu.asm -odir "$UIT/crt" > "$UIT/crt/taalmenu.log" 2>&1 \
      || { tail -20 "$UIT/crt/taalmenu.log" >&2; fout "assembleren (taalmenu)"; }
    CRT_ARGS=("MENU=$UIT/crt/taalmenu.prg" "${CRT_ARGS[@]}")
  fi
  "$JAVA" -jar "$KICKASS" src/crtboot.asm -odir "$UIT/crt" :autotaal=$AUTOTAAL > "$UIT/crt/boot.log" 2>&1 \
    || { cat "$UIT/crt/boot.log" >&2; fout "assembleren (crtboot)"; }
  "$PYTHON" tools/crt.py "$UIT/$NAAM.crt" "$UIT/crt/crtboot.bin" ${CRT_ARGS[@]} | sed 's/^/[build]   /' \
    || fout "tools/crt.py"
  [[ -s "$UIT/$NAAM.crt" ]] || fout "geen $NAAM.crt"
fi

print "[build] OK: ${D64#$ROOT/}"

if (( START_VICE )); then
  # Eigen procesgroep: bin/x64sc start op macOS een kindproces; zo stop je later alleen deze VICE.
  perl -e 'setpgrp(0,0); exec @ARGV' "$VICE_BIN/x64sc" -pal -autostart "$D64" >/dev/null 2>&1 &!
  print "[build] VICE gestart: cursor met joystick 2 of de pijltjestoetsen (CRSR), vuur = spatie of linker Control"
fi
