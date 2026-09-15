[![Python](https://img.shields.io/badge/python-3.13-blue?style=flat-square)](https://www.python.org/downloads/release/python-3130/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Ko--fi-red?style=flat-square)](https://ko-fi.com/kryoseu)
# Whoops

Whoops is a simple Flask application that imports your Whoop data into a PostgreSQL or MySQL database.  

**Features:**

- Manual and daily imports.
- Automatic API token refresh.
- Import of the Whoop data export (CSV), including the Journal which the API does not provide.

## Requirements

- Docker (or a Kubernetes cluster)
- A Whoop API **Client ID** and **Client Secret** from the [Whoop Developer Dashboard](https://developer-dashboard.whoop.com/)

> [!NOTE]
> The redirect URL configured for your Whoop app must match the URL where Whoops will run (e.g., `http://localhost:5000/callback`).

# Getting Started

Example Docker compose file and kubernetes manifests are provided in the [templates](https://github.com/kryoseu/whoops/tree/main/templates) section, which also include how to install a database along with Whoops, in case you don't have one yet.

## With Docker

Using Docker compose:

```yaml
services:
  whoops:
    image: docker.io/kryoseu/whoops:latest
    container_name: whoops
    ports:
      - "5000:5000"
    environment:
      CLIENT_ID: "<your-whoop-client-id-here"
      CLIENT_SECRET: "<your-whoop-client-secret-here"
      REDIRECT_URI: "http://localhost:5000/callback"
      SQLALCHEMY_DATABASE_URI: "postgresql+psycopg2://whoops:whoops@127.0.0.1:5432/whoop_data"
    restart: unless-stopped
```

or Docker run:

```bash
docker run -d \
  --name whoops \
  --network host \
  -e CLIENT_ID="<your-whoop-client-id>" \
  -e CLIENT_SECRET="<your-whoop-client-secret>" \
  -e REDIRECT_URI="http://localhost:5000/callback" \
  -e SQLALCHEMY_DATABASE_URI="postgresql+psycopg2://whoops:whoops@127.0.0.1:5432/whoop_data" \
  docker.io/kryoseu/whoops:latest
```

Update `SQLALCHEMY_DATABASE_URI` depending on your database:

- PostgreSQL: `postgresql+psycopg2://<user>:<password>@<host>:5432/whoop_data`
- MySQL: `mysql+pymysql://<user>:<password>@<host>:3306/whoop_data`

# Usage

1. Navigate to [http://localhost:5000/authorize](http://localhost:5000/authorize) to authorize Whoops to access your Whoop data.
2. Navigate to [http://localhost:5000](http://localhost:5000) to set when import job runs or trigger a manual import.

> [!TIP]
> The app will automatically refresh tokens and import your data every 24 hours.

## Importing a Whoop data export

The Whoop app can export your data as CSV files (**Settings > Data Export**, delivered as a zip).
The export contains data the Whoop API does not provide:

| Data | Whoop API | Data export |
| --- | --- | --- |
| Journal answers (alcohol, caffeine, custom questions...) and notes | No | Yes |
| Total sleep need, time asleep | Parts only | Yes |
| Workout GPS flag | No | Yes |

Upload the zip, or any of its CSV files, from [http://localhost:5000](http://localhost:5000), or with curl:

```bash
curl -F file=@my_whoop_data_2026_02_10.zip http://localhost:5000/import/export
```

Each file is stored in its own table, next to the API tables which are left untouched:

| File | Table | Key |
| --- | --- | --- |
| `physiological_cycles.csv` | `whoop_export_cycle` | `cycle_start` |
| `sleeps.csv` | `whoop_export_sleep` | `sleep_onset` |
| `workouts.csv` | `whoop_export_workout` | `workout_start` |
| `journal_entries.csv` | `whoop_export_journal` | `cycle_start`, `question` |

Times are stored in UTC and durations in milliseconds, like the API tables. Every export contains your full
history, so importing a newer one updates the existing rows. Upload the files as exported: CSV files re-saved by
a spreadsheet app (other separators and date formats) are rejected.

Journal answers given on waking are attached by Whoop to the cycle that starts with that night's sleep. To relate a
behavior to its recovery, join both tables on `cycle_start`:

```sql
SELECT j.question, j.answered_yes, c.recovery_score, c.hrv_rmssd_ms
FROM whoop_export_journal j
JOIN whoop_export_cycle c ON c.cycle_start = j.cycle_start;
```

# Visualizing Your Data

## Whoops UI (Recommended for a Simple Setup)

For a lightweight, purpose-built UI to explore your Whoop metrics, you can use [whoops-ui](https://github.com/kryoseu/whoops-ui).

`whoops-ui` retrieves data directly from `whoops` or the Whoop API and provides a clean web interface for exploring and visualizing your data, including support for custom graphs and dashboards—without requiring Grafana.

## Grafana

If you have [Grafana](https://grafana.com/docs/grafana/latest/setup-grafana/installation/) installed, you can import the provided [dashboard](https://grafana.com/grafana/dashboards/25022-whoops-recovery-sleep-insights/) to visualize your Whoop data.

The [dashboard template](templates/grafana.json) also has a **Journal (Whoop data export)** row, filled once an export is imported:
how each journal behavior relates to recovery, HRV, resting heart rate and sleep performance, a log of your answers,
and sleep need against time asleep.

<img width="1249" height="1222" alt="260317_11h15m30s_screenshot" src="https://github.com/user-attachments/assets/b726578d-9b30-472b-a51f-249d2ddb84cc" />

## Support This Project ☕️

If you like **Whoops** and want to help keep it improving, you can support me via:

[![Buy me a coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Ko--fi-red?style=flat-square)](https://ko-fi.com/kryoseu)

Thank you for your support! 💛

## Star History

<a href="https://www.star-history.com/?repos=kryoseu%2Fwhoops&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=kryoseu/whoops&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=kryoseu/whoops&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=kryoseu/whoops&type=date&legend=top-left" />
 </picture>
</a>
