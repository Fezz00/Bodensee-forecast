"""Archive live hydro data from BAFU via LINDAS (Swiss linked open data).

LINDAS only exposes the *latest* observation per station (updated every 10 min),
so like Pegelonline we poll it regularly and append to a local archive.

Stations:
  2473 Diepoldsau, Alpine Rhine just before it enters the lake (main inflow)
  2032 Romanshorn, lake level on the Swiss shore

Usage:  python -m bodensee.ingest.lindas
"""

import pandas as pd
import requests

from bodensee import DATA_DIR
from bodensee.ingest.pegelonline import merge_into_archive

SPARQL_ENDPOINT = "https://ld.admin.ch/query"
ARCHIVE_DIR = DATA_DIR / "raw" / "lindas"

# station id -> kind ("river" or "lake" is part of the observation URI)
STATIONS = {"2473": "river", "2032": "lake"}

QUERY = """
PREFIX dim: <https://environment.ld.admin.ch/foen/hydro/dimension/>
SELECT ?time ?discharge ?level ?temp WHERE {{
  <https://environment.ld.admin.ch/foen/hydro/{kind}/observation/{station}> dim:measurementTime ?time .
  OPTIONAL {{ <https://environment.ld.admin.ch/foen/hydro/{kind}/observation/{station}> dim:discharge ?discharge }}
  OPTIONAL {{ <https://environment.ld.admin.ch/foen/hydro/{kind}/observation/{station}> dim:waterLevel ?level }}
  OPTIONAL {{ <https://environment.ld.admin.ch/foen/hydro/{kind}/observation/{station}> dim:waterTemperature ?temp }}
}}
"""

# SPARQL variable -> our column name
FIELDS = {"discharge": "discharge_m3s", "level": "water_level_m", "temp": "water_temp_c"}


def parse_sparql_result(result: dict) -> pd.DataFrame:
    """Turn a SPARQL JSON result into a one-row DataFrame (timestamp in UTC)."""
    bindings = result["results"]["bindings"]
    if not bindings:
        raise ValueError("No observation returned")
    row = bindings[0]  # LINDAS keeps only the latest observation -> one row
    record = {"timestamp": pd.to_datetime(row["time"]["value"], utc=True)}
    for var, column in FIELDS.items():
        record[column] = float(row[var]["value"]) if var in row else None
    return pd.DataFrame([record])


def fetch_latest(station: str) -> pd.DataFrame:
    query = QUERY.format(kind=STATIONS[station], station=station)
    resp = requests.post(
        SPARQL_ENDPOINT,
        data={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        timeout=30,
    )
    resp.raise_for_status()
    return parse_sparql_result(resp.json())


def update_archives() -> dict[str, pd.DataFrame]:
    results = {}
    for station in STATIONS:
        path = ARCHIVE_DIR / f"{station}.parquet"
        archive = pd.read_parquet(path) if path.exists() else None
        merged = merge_into_archive(archive, fetch_latest(station))
        path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_parquet(path, index=False)
        results[station] = merged
    return results


if __name__ == "__main__":
    for station, df in update_archives().items():
        print(f"{station}: {len(df)} rows, latest:\n{df.tail(1).to_string(index=False)}\n")
