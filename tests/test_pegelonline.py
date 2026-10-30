import pandas as pd

from bodensee.ingest.pegelonline import merge_into_archive


def _frame(rows):
    df = pd.DataFrame(rows, columns=["timestamp", "level_cm"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


def test_merge_into_empty_archive_returns_new_data():
    new = _frame([("2026-10-01T00:00Z", 250.0)])
    assert merge_into_archive(None, new).equals(new)


def test_merge_is_idempotent():
    data = _frame([("2026-10-01T00:00Z", 250.0), ("2026-10-01T00:15Z", 251.0)])
    once = merge_into_archive(None, data)
    twice = merge_into_archive(once, data)
    assert twice.equals(once)


def test_overlap_prefers_new_value_and_keeps_order():
    archive = _frame([("2026-10-01T00:00Z", 250.0), ("2026-10-01T00:15Z", 999.0)])
    new = _frame([("2026-10-01T00:15Z", 251.0), ("2026-10-01T00:30Z", 252.0)])
    merged = merge_into_archive(archive, new)
    assert merged["level_cm"].tolist() == [250.0, 251.0, 252.0]
    assert merged["timestamp"].is_monotonic_increasing
