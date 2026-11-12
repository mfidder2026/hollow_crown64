#!/usr/bin/env python3
"""Muziek voor de C64: een MIDI-bestand wordt drie SID-stemmen, of een bestaande .sid wordt nagekeken.

    python3 muziek.py info liedje.mid                 # welke partijen (sporen/kanalen) er in de MIDI zitten
    python3 muziek.py omzetten liedje.mid -o muziek.asm --melodie 3 --bas 5 --drums 9 --tot 40
    python3 muziek.py sid liedje.sid                  # adres, init/play, timing van een kant-en-klare SID (HVSC)
    python3 muziek.py opnemen build/intro.prg -o intro.wav --sec 20   # VICE speelt, het geluid wordt een WAV
    python3 muziek.py luister intro.wav               # welke noten er klinken, per kwart seconde

omzetten schrijft één Kick Assembler-bestand met de speler en de noten: zet het waar je wilt (`*=$8000 "Muziek"` en
dan `#import "muziek.asm"`), roep muziek_init één keer aan en muziek_play 50 keer per seconde (raster-IRQ, PAL).
De speler gebruikt geen zeropage. Stem 1 = melodie, stem 2 = bas, stem 3 = drums (of een derde partij met --derde).
"""
import argparse, os, struct, subprocess, sys, time

PAL_CLOCK = 985248
FRAMES_PER_SEC = 50          # muziek_play één keer per beeld (PAL)
LOW, HIGH = 12, 106          # MIDI-noten die de SID kan spelen (C0 .. A#7)
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
GM = ["piano", "piano", "piano", "piano", "e-piano", "e-piano", "klavecimbel", "clavinet", "celesta", "glockenspiel",
      "muziekdoos", "vibrafoon", "marimba", "xylofoon", "buisklokken", "dulcimer", "orgel", "orgel", "orgel", "kerkorgel",
      "orgel", "accordeon", "mondharmonica", "accordeon", "gitaar", "gitaar", "gitaar", "gitaar", "gitaar", "gitaar",
      "gitaar", "gitaar", "bas", "bas", "bas", "bas", "bas", "bas", "synthbas", "synthbas", "viool", "altviool", "cello",
      "contrabas", "strijkers", "strijkers", "harp", "pauken", "strijkers", "strijkers", "synthstrijkers",
      "synthstrijkers", "koor", "koor", "koor", "orkesthit", "trompet", "trombone", "tuba", "trompet", "hoorn", "koper",
      "synthkoper", "synthkoper", "sax", "sax", "sax", "sax", "hobo", "hoorn", "fagot", "klarinet", "piccolo", "fluit",
      "blokfluit", "panfluit", "fles", "shakuhachi", "fluitje", "ocarina", "synthlead", "synthlead", "synthlead",
      "synthlead", "synthlead", "synthlead", "synthlead", "synthlead", "synthpad", "synthpad", "synthpad", "synthpad",
      "synthpad", "synthpad", "synthpad", "synthpad"] + ["effect"] * 32

# GM-drums (kanaal 10) -> de drums van de speler; hoe lager het nummer, hoe belangrijker als er twee tegelijk vallen.
# Alles wat niet genoemd is (maracas, shaker, tamboerijn, koebel, claves …) tikt als hihat.
DRUMS = {k: 5 for k in range(27, 88)}
DRUMS.update({35: 1, 36: 1, 37: 2, 38: 2, 39: 2, 40: 2, 41: 3, 43: 3, 45: 3, 47: 3, 48: 3, 50: 3,
              60: 3, 61: 3, 62: 3, 63: 3, 64: 3, 65: 3, 66: 3, 46: 4, 49: 4, 52: 4, 55: 4, 57: 4})
DRUM_NAMES = {1: "kick", 2: "snare", 3: "tom", 4: "open hihat/bekken", 5: "hihat"}

# klanken: golfvorm, attack/decay, sustain/release, pulsbreedte (alleen bij puls), pulsbreedte-modulatie per beeld
KLANKEN = {
    "puls":     (0x41, 0x08, 0xa6, 0x0600, 24),
    "pulskort": (0x41, 0x06, 0x48, 0x0800, 16),
    "zaag":     (0x21, 0x08, 0xa6, 0, 0),
    "zaagkort": (0x21, 0x06, 0x48, 0, 0),
    "driehoek": (0x11, 0x08, 0xa8, 0, 0),
    "fluit":    (0x11, 0x28, 0xc8, 0, 0),
}


def name(n):
    return NAMES[n % 12] + str(n // 12 - 1)


# ---------------------------------------------------------------------------------------------------------- MIDI lezen
def varlen(d, i):
    v = 0
    while True:
        b = d[i]; i += 1
        v = (v << 7) | (b & 0x7f)
        if b < 0x80:
            return v, i


def read_midi(path):
    d = open(path, "rb").read()
    if d[:4] != b"MThd":
        sys.exit("FOUT: " + path + " is geen MIDI-bestand (MThd ontbreekt)")
    hlen = struct.unpack(">I", d[4:8])[0]
    fmt, ntracks, division = struct.unpack(">HHH", d[8:14])
    if division & 0x8000:
        sys.exit("FOUT: SMPTE-tijd in de MIDI wordt niet ondersteund")
    i = 8 + hlen
    tracks, tempos = [], []
    for t in range(ntracks):
        while d[i:i + 4] != b"MTrk":
            if i >= len(d):
                break
            i += 8 + struct.unpack(">I", d[i + 4:i + 8])[0]
        length = struct.unpack(">I", d[i + 4:i + 8])[0]
        j, end = i + 8, i + 8 + length
        i = end
        tick, status, tname = 0, 0, ""
        open_notes, notes, programs = {}, [], {}
        while j < end:
            delta, j = varlen(d, j)
            tick += delta
            b = d[j]
            if b >= 0x80:
                status = b; j += 1
            if status == 0xff:
                kind = d[j]; ln, j = varlen(d, j + 1)
                data = d[j:j + ln]; j += ln
                if kind == 0x51 and ln == 3:
                    tempos.append((tick, (data[0] << 16) | (data[1] << 8) | data[2]))
                elif kind == 0x03 and not tname:
                    tname = data.decode("latin-1").strip()
                elif kind == 0x2f:
                    break
                continue
            if status in (0xf0, 0xf7):
                ln, j = varlen(d, j); j += ln
                continue
            hi, ch = status & 0xf0, status & 0x0f
            if hi in (0xc0, 0xd0):
                if hi == 0xc0:
                    programs.setdefault(ch, d[j])
                j += 1
                continue
            a, b2 = d[j], d[j + 1]; j += 2
            if hi == 0x90 and b2 > 0:
                key = (ch, a)
                if key in open_notes:      # dezelfde toets opnieuw: de vorige houdt hier op
                    s, v = open_notes.pop(key)
                    notes.append([s, tick, a, v, ch])
                open_notes[key] = (tick, b2)
            elif hi == 0x80 or (hi == 0x90 and b2 == 0):
                if (ch, a) in open_notes:
                    s, v = open_notes.pop((ch, a))
                    notes.append([s, tick, a, v, ch])
        for (ch, a), (s, v) in open_notes.items():
            notes.append([s, tick, a, v, ch])
        tracks.append({"name": tname, "notes": sorted(notes), "programs": programs})
    tempos.sort()
    if not tempos or tempos[0][0] > 0:
        tempos.insert(0, (0, 500000))
    return {"format": fmt, "division": division, "tracks": tracks, "tempos": tempos}


def seconds(midi):
    """tick -> seconden, met de tempowisselingen erin"""
    div, marks, sec, last_tick, last_tempo = midi["division"], [], 0.0, 0, midi["tempos"][0][1]
    for tick, tempo in midi["tempos"]:
        sec += (tick - last_tick) * last_tempo / div / 1e6
        marks.append((tick, sec, tempo))
        last_tick, last_tempo = tick, tempo

    def at(tick):
        k = 0
        for n, (t, s, tp) in enumerate(marks):
            if t <= tick:
                k = n
        t, s, tp = marks[k]
        return s + (tick - t) * tp / div / 1e6
    return at


def ticks(midi):
    """seconden -> tick (het omgekeerde van seconds)"""
    div, marks, sec, last_tick, last_tempo = midi["division"], [], 0.0, 0, midi["tempos"][0][1]
    for t, tempo in midi["tempos"]:
        sec += (t - last_tick) * last_tempo / div / 1e6
        marks.append((t, sec, tempo))
        last_tick, last_tempo = t, tempo

    def at(s):
        k = 0
        for n, (t, s0, tp) in enumerate(marks):
            if s0 <= s:
                k = n
        t, s0, tp = marks[k]
        return round(t + (s - s0) * 1e6 * div / tp)
    return at


def parts(midi):
    """elke combinatie van spoor en kanaal met noten is een partij"""
    out = []
    for t, tr in enumerate(midi["tracks"]):
        for ch in sorted({n[4] for n in tr["notes"]}):
            notes = [n for n in tr["notes"] if n[4] == ch]
            out.append({"track": t, "channel": ch, "name": tr["name"], "notes": notes,
                        "program": tr["programs"].get(ch)})
    return out


def polyphony(notes):
    events = sorted([(n[0], 1) for n in notes] + [(n[1], -1) for n in notes], key=lambda e: (e[0], e[1]))
    now = top = 0
    for _, step in events:
        now += step; top = max(top, now)
    return top


def cmd_info(a):
    midi = read_midi(a.midi)
    at = seconds(midi)
    bpm = 60e6 / midi["tempos"][0][1]
    end = max((at(n[1]) for tr in midi["tracks"] for n in tr["notes"]), default=0)
    print(f"{a.midi}: formaat {midi['format']}, {len(midi['tracks'])} sporen, {midi['division']} ticks per tel, "
          f"tempo {bpm:.0f} bpm" + (f" ({len(midi['tempos'])} tempowisselingen)" if len(midi["tempos"]) > 1 else "")
          + f", {end:.0f} seconden")
    print()
    print(" spoor kanaal  noten  bereik      gem.  tegelijk  begint   instrument / naam")
    for p in parts(midi):
        ns = p["notes"]
        lo, hi = min(n[2] for n in ns), max(n[2] for n in ns)
        mean = sum(n[2] for n in ns) / len(ns)
        drums = p["channel"] == 9
        inst = "DRUMS" if drums else (GM[p["program"]] if p["program"] is not None else "?")
        rng = "-" if drums else f"{name(lo)}-{name(hi)}"
        print(f" {p['track']:5} {p['channel'] + 1:7} {len(ns):6}  {rng:10} {'' if drums else name(round(mean)):5} "
              f"{polyphony(ns):8}  {at(ns[0][0]):5.1f} s   {inst}" + (f" / {p['name']}" if p["name"] else ""))
    print()
    print("Kies de melodie (meestal: hoog, veel noten, 1 tegelijk), de bas (laag) en de drums (kanaal 10).")
    print("Geef ze op als spoor (--melodie 3) of spoor:kanaal (--melodie 3:4).")


# --------------------------------------------------------------------------------------------------------- omzetten
def pick(midi, spec):
    """'3' of '3:4' (spoor, kanaal 1-16) -> de noten van die partij"""
    if spec is None:
        return []
    t, _, ch = str(spec).partition(":")
    notes = midi["tracks"][int(t)]["notes"]
    if ch:
        notes = [n for n in notes if n[4] == int(ch) - 1]
    if not notes:
        sys.exit(f"FOUT: spoor {spec} heeft geen noten (kijk met: muziek.py info)")
    return notes


def to_frames(midi, a):
    if a.rooster:   # een vast raster: een zestiende noot = precies N beelden, zonder heen-en-weer van een halve beeld
        per16 = midi["division"] / 4
        return lambda tick: round(tick / per16 * a.rooster)
    at = seconds(midi)
    return lambda tick: round(at(tick) * FRAMES_PER_SEC * a.snelheid)


def fit(pitch, transpose):
    p = pitch + transpose
    while p < LOW:
        p += 12
    while p > HIGH:
        p -= 12
    return p


def mono(notes, frame, first, last, highest, transpose):
    """één noot tegelijk: bij akkoorden de hoogste (melodie) of de laagste (bas); een noot houdt op als de volgende
    begint"""
    starts = {}
    for n in notes:
        f0, f1 = frame(n[0]), frame(n[1])
        if f1 <= first or f0 >= last:
            continue
        f0, f1 = max(f0, first) - first, min(f1, last) - first
        if f1 <= f0:
            f1 = f0 + 1
        p = fit(n[2], transpose)
        keep = starts.get(f0)
        if keep is None or (p > keep[1] if highest else p < keep[1]):
            starts[f0] = (f1, p)
    out, cur = [], None
    for f0 in sorted(starts):
        f1, p = starts[f0]
        if cur and cur[1] > f0:
            # er klinkt nog een noot: een lagere (melodie) of hogere (bas) noot ertussen telt niet
            if (p < cur[2]) if highest else (p > cur[2]):
                continue
            cur[1] = f0
        cur = [f0, f1, p]
        out.append(cur)
    return [(f0, f1, p) for f0, f1, p in out if f1 > f0]


def drum_hits(notes, frame, first, last):
    hits = {}
    for n in notes:
        kind = DRUMS.get(n[2])
        f0 = frame(n[0])
        if kind is None or not first <= f0 < last:
            continue
        f0 -= first
        hits[f0] = min(hits.get(f0, 9), kind)
    return [(f, min(f + 8, last - first), 0x80 + k) for f, k in sorted(hits.items())]


def stream(events, total):
    """(begin, eind, noot) -> bytes: duur (1-255 beelden), noot (0 = rust, 12-106, $7f = doorklinken, $80+ = drum)"""
    out, now = [], 0

    def put(dur, note):
        first = True
        while dur > 0:
            step = min(dur, 255)
            out.append((step, note if first or note in (0,) or note >= 0x80 else 0x7f))
            if note >= 0x80:
                note = 0
            first = False
            dur -= step
    for k, (f0, f1, p) in enumerate(events):
        f1 = min(f1, events[k + 1][0]) if k + 1 < len(events) else f1
        if f0 > now:
            put(f0 - now, 0)
        put(f1 - f0, p)
        now = f1
    if total > now:
        put(total - now, 0)
    return out


def klank(spec, default):
    spec = spec or default
    if spec in KLANKEN:
        return KLANKEN[spec]
    parts_ = spec.split(":")    # eigen klank: golf:ad:sr[:pulsbreedte[:modulatie]], hex
    try:
        v = [int(x, 16) for x in parts_]
    except ValueError:
        sys.exit("FOUT: klank " + spec + " ken ik niet; kies " + ", ".join(KLANKEN) + " of golf:ad:sr (hex)")
    return tuple(v + [0, 0][len(v) - 3:]) if len(v) >= 3 else sys.exit("FOUT: klank " + spec)


def asm_bytes(label, items):
    lines = [f"{label}:"]
    flat = [b for item in items for b in item]
    for k in range(0, len(flat), 16):
        lines.append("        .byte " + ",".join(f"${b:02x}" for b in flat[k:k + 16]))
    return lines


def cmd_omzetten(a):
    midi = read_midi(a.midi)
    frame = to_frames(midi, a)
    tick = ticks(midi)
    # --van en --tot zijn seconden in het origineel (zoals info ze toont), ook met --rooster of --snelheid
    first = frame(tick(a.van))
    all_notes = [n for tr in midi["tracks"] for n in tr["notes"]]
    song_end = max(frame(n[1]) for n in all_notes)
    last = min(song_end, frame(tick(a.tot))) if a.tot else song_end
    total = last - first
    if total <= 0:
        sys.exit("FOUT: --van/--tot laten niets over")
    voices = [mono(pick(midi, a.melodie), frame, first, last, True, a.transponeer),
              mono(pick(midi, a.bas), frame, first, last, False, a.transponeer)]
    if a.derde is not None:
        voices.append(mono(pick(midi, a.derde), frame, first, last, True, a.transponeer))
    elif a.drums is not None:
        voices.append(drum_hits(pick(midi, a.drums), frame, first, last))
    else:
        voices.append([])
    streams = [stream(v, total) for v in voices]
    sounds = [klank(a.klank1, "puls"), klank(a.klank2, "zaagkort"), klank(a.klank3, "driehoek")]
    player = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sidspeler.asm")).read()
    title = os.path.basename(a.midi)
    lines = [f"// muziek.asm — gemaakt door muziek.py uit {title}"
             f" ({a.van:g}-{last / FRAMES_PER_SEC:g} s, {total} beelden, {'eenmaal' if a.eenmaal else 'herhaalt'})",
             f"// stem 1: spoor {a.melodie}, stem 2: spoor {a.bas}, stem 3: "
             + (f"spoor {a.derde}" if a.derde is not None else f"drums uit spoor {a.drums}" if a.drums is not None else "stil"),
             "// muziek_init één keer, muziek_play 50 keer per seconde. Geen zeropage.",
             f".const MUZIEK_EENMAAL = {1 if a.eenmaal else 0}",
             f".const MUZIEK_VOLUME = {a.volume}"]
    for k, s in enumerate(sounds):
        wave, ad, sr, pw, pwm = s
        n = k + 1
        lines += [f".const MUZIEK_GOLF{n} = ${wave:02x}      // stem {n}: golfvorm (+1 = gate)",
                  f".const MUZIEK_AD{n} = ${ad:02x}        // attack (hoog), decay (laag)",
                  f".const MUZIEK_SR{n} = ${sr:02x}        // sustain (hoog), release (laag)",
                  f".const MUZIEK_PW{n} = ${pw:04x}      // pulsbreedte (alleen bij puls, $0000-$0fff)",
                  f".const MUZIEK_PWM{n} = {pwm}        // pulsbreedte-modulatie per beeld (0 = uit)"]
    lines.append("")
    lines.append(player.rstrip())
    lines.append("")
    for k, s in enumerate(streams):
        lines += asm_bytes(f"muziek_stem{k + 1}", s + [(0, 1 if a.eenmaal else 0)])
    open(a.o, "w").write("\n".join(lines) + "\n")
    size = sum(len(s) * 2 + 2 for s in streams)
    print(f"[muziek] {a.o}: {total / FRAMES_PER_SEC:.1f} seconden, noten {size} bytes + speler")
    for k, (v, s) in enumerate(zip(voices, streams)):
        kind = "drums" if v and v[0][2] >= 0x80 else "noten"
        rng = "" if not v or kind == "drums" else f", {name(min(e[2] for e in v))}-{name(max(e[2] for e in v))}"
        print(f"[muziek]   stem {k + 1}: {len(v)} {kind}{rng}")
    if a.rooster is None and a.snelheid == 1:
        bpm = 60e6 / midi["tempos"][0][1]
        print(f"[muziek] tempo {bpm:.0f} bpm: een zestiende is {FRAMES_PER_SEC * 60 / bpm / 4:.2f} beelden; "
              f"met --rooster {max(1, round(FRAMES_PER_SEC * 60 / bpm / 4))} wordt het ritme strak")


# -------------------------------------------------------------------------------------------------------- SID nakijken
def cmd_sid(a):
    d = open(a.sid, "rb").read()
    if d[:4] not in (b"PSID", b"RSID"):
        sys.exit("FOUT: geen PSID/RSID-bestand")
    version, off, load, init, play, songs, start = struct.unpack(">HHHHHHH", d[4:18])
    speed = struct.unpack(">I", d[18:22])[0]
    text = [d[22 + 32 * k:54 + 32 * k].split(b"\0")[0].decode("latin-1") for k in range(3)]
    body = d[off:]
    if load == 0:
        load, body = body[0] | body[1] << 8, body[2:]
    end = load + len(body) - 1
    flags = struct.unpack(">H", d[0x76:0x78])[0] if version >= 2 and off >= 0x7c else 0
    print(f"{a.sid}: {d[:4].decode()} v{version}, \"{text[0]}\" door {text[1]} ({text[2]})")
    print(f"  geheugen ${load:04x}-${end:04x} ({len(body)} bytes), init ${init:04x}, play ${play:04x}, "
          f"{songs} liedje(s), standaard {start}")
    cia = [bool(speed >> k & 1) for k in range(min(songs, 32))]
    print("  timing: " + ", ".join(f"liedje {k + 1}: {'CIA-timer (eigen tempo)' if c else '50 Hz (raster)'}"
                                   for k, c in enumerate(cia[:4])) + (" ..." if songs > 4 else ""))
    if flags:
        model = {1: "6581", 2: "8580", 3: "6581 en 8580"}.get(flags >> 4 & 3, "onbekend")
        video = {1: "PAL", 2: "NTSC", 3: "PAL en NTSC"}.get(flags >> 2 & 3, "onbekend")
        print(f"  gemaakt voor: {video}, SID {model}")
    if d[:4] == b"RSID":
        print("  LET OP: RSID — de muziek wil de hele C64 voor zich (eigen IRQ's); meestal niet bruikbaar in een intro")
    if play == 0:
        print("  LET OP: play $0000 — de muziek zet zelf een IRQ op; roep alleen init aan")
    warn = []
    if load < 0x0801 + 0x100:
        warn.append("begint in het BASIC-gebied: je eigen programma moet erachter of eromheen")
    if load <= 0xbfff and end >= 0xa000:
        warn.append("ligt (deels) onder de BASIC-ROM ($a000-$bfff): zet `lda #$36` / `sta $01` vóór init en laat "
                    "het zo (de kernal blijft aan)")
    if load <= 0xffff and end >= 0xd000 and load < 0xe000:
        warn.append("raakt $d000-$dfff (I/O): dit laadt niet goed met een gewone prg")
    for w in warn:
        print("  LET OP: " + w)
    print("  Kick Assembler: .var muziek = LoadSid(\"" + os.path.basename(a.sid) + "\")  …  "
          "*=muziek.location \"Muziek\"  .fill muziek.size, muziek.getData(i)")
    if any(cia):
        print("  Een CIA-timer-tune roep je aan vanuit de kernal-IRQ ($0314, die door de CIA-timer komt), niet vanuit "
              "een raster-IRQ: init zet zelf het tempo van die timer. Zie SKILL.md §13.")


# --------------------------------------------------------------------------------------------------- opnemen, luisteren
VICE = "/Applications/vice-arm64-gtk3-3.9/bin/x64sc"


def cmd_opnemen(a):
    if not os.path.exists(VICE):
        sys.exit("VICE staat niet op " + VICE)
    wav = os.path.abspath(a.o)
    if os.path.exists(wav):
        os.remove(wav)
    cycles = int((a.sec + a.start) * PAL_CLOCK)
    log = open(a.log, "w")
    # op echte snelheid: in warp slaat VICE geluid over. -limitcycles stopt VICE zelf.
    p = subprocess.Popen([VICE, "-default", "-sound", "-sounddev", "wav", "-soundarg", wav, "-soundrate", "44100",
                          "-sidenginemodel", "256", "+autostart-warp", "-autostartprgmode", "1", "-limitcycles", str(cycles), "-logfile", os.path.abspath(a.log),
                          "-autostart", os.path.abspath(a.prg)], stdout=log, stderr=log, start_new_session=True)
    try:
        p.wait(timeout=a.sec + a.start + 60)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, 9)
        sys.exit("FOUT: VICE stopte niet vanzelf; zie " + a.log)
    if not os.path.exists(wav) or os.path.getsize(wav) < 1000:
        sys.exit("FOUT: er is geen geluid opgenomen; zie " + a.log)
    print(f"[muziek] {a.o}: {os.path.getsize(wav) / 44100 / 2:.1f} seconden opgenomen (de eerste {a.start:g} s is het "
          f"opstarten van de C64)")


def cmd_luister(a):
    import wave
    import numpy as np
    w = wave.open(a.wav)
    rate, ch, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
    raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16 if width == 2 else np.int8).astype(float)
    if ch > 1:
        raw = raw.reshape(-1, ch).mean(axis=1)
    step = int(rate * a.stap)
    size = 1 << int(np.ceil(np.log2(rate * 0.1)))        # 0,1 s venster: genoeg voor de bas
    pad = size * 4                                        # aangevuld met nullen: de piek preciezer (D#2 en E2 schelen 4,6 Hz)
    freqs = np.fft.rfftfreq(pad, 1 / rate)
    win = np.hanning(size)
    starts = list(range(0, max(0, len(raw) - size), step))
    levels = np.array([np.sqrt((raw[k:k + size] ** 2).mean()) for k in starts])
    # luidheid tegen het luide deel van de opname, niet tegen één tik bij het aanzetten
    ref = max(1.0, float(np.percentile(levels, 95))) if len(levels) else 1.0
    print(f"{a.wav}: {len(raw) / rate:.1f} s. Per {a.stap:g} s: luidheid en de sterkste tonen (laag tot hoog).")
    for k, level in zip(starts, levels):
        loud = level / ref
        if loud < 0.03:
            print(f"{k / rate:6.2f}  stil")
            continue
        spec = np.abs(np.fft.rfft(raw[k:k + size] * win, pad))
        found = []
        for _ in range(a.tonen):
            i = int(spec[12:].argmax()) + 12
            if spec[i] < spec.max() * 0.15 or freqs[i] < 25:
                break
            # de top tussen twee punten in (parabool door de drie hoogste)
            y0, y1, y2 = spec[i - 1], spec[i], spec[min(i + 1, len(spec) - 1)]
            shift = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) if (y0 - 2 * y1 + y2) else 0
            f = freqs[i] + shift * (freqs[1] - freqs[0])
            note = int(round(69 + 12 * np.log2(f / 440)))
            # een boventoon van een gevonden toon telt niet als eigen toon
            if not any(abs(f / g - round(f / g)) < 0.03 for g in [x[1] for x in found]):
                found.append((note, f))
            spec[max(0, i - 16):i + 17] = 0
        print(f"{k / rate:6.2f}  {'#' * min(12, int(loud * 10)):<12} " + " ".join(name(n) for n, _ in sorted(found)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("info", help="de partijen in een MIDI-bestand")
    p.add_argument("midi")
    p = sub.add_parser("omzetten", help="MIDI -> muziek.asm (speler + noten)")
    p.add_argument("midi")
    p.add_argument("-o", default="muziek.asm")
    p.add_argument("--melodie", required=True, help="spoor of spoor:kanaal voor stem 1")
    p.add_argument("--bas", required=True, help="spoor of spoor:kanaal voor stem 2")
    p.add_argument("--drums", help="spoor(:10) met de drums voor stem 3")
    p.add_argument("--derde", help="een melodische partij voor stem 3, in plaats van drums")
    p.add_argument("--van", type=float, default=0, help="begin, in seconden")
    p.add_argument("--tot", type=float, help="einde, in seconden (een intro: 20-40)")
    p.add_argument("--rooster", type=int, help="beelden per zestiende noot: strak ritme (zie de tip na omzetten)")
    p.add_argument("--snelheid", type=float, default=1, help="sneller (>1) of langzamer (<1), zonder --rooster")
    p.add_argument("--transponeer", type=int, default=0, help="halve tonen omhoog (+) of omlaag (-)")
    p.add_argument("--klank1", help="klank van stem 1: " + ", ".join(KLANKEN) + " (standaard puls)")
    p.add_argument("--klank2", help="klank van stem 2 (standaard zaagkort)")
    p.add_argument("--klank3", help="klank van stem 3 als die geen drums speelt (standaard driehoek)")
    p.add_argument("--volume", type=int, default=15, choices=range(16), metavar="0-15")
    p.add_argument("--eenmaal", action="store_true", help="één keer spelen in plaats van herhalen")
    p = sub.add_parser("sid", help="een kant-en-klare .sid nakijken (HVSC)")
    p.add_argument("sid")
    p = sub.add_parser("opnemen", help="een prg in VICE laten spelen en het geluid als WAV bewaren")
    p.add_argument("prg")
    p.add_argument("-o", default="muziek.wav")
    p.add_argument("--sec", type=float, default=15, help="seconden muziek")
    p.add_argument("--start", type=float, default=4, help="seconden voor het opstarten (autostart)")
    p.add_argument("--log", default="vice.log")
    p = sub.add_parser("luister", help="welke tonen er in een WAV klinken")
    p.add_argument("wav")
    p.add_argument("--stap", type=float, default=0.25, help="seconden per regel")
    p.add_argument("--tonen", type=int, default=3, help="hoeveel tonen per regel")
    a = ap.parse_args()
    {"info": cmd_info, "omzetten": cmd_omzetten, "sid": cmd_sid, "opnemen": cmd_opnemen, "luister": cmd_luister}[a.cmd](a)


if __name__ == "__main__":
    main()
