[![Python](https://img.shields.io/badge/python-3.13-blue?style=flat-square)](https://www.python.org/downloads/release/python-3130/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Ko--fi-red?style=flat-square)](https://ko-fi.com/kryoseu)
# Whoops

Whoops is a simple Flask application that imports your Whoop data into a PostgreSQL or MySQL database.  

**Features:**

- Manual and daily imports.
- Automatic API token refresh.

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

# Visualizing Your Data

## Whoops UI (Recommended for a Simple Setup)

For a lightweight, purpose-built UI to explore your Whoop metrics, you can use [whoops-ui](https://github.com/kryoseu/whoops-ui).

`whoops-ui` retrieves data directly from `whoops` or the Whoop API and provides a clean web interface for exploring and visualizing your data, including support for custom graphs and dashboards—without requiring Grafana.

## Grafana

If you have [Grafana](https://grafana.com/docs/grafana/latest/setup-grafana/installation/) installed, you can import the provided [dashboard](https://grafana.com/grafana/dashboards/25022-whoops-recovery-sleep-insights/) to visualize your Whoop data.

<img width="1249" height="1222" alt="260317_11h15m30s_screenshot" src="https://github.com/user-attachments/assets/b726578d-9b30-472b-a51f-249d2ddb84cc" />

## Support This Project ☕️

If you like **Whoops** and want to help keep it improving, you can support me via:

[![Buy me a coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Ko--fi-red?style=flat-square)](https://ko-fi.com/kryoseu)

Thank you for your support! 💛

