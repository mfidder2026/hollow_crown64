#!/usr/bin/env python3
"""vicetest.py — speelt een invoerband af in VICE en controleert de spelstatus (projectprompt §7).

    python3 tools/vicetest.py tests/wacht.band            bouwt eerst (./build.sh --autotest), dan de test
    python3 tools/vicetest.py tests/*.band --geen-build   meerdere banden, zonder te bouwen
    opties: --kijk (meekijken: venster, normale snelheid, geluid, echte drive), --geen-warp, --echte-drive (1541-emulatie, voor laadtijden), --houd-open

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
import argparse, json, os, re, shutil, signal, socket, subprocess, sys, time

# ---- instellingen: het pad naar VICE staat hier (en bovenin build.sh) ----------------------------
VICE_BIN = os.environ.get("VICE_BIN", "/Applications/vice-arm64-gtk3-3.10/bin")
# ---------------------------------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build", "autotest")
TESTUIT = os.path.join(ROOT, "build", "test")

# opcodes van de invoerband: gelijk houden met src/autotest.asm
OP_EINDE, OP_WACHT, OP_MARKEER, OP_CURSOR, OP_VUUR, OP_RUW, OP_MUIS, OP_WACHT_STIL, OP_START, OP_WACHT_VM, \
    OP_INTRO = range(11)
JOY = {"op": 1, "neer": 2, "links": 4, "rechts": 8, "vuur": 16}
# toets -> (rij, bit) in de matrix; rijen 0, 1, 6 (zie src/invoer.asm)
TOETS = {"crsr_neer": (0, 0x80), "crsr_rechts": (0, 0x04), "return": (0, 0x02), "shift": (1, 0x80), "rshift": (6, 0x10),
         "spatie": (7, 0x10), "ctrl": (7, 0x04),
         "f1": (0, 0x10), "f5": (0, 0x40), "f7": (0, 0x08)}
MUISKNOP = {"links": 0x10, "rechts": 0x01}
BAND_WACHT, BAND_LOOPT, BAND_KLAAR, BAND_FOUT = 0, 1, 2, 0xFF
BAND_GROOTTE = 1024          # de ring in src/autotest.asm; een band mag langer zijn: hij wordt bijgevuld
BAND_SPIEGEL = 16


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

    def regels(p, diepte=0):
        """de regels van de band; 'voeg_in andere.band' zet daar de stappen van een andere band (zonder .verwacht)"""
        for nr, r in enumerate(open(p, encoding="utf-8"), 1):
            kaal = r.split("#", 1)[0].strip()
            if kaal.startswith("voeg_in "):
                ander = os.path.join(os.path.dirname(p), kaal.split(None, 1)[1])
                if diepte > 3 or not os.path.exists(ander):
                    raise Fout("%s:%d: voeg_in: %s" % (p, nr, ander))
                yield from regels(ander, diepte + 1)
            else:
                yield nr, r

    for nr, regel in regels(pad):
        regel = regel.split("#", 1)[0].strip()
        if not regel:
            continue
        woorden = regel.split(None, 1)
        cmd, arg = woorden[0].lower(), (woorden[1].strip() if len(woorden) > 1 else "")
        if cmd == "echte_drive" and not arg:              # (voor draai(): deze band met de 1541-emulatie)
            continue
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
                data += bytes([OP_MARKEER, (len(namen) - 1) % 255 + 1])
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
            elif cmd == "intro" and not arg:
                if data:
                    raise Fout("%s:%d: intro moet de eerste stap zijn" % (pad, nr))
                data += bytes([OP_INTRO])
            elif cmd == "verwacht_slot":
                d = arg.split()                          # slot figuur   (de figuur bij naam: tools/scriptc.py-volgorde)
                if len(d) != 2 or d[0] not in ("0", "1"):
                    raise ValueError
                namen.append(("SLOT", int(d[0]), d[1]))
                data += bytes([OP_MARKEER, (len(namen) - 1) % 255 + 1])
            elif cmd == "verwacht_logo" and not arg:
                namen.append(("LOGO", None))
                data += bytes([OP_MARKEER, (len(namen) - 1) % 255 + 1])
            elif cmd == "verwacht_muziek" and not arg:
                namen.append(("MUZIEK", None))
                data += bytes([OP_MARKEER, (len(namen) - 1) % 255 + 1])
            elif cmd == "wacht_op_script" and not arg:
                data += bytes([OP_WACHT_VM])
            elif cmd in ("onthoud_kleur", "verwacht_kleur_volgend"):
                d = arg.split()                          # naam rij,kol [kleur,kleur,...]
                if (cmd == "onthoud_kleur" and len(d) != 2) or (cmd != "onthoud_kleur" and len(d) != 3):
                    raise ValueError
                rij, kol = (int(v) for v in d[1].split(","))
                namen.append((cmd.upper(), d[0], rij, kol, d[2].split(",") if len(d) == 3 else None))
                data += bytes([OP_MARKEER, (len(namen) - 1) % 255 + 1])
            elif cmd == "verwacht_kamer" and re.fullmatch(r"\w+", arg):
                namen.append(("VERWACHT_KAMER", arg))
                data += bytes([OP_MARKEER, (len(namen) - 1) % 255 + 1])
            elif cmd in ("verwacht_vlag", "verwacht_eigenaar", "verwacht_stand"):
                d = arg.split()
                if len(d) != 2:
                    raise ValueError
                namen.append((cmd.upper(), d[0], d[1]))
                data += bytes([OP_MARKEER, (len(namen) - 1) % 255 + 1])
            elif cmd == "wacht_tot_stil" and not arg:
                data += bytes([OP_WACHT_STIL])
            elif cmd == "verwacht_tekst":
                m = re.fullmatch(r'(\d+)\s+"(.*)"', arg)
                if not m or not 0 <= int(m.group(1)) < 25:
                    raise ValueError
                namen.append(("TEKST", int(m.group(1)), m.group(2)))
                data += bytes([OP_MARKEER, (len(namen) - 1) % 255 + 1])
            elif cmd == "verwacht":
                r = verwacht_regel(arg)
                if not r:
                    raise ValueError
                namen.append(r)
                data += bytes([OP_MARKEER, (len(namen) - 1) % 255 + 1])
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
    return data, namen, starts


VERWACHT_RE = r"([A-Za-z_]\w*)(?:\+(\d+))?(\.w)?\s*(=|!=|<=|>=|<|>)\s*(\$[0-9A-Fa-f]+|\d+)"


def figuur_nummers(regel):
    """'npc_py+@mira_mee' -> 'npc_py+9': het nummer van een figuur bij naam (build/gen/spel.json), zodat een test niet
    breekt als er figuren bijkomen"""
    def nummer(m):
        figuren = json.load(open(os.path.join(ROOT, "build", "gen", "spel.json")))["figuren"]
        if m.group(1) not in figuren:
            raise Fout("onbekende figuur @%s" % m.group(1))
        return str(figuren.index(m.group(1)))
    return re.sub(r"@(\w+)", nummer, regel)


def verwacht_regel(regel):
    regel = figuur_nummers(regel)
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
        if re.fullmatch(r"basic\s*=\s*klaar", regel):
            regels.append((regel, "basic", 0, False, "basic", 0))
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
PROMPT = re.compile(rb"\((?:C|8):\$[0-9a-f]{4}\) $")


class Vice:
    def __init__(self, d64, warp=True, echte_drive=False, zichtbaar_houden=False, geluid=False, snelheid=100,
                 drive=1541):
        self.houd_open = zichtbaar_houden
        s = socket.socket()
        s.bind(("127.0.0.1", 0))                 # een vrije poort, zodat testen naast elkaar kunnen
        self.poort = s.getsockname()[1]
        s.close()
        args = [os.path.join(VICE_BIN, "x64sc"), "-pal", "-default",
                "-remotemonitor", "-remotemonitoraddress", "ip4://127.0.0.1:%d" % self.poort,
                "+confirmonexit",
                "-drive8truedrive" if echte_drive else "+drive8truedrive", "-drive8type", str(drive)]
        if not echte_drive:
            args.append("-busdevice8")           # virtueel apparaat 8: het spel laadt zelf kamers (Kernal LOAD)
        if not geluid:
            args += ["-sounddev", "dummy"]
        if warp:
            args.append("-warp")
        elif snelheid != 100:
            args += ["-speed", str(snelheid)]    # procent van de echte C64 (--snelheid)
        if not zichtbaar_houden:
            args.append("-console")              # geen venster: de test pakt de focus niet af (macOS)
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
            if PROMPT.search(buf) and len(re.findall(rb"\((?:C|8):\$[0-9a-f]{4}\) ", buf)) >= nodig:
                break
        return re.sub(r"\((?:C|8):\$[0-9a-f]{4}\) ", "", buf.decode(errors="replace"))

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
    for n in range(7, -1, -1):                  # hoog nummer eerst: een lager nummer komt erbovenop
        if not vic[0x15] & (1 << n):
            continue
        data = vice.lees(0xC000 + scherm[0x3F8 + n] * 64, 63)
        sx = vic[2 * n] + (256 if vic[0x10] & (1 << n) else 0) - 24
        sy = vic[2 * n + 1] - 50
        mc = vic[0x1C] & (1 << n)
        prio = vic[0x1B] & (1 << n)
        eigen = vic[0x27 + n] & 15
        hoog = 2 if vic[0x17] & (1 << n) else 1  # vergroot ($d017 hoogte, $d01d breedte): een reus (src/npc.asm)
        breed = 2 if vic[0x1D] & (1 << n) else 1
        for r in range(21 * hoog):
            rr = r // hoog
            bits = data[rr * 3] << 16 | data[rr * 3 + 1] << 8 | data[rr * 3 + 2]
            y = sy + r
            if not 0 <= y < 200:
                continue
            for xx in range(24 * breed):
                x = xx // breed
                if mc:
                    code = bits >> (22 - (x & ~1)) & 3
                    k = (None, vic[0x25] & 15, eigen, vic[0x26] & 15)[code]
                else:
                    k = eigen if bits >> (23 - x) & 1 else None
                px = sx + xx
                if k is None or not 0 <= px < 320 or (prio and voor[y][px]):
                    continue
                pix[y][px] = k
    return pix


def kamerbuffer_klopt(vice, sym, spel):
    """De kamerbuffer ($A000) moet byte voor byte het kamerbestand van de huidige kamer zijn: anders laat het
    scherm wel 'iets' zien dat bij het geheugen past, maar niet de kamer (zo bleef een mislukt laden onopgemerkt)."""
    if "st_kamer" not in sym or "laad_teller" not in sym:
        return True, "(geen kamers van de diskette)"
    terug = {v: k for k, v in spel["kamers"].items()}
    naam = terug.get(vice.lees(sym["st_kamer"])[0], "?")
    pad = os.path.join(ROOT, "build", "gen", "kamer_%s.prg" % naam)
    if not os.path.exists(pad):
        return False, "geen bestand voor kamer %s" % naam
    data = open(pad, "rb").read()[2:]
    vice.cmd("bank ram")
    try:
        echt = vice.lees(0xA000, len(data))
    finally:
        vice.cmd("bank cpu")
    if bytes(echt) != data:
        eerste = next(i for i in range(len(data)) if echt[i] != data[i])
        return False, "kamerbuffer is niet %s (eerste verschil op +%d)" % (os.path.basename(pad), eerste)
    return True, "kamerbuffer = %s (%d bytes)" % (os.path.basename(pad), len(data))


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
def muziek_klopt(vice, sym):
    """Controle zonder oren (§9): wat de speler naar de SID schreef (muz_flo/fhi/ctrl, ook in de SID zelf te
    schrijven maar niet terug te lezen) moet kloppen met de noten van tools/thema.py op dit beeld (muz_beelden).
    Melodie en bas: precies die noot, gate uit in het laatste beeld en in rusten. Arpeggio: de juiste toon van het
    akkoord (elke 2 beelden de volgende)."""
    alles = json.load(open(os.path.join(ROOT, "build", "gen", "muziek.json")))
    if not vice.lees(sym["muz_aan"])[0]:
        return False, "muziek: de speler loopt niet (muz_aan = 0)"
    m = alles["stukken"][vice.lees(sym["muz_lied"])[0]]
    m["akkoorden"], m["freq"] = alles["akkoorden"], alles["freq"]
    b = vice.lees(sym["muz_beelden"], 2)
    f = b[0] | b[1] << 8
    t = (f - 1) % m["lengte"]
    flo, fhi, ctrl = vice.lees(sym["muz_flo"], 3), vice.lees(sym["muz_fhi"], 3), vice.lees(sym["muz_ctrl"], 3)
    fouten, uitleg = [], []
    for v, stem in enumerate(m["stemmen"]):
        begin = 0
        for noot, duur in stem:
            if begin <= t < begin + duur:
                break
            begin += duur
        gate_verwacht = 0 if noot == 0 or t == begin + duur - 1 else 1
        echt_f = flo[v] | fhi[v] << 8
        if noot == 0:
            verwacht_f, naam = None, "rust"
        elif v == 2 and m["arp"]:
            c = t - begin
            midi_n = m["akkoorden"][noot - 1][((c + 1) % 6) // 2]
            verwacht_f, naam = m["freq"][midi_n], "akkoord %d toon %d" % (noot, ((c + 1) % 6) // 2)
        else:
            verwacht_f, naam = m["freq"][noot], "noot %d" % noot
        ok = (verwacht_f is None or echt_f == verwacht_f) and (ctrl[v] & 1) == gate_verwacht
        uitleg.append("stem %d %s%s" % (v + 1, naam, "" if ok else " (freq $%04x, gate %d)" % (echt_f, ctrl[v] & 1)))
        if not ok:
            fouten.append(v + 1)
    return not fouten, "muziek %s op beeld %d (tel %.2f): %s" % (m["naam"], f, t / m["tel"], "; ".join(uitleg))


def vergelijk(op, a, b):
    return {"=": a == b, "!=": a != b, "<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]


def scherm_tekst(vice, rij):
    """Tekenrij <rij> uit het schermgeheugen, terugvertaald met het eigen lettertype (tools/lettertype.py)."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import lettertype
    terug = {lettertype.code_van(t): t for t in lettertype.TEKENS}
    return "".join(terug.get(c, "?") for c in vice.lees(0xC000 + rij * 40, 40)).rstrip()


ONTHOUDEN = {}
KLEURNAMEN = ["zwart", "wit", "rood", "cyaan", "paars", "groen", "blauw", "geel", "oranje", "bruin", "roze",
              "donkergrijs", "grijs", "lichtgroen", "lichtblauw", "lichtgrijs"]


def controleer(vice, sym, regel, spel=None):
    if regel[0] == "ONTHOUD_KLEUR":
        _, naam, rij, kol, _ = regel
        ONTHOUDEN[naam] = (vice.lees(0xD800 + rij * 40 + kol)[0] & 15, vice.lees(sym["fl_stappen"])[0])
        return True, "onthouden: kleur-RAM rij %d kolom %d = %s" % (rij, kol, KLEURNAMEN[ONTHOUDEN[naam][0]])
    if regel[0] == "VERWACHT_KLEUR_VOLGEND":
        _, naam, rij, kol, rij_kleuren = regel
        # de kleur moet precies zoveel plekken in de rij opgeschoven zijn als er stappen waren (minstens één)
        nu = vice.lees(0xD800 + rij * 40 + kol)[0] & 15
        stappen_nu = vice.lees(sym["fl_stappen"])[0]
        oud, stappen_oud = ONTHOUDEN.get(naam, (None, 0))
        nrs = [KLEURNAMEN.index(k) for k in rij_kleuren]
        if oud not in nrs:
            return False, "onthouden kleur %s zit niet in de rij %s" % (KLEURNAMEN[oud] if oud is not None else "?", rij_kleuren)
        n = (stappen_nu - stappen_oud) & 255
        verwacht = nrs[(nrs.index(oud) + n) % len(nrs)]
        ONTHOUDEN[naam] = (nu, stappen_nu)
        ok = nu == verwacht and n >= 1
        return ok, "kleur rij %d kolom %d: %s, %d stap(pen) verder: %s%s" % (
            rij, kol, KLEURNAMEN[oud], n, KLEURNAMEN[verwacht], "" if ok else "  (is %s)" % KLEURNAMEN[nu])
    if regel[0] == "MUZIEK":
        return muziek_klopt(vice, sym)
    if regel[0] == "SLOT":
        _, slot, naam = regel
        figuren = spel["figuren"]
        echt = vice.lees(sym["slot_npc"] + slot)[0]
        echt_n = figuren[echt] if echt < len(figuren) else ("geen" if echt == 255 else str(echt))
        return echt_n == naam, "figuurslot %d = %s%s" % (slot, naam, "" if echt_n == naam else "  (is %s)" % echt_n)
    if regel[0] == "LOGO":
        # de kleurenloop: elke logokolom k heeft kleur logo_kleuren[(k + intro_kleur) & 15], in alle 3 de rijen
        stap = vice.lees(sym["intro_kleur"])[0]
        tabel = vice.lees(sym["logo_kleuren"], 16)
        rij = 19                                 # RIJ_LOGO in src/intro.asm (rij 18 blijft leeg: de naad)
        scherm = vice.lees(0xC000 + rij * 40, 120)
        kleur = [b & 15 for b in vice.lees(0xD800 + rij * 40, 120)]
        tekens = sum(1 for c in scherm if c >= 0x80)
        fout = [i for i in range(120) if kleur[i] != tabel[(i % 40 + stap) & 15]]
        return tekens > 60 and not fout, "logo: %d logotekens, kleurenloop op stap %d%s" % (
            tekens, stap, "" if not fout else "  (fout in %d vakjes)" % len(fout))
    if regel[0] == "VERWACHT_VLAG":
        _, naam, waarde = regel
        nr = spel["vlaggen"][naam]
        echt = vice.lees(sym["st_vlaggen"] + nr // 8)[0] >> (nr % 8) & 1
        return echt == int(waarde), "vlag %s = %s%s" % (naam, waarde, "" if echt == int(waarde) else "  (is %d)" % echt)
    if regel[0] == "VERWACHT_KAMER":
        terug = {v: k for k, v in spel["kamers"].items()}
        echt = terug.get(vice.lees(sym["st_kamer"])[0], "?")
        return echt == regel[1], "kamer = %s%s" % (regel[1], "" if echt == regel[1] else "  (is %s)" % echt)
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
    basic_klaar = any(r[1] == "basic" for r in verwacht)
    verwacht = [r for r in verwacht if r[1] not in ("scherm", "basic")]
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
                                     ("TEKST", "VERWACHT_VLAG", "VERWACHT_EIGENAAR", "VERWACHT_STAND", "VERWACHT_KAMER",
                                      "ONTHOUD_KLEUR", "VERWACHT_KLEUR_VOLGEND", "MUZIEK", "LOGO", "SLOT")]:
        if label not in sym:
            raise Fout("%s: onbekend label %s" % (verwachtpad, label))
    controles = [m for m in shots if isinstance(m, tuple)]
    shots_n = len(shots) - len(controles)
    os.makedirs(TESTUIT, exist_ok=True)

    print("[test] %s: %d stappen-bytes, %d screenshots, %d tussencontroles" % (naam, len(band), shots_n, len(controles)))
    t0 = time.time()
    if args.d71:                                       # alles op één D71, in een 1571: nooit een wissel
        d64 = os.path.join(TESTUIT, naam + ".d71")
        shutil.copyfile(os.path.join(BUILD, "hollowcrown.d71"), d64)
        diskettes = {1: d64}
    else:
        d64 = os.path.join(TESTUIT, naam + ".d64")     # een eigen kopie: opslaan (F5) schrijft op de diskette
        shutil.copyfile(os.path.join(BUILD, "hollowcrown.d64"), d64)
        diskettes = {1: d64, 2: os.path.join(TESTUIT, naam + "_2.d64")}   # diskette 2 (build.sh: schijf=2 in kamers.txt)
        if os.path.exists(os.path.join(BUILD, "hollowcrown_2.d64")):
            shutil.copyfile(os.path.join(BUILD, "hollowcrown_2.d64"), diskettes[2])
    # een band met de regel "echte_drive" draait altijd met de 1541-emulatie (voor de snellader: turbo.asm)
    echte_drive = args.echte_drive or any(r.split("#", 1)[0].strip() == "echte_drive" for r in open(bandpad))
    vice = Vice(d64, warp=not args.geen_warp,
                echte_drive=echte_drive, zichtbaar_houden=args.houd_open,
                geluid=args.kijk and not args.stil, snelheid=args.snelheid,
                drive=1571 if args.d71 else 1541)
    try:
        # 1. wachten tot het spel draait: magic "HC" staat er en de band wacht op ons
        eind = time.time() + args.starttijd
        in_spel = 0
        while True:
            if (vice.lees(sym["st_magic"], 2) == [0x48, 0x43] and vice.lees(sym["band_status"])[0] == BAND_WACHT
                    and vice.lees(sym["band_markering"])[0] == 0):
                # (met de echte drive laadt het programma langzaam: "HC" staat al in de prg, dus ook halverwege het
                #  laden. Pas als de processor een paar keer achter elkaar in het spel zelf staat, niet in de Kernal,
                #  is het echt gestart: één keer kan toeval zijn, zeker op normale snelheid.)
                pc = int(re.search(r";([0-9a-f]{4})", vice.cmd("r")).group(1), 16)
                in_spel = in_spel + 1 if pc < 0xa000 else 0
                if in_spel >= (6 if echte_drive else 1):
                    break
            else:
                in_spel = 0
            vice.verder()
            if time.time() > eind:
                raise Fout("het spel startte niet binnen %d s" % args.starttijd)
            time.sleep(0.25)
        print("[test]   spel draait na %.1f s" % (time.time() - t0))
        if "laad_fout" in sym and vice.lees(sym["laad_fout"])[0]:
            raise Fout("de eerste kamer laadde niet van de diskette (laad_fout = %d, Kernal-status $%02x)"
                       % (vice.lees(sym["laad_fout"])[0], vice.lees(0x90)[0]))

        # 2. band laden en starten. De band in het spel is een ring van BAND_GROOTTE bytes: eerst het begin, daarna
        #    vult de lus hieronder achter de leeskop (zp_band, $06) bij. De eerste BAND_SPIEGEL bytes van de ring staan
        #    ook achter het einde, zodat een opdracht die over de rand loopt in één keer te lezen is.
        def ring_schrijven(van, tot):
            for p in range(van, tot, 256):
                stuk = band[p:min(tot, p + 256)]
                plek = p % BAND_GROOTTE
                if plek + len(stuk) > BAND_GROOTTE:            # over de rand: in twee delen
                    n = BAND_GROOTTE - plek
                    ring_schrijven_stuk(plek, stuk[:n])
                    ring_schrijven_stuk(0, stuk[n:])
                else:
                    ring_schrijven_stuk(plek, stuk)

        def ring_schrijven_stuk(plek, stuk):
            vice.schrijf(sym["band"] + plek, stuk)
            if plek < BAND_SPIEGEL:                          # de spiegel achter het einde
                vice.schrijf(sym["band"] + BAND_GROOTTE + plek, stuk[:BAND_SPIEGEL - plek])

        voorruimte = BAND_GROOTTE - 256                      # zoveel mag er vóór de leeskop klaarstaan
        geschreven = min(len(band), voorruimte)
        ring_schrijven(0, geschreven)
        if bytes(vice.lees(sym["band"], min(geschreven, 256))) != band[:min(geschreven, 256)]:
            raise Fout("de band staat niet goed in het geheugen")
        rondes, vorige_plek = 0, 0
        in_drive = 1                                         # welke diskette er nu in zit
        vice.schrijf(sym["band_status"], [BAND_LOOPT])
        vice.verder()

        # 3. de band volgen: markeringen afhandelen tot hij klaar is
        schermfouten = 0
        volgende = 0
        eind = time.time() + args.max_tijd
        while True:
            # (elke blik in het geheugen zet de emulatie even stil: op normale snelheid hoor je dat. In de kijkstand
            #  daarom maar één keer per seconde, en alleen de ring bijvullen als die bijna op is.)
            time.sleep(1.0 if args.kijk else 0.05)
            if sym["band_markering"] == sym["band_status"] + 1:
                status, markering = vice.lees(sym["band_status"], 2)
            else:
                status, markering = vice.lees(sym["band_status"])[0], vice.lees(sym["band_markering"])[0]
            if geschreven < len(band):                       # de ring bijvullen achter de leeskop
                lo, hi = vice.lees(0x06, 2)
                plek = (lo | hi << 8) - sym["band"]
                if plek < vorige_plek:
                    rondes += 1
                vorige_plek = plek
                gelezen = rondes * BAND_GROOTTE + plek
                tot = min(len(band), gelezen + voorruimte)
                if tot > geschreven:
                    ring_schrijven(geschreven, tot)
                    geschreven = tot
            nodig = vice.lees(sym["schijf_nodig"])[0] if "schijf_nodig" in sym else 0
            if nodig:                                 # het spel vraagt om een andere diskette: erin stoppen
                if nodig not in diskettes or not os.path.exists(diskettes[nodig]):
                    raise Fout("het spel vraagt diskette %d, en die is er niet" % nodig)
                if nodig != in_drive:                # (zit hij er al in, dan niet opnieuw: een nieuwe wissel laat
                    vice.cmd('attach "%s" 8' % diskettes[nodig])   # de echte 1541 weer van voren af beginnen)
                    in_drive = nodig
                    print("[test]   diskette %d erin" % nodig, flush=True)
                else:
                    print("[test]   diskette %d zit er al in" % nodig, flush=True)
                vice.schrijf(sym["schijf_nodig"], [0])
            if markering:
                # de markeringen tellen rond (1..255): de volgende in de rij is aan de beurt
                if volgende >= len(shots) or markering != volgende % 255 + 1:
                    raise Fout("onverwachte markering %d (verwacht %d)" % (markering, volgende % 255 + 1))
                m = shots[volgende]
                volgende += 1
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
                        ok, uitleg = kamerbuffer_klopt(vice, sym, spel)
                        schermfouten += 0 if ok else 1
                        print("[test]   %-4s kamer: %s" % ("ok" if ok else "FOUT", uitleg))
                vice.schrijf(sym["band_markering"], [0])
            if status == BAND_KLAAR:
                break
            if status == BAND_FOUT:
                raise Fout("het spel kent bandopcode $%02x niet (nog niet gebouwd?)" % vice.lees(sym["band_fout"])[0])
            vice.verder()
            if time.time() > eind:
                regs = vice.cmd("r").strip().splitlines()[-1]
                pc = int(re.search(r";([0-9a-f]{4})", regs).group(1), 16)
                labels = sorted((a, n) for n, a in sym.items() if a <= pc)
                waar = "%s+%d" % (labels[-1][1], pc - labels[-1][0]) if labels else "?"
                extra = ", ".join("%s=%d" % (n, vice.lees(sym[n])[0]) for n in
                                  ("turbo_uit", "turbo_teller", "laad_teller", "laad_fout", "schijf_nodig") if n in sym)
                if echte_drive:                          # en waar de drive staat (de snellader draait op $0500)
                    try:
                        vice.cmd("device 8:")
                        d_regs = vice.cmd("r").strip().splitlines()[-1]
                        d_mem = vice.cmd("m 0000 000f").strip().splitlines()[-1]
                        vice.cmd("device c:")
                        extra += "; drive: %s | %s" % (d_regs.strip(), d_mem.strip())
                    except Exception as e:
                        extra += "; drive: ? (%s)" % e
                raise Fout("band niet klaar binnen %d s (de C64 staat op $%04x: %s; %s)"
                           % (args.max_tijd, pc, waar, extra))

        # 4. de status vergelijken (de C64 staat stil in de monitor)
        goed = schermfouten == 0
        if scherm_ideaal and not shots_n:
            print("[test]   FOUT scherm = ideaal, maar de band maakt geen screenshot")
            goed = False
        if basic_klaar:
            # menu Bestand, Exit: terug in BASIC? Het gewone scherm op $0400 moet READY. laten zien.
            for _ in range(40):
                vice.verder()
                time.sleep(0.05)
                codes = vice.lees(0x0400, 1000)
                tekst = "".join(chr(c + 64) if 1 <= c <= 26 else chr(c) if 32 <= c <= 63 else " " for c in codes)
                if "READY." in tekst:
                    break
            ok = "READY." in tekst and vice.lees(0x0001)[0] & 7 == 7
            goed &= ok
            print("[test]   %-4s basic = klaar: READY. op het scherm, BASIC- en Kernal-ROM aan%s" % (
                "ok" if ok else "FOUT", "" if ok else "  (scherm: %r)" % tekst.strip()[:80]))
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
    p.add_argument("--max-tijd", type=int, default=600, help="seconden voor de hele band")
    p.add_argument("--kijk", action="store_true",
                   help="om mee te kijken: venster, normale snelheid, geluid, echte 1541 (de snellader), ruime tijd")
    p.add_argument("--snelheid", type=int, default=100, help="zonder warp: zoveel procent van de echte C64 (200 = dubbel)")
    p.add_argument("--stil", action="store_true", help="in de kijkstand zonder geluid")
    p.add_argument("--d71", action="store_true", help="build/hollowcrown.d71 (alles op één diskette) in een 1571")
    args = p.parse_args()
    if args.kijk:
        args.geen_warp = args.houd_open = args.echte_drive = True
        args.starttijd, args.max_tijd = max(args.starttijd, 300), max(args.max_tijd, 4 * 3600)
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
