# Data attribution

This project uses open data from public agencies. Forecasts, statistics and charts
in this repository and on the dashboard are **our own calculations based on this
data**. They are not official forecasts and are not endorsed by any of the agencies below.

| Data | Provider | License | Attribution |
|---|---|---|---|
| Water level, gauge Konstanz (15 min) | Wasserstraßen- und Schifffahrtsverwaltung des Bundes (WSV), [PEGELONLINE](https://www.pegelonline.wsv.de) | [DL-DE Zero 2.0](https://www.govdata.de/dl-de/zero-2-0) | not required, given as courtesy |
| Daily weather observations, station Konstanz (02712) | Deutscher Wetterdienst (DWD), [Open Data](https://opendata.dwd.de) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Datenbasis: Deutscher Wetterdienst, eigene Berechnungen |
| Water level and water temperature, gauge Lindau / Bodensee (daily) | Bayerisches Landesamt für Umwelt (LfU), [Gewässerkundlicher Dienst Bayern](https://www.gkd.bayern.de) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Datenquelle: Bayerisches Landesamt für Umwelt, www.lfu.bayern.de |
| Discharge, water level and water temperature, Alpine Rhine at Diepoldsau (2473); water level Romanshorn (2032) | Bundesamt für Umwelt (BAFU / FOEN), via [LINDAS](https://lindas.admin.ch) and [hydrodaten.admin.ch](https://www.hydrodaten.admin.ch) | [Open use. Must provide the source.](https://opendata.swiss/en/terms-of-use) | Quelle: BAFU |

**Changes made to the data:** timestamps converted to UTC, missing-value markers
replaced, series merged, resampled and used as model inputs.

## Short form (dashboard footer)

> Daten: PEGELONLINE (WSV) · Datenbasis: Deutscher Wetterdienst, eigene Berechnungen ·
> Datenquelle: Bayerisches Landesamt für Umwelt, www.lfu.bayern.de · Quelle: BAFU ·
> Prognosen sind eigene Modellberechnungen, keine amtlichen Vorhersagen.
