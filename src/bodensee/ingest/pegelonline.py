"""Archive the Konstanz water level from Pegelonline.

Pegelonline only keeps ~31 days of 15-minute data. To build our own history we
fetch that window regularly and *merge* it into a local parquet archive. Running
this at least every few weeks means we never lose data; running it daily is safer.

Usage:  python -m bodensee.ingest.pegelonline
"""

from pathlib import Path

import pandas as pd
import requests

from bodensee import DATA_DIR

BASE_URL = "https://www.pegelonline.wsv.de/webservices/rest-api/v2"
STATION = "KONSTANZ"
TIMESERIES = "W"  # W = Wasserstand (water level), in cm above gauge zero
ARCHIVE_PATH = DATA_DIR / "raw" / "pegelonline" / f"{STATION.lower()}_{TIMESERIES}.parquet"


def fetch_measurements(period: str = "P31D") -> pd.DataFrame:
    """Fetch the last `period` (ISO-8601 duration) of measurements.

    Returns a DataFrame with a UTC `timestamp` and `level_cm`.
    """
    url = f"{BASE_URL}/stations/{STATION}/{TIMESERIES}/measurements.json"
    resp = requests.get(url, params={"start": period}, timeout=30)
    resp.raise_for_status()

    df = pd.DataFrame(resp.json())
    # The API returns local time with offsets (+01:00 / +02:00). Converting to UTC
    # gives one unambiguous timeline across the DST switch.
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df.rename(columns={"value": "level_cm"})[["timestamp", "level_cm"]]


def merge_into_archive(archive: pd.DataFrame | None, new: pd.DataFrame) -> pd.DataFrame:
    """Combine old archive and fresh data. Idempotent: running twice adds nothing.

    On overlapping timestamps the *new* value wins, because the authority may
    correct raw data after the fact.
    """
    if archive is None or archive.empty:
        combined = new
    else:
        combined = pd.concat([archive, new], ignore_index=True)
    return (
        combined.drop_duplicates(subset="timestamp", keep="last")
        .sort_values("timestamp")
        .reset_index(drop=True)
    )


def update_archive(path: Path = ARCHIVE_PATH) -> pd.DataFrame:
    archive = pd.read_parquet(path) if path.exists() else None
    merged = merge_into_archive(archive, fetch_measurements())
    path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(path, index=False)
    return merged


if __name__ == "__main__":
    df = update_archive()
    print(f"Archive: {len(df)} rows, {df.timestamp.min()} -> {df.timestamp.max()}")
    print(f"Saved to {ARCHIVE_PATH}")
