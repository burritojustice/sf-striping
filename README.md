# sf-striping

A map of SFMTA's street striping diagrams: hover a street to see which diagram covers it and a preview, click to open it, zoom in, or download the PDF.

Live site: https://burritojustice.github.io/sf-striping/ (link to a diagram with `#id=8218.2`)

## Files

| Path | What it is |
|---|---|
| `index.html` | The map (HTML, CSS, JS in one file) |
| `samples.html` | Compares diagram images at several sizes (see Samples) |
| `data/streets.json` | San Francisco street segments and intersections, copied from [sf-blocks](https://github.com/burritojustice/sf-blocks) |
| `data/striping.json` | Every striping PDF, with the blocks (CNNs) and intersections it covers. Built by `build_striping.py` |
| `data/striping_review.csv` | Every drawing with its match confidence, worst first, for review |
| `data/striping_overrides.csv` | Your corrections (create it when needed; see Checking matches) |
| `data/striping_changes.json` | Log of what changed in SFMTA's files from week to week (created the first time something changes) |
| `previews/<key>.webp` | 1000 px images for the hover card and side panel; `previews/manifest.json` records their sources |
| `hi/<key>.webp` | 3000 px images for the zoomable viewer |
| `scripts/build_striping.py` | Reads SFMTA's file index, matches each PDF to blocks, writes the data files |
| `scripts/render.py` | Downloads PDFs and renders both image sizes |
| `scripts/match_blocks.py` | Street matcher, copied from sf-blocks |
| `.github/workflows/refresh.yml` | Weekly job: runs both scripts and commits the results |
| `.github/workflows/samples.yml` | On-demand job for `samples.html` |

`<key>` is the first 12 hex digits of the SHA-1 of the PDF's path in SFMTA's index (the `preview` field in `striping.json`).

## Where the data comes from

- **Diagrams:** SFMTA's street document library, https://streets-docs.apps.sfmta.com/?library=striping-diagrams&lang=en. The page is built from a file index, https://safitwebapps.blob.core.windows.net/$web/webappsindex.json, which lists every PDF with its upload time and size.
- **Streets:** DataSF, through [sf-blocks](https://github.com/burritojustice/sf-blocks) (Streets – Active and Retired, and List of Intersections only).

## How diagrams are placed

`build_striping.py` keeps the PDFs under `Striping Drawings/` and parses each file name, for example `2-Fulton St_str-7970.1 (42nd Ave to 34th Ave).pdf` → series 2, Fulton St, ID 7970.1, from 42nd Ave to 34th Ave. It then finds the blocks of that street between the two cross streets, using the sf-blocks matcher.

The parser handles the usual variations: `_Str-`, `STR `, `Str4896`, IDs before the street name, revision tails (`r6`, `rev1`, `_see [name] [date]`), "A to B", "A - B", "A & B", several ranges in one name, single intersections, spelling differences ("GreatHigh Way", "JFK", "Terminus"), and streets with gaps in the city data (matched by position along the street). The street part of the name has to be a real street on its own, so "Forest Hill" isn't read as Hill St.

- The `03_Detail STR` standard drawings and Caltrans plans aren't locations and are skipped.
- When several uploads share an ID, the newest is the "current" one shown on the map.
- One of the two cross streets in a file name is often only partly drawn; the block leading to it is still included.

Each drawing gets a confidence: **high** (street and both cross streets found), **medium** (a spelling fix, or "A & B" read as the stretch between them), **low** (only one cross street found, or the whole street used), **none** (not placed), or **confirmed** (checked by a person).

## The map

- Streets with a diagram are teal; gray ones have none.
- **Hover** a street: the whole diagram's stretch lights up, with a card showing its ID and a preview turned to match the street (the drawing's left edge points at the first cross street in the file name).
- **Click**: the diagram is picked, with its ends labeled. The side panel shows the preview, Open PDF, file details, other sheets in the set, and other diagrams covering that block. Hovering the panel preview enlarges it; clicking it opens a full-screen viewer (scroll or pinch to zoom, drag to move, Esc to close) with the 3000 px image.
- **Search** by street, ID, or cross street.
- **Labels** and **Match quality** toggles show each diagram's ID and file name (zoom 14+) and color streets by confidence.

## Checking matches

The panel's "Check matches" section lists diagrams not on the map, low confidence, and medium confidence, and can step through them one at a time (Prev / Next, or `[` and `]`; your place is remembered on that computer). It also links `data/striping_review.csv`.

To correct a drawing, fill in its review columns in the review file and copy those rows, with the header row, into `data/striping_overrides.csv`:

| Column | Use |
|---|---|
| `status` | `ok` = the match is right (shown as confirmed, green under Match quality); `exclude` = not a street location, keep it off the map |
| `fix_street`, `fix_from_street`, `fix_to_street` | Re-match with these names instead of the file name's; leave `fix_to_street` empty for an intersection |
| `review_note` | Why; shown with the diagram |

The next build applies them. Overrides are matched by file name, so if SFMTA renames a file, its row needs the new name (the change log shows renames).

## Keeping it current

`.github/workflows/refresh.yml` runs every Monday. It rebuilds the data files, logs changes to `data/striping_changes.json` (added, removed, renamed under the same ID, re-uploaded with a new time), then renders images only for new or changed diagrams, committing every 200 so a long run keeps its progress. Run it by hand from the Actions tab ("Refresh striping diagrams"); the `limit` input renders just a few for testing.

The first run renders every diagram (about 1,600 PDFs, 1.2 GB of downloads) and takes one to two hours. Images total roughly 75 MB of previews and 450 MB of 3000 px images, under GitHub Pages' 1 GB limit.

GitHub may pause scheduled workflows in a repo with no activity for 60 days; it emails a warning, and re-enabling is one click in the Actions tab.

**Repo settings:** Pages from `main`, root folder; Actions → General → Workflow permissions → Read and write.

## Samples

To compare image sizes, run "Preview samples" from the Actions tab with a few IDs and widths. Results appear on `samples.html`, with a 100% crop and file size for each.

## Updating the street data

`data/streets.json` and `scripts/match_blocks.py` are copies from [sf-blocks](https://github.com/burritojustice/sf-blocks); their headers say which version. To update, copy the newer files from sf-blocks and run the refresh workflow.

## Running locally

```
python3 -m http.server 8000             # then open http://localhost:8000
python3 scripts/build_striping.py       # rebuild data (downloads SFMTA's index)
python3 scripts/render.py --limit 5     # needs poppler and Pillow
```

## Settings (top of the script in `index.html`)

- `CONFIG.PROTOMAPS_KEY`: basemap key. If it's restricted by domain, `burritojustice.github.io` (and `localhost` for testing) must be allowed.
- `CONFIG.PREVIEWS`, `CONFIG.PREVIEWS_HI`: where the two image sizes live; change these if the images ever move to other storage.
