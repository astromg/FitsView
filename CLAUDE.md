# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

FitsView is a PyQt6 desktop application for viewing FITS astronomical images. It displays the
image, a viewfinder/aperture window, a zoomable thumbnail, and supports marking points, reading
`daophot` output files (`.coo`, `.ap`, `.lst`, `.als`, `.out`, `.tfr`, `.rsl`), photometry
(background/zero-point/counts queries), column/line/radial profiles, isophote plotting, and frame
quality statistics (FWHM, ellipticity, sky gradient, line detection) via the `pyaraucaria` FFS
module.

## Commands

Dependencies are managed with Poetry.

```console
poetry install                 # install dependencies (poetry.lock is gitignored)
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

## Qt: PyQt6 through PyQtX (2026-11-11)

FitsView is on PyQt6, like TOI (needed to embed it in TOI later: PyQt5 and PyQt6 cannot share one process).
- All Qt imports go through `fitsview/PyQtX` (`from fitsview.PyQtX.QtWidgets import ...`,
  `from fitsview.PyQtX import QtCore, QtGui`) — a verbatim copy of TOI's `PyQtX/` (PyQt6, else PyQt5, plus aliases of
  some short Qt5 enum names). Keep the `Qt*.py` files identical to TOI's, so they can later move to a shared module;
  do not add aliases there.
- Write enums with their full names (`Qt.WindowType.Tool`, `Qt.CheckState.Checked`, `QSizePolicy.Policy.Expanding`,
  `QAbstractItemView.EditTrigger.NoEditTriggers`) — they work in both PyQt5 5.15 and PyQt6. Use `exec()`, not `exec_()`.
- Use `checkbox.isChecked()`, never `if checkbox.checkState():` — in PyQt6 enum members are always truthy.
- Import PyQtX **before** any `matplotlib.backends.backend_qtagg` import: matplotlib picks the Qt binding that is
  already imported (the pipx venv may still contain PyQt5). Use `backend_qtagg`, not `backend_qt5agg`.
- `fitsview.py:setup_qt()` (standalone only): forces `QT_QPA_PLATFORM=xcb` on Wayland (as TOI does — native
  Wayland ignores window positioning, `fv_windows.place_window`) and enables HiDPI scaling when running on Qt5.

## Theme (2026-11-11)

TOI's themes: `fitsview/toi_theme.py` is a copy of TOI's `toi_theme.py` (only the PyQtX imports changed; keep it in
sync, later a shared module). `fitsview/fv_theme.py` wraps it: choice in Configuration → Theme, stored in
`QSettings("OCA","FitsView")/theme`; default `"toi"` = the theme TOI uses (`QSettings("OCA","TOI")/theme`, read at
start). FitsView never writes TOI's setting. Colours via `theme.c(key)` / `theme.qcolor(key)` with TOI's semantic keys;
matplotlib figures via `theme.style_figure(fig, axes)`; `axes.clear()` resets the axes facecolor, so set
`theme.bg()` after it. Widgets with figures implement `style_theme()`; `FitsView.apply_theme()` (registered with
`theme.on_change`) calls it on tabs and `active_windows`. Image colormaps are not themed.

## Panels and docking (2026-11-11)

Helper windows (Query, Profile, Radial profile, Isophotes, FFS, Header, Figure, Configuration, Help) are "panels"
(`fitsview/fv_windows.py`):
- In a constructor call `init_panel(self, anchor, kind, title, w, h, dy)` (never `place_window` + `show()`); show with
  `show_panel(win)`, close with `close_panel(win)` (never `self.show()` / `self.close()` / `raise_()`).
- **Docking is optional, off by default** (2026-11-11: on a laptop screen docks only took space from the image).
  Configuration → "Dock panels in the main window (after restart)" = `QSettings("OCA","FitsView")/docking`;
  `fitsview.py` then builds `FitsViewWindow`, otherwise a plain `FitsView` with panels as separate windows.
- With docking, `FitsViewWindow` holds one `QDockWidget` per kind (`PANELS`, all created hidden at start so the saved
  layout covers every kind). A new widget of the same kind (new frame, other cube plane) replaces the dock's widget;
  the old one becomes a hidden parentless window and returns to the dock when `show_panel`'d again.
- Layout and window geometry are saved on close in `QSettings("OCA","FitsView")` (`dock_state`, `window_geometry`).
- Embedded (no `FitsViewWindow`): panels are ordinary windows placed by `place_window`.
- **Gotcha:** these classes set `self.parent = <Image>`, shadowing `QWidget.parent()` — use `parentWidget()`.
- `FitsView` sets titles via `self.window().setWindowTitle(...)` and closes via `self.window().close()`.

## FFS "Run fast" (calc_frame_fwhm as TOI), column range and sorting in tables (2026-11-11)

- **No separate drawing mechanisms** (mgorski): results are marked only through the existing ones — catalog tables
  (`Catalog` → markers / segments in `ImageView.update_points`), masks, maps.
- Catalog tables have a **range of the "color" column**: two sliders (min, max) with edit fields and an "outside"
  checkbox. Objects outside the range are not drawn (markers, segments; the `f` key skips them); in the table they are
  greyed (`muted_fg`) and moved to the end (`FitsTableModel.set_active`, stable after the current sort). Stored in
  the `table_data` entry as `mask`, `range`, `outside`; full range (and not outside) = `mask None`.
- Click a column header to sort: `FitsTableModel` keeps a permutation (`order`/`inverse`, `sort_key`); the table,
  `selected_index` and drawing stay in data order; the row header shows the data row number.
- `add_coo(..., preset={"marker", "mksize", "valuecol", "range", "outside"})` presets a new table's Catalog settings
  (kept on replacement). Markers "open circle" and "open square" are drawn hollow.
- Marker **"whisker (ellipticity, theta)"** (offered only for tables with `ellipticity` and `theta`, e.g. `ffs.stars`):
  a headless `quiver` through each object along theta (FFS convention, x = column; `angles="xy"` so flips need no
  redraw), length = e x `WHISKER_FRAC` (0.2) of the visible axes width (as TOI; constant under zoom), Size = line
  thickness (Size x `WHISKER_PT` pt). Colour/range as other markers.
- Markers coloured by the "color" column use `FitsView_image.VALUE_CMAP`: two colours, blue (min) → red (max), via
  purple, no white middle (viridis was too many hues and its dark end vanished on the image). Maps keep their own cmap.
- `fitsview/fv_toi.py`: TOI's FFS call (`calc_frame_fwhm(threshold=10, fwhm=5, box=15, N_stars=50)`,
  `sky_gradient(n_segments=7)`, `calc_star_field_stats()`, saturation by `TELESCOP`: jk15 150000, else 45000), the
  TOI-panel summary text, and `views()`: the star table shown twice with a preset range as TOI marks them
  (`stars rejected` — color `shape`, range 0.55–0.95, outside, open squares; `stars saturated` — color `max_adu`,
  range from the saturation up, open circles). Lines use the normal `ffs.lines` table. The "Run fast" button (next to "Run all"; earlier "TOI run", "calc_frame_fwhm") runs it
  on the whole frame. Keep constants in sync with TOI `fits_gui.py` by hand.

## Maps: value label, colour range, psf field (2026-11-13)

- The label after the coordinates shows the current tab's value: `ImageView.value_text` (FITS `%d`, `MapTab` `%.4g`,
  `MaskTab` True/False).
- Min/max sliders are integer; colour = slider position x `clim_step` (`ImageView.clim()`; FITS 1, `MapTab.clim_auto`
  picks a power of 10 for 1000-10000 steps). Read the range through `clim()`, never `min_s.value()` directly.
- `add_map(..., cmap=None)`: default colormap of a map tab (`psf_theta` -> cyclic `twilight`).
- FFS product type `field`, `psf field` (tab `ffs.psf field`): the `psf_ellipticity` map with the `psf grid` table's
  lines over it (catalog tables draw on all image tabs — no own drawing). Lines without heads: ellipticity is an axis.

## Browsing and keys (2026-11-13)

- `FitsView.fits_list()` = full paths: `browse_files` (`fv *.fits`, files dropped on the window) or the FITS
  (`is_fits_name`, `FITS_EXT`) in `fits_directory` = the directory of the current file (set in `newFits`), without
  `*_ffs.fits` (Save MEF). `browse(step | to)` (← → Home End, buttons) calls `newFits(keep_view=True)`: zoom and centre
  stay when the new frame has the same shape. Window title = `title()` (file + position `(i/n)`).
- Navigation keys are handled first in `ImageView.keypressed`: "right", "home", "end", "escape" contain letters of
  other functions, which are tested with `"x" in event.key`.
- Esc: `fv_windows.close_last_panel()` (order kept by `show_panel`); `init_panel` adds an Esc shortcut to each panel.
  `?` shows `KEYS_HELP` as a tooltip. Mouse wheel zooms on the thumbnail too (`mouse_scroll`, same coordinates).
- Exceptions in Qt event handlers (e.g. `dropEvent`) abort the program in PyQt6 — catch them and show `errmssg`.
- One entry for files: `FitsView.open_files(paths)` ("Open..." `open_dialog`, `dropEvent`, command line).
  `file_kind(path)` (headers only): FITS with a 2D/3D image HDU -> "image" (new frame; several -> `browse_files`),
  anything else (daophot, text, FITS with tables only) -> "table" (`load_coo` on the current frame). The combo
  `coo_l` lists non-FITS files with the frame's name and loads on `activated`. Old "Load FITS" / "Load COO" are gone
  (`load_fits` kept as an alias of `open_dialog`). `_ffs.fits` (Save MEF) counts as an image for now.
- FFS window: tables are shown after a run through `FFSWindow.auto_show` - an empty table gets no tab (its old tab
  is hidden); "Run fast" also opens the full `ffs.stars` table next to the TOI views.
- `newFits` drops everything of the previous frame: `table_data` (coo, FFS tables), `map_data`, `mask_data`, the
  view (unless `keep_view`), and closes the old FFS window (its "Show" would add old products to the new frame).

## Keys e and r: star measurement as FFS (2026-11-13)

- `fitsview/fv_star.py`: `measure_star(dane, x, y, search, box=10, saturation)` = the recipe of `FFS.star_info` for one
  star (brightest pixel within `search`, cut-out +-box, background = median of the border, FFS.fwhm / adaptive_moments
  (pca fallback) / cpe / concentration_index) — only FFS static methods, no pyaraucaria changes; keep in sync with
  `star_info` by hand. Verified: same FWHM, e, theta, CPE, CI as the FFS stars table.
- `e` (`ImageView.draw_isophotes`): cut-out in screen orientation (rot90 as `to_screen`: X = y, Y = nx-1-x; flips via
  limits), asinh scale, isophotes 10/25/50/75/90 % of the peak above background + 3 sigma, FWHM ellipse from moments
  (`fv_star.moment_axes`), numbers as the x label (a box on the image covered the cut-out).
- Result panels (Query, Profile, Radial, Isophotes) show through `fv_windows.show_keep_focus(win, anchor)`: focus
  back to the image, then the panel is raised again — a plain `activateWindow()` put the main window over panels
  that overlap it (small screen), so plots were computed but hidden.
- `c` / `l` mark the column / row with `ImageView.profile_line` (original coordinates), drawn by
  `draw_profile_line` inside `update_points` while the profile panel is visible. Anything drawn on `self.axes` in
  `update()` is lost: `update_points` removes all lines and collections first.
- `m` adds a row (id, x, y, counts) to the catalog table `marked` (`FitsView.mark_point`, `add_coo(..., redraw=False)`:
  overlays only); `d` deletes the nearest point of `marked` or of the measurement markers `int_x`/`int_y`
  (`unmark_point`); an empty `marked` is hidden. `int_x`/`int_y` and `ext_x`/`ext_y` are drawn by
  `draw_int_points` inside `update_points` (drawn in `update()` they vanished, as the `c`/`l` line did).
- `r`: Gaussian fit started from the data (peak - bkg, FWHM(FFS)/2.355, bkg), failure handled; FFS FWHM shown too.

## Local dependency: pyaraucaria

`pyaraucaria` is declared in `pyproject.toml` as a git dependency on its `master`
(`{git = "https://github.com/araucaria-project/pyaraucaria.git"}`, as in TOI; since 2026-11-13, before it was the path
`../pyaraucaria`). `poetry.lock` is gitignored, so every install takes the current `master`. The FFS (Frame Fits Statistics) integration (`FFS` class, used from the `s` key
handler in the image view) comes from `pyaraucaria.ffs`. If `pyaraucaria` is missing or its API
changes, the FFS-related features (`FitsView_widgets.FFSWindow`) will break independently of this
codebase.

The pipx install (`fv`, `FitsView`) holds **copies**: FitsView from the working tree, pyaraucaria from GitHub
`master` — FFS changes reach `fv` only after they are pushed to pyaraucaria `master` and `pipx install --force .`.
To test unpushed FFS changes (e.g. on `mgorski_dev`), run from source with `PYTHONPATH=.:../pyaraucaria`.

### FFT (Fourier) is FitsView's, not FFS's (2026-11-08)
FFS (`pyaraucaria.ffs`) is developed by hand by its author and holds only frame statistics, stars,
lines, masks and maps. Do not add viewer-only features to it. The power spectrum was once added
to FFS as `FFS.power_spectrum` without agreement and was removed; it now lives in FitsView:

- `FitsView_widgets.power_spectrum(ffs, window=True, min_freq=0.02, exclude=FFS.EXCLUDE_ALL)` — a
  plain function that only reads the FFS object (`ffs.image`, `ffs.maps["sky"]` if present,
  `ffs.bad_mask(exclude)`): residual = image − sky, bad pixels set to 0, optional 2D Hann window,
  `fftshift(fft2)`, power = |F|² / N. Returns `(log10 power, {"period", "angle", "peak"})` — the
  strongest peak with frequency ≥ `min_freq`: period in px, angle of the wave vector in degrees
  (stripes are perpendicular), peak / median power (noise ~20, a clear pattern 10³–10⁴).
- `FFSWindow` keeps the result in `self.fourier` / `self.fft_peak` (cleared by `reset_ffs` and when
  the product is removed), not on the FFS object. The "Fourier" button and the "FFT" parameter
  tab work like the FFS stages: the parameter fields come from the function's signature and
  numpydoc docstring (`mk_params` skips the first argument, here `ffs`).
- Product type `fft`, tab `ffs.fourier`: the spectrum has the cut-out size but is **not** in image
  coordinates (offset (dx, dy) from the centre = frequency (dx/nx, dy/ny) cycles/px), so it is shown
  with `add_map(..., frame=False)` (no `full_frame`; `MapTab.update_points` draws no overlays).
- Not part of "Run all" and not saved in the MEF (`FFS.save_mef` knows only FFS products).

## Architecture

The app has no automated entry-point routing beyond `fitsview/fitsview.py:main()`, which parses
`sys.argv` (a FITS filename, an optional coordinate/marker file, or `x y` point coordinates) and
drives a `FitsView_gui.FitsView` widget (a `QWidget`, embeddable e.g. in TOI); with the optional docking it sits
inside `FitsView_gui.FitsViewWindow` (`QMainWindow`).

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
  detection; plus FitsView's own `power_spectrum`, see "FFT (Fourier) is FitsView's, not FFS's"),
  and `HeaderTabLocal`.
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
