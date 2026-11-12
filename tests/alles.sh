#!/bin/zsh
# alles.sh — alle tests: de compiler (foute scripts weigeren) en alle banden in VICE.
#   ./tests/alles.sh          exitcode 0 = alles geslaagd
cd "${0:A:h}/.."
uit=$(python3 tools/compilertest.py); rc1=$?
print -r -- "$uit" | grep -E 'FOUT|goed$'
uit=$(python3 tools/vicetest.py tests/*.band 2>&1); rc2=$?
print -r -- "$uit" | grep -E '^\[test\] [a-z_]+: (GESLAAGD|MISLUKT|FOUT)|^\[test\] [0-9]+ van|FOUT'
(( rc1 == 0 && rc2 == 0 ))
