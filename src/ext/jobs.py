import datetime
import logging

import requests
from apscheduler.schedulers.background import BackgroundScheduler

from src.ext.database import add_all
from src.models import WhoopCycle, WhoopRecovery, WhoopSleep, WhoopWorkout
from src.retry import retry
from src.utils import ImportStatus, ImportTask

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


def fill_backlog(app):
    whoop_client = app.config["WhoopClient"]
    import_queue = app.config["ImportQueue"]

    import_queue.add(ImportTask(WhoopWorkout, whoop_client.get_workouts))
    import_queue.add(ImportTask(WhoopCycle, whoop_client.get_cycles))
    import_queue.add(ImportTask(WhoopSleep, whoop_client.get_sleeps))
    import_queue.add(ImportTask(WhoopRecovery, whoop_client.get_recoveries))

    # request immediate import
    job = app.config["Scheduler"].get_job("import_worker")
    job.modify(next_run_time=datetime.datetime.now())


@retry(requests.HTTPError, tries=6, delay=4, backoff=2)
def _import_worker(app):
    import_queue = app.config["ImportQueue"]

    if not import_queue:
        return

    logger.info(f"Import queue size: {len(import_queue)}")

    task = import_queue.pop()
    status = ImportStatus.STARTED

    try:
        result = task.callable()
        with app.app_context():
            add_all(result)

        logger.info(f"{task.model.__name__} imported successfully ({len(result)})")
        status = ImportStatus.SUCCESS

    except requests.HTTPError as e:
        status_code = getattr(e.response, "status_code", None)

        if status_code == 401:
            logger.exception("Unauthorized error")
            status = ImportStatus.UNAUTHORIZED
            import_queue.clear()
        elif status_code == 429:
            logger.exception("Rate limit hit, re-queueing task")
            status = ImportStatus.RATE_LIMIT
            import_queue.add(task)
            raise
        else:
            logger.exception("Unexpected HTTP error")
            status = ImportStatus.UNEXPECTED_ERROR

    except requests.ConnectionError:
        logger.exception("Connection error, re-queueing task")
        status = ImportStatus.CONNECTION_ERROR
        import_queue.add(task)
        raise

    except requests.Timeout:
        logger.exception("Request timed out, re-queueing task")
        status = ImportStatus.TIMEOUT
        import_queue.add(task)
        raise

    except Exception:
        logger.exception("Unexpected error")
        status = ImportStatus.UNEXPECTED_ERROR

    finally:
        logger.info(f"Import queue size: {len(import_queue)}")
        app.config["LastImportStatus"] = status


def init_app(app):
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        refresh_token_job,
        "interval",
        minutes=5,
        args=[app],
        id="refresh_token_job",
    )

    scheduler.add_job(
        _import_worker,
        "interval",
        minutes=1,
        args=[app],
        id="import_worker",
    )

    app.config["Scheduler"] = scheduler

    scheduler.start()
