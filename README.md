# Bodensee Forecast

Forecasting the water level (and later the water temperature) of Lake Constance
(Bodensee) a few days ahead, run as a real service: scheduled ingestion,
retraining, drift monitoring, public dashboard.

## Roadmap

| Phase | Goal | Status |
|---|---|---|
| 1 | Data foundation: find sources, ingest, archive | in progress |
| 2 | EDA + naive baselines (persistence, seasonal climatology) | |
| 3 | ARIMA / SARIMAX with weather regressors | |
| 4 | Gradient boosting (LightGBM) with lag features | |
| 5 | LSTM / temporal models | |
| 6 | Honest comparison: backtesting, error by horizon and season | |
| 7 | Service: Spring Boot API, containers, Kubernetes, Terraform, monitoring, dashboard | |

## Architecture

Python does data and ML, Spring Boot does services, PostgreSQL sits in between.
Forecasts are computed once a day as a batch job, so the API only reads results
from the database and never runs a model itself.

```
Python CronJobs (ingest, train, predict, evaluate) ──► PostgreSQL ◄── Spring Boot (API, dashboard, metrics)
```

Planned stack: Python (pandas, statsmodels, LightGBM, PyTorch, MLflow) ·
Spring Boot 3 (JPA, Flyway, Actuator) · PostgreSQL · Docker · GitHub Actions ·
Kubernetes (minikube locally, DigitalOcean DOKS in the cloud) · Argo CD ·
Terraform · Prometheus + Grafana.

## Data sources (verified 2026-10-30)

| Source | What | Resolution | History | Access |
|---|---|---|---|---|
| [Pegelonline](https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json?waters=BODENSEE) | Water level, Konstanz | 15 min | **only ~31 days** | REST API |
| [DWD](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/) | Daily weather, Konstanz (02712) | daily | 1959 → yesterday | HTTPS zip |
| [GKD Bayern](https://www.gkd.bayern.de/de/seen/wasserstand/bayern/lindau-20001001/gesamtzeitraum) | Water level, Lindau | daily | **1871** → today | manual browser download |
| [GKD Bayern](https://gkd.bayern.de/de/seen/wassertemperatur/bayern/lindau-20001001/gesamtzeitraum) | Water temperature, Lindau | daily | 2004 → today | manual browser download |
| [BAFU LINDAS](https://lindas.admin.ch) | Alpine Rhine at Diepoldsau: discharge, temperature, level | 10 min | **latest value only** | SPARQL |

Findings:
- Pegelonline and LINDAS only serve recent data → we archive them ourselves, starting now.
- GKD has no public API, so its history is downloaded once by hand.
- The Alpine Rhine (Diepoldsau) carries most of the lake's inflow and should lead the lake level by days.
- Gauges use different reference heights (German vs. Swiss systems, gauge zeros) and must be aligned before combining.
- The raw Konstanz gauge has gaps (e.g. 21 h on 2026-10-21/22) and is reported in whole cm.

Credits and licenses for all data: [ATTRIBUTION.md](ATTRIBUTION.md).

## Setup

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

## Ingestion

```bash
.venv/bin/python -m bodensee.ingest.pegelonline   # merge last 31 days into archive
.venv/bin/python -m bodensee.ingest.dwd           # full daily weather history
```

Output goes to `data/raw/` (git-ignored). The DWD data can always be re-downloaded;
**the Pegelonline archive cannot**. Run it at least every few weeks until it is automated.
