#!/bin/zsh
# build.sh — Kick Assembler buildpipeline voor macOS (variant op build.bat)
# Pipeline: syntax checker (0 ERRORs) -> KickAss.jar assembleren -> prg in build/ -> optioneel VICE
# Gebruik:  ./build.sh [bron.asm] [opties...]   Zie --help.
# Zoekvolgorde bron/gereedschap: env-var -> projectmap -> map van dit script -> bekende macOS-paden.

set -u
SCRIPT_DIR="${0:A:h}"
OUTDIR="${OUTDIR:-build}"
KA_OPTS="${KA_OPTS:--vicesymbols -showmem}"
VICE_EXE="${VICE_EXE:-/Applications/vice-arm64-gtk3-3.9/x64sc.app/Contents/MacOS/x64sc}"

usage() {
  cat <<'TXT'
Gebruik: build.sh [bron.asm] [opties]
  --clean        build/ eerst leegmaken
  --no-check     syntax-check overslaan
  --check-only   alleen checken, niet assembleren
  --no-vice      niet starten in VICE na de build
  --vice         wél starten in VICE (standaard uit op macOS)
  --help, -h     dit tekstje
Overige argumenten gaan rechtstreeks naar Kick Assembler (-libdir, -define, ...).
Environment: JAVA_EXE, KICKASS_JAR, PYTHON_EXE, CHECKER, VICE_EXE, OUTDIR, KA_OPTS
TXT
}

err() { print -u2 "[build] ERROR: $*"; exit 1; }
note() { print "[build] $*"; }

# Een kopie in een projectmap (cp "$S/build.sh" .) gebruikt de build.sh van de skill, zodat verbeteringen ook daar
# gelden. KickAss.jar en de bron worden gevonden vanuit de map waarin je bouwt. BUILD_SH_EIGEN=1 houdt deze kopie.
SKILL_BUILD="$HOME/Library/Application Support/MacAIMagic/Skills/c64-kickassembler/build.sh"
if [[ -z "${BUILD_SH_EIGEN:-}" && -f "$SKILL_BUILD" && "${0:A}" != "${SKILL_BUILD:A}" ]]; then
  BUILD_SH_EIGEN=1 exec "$SKILL_BUILD" "$@"
fi

# --- Java opzoeken: de macOS-stub /usr/bin/java faalt, dus eerst echte JDK's proberen ---
find_java() {
  local c
  for c in "${JAVA_EXE:-}" \
           /opt/homebrew/opt/openjdk/bin/java \
           /opt/homebrew/opt/openjdk@27/bin/java \
           /Library/Java/JavaVirtualMachines/*/Contents/Home/bin/java(N) \
           /usr/bin/java; do
    [[ -n "$c" && -x "$c" ]] || continue
    if "$c" -version >/dev/null 2>&1; then print -r -- "$c"; return 0; fi
  done
  return 1
}

SRC=""
RUN_CHECK=1; DO_ASSEMBLE=1; START_VICE=0; CLEAN=0
EXTRA=()
while (( $# )); do
  case "$1" in
    --clean) CLEAN=1 ;;
    --no-check) RUN_CHECK=0 ;;
    --check-only) DO_ASSEMBLE=0 ;;
    --no-vice) START_VICE=0 ;;
    --vice) START_VICE=1 ;;
    --help|-h|"/?") usage; exit 0 ;;
    *.asm) [[ -z "$SRC" ]] && SRC="$1" || EXTRA+=("$1") ;;
    *) EXTRA+=("$1") ;;
  esac
  shift
done

# --- Java ---
JAVA="$(find_java)" || err "geen werkende Java gevonden. Installeer: brew install openjdk, of zet JAVA_EXE=/pad/to/java"
note "java: $JAVA"

# --- KickAss.jar: env -> projectmap -> scriptmap -> skill-map ---
SKILL_DIR="$HOME/Library/Application Support/MacAIMagic/Skills/c64-kickassembler"
JAR="${KICKASS_JAR:-}"
if [[ -z "$JAR" ]]; then
  for cand in "./KickAss.jar" "$SCRIPT_DIR/KickAss.jar" "$SCRIPT_DIR"/*.jar(N) "$SKILL_DIR/KickAss.jar"; do
    [[ -f "$cand" ]] && { JAR="$cand"; break }
  done
fi
[[ -n "$JAR" && -f "$JAR" ]] || err "KickAss.jar niet gevonden (zet KICKASS_JAR=/pad/to/KickAss.jar)"
note "jar: $JAR"

# --- bronbestand ---
if [[ -z "$SRC" ]]; then
  files=(*.asm(N))
  if (( ${#files[@]} == 1 )); then
    SRC="${files[1]}"; note "no source file given, the only .asm here: $SRC"
  elif (( ${#files[@]} == 0 )); then
    err "geen .asm gevonden in $PWD"
  else
    err "meerdere .asm bestanden: ${files[*]} — geef er één op"; fi
fi
[[ -f "$SRC" ]] || err "bronbestand niet gevonden: $SRC"
BASE="${SRC:t:r}"

# --- syntax checker ---
CHECKER="${CHECKER:-}"
if [[ -z "$CHECKER" ]]; then
  for cand in "./c64_ka_syntax_checker.py" "$SCRIPT_DIR/c64_ka_syntax_checker.py" "$SKILL_DIR/c64_ka_syntax_checker.py"; do
    [[ -f "$cand" ]] && { CHECKER="$cand"; break }
  done
fi
if (( RUN_CHECK )); then
  if [[ -n "$CHECKER" ]]; then
    PY="${PYTHON_EXE:-python3}"
    command -v "$PY" >/dev/null 2>&1 || err "python niet gevonden voor de syntax-check (PYTHON_EXE)"
    note "syntax-check $SRC"
    "$PY" "$CHECKER" "$SRC" || err "syntax checker vond ERRORs — eerst repareren"
  else
    note "geen c64_ka_syntax_checker.py gevonden — check overgeslagen"
  fi
fi
(( DO_ASSEMBLE )) || { note "check-only: klaar"; exit 0; }

# --- assembleren ---
(( CLEAN )) && rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
note "assembling..."
SRC_DIR="${SRC:A:h}"
KA_LOG="$OUTDIR/kickass.log"
"$JAVA" -jar "$JAR" ${=KA_OPTS} -o "$OUTDIR/$BASE.prg" "$SRC" ${EXTRA[@]} > "$KA_LOG" 2>&1
KA_RC=$?
# zonder de kop van vijf regels: wie de uitvoer met head inkort, ziet dan meer van de fout
grep -vE '^//-+$|^//[[:space:]]+Kick Assembler|^//[[:space:]]*$' "$KA_LOG"
if (( KA_RC != 0 )); then
  # De fout staat op de regel boven de ^ van KickAss. Een model zocht hem in de regels daarboven en schreef het
  # bestand 14 keer opnieuw (11 nov 2026, '!t1-done'). Daarom hier de foute regel apart, met een hint.
  PY="${PYTHON_EXE:-python3}"
  if command -v "$PY" >/dev/null 2>&1; then
    "$PY" - "$KA_LOG" "$SRC" <<'PYEOF'
import os, re, sys
log, src = sys.argv[1], sys.argv[2]
text = open(log, errors="replace").read()
errs = [(m.group(1), int(m.group(2)), int(m.group(3)), m.group(4).strip())
        for m in re.finditer(r"^\s*\((.+?) (\d+):(\d+)\) (.+)$", text, re.M)]
if not errs:
    m = re.search(r"^Error: (.+)\nat line (\d+), column (\d+) in (.+)$", text, re.M)
    if m:
        errs.append((m.group(4).strip(), int(m.group(2)), int(m.group(3)), m.group(1).strip()))
if not errs:
    sys.exit(0)

def source_line(path, n):
    for p in (path, os.path.join(os.path.dirname(os.path.abspath(src)), path)):
        try:
            with open(p, errors="replace") as fh:
                lines = fh.read().splitlines()
            return lines[n - 1] if 0 < n <= len(lines) else ""
        except OSError:
            pass
    return ""

IN_NAME = re.compile(r"!([A-Za-z_]\w*)([-+]+)([A-Za-z_]\w*)")
def hint(msg, line):
    code = line.split("//")[0]
    m = IN_NAME.search(code)
    if m:
        name = m.group(1) + "_" + m.group(3)
        return ("een !-label mag geen - of + in de naam hebben: KickAss leest '!%s%s' als 'het %s !%s'. "
                "Gebruik een gewoon label: '%s:' en 'beq %s'"
                % (m.group(1), m.group(2), "vorige" if m.group(2)[0] == "-" else "volgende", m.group(1), name, name))
    if re.match(r"\s*\.zp\b", code) and "{" not in code:
        return "'.zp' is een blok: '.zp { teller: .byte 0 }'"
    m = re.match(r"\s*\.(\w+)\s*:", code)
    if m:
        return "een label begint niet met een punt: schrijf '%s:'" % m.group(1)
    if re.match(r"Unknown symbol '!", msg):
        return ("verkeerde richting: '!naam-' is het vorige !naam-label (erboven), '!naam+' het volgende (eronder); "
                "bestaat er geen, gebruik een gewoon label")
    m = re.match(r"Unknown symbol '(\w+)'", msg)
    if m:
        name = m.group(1)
        if name in ("x", "y") and re.search(r"\+\s*%s\b" % name, code):
            return "de index komt na een komma: 'sta $0400+40*10,%s' (niet +%s)" % (name, name)
        if re.search(r"!%s(?![\w+\-:])" % re.escape(name), code):
            return "'!%s' zonder richting: schrijf '!%s-' (vorige) of '!%s+' (volgende)" % (name, name, name)
        return ("'%s' bestaat niet: is het gedefinieerd (label met ':', .const, .var) en goed gespeld? "
                "Zoek met: grep -n '%s' *.asm" % (name, name))
    return ""

out = []
def show(e, first):
    path, n, col, msg = e
    line = source_line(path, n)
    prefix = "[build]   %d | " % n
    out.append("[build] FOUT in %s regel %d, kolom %d: %s" % (os.path.basename(path), n, col, msg))
    out.append(prefix + line.replace("\t", " "))
    if first and col > 0:
        out.append(" " * (len(prefix) + col - 1) + "^")
    h = hint(msg, line)
    if h:
        out.append("[build]   hint: " + h)

if len(errs) > 1:
    for e in errs[1:5]:
        show(e, False)
    if len(errs) > 5:
        out.append("[build] ... en nog %d fouten" % (len(errs) - 5))
    out.append("[build] De eerste fout:")
show(errs[0], True)
out.append("[build] Verander alleen die regel (edit_file) en bouw opnieuw; schrijf het bestand niet opnieuw. "
           "Vaak verdwijnen de volgende fouten dan vanzelf.")
print("\n".join(out))
PYEOF
  fi
  err "assembleren mislukt"
fi
# Een .file[name=...] in de bron schrijft zijn eigen prg (relatief aan de bronmap) en negeert -o:
# verzamel alle prg's die de afgelopen 60 seconden zijn geschreven en zet ze in OUTDIR.
# (zsh: ms-60 = minder dan 60 seconden oud; m-1 was "minder dan een dag" en nam ook oude prg's mee)
prgs=("$OUTDIR/$BASE.prg" "$SRC_DIR"/*.prg(N.ms-60))
if (( ${#prgs[@]} )); then
  for p in "${prgs[@]}"; do
    [[ "$p" == "$OUTDIR"/* ]] && continue
    mv -f "$p" "$OUTDIR/" && note "verplaatst: ${p:t} -> $OUTDIR/"
  done
fi
[[ -f "$OUTDIR/$BASE.prg" ]] || ls "$OUTDIR"/*.prg(N) >/dev/null 2>&1 || err "geen prg ontstaan in $OUTDIR"

# --- optioneel VICE ---
if (( START_VICE )); then
  if [[ -x "$VICE_EXE" ]]; then
    note "starting in VICE"
    "$VICE_EXE" -autostart "$PWD/$OUTDIR/$BASE.prg" +confirmonexit >/dev/null 2>&1 &!
  else
    note "VICE niet gevonden ($VICE_EXE) — prg staat in $OUTDIR/$BASE.prg"
  fi
fi
note "OK: $OUTDIR/$BASE.prg"
