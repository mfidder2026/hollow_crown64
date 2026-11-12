# 🕹️ KickAss C64 — AI Skill Kit

```text
    **** COMMODORE 64 BASIC V2 ****
    64K RAM SYSTEM  38911 BASIC BYTES FREE

    READY.
    LOAD"KICKASS SKILL KIT",8,1
    SEARCHING FOR KICKASS SKILL KIT
    LOADING
    READY.
    RUN
```

> 🇳🇱 Lees dit document in het Nederlands? Zie **[README.nl.md](README.nl.md)**.

A complete, battle-tested toolchain that lets an **AI agent** (or a human)
write correct **6502/6510 assembly** for the Commodore 64, statically check
it, assemble it, and test it in **VICE** — built around **Kick Assembler
5.x**.

![platform](https://img.shields.io/badge/platform-Commodore%2064-e62429)
![assembler](https://img.shields.io/badge/assembler-Kick%20Assembler%205.x-4e9a06)
![checker](https://img.shields.io/badge/syntax%20checker-Python%203.7%2B-306998)
![build](https://img.shields.io/badge/build%20script-Windows%20cmd.exe-0078D6)
![skill](https://img.shields.io/badge/skill-AI%20agent%20ready-8f4cc9)

---

## 📑 Contents

1. [What is this?](#-what-is-this)
2. [The three components](#-the-three-components)
3. [Quick start](#-quick-start)
4. [The pipeline](#-the-pipeline)
5. [build.bat — reference](#-buildbat--reference)
6. [c64_ka_syntax_checker.py — reference](#-c64_ka_syntax_checkerpy--reference)
7. [C64_KICKASS_SKILL.md — table of contents](#-c64_kickass_skillmd--table-of-contents)
8. [The 12 hard rules](#-the-12-hard-rules)
9. [Practical lessons — greatest hits](#-practical-lessons--greatest-hits)
10. [Smallest working example](#-smallest-working-example)
11. [Requirements & installation](#-requirements--installation)
12. [Use by an AI agent](#-use-by-an-ai-agent)
13. [Project structure](#-project-structure)

---

## ✨ What is this?

LLMs *think* they can write 6502 assembly — until you actually assemble the
output. Then you discover `;` comments (Kick Ass uses `//`), parentheses
silently parsed as indirect addressing, and zeropage conflicts that crash
the program on the first `jsr`.

This repo solves that with three components that together form one
**enforced quality pipeline**:

```text
agent reads skill ─▶ writes code ─▶ checklist ─▶ syntax checker (0 ERRORs)
                              ─▶ Kick Ass (0 errors) ─▶ VICE (testing)
```

Target platform: **real Commodore 64 / VICE, PAL.** Every lesson in the
skill was tested on actual hardware emulation during the development of the
games *"Captain Cock en de Black Whore"* and *"Super Pong"*.

---

## 🧩 The three components

| File | Role | When |
|---|---|---|
| [`C64_KICKASS_SKILL.md`](C64_KICKASS_SKILL.md) | 3,726 lines of working instructions: syntax, addressing, script language, macros, segments, 21 recipes, 28 practical lessons | The agent reads this before writing a single line |
| [`c64_ka_syntax_checker.py`](c64_ka_syntax_checker.py) | Static checker with a CLI and a Python API. Catches the classic mistakes before assembling | Mandatory before every build — **0 ERRORs or nothing gets built** |
| [`build.bat`](build.bat) | Generic Windows build script: syntax-check → assemble → VICE. One command, Git-ready | Every build; everyone just fills in their tool paths |

---

## 🚀 Quick start

**1. Clone the repo next to your project** (or into it).

**2. Fill in your tool paths** in the `[1] CONFIG` block at the top of
`build.bat`:

```bat
set "JAVA_EXE=C:\path\to\java.exe"
set "KICKASS_JAR=C:\path\to\KickAss.jar"
set "VICE_EXE=C:\path\to\x64sc.exe"
```

Only `JAVA_EXE` and `KICKASS_JAR` are required. Python, the checker, and
VICE are optional: anything missing is skipped gracefully with a clear
message.

**3. Build:**

```text
build.bat                builds the only .asm in the current directory
build.bat main.asm       builds main.asm
build.bat main.asm -libdir lib -define DEBUG
                         extra options go straight to Kick Ass
build.bat --check-only   syntax check only, no assembling
build.bat --help         all options
```

Output lands in `build\`: `<name>.prg` and `<name>.vs` (VICE symbols).
Kick Ass additionally writes `<name>.sym` next to the source.

---

## ⚙️ The pipeline

The skill prescribes (§0) that **every assignment** follows the same fixed
route:

1. **Read the hard rules** (§1) before writing a single line of code.
2. **Write code** following the patterns in §3 through §13.
3. **Run through the verification checklist** (§16).
4. **Run `c64_ka_syntax_checker.py`** — 0 ERRORs is mandatory.
5. **Assemble with Kick Ass** — 0 errors is mandatory.
6. **Test in VICE.**

And: if something is not possible, **say so explicitly**. Never invent
directives or opcodes. `build.bat` enforces steps 4 and 5 for you.

---

## 🦇 build.bat — reference

Generic build script for Windows **cmd.exe** (not PowerShell — see §18.14
of the skill). Works from any location; every path is resolved by the
`:resolve` subroutine in this order:

```text
configured value → project directory → build.bat directory → PATH
```

### Configuration (block [1])

| Variable | Required | Default | Meaning |
|---|:---:|---|---|
| `JAVA_EXE` | ✅ | `java` | Java runtime that runs Kick Ass |
| `KICKASS_JAR` | ✅ | `KickAss.jar` | Path to the assembler jar |
| `PYTHON_EXE` | ➖ | `python` | For the syntax check; empty/missing → step skipped |
| `CHECKER` | ➖ | `c64_ka_syntax_checker.py` | Searched in project and script directories |
| `VICE_EXE` | ➖ | *(empty)* | Emulator; empty/missing → VICE not started |
| `OUTDIR` | ➖ | `build` | Where `.prg`/`.vs` end up |
| `KA_OPTS` | ➖ | `-vicesymbols -showmem` | Fixed options for every Kick Ass invocation |

### Switches

| Switch | Effect |
|---|---|
| `--clean` | Wipe the output directory before building |
| `--no-check` | Skip the syntax check |
| `--check-only` | Syntax check only, do not assemble |
| `--no-vice` | Don't start VICE after the build |
| `--help`, `-h`, `/?` | Help text |
| *other arguments* | Passed straight to Kick Ass (`-libdir`, `-define`, …) |

### Behavior

- **Source auto-detection**: no argument → if exactly one `.asm` exists in
  the directory, it gets built. With multiple files you get a list to choose
  from.
- **Error handling**: clear `[build] ERROR: …` messages; every failed step
  halts the build.
- **Exit codes**: `0` = success, `1` = failure — CI-friendly.
- **VICE launch**: `x64sc -autostart <prg> +confirmonexit`, so you won't be
  asked for confirmation on exit.

---

## 🐍 c64_ka_syntax_checker.py — reference

Static checker that catches the classic Kick Ass pitfalls **before** the
slow Java assembler runs. Fast, side-effect-free, CI-friendly.

### CLI

```bash
python c64_ka_syntax_checker.py main.asm
python c64_ka_syntax_checker.py main.asm --json
python c64_ka_syntax_checker.py main.asm --no-warn
python c64_ka_syntax_checker.py main.asm --cpu _65c02
```

| Exit code | Meaning |
|:---:|---|
| `0` | 0 ERRORs (warnings allowed) |
| `1` | ERRORs found |
| `2` | Usage error: file not found, unknown cpu, … |

Environment variable `KA_NO_WARN=1` suppresses warnings without the flag.

### What the checker detects

- Unbalanced `()`, `[]`, `{}` and `#if`/`#endif`; unterminated strings and
  block comments
- Unknown directives, preprocessor directives, and mnemonics; mnemonics
  outside the configured `.cpu`
- Invalid addressing modes (`sta #$10`, `ldx $10,x`, `lda ($10),x`)
- `;` used as a comment; a leading `(` read as indirection
- Value ranges (`#$100`, `.byte 300`, `.word $12345`)
- `.for` headers without double semicolons; `.function` without `.return`
- Macro calls with the wrong argument count
- Duplicate labels within the same scope; `.eval` on an undeclared variable
- Missing import files for both `.import` and `#import`
- `jmp`/`jsr` to a label that contains data instead of code
- A raster IRQ that gets enabled but never acknowledged via `$d019`
- A hardware vector `$fffe` that ends through the kernal (`$ea31`/`$ea81`)

### What the checker does NOT check

It is static, not an assembler: **branch ranges** (±127 bytes), **memory
overlaps**, and **zeropage selection** are not checked. The real assembly
step remains mandatory.

### Python API

```python
from c64_ka_syntax_checker import check_source, check_file

report = check_source(src, print_errors=False)        # text report
data   = check_source(src, return_structured=True)    # dict: issues + summary
rc     = check_file("main.asm")                       # 0 = ok, 1 = errors
```

The API mirrors that of the BASIC sibling `c64_syntax_checker.py`, so agents
can call both checkers uniformly.

---

## 📚 C64_KICKASS_SKILL.md — table of contents

The heart of the repo: one document, §0 through §19 plus two appendices,
ordered the way an agent needs them.

| § | Topic |
|---|---|
| 0 | **Work order** — the fixed six-step pipeline for every assignment |
| 1 | **The 12 hard rules** — syntax laws almost every AI agent violates otherwise |
| 2 | **Toolchain** — CLI options, `KickAss.cfg`, checker, VICE |
| 3 | Syntax: mnemonics, addressing modes, number formats, labels, zeropage labels |
| 4 | Memory & data: `*=`, data directives, encodings, binary import, console/debug |
| 5 | Script language: variables, scopes, value types, math, strings, lists/hashtables/structs |
| 6 | Functions, macros, and pseudocommands |
| 7 | Preprocessor: `#if`, `#import`, `#define`, … |
| 8 | Scopes and namespaces (incl. escaping to the root) |
| 9 | Segments: defining, switching, output, bounds, patching, modifiers |
| 10 | `.file` and `.disk` — prg and d64 output |
| 11 | Command-line variables, importing binaries/SID/graphics, custom files, label export |
| 12 | Source file name, BASIC upstart, opcode and color constants |
| 13 | **21 C64 recipes**: raster IRQ, kernal takeover, sprites, SID music, Koala bitmap, screen-line tables, sine/speedcode, IRQ building blocks, PAL/NTSC detection, … |
| 14 | Linking with the BASIC pipeline (companion document `C64_BASIC_SKILL.md`) |
| 15 | Common mistakes |
| 16 | **Verification checklist** — 30+ checkable items covering syntax, structure, script, hardware, segments, and tooling |
| 17 | Two complete templates (main and library file), checker-clean: 0 errors, 0 warnings |
| 18 | **16 practical lessons** from *"Captain Cock en de Black Whore"* |
| 19 | **12 practical lessons** from *"Super Pong"* |
| A | Appendix: addressing modes per mnemonic (standard 6502, illegals, DTV, 65c02) |
| B | Appendix: directive overview |

---

## 📏 The 12 hard rules

The number-one reason LLM-generated Kick Ass code fails: the AI writes
"generic 6502" instead of Kick Ass. §1 of the skill enforces these laws:

| # | Rule | Why |
|:---:|---|---|
| 1 | `//` is a comment, `;` is a statement separator | `lda #0 ; set border` executes `set` as a command |
| 2 | `[ ]` for grouping, `( )` means indirect | `lda (2+5)*2` becomes indirect addressing |
| 3 | Every program starts with `*=` or a segment | Otherwise the assembler doesn't know where code belongs |
| 4 | Labels: `loop:` at definition, `loop` at use | Consistency prevents ambiguity |
| 5 | Illegal opcodes are on by default | `.cpu _6502` is the default; exclude them with `_6502NoIllegals` |
| 6 | Immediate values must fit in a byte | `lda #$100` is an error — use `#<label` / `#>label` |
| 7 | `.var` declares, `.eval` modifies | `.eval x=1` without a prior `.var x` is an error |
| 8 | Mutable values must be locked outside their pass | `.lock()` or inside a `.define` block |
| 9 | Macros/functions/pseudocommands may be defined *after* their call | Only `.var` and `.const` must precede use |
| 10 | One sprite = 63 bytes, pointer value = address/64 | See §13.3 |
| 11 | Late-defined zeropage labels must be marked `.zp` | Otherwise absolute form: +1 byte, +1 cycle per access |
| 12 | Let the assembler do the math, not you | `.fill 256, round(...)` beats a hand-typed table |

---

## 🎓 Practical lessons — greatest hits

§18 and §19 contain 28 lessons, each one paid for with real debugging
sessions. The most famous:

- **§18.2 — Zeropage conflict: THE classic trap.** Kernal variables wipe out
  your own zp variables unless you reserve what the kernal uses.
- **§18.3 — Screencode vs PETSCII:** which encoding belongs to which output
  route (direct screen memory vs `$ffd2` via the kernal).
- **§18.4 — "Screen full of green bars":** what happens when you print
  screencodes as PETSCII — the classic first-run trap.
- **§18.8 — Using `BasicUpstart2` correctly** (without your own `*=$0801`
  around it).
- **§18.14 — cmd.exe vs PowerShell:** pipes, `&&`, and quoting differ;
  build scripts belong under cmd.exe.
- **§19.3 — Never wipe the sprite x-hi bits on update:** mask with `and`/`ora`
  or sprites glitch at the screen edge.
- **§19.10 — Branch range ±127 bytes:** the checker doesn't catch this; the
  skill teaches you to spot `jmp` trampolines.
- **§19.11 — `.const` WITH a dot:** the most common Kick Ass typo.

---

## 🧪 Smallest working example

This minimal program has been run through the full pipeline
(checker: 0 errors / 0 warnings, Kick Ass 5.25: 0 errors):

```asm
// minitest.asm - tiny test program for build.bat
:BasicUpstart2(main)

main:
    lda #0
    sta $d020
    sta $d021

halt:
    jmp halt
```

Expected output of `build.bat`:

```text
[build] no source file given, the only .asm here: minitest.asm
[build] syntax-check minitest.asm
Summary: 0 error(s), 0 warning(s)
[build] assembling...
[build] starting in VICE
[build] OK: build\minitest.prg
```

For a full skeleton with segments, a raster IRQ, and a library file, see the
templates in §17 of the skill.

---

## 📦 Requirements & installation

| Tool | Version | Required for | Where |
|---|---|---|---|
| [Kick Assembler](http://www.theweb.dk/KickAssembler/) | 5.x | assembling | by Mads Nielsen |
| [Java](https://adoptium.net/) | 8+ | assembling | Kick Ass is a jar |
| [Python](https://www.python.org/) | 3.7+ | syntax check | CLI and API |
| [VICE](https://github.com/vice-emu/vice) | recent | run/test | `x64sc` (accurate PAL emulation) |
| Windows + cmd.exe | — | build.bat | the script uses cmd-specific syntax |

The checker itself is platform-independent (pure Python); only `build.bat`
is Windows-specific.

---

## 🤖 Use by an AI agent

### Skill format

`C64_KICKASS_SKILL.md` carries YAML frontmatter and can be installed
directly as a skill file:

```yaml
---
name: c64-kickassembler
description: Complete work instruction for writing correct Kick Assembler
  code for the Commodore 64 — syntax, addressing modes, script language,
  macros, scopes, segments, d64 output, and ready-made recipes for raster
  IRQs, sprites, SID, and graphics. Always use this document whenever
  6502/6510 assembly is written, reviewed, or debugged for a real C64 or
  VICE.
---
```

For example: drop the file into
`.claude/skills/c64-kickassembler/SKILL.md` (or your agent's skill folder),
or adapt frontmatter + document to whatever your tool expects.

### System prompt recipe

> Read `C64_KICKASS_SKILL.md` in full before writing or reviewing C64
> assembly. Follow the work order in §0, the hard rules in §1, and the
> checklist in §16. Run `c64_ka_syntax_checker.py` before every build —
> 0 ERRORs is mandatory; then assemble and test in VICE. If something is
> not possible, say so explicitly: never invent directives or opcodes.

### Why this works

The combination enforces three things LLMs naturally skip:

1. **Knowledge**: the skill document is the single source of truth — no
   hallucinated directives that don't exist.
2. **Checking**: the statically catches what LLMs systematically get wrong
   (`;` comments, `()` grouping, value ranges, IRQ hygiene).
3. **Proof**: only code that survives the checker *and* the assembler *and*
   VICE counts as "done" — not what the agent itself believes to be correct.

---

## 🗂️ Project structure

```text
KickAss/
├── C64_KICKASS_SKILL.md       # The skill: 3,726 lines (§0–§19 + 2 appendices)
├── c64_ka_syntax_checker.py   # Static checker: CLI + Python API
├── build.bat                  # Generic build script: check → assemble → VICE
├── README.md                  # This file (English)
├── README.nl.md               # Dutch version of this file
└── .gitignore                 # Keeps build artifacts out of the repo

# Generated during a build (gitignored):
build/                         # <name>.prg + <name>.vs (VICE symbols)
<name>.sym                    # Kick Ass symbol file, next to the source
```

---

```text
10 PRINT "NO ZEROPAGE CONFLICTS TODAY"
20 GOTO 10
RUN

READY.
█