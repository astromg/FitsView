# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

FitsView is a PyQt5 desktop application for viewing FITS astronomical images. It displays the
image, a viewfinder/aperture window, a zoomable thumbnail, and supports marking points, reading
`daophot` output files (`.coo`, `.ap`, `.lst`, `.als`, `.out`, `.tfr`, `.rsl`), photometry
(background/zero-point/counts queries), column/line/radial profiles, isophote plotting, and frame
quality statistics (FWHM, ellipticity, sky gradient, line detection) via the `pyaraucaria` FFS
module.

## Commands

Dependencies are managed with Poetry.

```console
poetry install                 # install dependencies (uses poetry.lock)
poetry run FitsView file.fits  # run the app (entry point defined in pyproject.toml)
poetry run fv file.fits        # same, shorter alias
```

Run directly without Poetry's entry points:

```console
./fitsview/fitsview.py file.fits
./fitsview/fitsview.py file.fits 400 500   # open file and mark point at x=400,y=500
./fitsview/fitsview.py file.fits file.out  # open file and load all points from file.out
```

There is no test suite, linter, or CI configuration in this repo. `fitsview/test.py` (poetry
script `test`) is an ad hoc manual script that hardcodes a local data path
(`/Users/mgorski/work/data/fits_examples`) and exercises `pyaraucaria.ffs.FFS` — it is not an
automated test and will fail on another machine without that directory.

Packaging: `pipx install .` / `pipx reinstall fitsview`.

## Local dependency: pyaraucaria

`pyaraucaria` is declared in `pyproject.toml` as a local, editable path dependency
(`../pyaraucaria`), i.e. it is expected to live as a sibling directory to this repo, not to be
fetched from PyPI. The FFS (Frame Fits Statistics) integration (`FFS` class, used from the `s` key
handler in the image view) comes from `pyaraucaria.ffs`. If `pyaraucaria` is missing or its API
changes, the FFS-related features (`FitsView_widgets.FFSWindow`) will break independently of this
codebase.

## Architecture

The app has no automated entry-point routing beyond `fitsview/fitsview.py:main()`, which parses
`sys.argv` (a FITS filename, an optional coordinate/marker file, or `x y` point coordinates) and
drives a single `FitsView_gui.FitsView` widget (a `QWidget`, not `QMainWindow`).

Module breakdown:

- **`fitsview/fitsview.py`** — CLI entry point. Builds the `QApplication` and one `FitsView`
  widget, then interprets argv loosely (extension sniffing, not a real arg parser).
- **`fitsview/FitsView_gui.py`** — the main `FitsView` widget: overall UI layout, tab management
  (`TabWindow`, one tab per open FITS image), FITS loading (`getFits`/`newFits`), coordinate-file
  loading/listing, and the config system (`conf()` reads `FitsView.cfg` at startup; `Settings`
  is the config-editing dialog, written back via "Save CFG"/"Update CFG"). Also defines
  `Communicate` (Qt signals, notably `xPressed` for the "special/external" key hook), `HeaderTab`,
  and `HelpWindow`.
- **`fitsview/FitsView_image.py`** — the `Image` widget: the actual matplotlib canvas embedded per
  tab. Owns image display state (zoom, flip, rotate, colormap, clim/vmin/vmax, viewfinder
  aperture), marker lists (`int_x`/`int_y` for user-marked points, driven by the loaded coordinate
  table), and **`keypressed()`**, which is the dispatch table for all single-key interactions
  (`m` mark, `d` delete, `g` goto, `f` find, `b` background, `z` zero-point, `q` query/photometry,
  `c` column profile, `l` line profile, `e` ellipse/isophotes, `r` radial profile + Gaussian FWHM
  fit, `s` opens the FFS statistics window, `x` the special/external hook). Any new keyboard
  feature is added as another branch in `keypressed()`.
- **`fitsview/FitsView_widgets.py`** — secondary popup windows spawned from `Image`: `TextWindow`
  (short numeric results), `PlotWindow`/`FigureWindow` (profile and isophote plots), `FFSWindow`
  (frame-quality stats UI wrapping `pyaraucaria.ffs.FFS`: find stars, sky gradient check, line
  detection), and `HeaderTabLocal`.
- **`fitsview/FitsView_catalog.py`** — `Catalog` widget (table view of loaded coordinate/photometry
  data via `FitsTableModel`, a `QAbstractTableModel`) and `ColorButton` for per-catalog marker
  coloring; feeds the point overlays drawn in `Image`.
- **`fitsview/fv_lib.py`** — `daophot_files_parser(file_name)`: pure parsing of DAOPHOT-family
  text files (`.ap`, `.coo`, `.als`/`.out`, `.lst`) into `astropy.table.Table` objects, dispatched
  by file extension. Column semantics (id/x/y/mag/sky/etc.) are fixed per format and hardcoded
  here — this is the place to extend if a new DAOPHOT file variant needs support.
- **`fitsview/FitsView.cfg`** — the persisted user config (geometry, aperture size, background,
  zero-point, marker styles, header-keyword search lists for the header display, etc.), rewritten
  by the `Settings` dialog. Config keys are read as plain `key=value` lines and `eval()`'d for
  non-string types (tuples/lists/bools) — see `conf()` in `FitsView_gui.py`.
- **`fitsview/FitsView.hlp`** — help text shown by `HelpWindow`.

### Cross-cutting conventions

- Instrumental (pixel) coordinates are tracked separately from any display transform: flip/rotate
  only change what's rendered, never the underlying working coordinates used for
  marking/querying/photometry.
- The widget can be embedded in other PyQt scripts rather than run standalone — see the "Widget"
  section of `README.md` for the `FitsView_gui.FitsView(cfg)` embedding pattern, including the
  `special`/`xPressed` hook used to intercept a single key (`x`) for caller-defined behavior.
- Many identifiers and inline comments are in Polish (e.g. `dane`, `bledy`, `wartosc`,
  "wywalam naglowek"); this is original author terminology, not an artifact to clean up.
