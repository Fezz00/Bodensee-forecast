import pandas as pd

from bodensee.ingest.gkd import combine, parse_gkd_csv

# Same layout as a real GKD export: metadata, blank line, title, table
SAMPLE = """﻿Quelle:;"Bayerisches Landesamt für Umwelt, www.gkd.bayern.de"
Datenbankabfrage:;"24.10.2026 00:01"
Zeitbezug:;MEZ
Messstellen-Name:;Lindau
Messstellen-Nr.:;20001001
Gewässer:;Bodensee
Ostwert:;551542;Nordwert:;5265912;"ETRS89 / UTM Zone 32N"
Pegelnullpunktshöhe:;"391,84 m NHN (DHHN2016)"

"Tageswerte Wasserstand [m ü. NN]"
Datum;Mittelwert;Maximum;Minimum;Prüfstatus
2026-10-29;394,37;394,38;394,36;Geprueft
2026-10-30;394,37;394,38;394,36;Rohdaten
2026-10-31;0,00;;;Geprueft
2026-11-01;0,00;394,50;394,50;Geprueft
"""


def test_zero_with_empty_max_min_is_a_gap(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_text(SAMPLE, encoding="utf-8")
    _, df = parse_gkd_csv(path)
    assert pd.isna(df["mean"].iloc[2])


def test_mean_outside_min_max_is_invalid(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_text(SAMPLE, encoding="utf-8")
    _, df = parse_gkd_csv(path)
    assert pd.isna(df["mean"].iloc[3])


def test_parse_reads_german_decimals_and_status(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_text(SAMPLE, encoding="utf-8")
    variable, df = parse_gkd_csv(path)
    assert variable == "water_level_m"
    assert df["mean"].tolist()[:2] == [394.37, 394.37]
    assert df["checked"].tolist() == [True, False, True, True]


def test_combine_prefers_checked_value():
    raw = pd.DataFrame({"date": pd.to_datetime(["2026-10-29"]), "mean": [999.0], "checked": [False]})
    checked = pd.DataFrame({"date": pd.to_datetime(["2026-10-29"]), "mean": [394.37], "checked": [True]})
    # Order of the inputs must not matter
    for frames in ([raw, checked], [checked, raw]):
        assert combine(frames)["mean"].tolist() == [394.37]
