import io

from src.ext.database import db
from src.models.export import WhoopExportCycle, WhoopExportJournal
from tests.conftest import CYCLES_CSV, EXPORT_FILES, make_zip


def post_export(client, content, filename="my_whoop_data.zip"):
    return client.post(
        "/import/export",
        data={"file": (io.BytesIO(content), filename)},
        content_type="multipart/form-data",
    )


def test_imports_export_zip(client, app):
    response = post_export(client, make_zip())

    assert response.status_code == 201
    assert response.json["imported"] == {
        "physiological_cycles.csv": 2,
        "sleeps.csv": 2,
        "workouts.csv": 1,
        "journal_entries.csv": 2,
    }
    with app.app_context():
        assert db.session.query(WhoopExportJournal).count() == 2


def test_reimporting_a_newer_export_updates_rows(client, app):
    post_export(client, make_zip())
    newer = {**EXPORT_FILES, "physiological_cycles.csv": CYCLES_CSV.replace(",61,50,", ",75,50,")}

    response = post_export(client, make_zip(newer))

    assert response.status_code == 201
    with app.app_context():
        assert db.session.query(WhoopExportCycle).count() == 2
        assert sorted(c.recovery_score for c in db.session.query(WhoopExportCycle)) == [40, 75]


def test_rejects_invalid_upload_with_a_readable_message(client):
    response = post_export(client, b"not an export", filename="notes.txt")

    assert response.status_code == 400
    assert "No Whoop export file found" in response.json["message"]


def test_rejects_request_without_file(client):
    response = client.post("/import/export")

    assert response.status_code == 400
