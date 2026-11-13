#!/usr/bin/env python3
"""flux.py — laat het beeldmodel van MacAIMagic (FLUX.2 Klein) een plaatje maken dat goed naar de C64 om te zetten is.

  python3 flux.py scene  "a haunted castle on a hill under a full moon" kasteel.png
  python3 flux.py sprite "a ghost with two big eyes far apart" spook.png
  python3 flux.py sprite "a purple bat with spread wings" vleermuis.png --groen --aantal 3

Beschrijf alleen het onderwerp, in het Engels; de stijl die de C64 nodig heeft komt er vanzelf achter
(scene: 8-bit pixelart, vlakke kleuren, veel contrast, geen tekst; sprite: heel simpel, grove pixels, effen magenta
achtergrond). --rauw laat die stijl weg. --groen geeft een sprite een groene achtergrond (voor iets paars of roze).
--aantal N maakt N versies met verschillende zaden (naam_1.png, naam_2.png ...): kies de beste.
--zaad N maakt een plaatje opnieuw precies zo.
--ref beeld.png (mag vaker) geeft een referentiebeeld mee (FLUX.2 kan daarmee "in dezelfde stijl" of "hetzelfde,
maar ..." maken). --init beeld.png --masker masker.png schildert alleen het witte deel van het masker opnieuw
(bv. een patch: dezelfde kamer met de tafel verschoven); --sterkte bepaalt hoeveel.

Daarna: python3 c64beeld.py bitmap kasteel.png kasteel   of   python3 c64beeld.py sprites figuren spook.png ...

Het draait dezelfde engine met dezelfde instellingen als de app (4 stappen), naast het chatmodel. Is daar te weinig
geheugen voor, dan zegt het dat: vraag het plaatje dan met make_image (de app maakt eerst ruimte) en zet het daarna om;
het staat dan als nieuwste .png in ~/Pictures/MacAIMagic.
"""
import argparse, os, random, re, subprocess, sys, time

MODEL = os.path.expanduser("~/Library/Application Support/MacAIMagic/models/flux-2-klein-4b/")
DELEN = ["flux-2-klein-4b-image.gguf", "flux-2-klein-4b-text.gguf", "flux-2-klein-4b-decoder.safetensors"]
STIJL = {
    "scene": ", 8-bit pixel art, Commodore 64 adventure game scene, chunky pixels, flat colors, few colors, "
             "high contrast, no text, no letters",
    "sprite": ", a very simple sprite for an 8-bit home computer, very low resolution, huge chunky square pixels, "
              "about 24 by 21 pixels, simple bold shape, centered, full figure, on a plain solid {achter} background, "
              "no text",
}


def engine():
    """de image-engine van de app die draait, anders die in /Applications"""
    kandidaten = []
    try:
        ps = subprocess.run(["ps", "-axo", "comm="], capture_output=True, text=True).stdout
        for regel in ps.splitlines():
            m = re.match(r"(.*\.app)/Contents/MacOS/MacAIMagic$", regel.strip())
            if m:
                kandidaten.append(m.group(1))
    except OSError:
        pass
    kandidaten += ["/Applications/MacAIMagic.app", os.path.expanduser("~/Applications/MacAIMagic.app")]
    for app in kandidaten:
        exe = os.path.join(app, "Contents/Resources/engine/image-engine")
        if os.access(exe, os.X_OK):
            return exe
    sys.exit("FOUT: de image-engine van MacAIMagic is niet gevonden (staat de app in /Applications?)")


def vrij_geheugen():
    """wat macOS zonder moeite kan geven, in GB: vrij + inactief + speculatief + opruimbaar"""
    uit = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
    pagina = int(re.search(r"page size of (\d+)", uit).group(1))
    som = 0
    for naam in ("Pages free", "Pages inactive", "Pages speculative", "Pages purgeable"):
        m = re.search(naam + r":\s+(\d+)", uit)
        som += int(m.group(1)) if m else 0
    return som * pagina / 1e9


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("soort", choices=["scene", "sprite"])
    ap.add_argument("beschrijving", help="het onderwerp, in het Engels")
    ap.add_argument("uit", help="naam.png")
    ap.add_argument("--aantal", type=int, default=1)
    ap.add_argument("--zaad", type=int)
    ap.add_argument("--groen", action="store_true")
    ap.add_argument("--rauw", action="store_true")
    ap.add_argument("--ref", action="append", default=[],
                    help="referentiebeeld (stijl/inhoud), mag vaker: bv. data/flux/dawnhaven.png voor dezelfde stijl")
    ap.add_argument("--init", help="beginbeeld (img2img of, met --masker, inpainting)")
    ap.add_argument("--masker", help="wit = opnieuw tekenen, zwart = laten (zelfde maat als --init)")
    ap.add_argument("--sterkte", type=float, default=0.75, help="hoeveel er van --init verandert (0-1)")
    a = ap.parse_args()

    for deel in DELEN:
        if not os.path.exists(MODEL + deel + ".ok"):
            sys.exit("FOUT: het beeldmodel is er nog niet. Vraag de gebruiker FLUX.2 Klein te downloaden "
                     "(download_model flux-2-klein-4b, de gebruiker keurt het goed).")
    if subprocess.run(["pgrep", "-x", "image-engine"], capture_output=True).returncode == 0:
        sys.exit("FOUT: de app maakt al een afbeelding. Wacht tot die klaar is en probeer het dan opnieuw.")
    vrij = vrij_geheugen()
    if vrij >= 12:
        budget, (w, h) = "5.0", ((1024, 640) if a.soort == "scene" else (512, 512))
    elif vrij >= 6:
        budget, (w, h) = "1.2", ((768, 480) if a.soort == "scene" else (512, 512))
    else:
        sys.exit(f"FOUT: te weinig vrij geheugen naast het chatmodel ({vrij:.1f} GB, nodig 6 GB). Vraag het plaatje "
                 "met make_image: de app maakt dan eerst ruimte. Het komt als nieuwste .png in ~/Pictures/MacAIMagic; "
                 "zet het in je volgende beurt om met c64beeld.py.")

    prompt = a.beschrijving.strip().rstrip(".")
    if not a.rauw:
        prompt += STIJL[a.soort].format(achter="green" if a.groen else "magenta")
    exe = engine()
    basis, ext = os.path.splitext(a.uit)
    zaad0 = a.zaad if a.zaad is not None else random.randint(1, 999999)
    for i in range(a.aantal):
        zaad = zaad0 + i
        uit = a.uit if a.aantal == 1 else f"{basis}_{i + 1}{ext or '.png'}"
        args = [exe, "--diffusion-model", MODEL + DELEN[0], "--llm", MODEL + DELEN[1], "--vae", MODEL + DELEN[2],
                "-p", prompt, "--steps", "4", "--cfg-scale", "1.0", "--sampling-method", "euler", "-s", str(zaad),
                "-W", str(w), "-H", str(h), "-o", os.path.abspath(uit), "--mmap", "--disable-image-metadata",
                "--max-vram", budget, "--vae-tiling"]
        for r in a.ref:
            args += ["-r", os.path.abspath(r)]
        if a.init:
            args += ["-i", os.path.abspath(a.init), "--strength", str(a.sterkte)]
        if a.masker:
            args += ["--mask", os.path.abspath(a.masker)]
        t = time.time()
        r = subprocess.run(args, cwd=os.path.dirname(exe), capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(uit):
            fout = [l for l in (r.stdout + r.stderr).splitlines() if "[E]" in l or "error" in l.lower()]
            sys.exit(f"FOUT: FLUX maakte {uit} niet: " + (" | ".join(fout[-3:]) or f"code {r.returncode}"))
        print(f"{uit}: {w}x{h}, zaad {zaad}, {time.time() - t:.0f} s")
    print("prompt:", prompt)


if __name__ == "__main__":
    main()
