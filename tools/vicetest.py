#!/usr/bin/env python3
"""vicetest.py — speelt een invoerband af in VICE en controleert de spelstatus (projectprompt §7).

    python3 tools/vicetest.py tests/wacht.band            bouwt eerst (./build.sh --autotest), dan de test
    python3 tools/vicetest.py tests/*.band --geen-build   meerdere banden, zonder te bouwen
    opties: --geen-warp, --echte-drive (1541-emulatie, voor laadtijden), --houd-open

Een band (tests/<naam>.band) is tekst, één stap per regel ('#' is commentaar):
    wacht 50              50 beelden niets doen
    screenshot begin      maak build/test/<naam>_begin.png (de C64 wacht zolang)
    cursor 100,80         cursor naar x,y            (vanaf hoofdstuk 1)
    vuur                  vuurknop                   (vanaf hoofdstuk 1)

Na de band leest de test het geheugen en vergelijkt het met tests/<naam>.verwacht:
    st_versie = 1         byte op label st_versie
    st_magic+1 = $43      met een verschuiving
    beelden.w >= 300      .w = woord (lo, hi); vergelijkingen: = != < <= > >=
Een test slaagt alleen als de status klopt; een screenshot alleen is geen bewijs.
"""
import argparse, os, re, signal, socket, subprocess, sys, time

# ---- instellingen: het pad naar VICE staat hier (en bovenin build.sh) ----------------------------
VICE_BIN = os.environ.get("VICE_BIN", "/Applications/vice-arm64-gtk3-3.10/bin")
# ---------------------------------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build", "autotest")
TESTUIT = os.path.join(ROOT, "build", "test")

# opcodes van de invoerband: gelijk houden met src/autotest.asm
OP_EINDE, OP_WACHT, OP_MARKEER, OP_CURSOR, OP_VUUR = 0, 1, 2, 3, 4
BAND_WACHT, BAND_LOOPT, BAND_KLAAR, BAND_FOUT = 0, 1, 2, 0xFF
BAND_GROOTTE = 1024


class Fout(Exception):
    pass


# ---------------------------------------------------------------------------------------------------
# De band
# ---------------------------------------------------------------------------------------------------
def lees_band(pad):
    """Geeft (bytes, lijst van screenshotnamen; markering k hoort bij namen[k-1])."""
    data, namen = bytearray(), []
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
            else:
                raise ValueError
        except ValueError:
            raise Fout("%s:%d: onbekende of foute stap: %s" % (pad, nr, regel))
    data.append(OP_EINDE)
    if len(data) > BAND_GROOTTE:
        raise Fout("%s: band is %d bytes, de buffer %d" % (pad, len(data), BAND_GROOTTE))
    return bytes(data), namen


def lees_verwacht(pad):
    regels = []
    for nr, regel in enumerate(open(pad, encoding="utf-8"), 1):
        regel = regel.split("#", 1)[0].strip()
        if not regel:
            continue
        m = re.fullmatch(r"([A-Za-z_]\w*)(?:\+(\d+))?(\.w)?\s*(=|!=|<=|>=|<|>)\s*(\$[0-9A-Fa-f]+|\d+)", regel)
        if not m:
            raise Fout("%s:%d: kan dit niet lezen: %s" % (pad, nr, regel))
        label, plus, woord, op, waarde = m.groups()
        waarde = int(waarde[1:], 16) if waarde.startswith("$") else int(waarde)
        regels.append((regel, label, int(plus or 0), bool(woord), op, waarde))
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
# Een test
# ---------------------------------------------------------------------------------------------------
def vergelijk(op, a, b):
    return {"=": a == b, "!=": a != b, "<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]


def draai(bandpad, args):
    naam = os.path.splitext(os.path.basename(bandpad))[0]
    band, shots = lees_band(bandpad)
    verwachtpad = os.path.splitext(bandpad)[0] + ".verwacht"
    if not os.path.exists(verwachtpad):
        raise Fout("%s ontbreekt: zonder verwachte status is er geen test" % verwachtpad)
    verwacht = lees_verwacht(verwachtpad)
    sym = lees_symbolen(os.path.join(BUILD, "hollowcrown.vs"))
    for nodig in ("band", "band_status", "band_markering", "band_fout", "st_magic"):
        if nodig not in sym:
            raise Fout("label %s niet in hollowcrown.vs: is dit een AUTOTEST-build?" % nodig)
    for _, label, *_ in verwacht:
        if label not in sym:
            raise Fout("%s: onbekend label %s" % (verwachtpad, label))
    os.makedirs(TESTUIT, exist_ok=True)

    print("[test] %s: %d stappen-bytes, %d screenshots" % (naam, len(band), len(shots)))
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
        eind = time.time() + args.max_tijd
        while True:
            time.sleep(0.05)
            status, markering = vice.lees(sym["band_status"])[0], vice.lees(sym["band_markering"])[0]
            if markering:
                if markering > len(shots):
                    raise Fout("onbekende markering %d" % markering)
                pad = os.path.join(TESTUIT, "%s_%s.png" % (naam, shots[markering - 1]))
                vice.screenshot(pad)
                print("[test]   screenshot %s" % os.path.relpath(pad, ROOT))
                vice.schrijf(sym["band_markering"], [0])
            if status == BAND_KLAAR:
                break
            if status == BAND_FOUT:
                raise Fout("het spel kent bandopcode $%02x niet (nog niet gebouwd?)" % vice.lees(sym["band_fout"])[0])
            vice.verder()
            if time.time() > eind:
                raise Fout("band niet klaar binnen %d s" % args.max_tijd)

        # 4. de status vergelijken (de C64 staat stil in de monitor)
        goed = True
        for tekst, label, plus, woord, op, waarde in verwacht:
            b = vice.lees(sym[label] + plus, 2 if woord else 1)
            echt = b[0] | (b[1] << 8) if woord else b[0]
            ok = vergelijk(op, echt, waarde)
            goed &= ok
            print("[test]   %-4s %-28s (is %d / $%x)" % ("ok" if ok else "FOUT", tekst, echt, echt))
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
