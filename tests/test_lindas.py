import pandas as pd
import pytest

from bodensee.ingest.lindas import parse_sparql_result


def _result(**values):
    row = {k: {"type": "literal", "value": v} for k, v in values.items()}
    return {"results": {"bindings": [row]}}


def test_parse_river_station_with_all_fields():
    df = parse_sparql_result(
        _result(time="2026-10-30T17:10:00+01:00", discharge="155.324", level="407.219", temp="9.51")
    )
    assert df["timestamp"].iloc[0] == pd.Timestamp("2026-10-30T16:10:00Z")
    assert df["discharge_m3s"].iloc[0] == 155.324
    assert df["water_temp_c"].iloc[0] == 9.51


def test_lake_station_without_discharge_gives_missing_value():
    df = parse_sparql_result(_result(time="2026-10-30T17:10:00+01:00", level="394.722"))
    assert df["water_level_m"].iloc[0] == 394.722
    assert pd.isna(df["discharge_m3s"].iloc[0])


def test_empty_result_raises():
    with pytest.raises(ValueError):
        parse_sparql_result({"results": {"bindings": []}})
