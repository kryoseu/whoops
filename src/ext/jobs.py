import logging

import requests
from apscheduler.schedulers.background import BackgroundScheduler

from src.retry import retry

from .database import add_all

logger = logging.getLogger(__name__)

logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)
logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)


def refresh_token_job(app):
    logger.info("Running refresh token job")

    whoop_client = app.config["WhoopClient"]
    if whoop_client.needs_refresh():
        try:
            whoop_client.refresh_token()
            logger.info("Token refreshed successfully.")
        except requests.HTTPError:
            logger.error("Manual authorization required. Visit /authorize.")


def import_job(app):
    logger.info("Running import job")
    try:
        run_import(app)
        logger.info("Data imported successfully.")
    except requests.HTTPError as e:
        logger.error(e)


@retry(requests.HTTPError, tries=3, delay=2, backoff=2)
def run_import(app):
    whoop_client = app.config["WhoopClient"]

    cycles = whoop_client.get_cycles()
    sleeps = whoop_client.get_sleeps()
    recoveries = whoop_client.get_recoveries()
    workouts = whoop_client.get_workouts()

    with app.app_context():
        add_all(cycles)
        add_all(sleeps)
        add_all(recoveries)
        add_all(workouts)


def init_app(app):
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        refresh_token_job,
        "interval",
        minutes=5,
        args=[app],
        id="refresh_token_job",
    )

    app.config["Scheduler"] = scheduler

    scheduler.start()
