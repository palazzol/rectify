# Rectify: session notes

Notes from working sessions on 2026-10-23, 2026-10-24, 2026-10-27 and 2026-10-30, so the work can be picked up again later.

## What the project is

Rectify is a PySide6 desktop app that prepares photos of PCBs for reverse engineering. You open a photo, place crosshair markers on features, and add constraints between them (horizontal, vertical, known distance). A solver then computes a transform that removes the photo's perspective.

**Current state:**
- **Working:** image viewing, markers, undo/redo, and project files.
- **Not done yet:** the constraint dialog is a layout mock-up with nothing wired up, the solvers aren't connected to the GUI, and nothing warps the image.
- **Git:** all work up to the solver matrix fix is committed on `main`, 3 commits ahead of `origin/main` and not pushed. The `project-files` and `fix-solver2-matrix` branches are merged and can be deleted.

**Running it:**
- Start it from the project root with `python src/rectify.py`. `config/config.ini` is found relative to the current directory, so starting from anywhere else silently falls back to default settings.
- Python 3.14 is needed. Several annotations only work because 3.14 evaluates them lazily (PEP 649).

## Code map

| File | Role |
|---|---|
| `src/rectify.py` | Entry point |
| `src/mainwindow.py` | Main window, menus, key handling (M = marker, C = constraint, Del/Backspace = delete), project open/save |
| `src/imageview.py` | `QGraphicsView`: zoom (wheel, steps of x1.25), pan (middle button), rubber-band select, marker create/delete/move as undoable actions |
| `src/marker.py` | `Marker` crosshair item. Pixmaps are drawn once from `config/config.ini`; it keeps a constant on-screen size and has a circular hit area |
| `src/constraint.py` | `ConstraintDialog`: layout only, not wired up |
| `src/undoredo.py` | Undo/redo built on actions: `undo()`, `redo()`, `clearHistory()`, `with undoContext("desc") as uctx: uctx.recordAction(fn, *args)`. Each action records its own inverse. Groups are separated by end marks |
| `src/project.py` | `.rct` project file format (`ProjectFile`, `MarkerData`) |
| `src/solver.py` | `SVDSolver`: linear fit from point pairs, pseudo-inverse, prefers zero perspective terms when the system is underdetermined |
| `src/solver2.py` | `NLLSSolver`: fits ΔX/ΔY constraints with `scipy.optimize.least_squares`. This matches what the constraint dialog asks for, and it is the one to use (see below) |
| `tools/makemarkers.py` | Script that tries out ways of drawing the crosshair |
| `old/gridit.py` | Old Tkinter prototype. It won't run against the current `undoredo`, and it is the only code that still imports `pynnex` |

Both solvers use the same model: similarity transform plus two perspective terms:
`X = (a·x + b·y + tx)/(1 + g·x + h·y)`, `Y = (−b·x + a·y + ty)/(1 + g·x + h·y)`.

The first parameter differs between them. In `solver`, `x[0]` is the difference from a scale of 1, so its matrix uses `x[0]+1`. In `solver2`, `x[0]` is the scale itself.

**Why `NLLSSolver` is the one to use:** distance constraints don't fix a world origin, and that freedom lets these six parameters represent any camera perspective that has some perspective in it. `SVDSolver` fits fixed world points, so it loses that freedom. On a simulated 100×80 mm board with 16 noise-free points, `NLLSSolver` fit to about 1e-13 mm up to 40° of tilt, while `SVDSolver` was off by 0.01 mm at 2°, 0.32 mm at 10° and 2.1 mm at 25°. Noisy marker clicks haven't been tested. Because of that same freedom, `tx` and `ty` from `NLLSSolver` are arbitrary, so the warp has to choose its own output offset.

## Changes made in these sessions

### 1. Fixed: pressing Delete with nothing selected broke undo for the session
- **Cause:** `ImageView.deleteSelection` returned early *inside* the `undoContext`. Closing the context then pushed an end mark with no actions in front of it, and `pushEndMark` raised. That error skipped the line that clears `insideContext`, so every later `undoContext` failed with "Nested UndoContext is not supported".
- **Fix:** `deleteSelection` now checks for an empty selection before it opens the context.
- **Safety net:** `_UndoRedoManager.exitContext` now resets `insideContext` in a `finally`, so a future mistake of this kind raises one error instead of breaking editing.

### 2. Added: project files (`.rct`)
- **Format:** a zip containing `project.json` (version, original image name, image member name, marker ids and positions) and the original image file, byte for byte, as `image.<format>` (e.g. `image.jpeg`). The member is named from the detected format, not the file name. Files that hold `image.png` still load, and are still version 1.
- **Saving** writes to a temporary file first, then swaps it in, so a failed save can't damage an existing project.
- **Loading** raises `ValueError` for files that aren't valid projects.
- **File menu:** Open Image (Ctrl+O), Open Project (Ctrl+P), Save Project (Ctrl+S), Save Project As (Ctrl+Shift+S). The window title shows the project name, or the image name plus "(unsaved)".
- **Opening an image now starts a new project:** it clears the markers. Opening an image or a project also clears the undo history.
- **New `ImageView` helpers:** `clearMarkers()`, `setMarkers()`, `markerData()`. They change markers without recording undo steps.
- **`Marker` ids:** creating a marker with a given id now moves `next_marker_id` past it, so new markers never reuse ids loaded from a file.
- **Tested headlessly** (`QT_QPA_PLATFORM=offscreen`): a save/load round trip restores the same ids, positions and pixels. After loading, undo history is empty and the next marker id follows on correctly. An invalid file gives a clear error. The real file dialogs were not clicked through.
- **Original image kept:** the project stores the original file's bytes instead of a PNG, because PNGs were far bigger (a 2.6 MB JPEG made a 9.9 MB project, and now makes a 2.6 MB one). `MainWindow` keeps the bytes in `_imageData` from the moment the image is opened, and `ProjectFile.pixmap()` decodes them. EXIF metadata is now kept too, including any GPS location, which matters when sharing project files.

### 3. Changed: solvers use Qt signals instead of `pynnex`
- `SVDSolver` and `NLLSSolver` are now `QObject`s with `Signal(object)` attributes. The names `emitcreateconstraint` and `emitdestroyconstraint` are unchanged.
- Both import without `pynnex`, and signals work without a `QApplication`, so the solvers can be used from scripts and tests.

### 4. Fixed: `solver2` returned the wrong matrix
- **Cause:** `T` added 1 to the diagonal, copied from `solver`, but `solver2` uses `x[0]` directly as the scale. The wrong matrix was returned as well as printed.
- **Result:** on the simulated board, the error using `T` as returned went from 410 mm to about 5e-14 mm at 10° of tilt. It stays below 1e-13 mm at every tilt tested, up to 40°.

## Known problems still open

1. **An exception inside an undo context corrupts the stacks.** Actions recorded before the error stay on the stack with no end mark, so the next group absorbs them. The code marks this as `# TBD - rollback?`. Possible fix: note the stack length in `enterContext`; on an exception, run and drop the actions recorded after that point.
2. **An exception during undo or redo leaves undo broken.** The mode stays `UNDOING` or `REDOING`, so later actions land on the wrong stack. `undoOrRedo` needs a `try/finally`. Nothing triggers this today unless an action fails.
3. **An empty undo group on an empty stack makes undo raise.** The guard in `pushEndMark` only checks a non-empty stack. Nothing in the app does this today, as `deleteSelection` checks first.
4. **`NLLSSolver` ignores constraint weights.**
5. **`SVDSolver` has smaller faults:**
   - Its pseudo-inverse doesn't zero singular values below the rank threshold. It leaves them as they are; the effect is negligible.
   - It raises `ValueError` when it has no constraints.
   - 11 lines assign one-element arrays to scalars, which NumPy says will become an error.
6. **Packaging gaps:**
   - `numpy` is only installed indirectly, through scipy.
   - `README.md`, which `pyproject.toml` refers to, doesn't exist.
   - `Marker._initPixmaps` saves debug PNGs to `images/`, which doesn't exist, so the saves fail silently.
   - There is no LICENSE file, and `mainwindow.py` and `imageview.py` come from CC BY-SA 4.0 code.
7. **Broken `.venv/bin/mypy` launcher.** Its shebang points to an old path. `python -m mypy` works; `uv sync` should fix the launcher.
8. **Existing mypy errors:**
   - `marker.py` has 6: `QPainter.Antialiasing` should be `QPainter.RenderHint.Antialiasing`, and the class attribute `offset` hides `QGraphicsPixmapItem.offset()`.
   - `solver2.py` has 1: there are no type stubs for scipy. Adding `scipy-stubs` as a dev dependency should clear it.
9. **Markers can land off the image.** M doesn't check for a loaded photo or the cursor position, and off-image markers on a loaded photo would be saved in the project.
10. **EXIF rotation is ignored.** `QPixmap` doesn't apply it, so `testimages/image1.jpg` shows rotated 180°.
11. **Smaller things:**
    - Resizing the window resets the zoom.
    - Copy, Paste and About in the menus aren't connected to anything.
    - The coordinate display is commented out.
    - `mainwindow` uses the private `viewer._scene`.
    - `Action.__init__` has the wrong type hints.
    - `ConstraintDialog`'s OK and Cancel do nothing; only Esc or closing the window dismisses it.
    - C works with two or more markers selected, but ΔX/ΔY only has a clear meaning for a pair.
    - From reading the code, not tested: holding M probably creates repeated markers on platforms that send key releases during auto-repeat, and clicking a hovered marker drops its hover look until the pointer re-enters.
12. **Project files:**
    - Nothing asks about unsaved changes before closing or opening another file. This could be tracked through the undo system.
    - Loading valid JSON that isn't an object raises `AttributeError`, which skips the error dialog.
    - `handleOpenProject` doesn't update `_path`, which is only used as the Open Image dialog's starting folder.
    - An image format Qt can only recognise by its extension is refused at Open Image, because formats are detected from the file's contents.

## Likely next steps

- Wire up `ConstraintDialog` to create ΔX/ΔY constraints between the selected markers.
- Save constraints in the project file. This needs a format version bump.
- Feed the constraints to `NLLSSolver`, then warp the image with the resulting transform. Nothing does the warp yet.
- Fix the open problems above, starting with undo rollback (1, 2) and packaging (6).
