# Changelog

## s6
- Moved from `civic-joy-fund/block-party` (`striping/`) to its own repo, `burritojustice/sf-striping`. The map is now at the site root; data paths are `data/…`.
- One job renders both image sizes from a single download per PDF: 1000 px previews in `previews/` and 3000 px zoomable images in `hi/` (`scripts/render.py`, replacing the separate preview and striping-images scripts). Commits every 200 images.
- One weekly workflow, "Refresh striping diagrams" (`refresh.yml`), and "Preview samples" (`samples.yml`).
- Review-file map links point to `burritojustice.github.io/sf-striping`.
- Street data and matcher are copies from `burritojustice/sf-blocks`.

## s5
- The zoomable viewer loaded 3000 px images from a separate images repo (folded back into this repo in s6).

## s4
- The hover popup is rotated to match the map, following the panel's checkbox.
- Clicking the panel preview opens a full-screen viewer: scroll, pinch, or double-click to zoom, drag to move, Fit, its own rotation checkbox, Open PDF, close with × or Esc.

## s3
- `data/striping_review.csv`: every drawing with match confidence, notes, map link, and PDF link, worst first, plus empty columns for corrections. Linked from "Check matches."
- Corrections through `data/striping_overrides.csv` (same columns): `status` ok or exclude, and `fix_street` / `fix_from_street` / `fix_to_street`.
- "Step through" in Check matches: Prev / Next (or `[` / `]`) through low or medium matches; your place is remembered.
- Spelling fixes in file names can't add words to a street name ("Forest Hill" no longer becomes Forest Hill Path), except a missing middle initial.

## s2
- Preview rotation: the first cross street in the file name always points to the drawing's left edge. The earlier "keep it upright" flip put the wrong end first on many north-south streets.
- Hovering the picked diagram's preview shows it large.
- **Labels** toggle (ID and file name, zoom 14+, colored by confidence) and **Match quality** toggle (high teal, medium amber, low orange).
- "Check matches" lists diagrams not on the map, low, and medium confidence, with notes. Every picked diagram shows its confidence.
- The street part of a file name must name a real street on its own: "Forest Hill" no longer matches Hill St, "Islais creek_41,798" no longer matches 41st Ave. Handles "3_", "TI_", "YBI_" prefixes, "Formerly", "Sgt", and two streets joined with "&".
- Samples: render chosen diagrams at several sizes, viewable on `samples.html`.

## s1
- First version: streets with an SFMTA striping diagram in teal; hover shows the diagram's blocks and a preview turned to match the street; click picks it, with Open PDF, file details, other sheets in the set, and other diagrams covering that block. Search by street or ID; `#id=` links.
- `build_striping.py` parses SFMTA's file index and file names and matches each drawing to blocks; weekly refresh and change log.
