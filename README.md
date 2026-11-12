# 👑 Hollow Crown

```text
    **** COMMODORE 64 BASIC V2 ****
 64K RAM SYSTEM  38911 BASIC BYTES FREE

READY.
LOAD"HOLLOW CROWN",8,1

SEARCHING FOR HOLLOW CROWN
LOADING
READY.
RUN
```

> *The sun has been stolen. The lantern is empty. The wolves are waiting.*
> *Somebody hand Eldric a jug.*

**Hollow Crown** is a point-and-click adventure for the **Commodore 64**, written from scratch in 6502 assembly.
It plays the way the classic late-80s C64 adventures did: the room on top, a bar of verbs below, and a cursor
you use to build sentences like **"Use jug with barrel"**. The story, world, characters, art, music and code are
all our own. We borrow only the genre and the way you control it.

![Eldric walking across the village square of Dawnhaven, in VICE](docs/images/hoofdstuk2_lopen.png)

![Eldric at three depths: front, by the smithy, between the houses at the back](docs/images/hoofdstuk2_diepte.png)

*Eldric mid-stride on his way round the fountain (top), and at three depths (above), running in VICE. Messages on top, Dawnhaven as a 160×128
multicolour room, the verb bar below (in Dutch for now). The test suite checks this screen pixel by pixel against
what memory says it should be.*

---

## 📜 The story

The kingdom of **Aethermoor** lived beneath the Eternal Sun, until the night of the double lunar eclipse. That
night the **Hollow King** crawled out of the earth, stole the sunlight and took the throne castle. Ever since,
the land has been stuck in an endless dusk.

You are **Eldric**, the last Warden of the Light Crown. Your sword holds the last fragment of sunlight, and you'll
need it, because there is no combat here. Shadow wolves, ghost knights and worse are puzzles to be solved, not
monsters to be hit.

| Who | What |
|---|---|
| **Eldric** | You. Last Warden, carrier of the last light, owner of a very important sword |
| **Mira** | A blind witch in Dawnhaven who *sees* paths, once she has her seeing stone back |
| **Baron Vex** | First servant of the Hollow King, lord of the Darkwood |
| **The Hollow King** | Stole the sun. Rude |

**Chapters:** Dawnhaven → Darkwood → Sea of Oblivion → Rock Gorge → Ice Peak → The Forgotten Castle.

Chapter 1 (*Dawnhaven*) comes first: four rooms, one chain of puzzles, no dead ends and no deaths.

---

## 🖥️ The screen

```text
row  0-1   messages: what a character says, in their own colour
row  2-17  the room: 160 × 128 multicolour bitmap
row 18     sentence line:  "Use jug with barrel"
row 19-21  12 verbs (3 × 4)
row 22-23  inventory, with ↑ ↓ arrows
row 24     chapter name
```

```text
Walk to     Pick up     Use         Open
Look at     Talk to     Give        Close
Push        Pull        Read        What is
```

*(In game the verbs are in Dutch for now; English comes later.)*

Three raster interrupts per frame switch between text, bitmap and text. Joystick, mouse and keyboard all work,
at the same time:

| | Move | Fire |
|---|---|---|
| Joystick (port 2) | stick | fire button |
| 1351 mouse (port 1) | mouse | left button |
| Keyboard | **CRSR** keys, with **SHIFT** for up/left (arrow keys in VICE) | **SPACE** or **CTRL** (left Control in VICE), also RETURN |
**F1** toggles music, **F5** saves, **F7** loads, and **space** skips text you've already read.

---

## ⚙️ Under the hood

The game is a small **SCUMM-style engine**. The engine is generic; the game itself is data and scripts.

- **Rooms:** one compressed file per room on the disk, loaded into a fixed buffer.
- **Foreground:** Eldric can walk *behind* things. The fountain's stone column is also a sprite with a lower
  number than Eldric's, switched on only while his feet stand behind it. The column in the bitmap gets exactly the
  sprite's colours, so you never see the switch, and the rest of the picture keeps all its colours.
- **Walkboxes:** rectangles with a neighbour graph. Paths are found with BFS, then Eldric walks in straight lines.
- **Actors:** two multicolour sprites stacked on top of each other, with poses copied into sprite slots on change.
  Actors **shrink with depth**: five sizes per pose, picked from the depth of their feet, so Eldric fits through
  the doors at the back of a room and walks a little slower there. The C64 cannot scale sprites, so the sizes are
  pre-made by the costume tool (the two smallest are hand-drawn).
- **Languages:** Dutch first. English and French follow later as their own disks from the same engine: every
  line the player reads lives in the scripts and a small text file, never in the engine code.
- **Scripts:** plain-text `.hcs` files, compiled by a Python compiler into bytecode for a tiny VM. The compiler
  also checks that chapter 1 can actually be finished.
- **Testing without hands:** an `AUTOTEST` build replays *input tapes* (cursor moves, fire, waits). VICE runs them
  and the test reads the game state straight from memory. A test only passes when the state is correct;
  a pretty screenshot alone doesn't count.

**Memory map (VIC bank 3):** program `$0801-$BFFF`, screen `$C000`, sprites `$C400`, bitmap `$E000` and font
`$F800`, both under the Kernal ROM. With the font there, one `$d018` value serves text and bitmap alike, so the
raster splits only touch `$d011` and `$d016`.

---

## 🧰 Toolchain

| Tool | Version | Used for |
|---|---|---|
| [Kick Assembler](http://theweb.dk/KickAssembler/) | 5.14 (`tools/KickAss.jar`) | 6502 assembly |
| Java (OpenJDK) | 17+ (tested on 27) | Runs Kick Assembler |
| [VICE](https://vice-emu.sourceforge.io/) | 3.10 (`x64sc`, `c1541`) | Emulation (PAL), disk images, automated tests |
| Python | 3.9+ with Pillow | Sprite, room, script and music tools |

On macOS, `/usr/bin/java` is only a stub. Use a real JDK, for example `brew install openjdk`.
Tool paths live in one place, at the top of `build.sh` and `tools/vicetest.py` (or set `JAVA` / `VICE_BIN`).

```bash
./build.sh                              # build/hollowcrown.d64
./build.sh --vice                       # ...and start it in VICE
./tests/alles.sh                        # every test: compiler errors + every input tape in VICE
```

---

## 🗂️ Project layout

```text
src/        the engine (*.asm)
scripts/    the game itself (*.hcs)
data/       FLUX art, rooms, music
tools/      Kick Assembler, converters, script compiler, test runner
tests/      input tapes and expected outcomes
docs/       development log and reference material
build/      everything the build produces (generated, not in git)
oud/        old experiments ("oud" is Dutch for "old")
```

---

## 🚧 Status

Early days. The build makes a D64; automated tests boot it in VICE, play input tapes, check the game state and
compare every screenshot pixel by pixel with the screen as memory says it should be, sprites included. The engine is being built
in this order:

- [x] 0. Setup: build script, memory map with asserts, D64, test runner
- [x] 1. The split screen and the cursor
- [x] 2. Eldric walks (walkboxes, pathfinding)
- [x] 3. Objects and the sentence line
- [x] 4. Script VM and compiler
- [x] 5. Inventory
- [ ] 6. More rooms, loading from disk
- [ ] 7. Conversations
- [ ] 8. Foreground masking (first object done: the fountain) and small animations
- [ ] 9. Chapter 1, fully playable
- [ ] 10. Title screen with original SID music

Progress notes are in [`docs/LOGBOEK.md`](docs/LOGBOEK.md) (in Dutch).

---

## 🙏 Inspiration

Hollow Crown owes its *genre* to the Lucasfilm Games adventures of the 1980s and to the modern C64 adventure
*Caren and the Tangled Tentacles*. We read about how those games were built; we don't copy their code, art,
text or music.

```text
READY.
█
```
