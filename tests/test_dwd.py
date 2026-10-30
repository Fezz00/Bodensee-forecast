import io
import zipfile

from bodensee.ingest.dwd import parse_dwd_zip

# Two rows in DWD's real format: padded headers, ';' separator, -999 = missing
SAMPLE = """STATIONS_ID;MESS_DATUM;QN_3;  FX;  FM;QN_4; RSK;RSKF; SDK;SHK_TAG;  NM; VPM;  PM; TMK; UPM; TXK; TNK; TGK;eor
       2712;20250101;   10;  -999;   2.1;    3;   1.2;   6;   0.5;   0;   7.0;   6.1; 970.1;   2.3;  85.0;   4.0;   0.1;  -1.0;eor
       2712;20250102;   10;  -999;   3.0;    3;  -999;   6;   1.0;   2;   6.0;   5.9; 968.0;   1.0;  90.0;   3.0;  -1.0;  -2.0;eor
"""


def _zip(text: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("produkt_klima_tag_20250101_20250102_02712.txt", text)
    return buf.getvalue()


def test_parse_renames_and_parses_dates():
    df = parse_dwd_zip(_zip(SAMPLE))
    assert list(df.columns)[:3] == ["date", "temp_mean_c", "temp_max_c"]
    assert str(df["date"].iloc[0].date()) == "2025-01-01"
    assert df["temp_mean_c"].iloc[0] == 2.3


def test_missing_marker_becomes_na():
    df = parse_dwd_zip(_zip(SAMPLE))
    assert df["precip_mm"].isna().iloc[1]
