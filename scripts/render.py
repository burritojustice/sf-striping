#!/usr/bin/env python3
"""
Render images of the striping diagram PDFs for the map, in one pass per PDF:

  previews/<key>.webp   1000 px wide, for hover cards and the side panel
  hi/<key>.webp         3000 px wide, for the zoomable viewer

<key> is the "preview" field in data/striping.json (first 12 hex digits of the SHA-1 of the PDF's path in
SFMTA's index). Only current diagrams that are new, have a new upload time, or are missing an image are
rendered. previews/manifest.json records what each pair of images was made from.

Usage (from the repo root):
  python3 scripts/render.py                          # new or changed only
  python3 scripts/render.py --limit 10               # try a few
  python3 scripts/render.py --commit-every 200       # commit and push in batches (the weekly job does this)
  python3 scripts/render.py --samples 8218.2 7970.1  # same drawings at several sizes -> samples/, see samples.html

Needs poppler (pdftoppm) and Pillow:
  macOS:  brew install poppler && pip3 install pillow
  Ubuntu: sudo apt install poppler-utils && pip3 install pillow
"""
import argparse, json, os, subprocess, sys, tempfile, urllib.request
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEWS = os.path.join(ROOT, "previews")
HI = os.path.join(ROOT, "hi")
MANIFEST = os.path.join(PREVIEWS, "manifest.json")
PREVIEW_WIDTH = 1000
HI_WIDTH = int(os.environ.get("STRIPING_HI_WIDTH") or 3000)
QUALITY = 55            # WebP quality; line drawings stay sharp at this level


def fetch_pdf(url, folder):
    pdf = os.path.join(folder, "d.pdf")
    req = urllib.request.Request(url, headers={"User-Agent": "sf-striping"})
    with urllib.request.urlopen(req, timeout=180) as r, open(pdf, "wb") as f:
        f.write(r.read())
    return pdf


def raster(pdf, dpi, folder):
    """page 1 of the PDF as a PIL image"""
    for n in os.listdir(folder):
        if n.endswith(".png"):
            os.remove(os.path.join(folder, n))
    subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-r", str(dpi), "-png", pdf, os.path.join(folder, "p")],
                   check=True, capture_output=True)
    png = next(os.path.join(folder, n) for n in os.listdir(folder) if n.endswith(".png"))
    Image.MAX_IMAGE_PIXELS = None
    return Image.open(png).convert("RGB")


def shrink(im, width):
    return im if im.width <= width else im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)


def render_pair(url, key, hi_width):
    """download once, save both sizes"""
    with tempfile.TemporaryDirectory() as tmp:
        big = raster(fetch_pdf(url, tmp), 200 if hi_width <= 3000 else 300, tmp)
        hi = shrink(big, hi_width)
        hi.save(os.path.join(HI, key + ".webp"), "WEBP", quality=QUALITY, method=6)
        pv = shrink(hi, PREVIEW_WIDTH)
        pv.save(os.path.join(PREVIEWS, key + ".webp"), "WEBP", quality=QUALITY, method=6)
        return pv.size, hi.size


def samples(data, ids, widths):
    out_root = os.path.join(ROOT, "samples")
    os.makedirs(out_root, exist_ok=True)
    idx_path = os.path.join(out_root, "index.json")
    index = json.load(open(idx_path)) if os.path.exists(idx_path) else {}
    for sid in ids:
        d = next((d for d in data["diagrams"] if d["id"] == sid and d["current"]), None)
        if not d:
            print(f"  no current diagram with ID {sid}"); continue
        folder = os.path.join(out_root, sid)
        os.makedirs(folder, exist_ok=True)
        entry = {"id": sid, "file": d["file"], "url": d["url"], "pdf_kb": d["size_kb"], "images": []}
        with tempfile.TemporaryDirectory() as tmp:
            full = raster(fetch_pdf(d["url"], tmp), 300, tmp)
            entry["page_px"] = list(full.size)
            for w in widths:
                im = full if w == "full" else shrink(full, int(w))
                name = f"{w}.webp"
                im.save(os.path.join(folder, name), "WEBP", quality=QUALITY if w != "full" else 70, method=6)
                kb = round(os.path.getsize(os.path.join(folder, name)) / 1024)
                entry["images"].append({"width": w, "px": list(im.size), "kb": kb, "src": f"samples/{sid}/{name}"})
                print(f"  {sid} {w}: {im.size[0]}x{im.size[1]} px, {kb} KB", flush=True)
        index[sid] = entry
    json.dump(index, open(idx_path, "w"), indent=1)


def git_push(message):
    subprocess.run(["git", "add", "previews", "hi"], cwd=ROOT, check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
        return
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=ROOT, check=True)
    subprocess.run(["git", "pull", "-q", "--rebase"], cwd=ROOT)
    subprocess.run(["git", "push", "-q"], cwd=ROOT, check=True)
    print("  pushed", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="redo every image")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--hi", type=int, default=HI_WIDTH, help="zoomable image width (default 3000)")
    ap.add_argument("--commit-every", type=int, default=0, help="commit and push after this many diagrams")
    ap.add_argument("--samples", nargs="*", help="diagram IDs to render at several sizes into samples/")
    ap.add_argument("--widths", default="1000,2000,3000,full")
    a = ap.parse_args()
    data = json.load(open(os.path.join(ROOT, "data", "striping.json"), encoding="utf-8"))
    if a.samples:
        samples(data, a.samples, a.widths.split(","))
        return

    os.makedirs(PREVIEWS, exist_ok=True); os.makedirs(HI, exist_ok=True)
    manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    has = lambda folder, k: os.path.exists(os.path.join(folder, k + ".webp"))
    todo = [d for d in data["diagrams"] if d["current"] and d["kind"] == "street" and
            (a.all or manifest.get(d["preview"], {}).get("modified") != d["modified"]
             or manifest.get(d["preview"], {}).get("hi") != a.hi
             or not has(PREVIEWS, d["preview"]) or not has(HI, d["preview"]))]
    if a.limit:
        todo = todo[:a.limit]
    print(f"{len(todo)} diagrams to render (previews {PREVIEW_WIDTH} px, zoomable {a.hi} px)", flush=True)

    done = failed = 0
    for i, d in enumerate(todo, 1):
        try:
            (w, h), (hw, hh) = render_pair(d["url"], d["preview"], a.hi)
            manifest[d["preview"]] = {"path": d["path"], "modified": d["modified"], "w": w, "h": h, "hi": a.hi, "hi_w": hw, "hi_h": hh}
            done += 1
        except Exception as e:
            failed += 1
            print(f"  failed {d['file']}: {e}", file=sys.stderr, flush=True)
        if i % 25 == 0:
            json.dump(manifest, open(MANIFEST, "w"), indent=0)
            print(f"  {i}/{len(todo)}", flush=True)
        if a.commit_every and i % a.commit_every == 0:
            json.dump(manifest, open(MANIFEST, "w"), indent=0)
            git_push(f"Render striping images ({i}/{len(todo)})")

    # forget images for diagrams that are gone or no longer current
    keep = {d["preview"] for d in data["diagrams"] if d["current"]}
    for k in [k for k in manifest if k not in keep]:
        manifest.pop(k)
        for folder in (PREVIEWS, HI):
            try: os.remove(os.path.join(folder, k + ".webp"))
            except FileNotFoundError: pass
    json.dump(manifest, open(MANIFEST, "w"), indent=0)
    if a.commit_every:
        git_push("Render striping images")
    print(f"rendered {done}, failed {failed}, total {len(manifest)}", flush=True)


if __name__ == "__main__":
    main()
