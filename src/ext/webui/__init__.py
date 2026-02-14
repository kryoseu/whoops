from flask import Blueprint

from .views import authorize, callback, manual_import, index, schedule

schedule.methods = ["POST"]  # type: ignore
manual_import.methods = ["POST"]  # type: ignore

bp = Blueprint(
    "webui",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/webui/static",
)

bp.add_url_rule("/", view_func=index)
bp.add_url_rule("/authorize", view_func=authorize)
bp.add_url_rule("/callback", view_func=callback)
bp.add_url_rule("/import", view_func=manual_import)
bp.add_url_rule("/schedule", view_func=schedule)


def init_app(app):
    """Initializes the web UI extension."""
    app.register_blueprint(bp)
