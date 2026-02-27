# How to Process Multiple .inp Files

This guide shows how to run OpenCoulomb over many input files — either with
shell scripting or the Python API.

## Shell loop (bash)

Process every `.inp` file in a directory and write outputs to a parallel
`results/` tree:

```bash
#!/usr/bin/env bash
set -euo pipefail

INPUT_DIR="./models"
OUTPUT_DIR="./results"

for inp in "$INPUT_DIR"/*.inp; do
    stem=$(basename "$inp" .inp)
    out="$OUTPUT_DIR/$stem"
    echo "Processing $stem ..."
    opencoulomb compute "$inp" -o "$out"
done

echo "All done."
```

Run it:

```bash
bash process_all.sh
```

## Shell loop with error handling

Continue even if one file fails, and log errors to a file:

```bash
#!/usr/bin/env bash
INPUT_DIR="./models"
OUTPUT_DIR="./results"
ERRORS="./errors.log"

> "$ERRORS"   # clear log

for inp in "$INPUT_DIR"/*.inp; do
    stem=$(basename "$inp" .inp)
    out="$OUTPUT_DIR/$stem"
    if opencoulomb compute "$inp" -o "$out" 2>>"$ERRORS"; then
        echo "OK:   $stem"
    else
        echo "FAIL: $stem  (see errors.log)"
    fi
done
```

## Validate before computing

Pre-screen all files to catch problems early:

```bash
for inp in models/*.inp; do
    echo "--- $(basename $inp) ---"
    opencoulomb validate "$inp"
done
```

## Python: process a list of files

```python
from pathlib import Path
from opencoulomb.io import read_inp, write_csv, write_dcff_cou
from opencoulomb.core import compute_grid

def process(inp_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    model = read_inp(inp_path)
    result = compute_grid(model)
    write_csv(result, output_dir / f"{inp_path.stem}.csv")
    write_dcff_cou(result, model, output_dir / f"{inp_path.stem}_dcff.cou")

models = Path("models")
for inp in sorted(models.glob("*.inp")):
    print(f"Processing {inp.name} ...")
    try:
        process(inp, Path("results") / inp.stem)
    except Exception as exc:
        print(f"  ERROR: {exc}")
```

## Python: parallel processing

For large batches, use `concurrent.futures` to run on multiple CPU cores:

```python
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from opencoulomb.io import read_inp, write_csv
from opencoulomb.core import compute_grid

def process_one(inp_path: Path) -> str:
    model = read_inp(inp_path)
    result = compute_grid(model)
    out = Path("results") / inp_path.stem
    out.mkdir(parents=True, exist_ok=True)
    write_csv(result, out / f"{inp_path.stem}.csv")
    return inp_path.name

files = list(Path("models").glob("*.inp"))

with ProcessPoolExecutor(max_workers=4) as pool:
    futures = {pool.submit(process_one, f): f for f in files}
    for future in as_completed(futures):
        try:
            name = future.result()
            print(f"Done: {name}")
        except Exception as exc:
            print(f"FAIL: {futures[future].name}: {exc}")
```

## Python: collect summary statistics

Gather peak CFS across many models:

```python
import csv
from pathlib import Path
import numpy as np
from opencoulomb.io import read_inp
from opencoulomb.core import compute_grid

rows = []
for inp in sorted(Path("models").glob("*.inp")):
    model = read_inp(inp)
    result = compute_grid(model)
    cfs = result.cfs
    rows.append({
        "file": inp.name,
        "title": model.title,
        "cfs_max_bar": float(np.nanmax(cfs)),
        "cfs_min_bar": float(np.nanmin(cfs)),
        "cfs_mean_bar": float(np.nanmean(cfs)),
    })

with open("summary.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote summary.csv with {len(rows)} models")
```

## Generating plots for all models

```bash
for inp in models/*.inp; do
    stem=$(basename "$inp" .inp)
    opencoulomb plot "$inp" -o "plots/${stem}_cfs.png" --dpi 150
done
```

Or limit color scale uniformly across all plots for comparison:

```bash
for inp in models/*.inp; do
    stem=$(basename "$inp" .inp)
    opencoulomb plot "$inp" -o "plots/${stem}.png" --vmax 1.0 --dpi 150
done
```

## Tips

- **Validate first** — run `validate` on all files before a big batch to catch
  parse errors early.
- **Consistent output naming** — use `inp.stem` as the output directory name
  so outputs are easy to match back to inputs.
- **Memory** — each `compute_grid` call holds the full result in memory. For
  very large grids (>500k points), process files sequentially rather than
  in parallel to avoid OOM.
