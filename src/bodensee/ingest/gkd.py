"""Load daily lake data for Lindau downloaded by hand from GKD Bayern.

GKD has no public API, so the CSV exports are downloaded manually from
gkd.bayern.de and dropped into data/raw/gkd/. This module combines all of them
(full history + newer partial downloads) into one clean parquet file per variable.

GKD CSV format: ~9 metadata lines, a title line such as
"Tageswerte Wasserstand [m ü. NN]", then a ';'-separated table with German
decimal commas and a Prüfstatus column (Geprueft = checked, Rohdaten = raw).

Usage:  python -m bodensee.ingest.gkd
"""

from pathlib import Path

import pandas as pd

from bodensee import DATA_DIR

GKD_DIR = DATA_DIR / "raw" / "gkd"

# Title line in the CSV -> output name
VARIABLES = {
    "Wasserstand": "water_level_m",
    "Wassertemperatur": "water_temp_c",
}


def parse_gkd_csv(path: Path) -> tuple[str, pd.DataFrame]:
    """Return (variable name, DataFrame with date, mean, max, min, checked)."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()  # -sig strips the BOM
    header_idx = next(i for i, line in enumerate(lines) if line.startswith("Datum;"))
    title = lines[header_idx - 1]
    variable = next((name for key, name in VARIABLES.items() if key in title), None)
    if variable is None:
        raise ValueError(f"Unknown GKD variable in {path.name}: {title!r}")

    df = pd.read_csv(path, sep=";", decimal=",", skiprows=header_idx, encoding="utf-8-sig")
    df.columns = ["date", "mean", "max", "min", "status"]
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df["checked"] = df.pop("status").eq("Geprueft")
    # GKD stores some gaps (e.g. 1895, 1945, 1947) as mean=0 with empty max/min.
    # Plain "0 = missing" would be wrong for temperature, where 0 °C is real.
    gap = df["mean"].eq(0) & df["max"].isna() & df["min"].isna()
    # A daily mean outside [min, max] is impossible (seen on the first day of a gap)
    inconsistent = (df["mean"] < df["min"]) | (df["mean"] > df["max"])
    df.loc[gap | inconsistent, "mean"] = float("nan")
    return variable, df


def combine(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Merge overlapping downloads. Per day, a checked value beats a raw one."""
    combined = pd.concat(frames, ignore_index=True)
    return (
        combined.sort_values(["date", "checked"])  # False before True ...
        .drop_duplicates(subset="date", keep="last")  # ... so a checked row wins
        .reset_index(drop=True)
    )


def build(gkd_dir: Path = GKD_DIR) -> dict[str, pd.DataFrame]:
    by_variable: dict[str, list[pd.DataFrame]] = {}
    for path in sorted(gkd_dir.glob("*.csv")):
        variable, df = parse_gkd_csv(path)
        by_variable.setdefault(variable, []).append(df)

    results = {}
    for variable, frames in by_variable.items():
        df = combine(frames)
        df.to_parquet(gkd_dir / f"lindau_{variable}.parquet", index=False)
        results[variable] = df
    return results


if __name__ == "__main__":
    for variable, df in build().items():
        print(f"{variable}: {len(df)} days, {df.date.min().date()} -> {df.date.max().date()}, "
              f"{(~df.checked).sum()} raw (unchecked) days")
