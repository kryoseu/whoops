import logging

import requests
from flask import (
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from src.ext.database import add_all, query_all
from src.ext.jobs import import_job, run_import
from src.models.cycle import WhoopCycle
from src.models.recovery import WhoopRecovery
from src.models.sleep import WhoopSleep
from src.models.workout import WhoopWorkout
from src.retry import retry

logger = logging.getLogger(__name__)


def index():
    """
    Retrieve data from database.
    """
    cycles = query_all(WhoopCycle)
    sleeps = query_all(WhoopSleep)
    recoveries = query_all(WhoopRecovery)
    workouts = query_all(WhoopWorkout)

    return render_template(
        "index.html",
        cycles=cycles,
        sleeps=sleeps,
        recoveries=recoveries,
        workouts=workouts,
    )


def authorize():
    """
    Initiates the OAuth2 authorization flow by redirecting to the authorization URL.
    """

    whoo_client = current_app.config["WhoopClient"]

    return redirect(whoo_client.authorization_url(), code=302)


def callback():
    """
    Handles the OAuth2 callback and exchanges the authorization code for tokens.
    """
    code = request.args.get("code")
    state = request.args.get("state")

    if state != current_app.config["OAuthState"]:
        flash("Invalid OAuth state", "danger")
        return redirect(url_for("webui.index"))

    try:
        current_app.config["WhoopClient"].set_tokens(code)
        flash("Authorized", "success")

    except requests.HTTPError as e:
        flash(f"Failed to set tokens: {e}", "danger")
        return redirect(url_for("webui.index"))

    return redirect(url_for("webui.index"))


def manual_import():
    """
    Manual retrieve and import Whoop data.
    """
    logger.info("Starting import via web UI")

    try:
        run_import(current_app)

        flash("Import finished", "success")
        return jsonify({"message": "Import finished"}), 201

    except requests.HTTPError as e:
        logger.error(e)
        abort(e.response.status_code, description=e)


def schedule():
    """
    Schedule data import.
    """

    scheduler = current_app.config.get("Scheduler")

    if not scheduler:
        return {"error": "Scheduler not configured"}, 500

    data = request.get_json()

    if not data:
        abort(400, description="Missing input")

    hour = data.get("hour")
    minute = data.get("minute")

    if hour is None or minute is None:
        abort(400, description="Invalid input")

    try:
        hour = int(hour)
        minute = int(minute)

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        abort(400, description="Invalid input")

    scheduler.add_job(
        func=import_job,
        trigger="cron",
        hour=hour,
        minute=minute,
        args=[current_app._get_current_object()],  # type: ignore
        id="import_job",
        replace_existing=True,
    )

    logger.info("Import job scheduled")

    return {"message": "Import scheduled successfully"}, 201
