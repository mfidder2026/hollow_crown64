#!/usr/bin/env python3
"""vicetest.py — speelt een invoerband af in VICE en controleert de spelstatus (projectprompt §7).

    python3 tools/vicetest.py tests/wacht.band            bouwt eerst (./build.sh --autotest), dan de test
    python3 tools/vicetest.py tests/*.band --geen-build   meerdere banden, zonder te bouwen
    opties: --geen-warp, --echte-drive (1541-emulatie, voor laadtijden), --houd-open

Een band (tests/<naam>.band) is tekst, één stap per regel ('#' is commentaar):
    wacht 50              50 beelden niets doen
    screenshot begin      maak build/test/<naam>_begin.png (de C64 wacht zolang)
    cursor 100,80         cursor naar x,y (beweegt met de gewone joystickcode, versnellen inbegrepen)
    vuur                  één beeld vuur
  Ruwe invoer, door dezelfde omzetcode als de echte joystick, toetsen en muis (src/invoer.asm):
    joystick neer,rechts 10    joystick 2: op neer links rechts vuur, n beelden
    toets crsr_neer,shift 8    toetsen: crsr_neer crsr_rechts spatie ctrl return shift rshift, n beelden
    muisknop links 2           1351 in poort 1: links / rechts, n beelden
    muis 10,-6                 de muis één beeld bewegen (pixels; -31..31; y negatief = omhoog)
  Lopen en tussendoor controleren:
    wacht_tot_stil             wacht tot Eldric stilstaat
    verwacht act_x.w = 120     controle op dit moment (zelfde vorm als in .verwacht); de C64 wacht zolang
    verwacht_tekst 18 "Bekijk fontein"   wat er op tekenrij 18 staat (schermgeheugen, zonder spaties achteraan)
  Scripts (namen uit build/gen/spel.json):
    start_script proef_vlaggen      start SCRIPT proef_vlaggen (tests/scripts/*.hcs)
    wacht_op_script                 wacht tot er geen script meer loopt
    verwacht_vlag munt_gepakt 1     een vlag (1 = gezet)
    verwacht_eigenaar munt eldric   eldric (inventaris), nergens, of een kamer
    verwacht_stand fontein 3

Na de band leest de test het geheugen en vergelijkt het met tests/<naam>.verwacht:
    st_versie = 1         byte op label st_versie
    st_magic+1 = $43      met een verschuiving
    beelden.w >= 300      .w = woord (lo, hi); vergelijkingen: = != < <= > >=
    scherm = ideaal       elke screenshot vergelijken met het scherm zoals het hoort, berekend uit het
                          geheugen (rij 0-1 en 18-24 tekst, 2-17 multicolor bitmap) mét de sprites.
                          Een verdwaalde pixel op een naad (rij 1/2, 17/18) is dan een fout.
Een test slaagt alleen als de status klopt; een screenshot alleen is geen bewijs.
"""
import argparse, json, os, re, signal, socket, subprocess, sys, time

# ---- instellingen: het pad naar VICE staat hier (en bovenin build.sh) ----------------------------
VICE_BIN = os.environ.get("VICE_BIN", "/Applications/vice-arm64-gtk3-3.10/bin")
# ---------------------------------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build", "autotest")
TESTUIT = os.path.join(ROOT, "build", "test")

# opcodes van de invoerband: gelijk houden met src/autotest.asm
OP_EINDE, OP_WACHT, OP_MARKEER, OP_CURSOR, OP_VUUR, OP_RUW, OP_MUIS, OP_WACHT_STIL, OP_START, OP_WACHT_VM = range(10)
JOY = {"op": 1, "neer": 2, "links": 4, "rechts": 8, "vuur": 16}
# toets -> (rij, bit) in de matrix; rijen 0, 1, 6 (zie src/invoer.asm)
TOETS = {"crsr_neer": (0, 0x80), "crsr_rechts": (0, 0x04), "return": (0, 0x02), "shift": (1, 0x80), "rshift": (6, 0x10),
         "spatie": (7, 0x10), "ctrl": (7, 0x04)}
MUISKNOP = {"links": 0x10, "rechts": 0x01}
BAND_WACHT, BAND_LOOPT, BAND_KLAAR, BAND_FOUT = 0, 1, 2, 0xFF
BAND_GROOTTE = 1024


class Fout(Exception):
    pass


# ---------------------------------------------------------------------------------------------------
# De band
# ---------------------------------------------------------------------------------------------------
def lees_band(pad):
    """Geeft (bytes, markeringen): markering k hoort bij namen[k-1], een screenshotnaam of een controle."""
    data, namen, starts = bytearray(), [], []
    pot = [0x24, 0x52]                           # potmeters van de muis: een willekeurige beginstand

    def ruw(arg, tabel):
        woorden = arg.split()
        if len(woorden) != 2:
            raise ValueError
        n = int(woorden[1])
        if not 0 < n < 256:
            raise ValueError
        return [tabel[w] for w in woorden[0].split(",")], n

    for nr, regel in enumerate(open(pad, encoding="utf-8"), 1):
        regel = regel.split("#", 1)[0].strip()
        if not regel:
            continue
        woorden = regel.split(None, 1)
        cmd, arg = woorden[0].lower(), (woorden[1].strip() if len(woorden) > 1 else "")
        try:
            if cmd == "wacht":
                n = int(arg)
                if not 0 < n < 65536:
                    raise ValueError
                data += bytes([OP_WACHT, n & 0xFF, n >> 8])
            elif cmd == "screenshot":
                if not re.fullmatch(r"[A-Za-z0-9_-]+", arg):
                    raise ValueError
                namen.append(arg)
                if len(namen) > 255:
                    raise Fout("%s:%d: te veel screenshots" % (pad, nr))
                data += bytes([OP_MARKEER, len(namen)])
            elif cmd == "cursor":
                x, y = (int(v) for v in arg.split(","))
                data += bytes([OP_CURSOR, x & 0xFF, x >> 8, y])
            elif cmd == "vuur" and not arg:
                data += bytes([OP_VUUR])
            elif cmd == "joystick":
                bits, n = ruw(arg, JOY)
                data += bytes([OP_RUW, sum(bits), 0, 0, 0, 0, 0, n])
            elif cmd == "toets":
                toetsen, n = ruw(arg, TOETS)
                rij = {0: 0, 1: 0, 6: 0, 7: 0}
                for r, b in toetsen:
                    rij[r] |= b
                data += bytes([OP_RUW, 0, rij[0], rij[1], rij[6], rij[7], 0, n])
            elif cmd == "muisknop":
                knoppen, n = ruw(arg, MUISKNOP)
                data += bytes([OP_RUW, 0, 0, 0, 0, 0, sum(knoppen), n])
            elif cmd == "start_script" and re.fullmatch(r"\w+", arg):
                data += bytes([OP_START, 0, 0])          # het adres vult draai() in (scr_<naam> uit hollowcrown.vs)
                starts.append((len(data) - 2, arg))
            elif cmd == "wacht_op_script" and not arg:
                data += bytes([OP_WACHT_VM])
            elif cmd in ("verwacht_vlag", "verwacht_eigenaar", "verwacht_stand"):
                d = arg.split()
                if len(d) != 2:
                    raise ValueError
                namen.append((cmd.upper(), d[0], d[1]))
                data += bytes([OP_MARKEER, len(namen)])
            elif cmd == "wacht_tot_stil" and not arg:
                data += bytes([OP_WACHT_STIL])
            elif cmd == "verwacht_tekst":
                m = re.fullmatch(r'(\d+)\s+"(.*)"', arg)
                if not m or not 0 <= int(m.group(1)) < 25:
                    raise ValueError
                namen.append(("TEKST", int(m.group(1)), m.group(2)))
                if len(namen) > 255:
                    raise Fout("%s:%d: te veel markeringen" % (pad, nr))
                data += bytes([OP_MARKEER, len(namen)])
            elif cmd == "verwacht":
                r = verwacht_regel(arg)
                if not r:
                    raise ValueError
                namen.append(r)
                if len(namen) > 255:
                    raise Fout("%s:%d: te veel markeringen" % (pad, nr))
                data += bytes([OP_MARKEER, len(namen)])
            elif cmd == "muis":
                dx, dy = (int(v) for v in arg.split(","))
                if not (-31 <= dx <= 31 and -31 <= dy <= 31):
                    raise ValueError
                pot[0] = (pot[0] + 2 * dx) & 0x7E
                pot[1] = (pot[1] - 2 * dy) & 0x7E      # de muis telt omhoog, het scherm omlaag
                data += bytes([OP_MUIS, pot[0], pot[1]])
            else:
                raise ValueError
        except (ValueError, KeyError):
            raise Fout("%s:%d: onbekende of foute stap: %s" % (pad, nr, regel))
    data.append(OP_EINDE)
    if len(data) > BAND_GROOTTE:
        raise Fout("%s: band is %d bytes, de buffer %d" % (pad, len(data), BAND_GROOTTE))
    return data, namen, starts


VERWACHT_RE = r"([A-Za-z_]\w*)(?:\+(\d+))?(\.w)?\s*(=|!=|<=|>=|<|>)\s*(\$[0-9A-Fa-f]+|\d+)"


def verwacht_regel(regel):
    m = re.fullmatch(VERWACHT_RE, regel)
    if not m:
        return None
    label, plus, woord, op, waarde = m.groups()
    waarde = int(waarde[1:], 16) if waarde.startswith("$") else int(waarde)
    return (regel, label, int(plus or 0), bool(woord), op, waarde)


def lees_verwacht(pad):
    regels = []
    for nr, regel in enumerate(open(pad, encoding="utf-8"), 1):
        regel = regel.split("#", 1)[0].strip()
        if not regel:
            continue
        if re.fullmatch(r"scherm\s*=\s*ideaal", regel):
            regels.append((regel, "scherm", 0, False, "ideaal", 0))
            continue
        r = verwacht_regel(regel)
        if not r:
            raise Fout("%s:%d: kan dit niet lezen: %s" % (pad, nr, regel))
        regels.append(r)
    return regels


def lees_symbolen(pad):
    """VICE-symboolbestand van Kick Assembler: 'al C:9d2 .beelden'."""
    sym = {}
    for regel in open(pad):
        m = re.match(r"al C:([0-9a-fA-F]+) \.(\S+)", regel)
        if m:
            sym[m.group(2)] = int(m.group(1), 16)
    return sym


# ---------------------------------------------------------------------------------------------------
# VICE en de remote monitor
# ---------------------------------------------------------------------------------------------------
PROMPT = re.compile(rb"\(C:\$[0-9a-f]{4}\) $")


class Vice:
    def __init__(self, d64, warp=True, echte_drive=False, zichtbaar_houden=False):
        self.houd_open = zichtbaar_houden
        s = socket.socket()
        s.bind(("127.0.0.1", 0))                 # een vrije poort, zodat testen naast elkaar kunnen
        self.poort = s.getsockname()[1]
        s.close()
        args = [os.path.join(VICE_BIN, "x64sc"), "-pal", "-default",
                "-remotemonitor", "-remotemonitoraddress", "ip4://127.0.0.1:%d" % self.poort,
                "-sounddev", "dummy", "+confirmonexit",
                "-drive8truedrive" if echte_drive else "+drive8truedrive"]
        if warp:
            args.append("-warp")
        args += ["-autostart", d64]
        # Eigen procesgroep: bin/x64sc start op macOS een kindproces. Bij het stoppen sluiten we alleen
        # deze groep af, nooit andere VICE's.
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     start_new_session=True)
        self.sock = None
        self.loopt = True                        # draait de emulatie (niet in de monitor)?
        eind = time.time() + 30
        while time.time() < eind:
            if self.proc.poll() is not None:
                raise Fout("VICE stopte meteen (code %s)" % self.proc.returncode)
            try:
                self.sock = socket.create_connection(("127.0.0.1", self.poort), timeout=1)
                break
            except OSError:
                time.sleep(0.1)
        if not self.sock:
            raise Fout("geen verbinding met de remote monitor van VICE")
        self.sock.settimeout(10)

    def cmd(self, tekst):
        """Stuurt een monitoropdracht en geeft de uitvoer terug. Komt de opdracht binnen terwijl de C64
        loopt, dan stopt VICE eerst (een prompt extra) en blijft daarna in de monitor tot 'x'."""
        self.sock.sendall(tekst.encode() + b"\n")
        nodig = 2 if self.loopt else 1
        self.loopt = False
        buf = b""
        while True:
            try:
                d = self.sock.recv(65536)
            except socket.timeout:
                raise Fout("monitor antwoordt niet op: %s" % tekst)
            if not d:
                raise Fout("verbinding met VICE verbroken")
            buf += d
            if PROMPT.search(buf) and len(re.findall(rb"\(C:\$[0-9a-f]{4}\) ", buf)) >= nodig:
                break
        return re.sub(r"\(C:\$[0-9a-f]{4}\) ", "", buf.decode(errors="replace"))

    def verder(self):
        if not self.loopt:
            self.sock.sendall(b"x\n")
            self.loopt = True

    def lees(self, adres, n=1):
        uit = self.cmd("m %04x %04x" % (adres, adres + n - 1))
        data = []
        for regel in uit.splitlines():
            m = re.match(r"\s*>C:([0-9a-f]{4})\s+(.*)", regel)
            if not m:
                continue
            woorden = m.group(2).split()
            rest = min(16, n - len(data))
            data += [int(w, 16) for w in woorden[:rest]]
        if len(data) != n:
            raise Fout("kon $%04x niet lezen: %r" % (adres, uit))
        return data

    def schrijf(self, adres, data):
        for i in range(0, len(data), 32):
            stuk = data[i:i + 32]
            self.cmd("> %04x %s" % (adres + i, " ".join("%02x" % b for b in stuk)))

    def screenshot(self, pad):
        self.cmd('screenshot "%s" 2' % pad)      # 2 = PNG; VICE wil een absoluut pad

    def stop(self):
        if self.houd_open and self.proc.poll() is None:
            self.verder()
            return
        try:
            self.sock.sendall(b"quit\n")
        except OSError:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        if self.proc.poll() is None:
            try:
                os.killpg(self.proc.pid, signal.SIGTERM)
                self.proc.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                os.killpg(self.proc.pid, signal.SIGKILL)


# ---------------------------------------------------------------------------------------------------
# Het scherm zoals het hoort, uit het geheugen (§4, §6.3)
# ---------------------------------------------------------------------------------------------------
# Kleuren zoals VICE 3.10 ze in een screenshot zet (dezelfde lijst als tools/c64beeld.py)
VICE_RGB = [(0, 0, 0), (255, 255, 255), (175, 60, 88), (126, 243, 214), (170, 64, 245), (98, 213, 50),
            (44, 61, 236), (255, 255, 70), (183, 99, 30), (119, 83, 0), (238, 123, 149), (98, 98, 98),
            (148, 148, 148), (183, 255, 134), (115, 133, 255), (205, 205, 205)]
RIJEN_TEKST = set(range(0, 2)) | set(range(18, 25))
RAND_X, RAND_Y = 32, 35          # waar schermpixel (0,0) in een VICE-screenshot staat (gecontroleerd)


def ideaal_scherm(vice):
    """320x200 C64-kleurnummers zoals het scherm hoort te zijn, mét sprites (prioriteit zoals de VIC-II:
    sprite 0 bovenop; met $d01b achter bitmapcode %10/%11 en achter tekenpixels)."""
    scherm = vice.lees(0xC000, 1024)
    kleur = [b & 15 for b in vice.lees(0xD800, 1000)]
    vic = vice.lees(0xD000, 0x2F)
    vice.cmd("bank ram")                         # bitmap en lettertype liggen onder de Kernal-ROM
    try:
        bitmap = vice.lees(0xE000, 0x1800)
        font = vice.lees(0xF800, 0x800)
    finally:
        vice.cmd("bank cpu")
    d018 = vic[0x18] & 0xFE                     # bit 0 bestaat niet en leest als 1
    if d018 != 0x0E:
        raise Fout("$d018 is $%02x, verwacht $0E" % d018)
    achter = vic[0x21] & 15
    pix = [[achter] * 320 for _ in range(200)]
    voor = [[False] * 320 for _ in range(200)]   # "voorgrond" voor sprites met $d01b
    for r in range(25):
        for c in range(40):
            i = r * 40 + c
            for y in range(8):
                rij, vr = pix[r * 8 + y], voor[r * 8 + y]
                if r in RIJEN_TEKST:                 # hires tekst
                    b = font[scherm[i] * 8 + y]
                    for x in range(8):
                        if b & (0x80 >> x):
                            rij[c * 8 + x] = kleur[i]
                            vr[c * 8 + x] = True
                else:                                # multicolor bitmap
                    b = bitmap[i * 8 + y]
                    kl = [achter, scherm[i] >> 4, scherm[i] & 15, kleur[i]]
                    for x in range(4):
                        code = (b >> (6 - 2 * x)) & 3
                        rij[c * 8 + 2 * x] = rij[c * 8 + 2 * x + 1] = kl[code]
                        vr[c * 8 + 2 * x] = vr[c * 8 + 2 * x + 1] = code >= 2
    if vic[0x17] or vic[0x1D]:
        raise Fout("vergrote sprites ($d017/$d01d) tekent de test nog niet")
    for n in range(7, -1, -1):                  # hoog nummer eerst: een lager nummer komt erbovenop
        if not vic[0x15] & (1 << n):
            continue
        data = vice.lees(0xC000 + scherm[0x3F8 + n] * 64, 63)
        sx = vic[2 * n] + (256 if vic[0x10] & (1 << n) else 0) - 24
        sy = vic[2 * n + 1] - 50
        mc = vic[0x1C] & (1 << n)
        prio = vic[0x1B] & (1 << n)
        eigen = vic[0x27 + n] & 15
        for r in range(21):
            bits = data[r * 3] << 16 | data[r * 3 + 1] << 8 | data[r * 3 + 2]
            y = sy + r
            if not 0 <= y < 200:
                continue
            for x in range(24):
                if mc:
                    code = bits >> (22 - (x & ~1)) & 3
                    k = (None, vic[0x25] & 15, eigen, vic[0x26] & 15)[code]
                else:
                    k = eigen if bits >> (23 - x) & 1 else None
                px = sx + x
                if k is None or not 0 <= px < 320 or (prio and voor[y][px]):
                    continue
                pix[y][px] = k
    return pix


def scherm_vergelijken(vice, png_pad):
    from PIL import Image
    pix = ideaal_scherm(vice)
    img = Image.open(png_pad).convert("RGB")
    W, H = img.size
    data = img.load()
    cache = {}

    def nummer(rgb):
        if rgb not in cache:
            cache[rgb] = min(range(16), key=lambda k: sum((a - b) ** 2 for a, b in zip(rgb, VICE_RGB[k])))
        return cache[rgb]
    fout_rijen = {}
    for y in range(200):
        for x in range(320):
            if nummer(data[RAND_X + x, RAND_Y + y]) != pix[y][x]:
                fout_rijen[y] = fout_rijen.get(y, 0) + 1
    if not fout_rijen:
        return True, "klopt pixel voor pixel (met sprites)"
    # een verschilplaatje: rood = anders dan het hoort
    uit = img.copy()
    for y in fout_rijen:
        for x in range(320):
            if nummer(data[RAND_X + x, RAND_Y + y]) != pix[y][x]:
                uit.putpixel((RAND_X + x, RAND_Y + y), (255, 0, 0))
    vpad = png_pad[:-4] + "_verschil.png"
    uit.save(vpad)
    rijen = sorted(fout_rijen)
    naden = [y for y in rijen if y in (14, 15, 16, 17, 142, 143, 144, 145)]   # rij 1/2 en 17/18
    return False, "%d pixels anders op %d pixelrijen (eerste %s%s); zie %s" % (
        sum(fout_rijen.values()), len(rijen), rijen[:8], ", op de naden: %s" % naden if naden else "",
        os.path.relpath(vpad, ROOT))


# ---------------------------------------------------------------------------------------------------
# Een test
# ---------------------------------------------------------------------------------------------------
def vergelijk(op, a, b):
    return {"=": a == b, "!=": a != b, "<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]


def scherm_tekst(vice, rij):
    """Tekenrij <rij> uit het schermgeheugen, terugvertaald met het eigen lettertype (tools/lettertype.py)."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import lettertype
    terug = {lettertype.code_van(t): t for t in lettertype.TEKENS}
    return "".join(terug.get(c, "?") for c in vice.lees(0xC000 + rij * 40, 40)).rstrip()


def controleer(vice, sym, regel, spel=None):
    if regel[0] == "VERWACHT_VLAG":
        _, naam, waarde = regel
        nr = spel["vlaggen"][naam]
        echt = vice.lees(sym["st_vlaggen"] + nr // 8)[0] >> (nr % 8) & 1
        return echt == int(waarde), "vlag %s = %s%s" % (naam, waarde, "" if echt == int(waarde) else "  (is %d)" % echt)
    if regel[0] == "VERWACHT_STAND":
        _, naam, waarde = regel
        echt = vice.lees(sym["st_stand"] + spel["voorwerpen"][naam])[0]
        return echt == int(waarde), "stand %s = %s%s" % (naam, waarde, "" if echt == int(waarde) else "  (is %d)" % echt)
    if regel[0] == "VERWACHT_EIGENAAR":
        _, naam, waar = regel
        terug = {v: k for k, v in spel["kamers"].items()}
        terug.update({v: k for k, v in spel["eigenaar"].items()})
        echt = vice.lees(sym["st_eigenaar"] + spel["voorwerpen"][naam])[0]
        echt_n = terug.get(echt, str(echt))
        return echt_n == waar, "%s is bij/in %s%s" % (naam, waar, "" if echt_n == waar else "  (is %s)" % echt_n)
    if regel[0] == "TEKST":
        _, rij, verwacht = regel
        echt = scherm_tekst(vice, rij)
        return echt == verwacht, 'rij %d = "%s"%s' % (rij, verwacht, "" if echt == verwacht else '  (is "%s")' % echt)
    tekst, label, plus, woord, op, waarde = regel
    b = vice.lees(sym[label] + plus, 2 if woord else 1)
    echt = b[0] | (b[1] << 8) if woord else b[0]
    return vergelijk(op, echt, waarde), "%-28s (is %d / $%x)" % (tekst, echt, echt)


def draai(bandpad, args):
    naam = os.path.splitext(os.path.basename(bandpad))[0]
    band, shots, starts = lees_band(bandpad)
    verwachtpad = os.path.splitext(bandpad)[0] + ".verwacht"
    if not os.path.exists(verwachtpad):
        raise Fout("%s ontbreekt: zonder verwachte status is er geen test" % verwachtpad)
    verwacht = lees_verwacht(verwachtpad)
    sym = lees_symbolen(os.path.join(BUILD, "hollowcrown.vs"))
    for nodig in ("band", "band_status", "band_markering", "band_fout", "st_magic"):
        if nodig not in sym:
            raise Fout("label %s niet in hollowcrown.vs: is dit een AUTOTEST-build?" % nodig)
    scherm_ideaal = any(r[1] == "scherm" for r in verwacht)
    verwacht = [r for r in verwacht if r[1] != "scherm"]
    for pos, naam_s in starts:                       # START: het adres van het script
        if "scr_" + naam_s not in sym:
            raise Fout("%s: onbekend script %s (SCRIPT %s: in tests/scripts/*.hcs?)" % (bandpad, naam_s, naam_s))
        adres = sym["scr_" + naam_s]
        band[pos], band[pos + 1] = adres & 255, adres >> 8
    band = bytes(band)
    spel = json.load(open(os.path.join(ROOT, "build", "gen", "spel.json")))
    for m in shots:
        if isinstance(m, tuple) and m[0] in ("VERWACHT_VLAG", "VERWACHT_EIGENAAR", "VERWACHT_STAND"):
            soort = {"VERWACHT_VLAG": "vlaggen"}.get(m[0], "voorwerpen")
            if m[1] not in spel[soort]:
                raise Fout("%s: onbekende %s %s" % (bandpad, "vlag" if soort == "vlaggen" else "voorwerp", m[1]))
    for _, label, *_ in verwacht + [m for m in shots if isinstance(m, tuple) and m[0] not in
                                     ("TEKST", "VERWACHT_VLAG", "VERWACHT_EIGENAAR", "VERWACHT_STAND")]:
        if label not in sym:
            raise Fout("%s: onbekend label %s" % (verwachtpad, label))
    controles = [m for m in shots if isinstance(m, tuple)]
    shots_n = len(shots) - len(controles)
    os.makedirs(TESTUIT, exist_ok=True)

    print("[test] %s: %d stappen-bytes, %d screenshots, %d tussencontroles" % (naam, len(band), shots_n, len(controles)))
    t0 = time.time()
    vice = Vice(os.path.join(BUILD, "hollowcrown.d64"), warp=not args.geen_warp,
                echte_drive=args.echte_drive, zichtbaar_houden=args.houd_open)
    try:
        # 1. wachten tot het spel draait: magic "HC" staat er en de band wacht op ons
        eind = time.time() + args.starttijd
        while True:
            if vice.lees(sym["st_magic"], 2) == [0x48, 0x43] and vice.lees(sym["band_status"])[0] == BAND_WACHT:
                break
            vice.verder()
            if time.time() > eind:
                raise Fout("het spel startte niet binnen %d s" % args.starttijd)
            time.sleep(0.25)
        print("[test]   spel draait na %.1f s" % (time.time() - t0))

        # 2. band laden en starten
        vice.schrijf(sym["band"], band)
        if bytes(vice.lees(sym["band"], len(band))) != band:
            raise Fout("de band staat niet goed in het geheugen")
        vice.schrijf(sym["band_status"], [BAND_LOOPT])
        vice.verder()

        # 3. de band volgen: markeringen afhandelen tot hij klaar is
        schermfouten = 0
        eind = time.time() + args.max_tijd
        while True:
            time.sleep(0.05)
            status, markering = vice.lees(sym["band_status"])[0], vice.lees(sym["band_markering"])[0]
            if markering:
                if markering > len(shots):
                    raise Fout("onbekende markering %d" % markering)
                m = shots[markering - 1]
                if isinstance(m, tuple):              # tussencontrole
                    ok, tekst = controleer(vice, sym, m, spel)
                    schermfouten += 0 if ok else 1
                    print("[test]   %-4s %s" % ("ok" if ok else "FOUT", tekst))
                else:
                    pad = os.path.join(TESTUIT, "%s_%s.png" % (naam, m))
                    vice.screenshot(pad)
                    print("[test]   screenshot %s" % os.path.relpath(pad, ROOT))
                    if scherm_ideaal:
                        ok, uitleg = scherm_vergelijken(vice, pad)
                        schermfouten += 0 if ok else 1
                        print("[test]   %-4s scherm: %s" % ("ok" if ok else "FOUT", uitleg))
                vice.schrijf(sym["band_markering"], [0])
            if status == BAND_KLAAR:
                break
            if status == BAND_FOUT:
                raise Fout("het spel kent bandopcode $%02x niet (nog niet gebouwd?)" % vice.lees(sym["band_fout"])[0])
            vice.verder()
            if time.time() > eind:
                raise Fout("band niet klaar binnen %d s" % args.max_tijd)

        # 4. de status vergelijken (de C64 staat stil in de monitor)
        goed = schermfouten == 0
        if scherm_ideaal and not shots_n:
            print("[test]   FOUT scherm = ideaal, maar de band maakt geen screenshot")
            goed = False
        for r in verwacht:
            ok, tekst = controleer(vice, sym, r)
            goed &= ok
            print("[test]   %-4s %s" % ("ok" if ok else "FOUT", tekst))
        print("[test] %s: %s in %.1f s" % (naam, "GESLAAGD" if goed else "MISLUKT", time.time() - t0))
        return goed
    finally:
        vice.stop()


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("banden", nargs="+")
    p.add_argument("--geen-build", action="store_true", help="niet eerst ./build.sh --autotest")
    p.add_argument("--geen-warp", action="store_true")
    p.add_argument("--echte-drive", action="store_true", help="echte 1541-emulatie (traag laden)")
    p.add_argument("--houd-open", action="store_true", help="VICE niet afsluiten na de test")
    p.add_argument("--starttijd", type=int, default=90, help="seconden om te laden en te starten")
    p.add_argument("--max-tijd", type=int, default=120, help="seconden voor de hele band")
    args = p.parse_args()
    if not args.geen_build:
        if subprocess.call([os.path.join(ROOT, "build.sh"), "--autotest"]) != 0:
            print("[test] build mislukt")
            return 1
    fouten = 0
    for band in args.banden:
        try:
            fouten += 0 if draai(band, args) else 1
        except Fout as e:
            print("[test] %s: FOUT: %s" % (band, e))
            fouten += 1
    print("[test] %d van %d geslaagd" % (len(args.banden) - fouten, len(args.banden)))
    return 1 if fouten else 0


if __name__ == "__main__":
    sys.exit(main())
