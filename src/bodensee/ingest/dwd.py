"""Download daily weather observations for Konstanz from DWD open data.

DWD splits each station into two zip files:
  - historical/: quality-controlled, from 1959 up to the end of last year
  - recent/:     the last ~500 days, not yet fully quality-controlled
We download both and prefer `historical` where they overlap.

Usage:  python -m bodensee.ingest.dwd
"""

import io
import re
import zipfile

import pandas as pd
import requests

from bodensee import DATA_DIR

BASE_URL = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl"
STATION_ID = "02712"  # Konstanz
OUT_PATH = DATA_DIR / "raw" / "dwd" / f"daily_{STATION_ID}.parquet"

# DWD column code -> readable name. Full list in the DWD dataset description.
COLUMNS = {
    "MESS_DATUM": "date",
    "TMK": "temp_mean_c",
    "TXK": "temp_max_c",
    "TNK": "temp_min_c",
    "RSK": "precip_mm",
    "SDK": "sunshine_h",
    "SHK_TAG": "snow_depth_cm",
    "UPM": "humidity_pct",
    "PM": "pressure_hpa",
    "FM": "wind_mean_ms",
}


def _find_zip_url(folder: str) -> str:
    """File names contain the date range, so we look them up instead of hardcoding."""
    listing = requests.get(f"{BASE_URL}/{folder}/", timeout=30)
    listing.raise_for_status()
    match = re.search(rf'href="(tageswerte_KL_{STATION_ID}_[^"]+\.zip)"', listing.text)
    if not match:
        raise FileNotFoundError(f"No zip for station {STATION_ID} in {folder}/")
    return f"{BASE_URL}/{folder}/{match.group(1)}"


def parse_dwd_zip(content: bytes) -> pd.DataFrame:
    """Extract the `produkt_klima_tag_*.txt` file from a DWD zip and clean it."""
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        name = next(n for n in zf.namelist() if n.startswith("produkt_klima_tag"))
        raw = pd.read_csv(zf.open(name), sep=";", skipinitialspace=True)

    raw.columns = raw.columns.str.strip()  # DWD pads headers with spaces
    df = raw[list(COLUMNS)].rename(columns=COLUMNS)
    df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d")
    # DWD uses -999 as its "missing" marker. Left in, it would wreck any mean.
    return df.replace(-999, pd.NA)


def download() -> pd.DataFrame:
    frames = []
    for folder in ("historical", "recent"):  # order matters: historical first
        resp = requests.get(_find_zip_url(folder), timeout=120)
        resp.raise_for_status()
        frames.append(parse_dwd_zip(resp.content))

    df = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates(subset="date", keep="first")  # keep quality-controlled value
        .sort_values("date")
        .reset_index(drop=True)
    )
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PATH, index=False)
    return df


if __name__ == "__main__":
    df = download()
    print(f"{len(df)} days, {df.date.min().date()} -> {df.date.max().date()}")
    print(df.tail())
    print(f"Saved to {OUT_PATH}")
