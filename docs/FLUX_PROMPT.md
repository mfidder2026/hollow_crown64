# Prompt for a Hollow Crown picture (FLUX)

One prompt that gets the setting, the look and feel, the size and the ratio right in one go. Fill in only the
**[SCENE]** part per room. Everything else stays as it is.

## The prompt (English: FLUX understands that best)

```text
Same art style, colors and thick black outlines as the reference picture.
Cartoon pixel art for a 1980s point-and-click adventure game, like a hand-drawn comic panel: bold black outlines
around every shape, flat colors with one darker shade per color, no gradients, no blur, no tiny details, no text.
Fantasy medieval village Dawnhaven at endless dusk: purple twilight sky, warm orange thatched roofs, grey stone,
dark wood, bright green grass, yellow dirt paths; warm firelight inside, cold shadows outside.

Camera: straight from the front at eye height, like a theatre stage, a wide flat view with almost no perspective.
Composition for a wide strip: the top 18 percent of the picture is only plain sky or plain ceiling, the bottom
18 percent is only plain floor or grass. Everything that matters sits in the middle band.
The walkable floor fills the lower third of that middle band, from the left edge to the right edge, in one plain
color (wood planks, packed earth or grass) with only a few lines on it.
Scale: a standing person in the front would be about one fifth of the picture height; a door is a little taller
than that person; furniture is small and low (a table reaches to a person's hip). Leave open floor in front of
every door and every object.

[SCENE]
```

## Examples for [SCENE]

**Inn (herberg):**
```text
The inside of a cozy medieval inn: a stone fireplace with a fire on the left, a narrow wooden front door next to
it, one small window with purple dusk sky, a small oil barrel with a tap against the back wall, a long bar
counter on the right with a few clay jugs on a shelf above it, a long low table with two small stools in the
middle of the floor, wooden plank floor.
```

**Smithy (smidse):**
```text
The inside of a village smithy: a big stone forge hearth with cold grey ashes in the middle of the back wall,
the smith's corner on the left, an iron anvil on a tree stump on the right, a wooden door on the right of the
back wall, tongs and hammers hanging on the wall, packed brown earth floor.
```

**Forest edge (bosrand):**
```text
The edge of a dark spooky forest at dusk: a yellow dirt path from the front into the dark woods in the middle,
a wooden signpost to the right of the path, big dark trees on the left and right, bright green grass in the
front, purple twilight sky between the trees.
```

## How to make it

```bash
python3 tools/flux.py scene "<the prompt above with [SCENE] filled in>" build/flux/herberg.png \
    --rauw --ref data/flux/dawnhaven.png --aantal 3
```

- `--rauw`: the style is already in the prompt (otherwise flux.py adds its own style sentence).
- `--ref data/flux/dawnhaven.png`: the plein as the style reference. This keeps every room looking like the plein.
- `--aantal 3`: three versions with different seeds. Pick the best one.
- **Redrawing your own layout** (for example a placeholder with the right proportions): pass that picture as the
  first reference and the plein as the second, and start the scene with *"Redraw the first image in exactly the
  art style of the second image. Keep the composition of the first image exactly: every object at the same
  place and the same size, nothing added and nothing removed."* (`--init` with `--sterkte` has no effect with
  this model: the result came out the same.)
- The first picture after the app starts takes a long time (the model loads). After that it takes about a
  minute per picture, about 1.5 minutes with two references.

## Size and ratio (why the prompt says this)

| | |
|---|---|
| FLUX makes | 1024 × 640 (16:10) |
| The game uses | a 5:2 strip across the full width: 1024 × 410 source pixels |
| That becomes | 160 × 128 multicolor pixels (rows 2–17 of the screen); each pixel is 2 wide |
| Crop in `data/kamers.txt` | `boven=115` (the 18% sky or ceiling is cut off at the top, the 18% floor at the bottom) |
| Converter | `kleur=1.5 licht=1.0 sterkte=0` (no dithering: flat areas, like the plein) |
| Eldric | front 34 room pixels tall (≈ 1/4 of the strip, ≈ 1/5 of the FLUX picture), at the back 14 or 10 |
| Doors | about 35 room pixels (a little taller than Eldric at the front) |
| Black | the top pixel row and the bottom 2 rows of the room turn black (the converter does this itself) |
| Floor | must convert to the room's `LOOPKLEUREN` (herberg: orange/brown, smithy: brown/orange, outside: green/yellow); the build checks every walkbox |

After converting: `python3 tools/kamer.py data/kamers.txt build/gen` and look at `build/gen/kamer_<name>.png`
(left: source strip, right: what the C64 shows). Then adjust the walkboxes and click boxes in `scripts/<room>.hcs`
(`python3 tools/loopkaart.py <room> --toon` shows where walking is allowed).

## Patches (the same room with something changed)

A patch must be the same picture with one small change in exactly the same place (table pushed aside, jug gone,
fire burning). Don't generate a new picture for it: copy the room picture and paint only that rectangle (Python/
Pillow), or use FLUX with the room picture as the only reference and "the same image, but ...". The patch
rectangle goes in `data/kamers.txt` (`patch=name:x,y,w,h:picture`, x and w a multiple of 4, y and h of 8).
