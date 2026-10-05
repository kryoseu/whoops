import io
from datetime import datetime, timezone

import pytest

from src.models.export import (
    WhoopExportCycle,
    WhoopExportJournal,
    WhoopExportSleep,
    WhoopExportWorkout,
)
from src.whoop_export import ExportFormatError, read_export
from tests.conftest import JOURNAL_CSV, SLEEPS_CSV, make_zip


def upload(name, content):
    data = content.encode() if isinstance(content, str) else content
    return name, io.BytesIO(data)


def test_reads_every_file_of_the_export_zip():
    records = read_export([upload("my_whoop_data_2026_01_03.zip", make_zip())])

    assert {model: len(rows) for model, rows in records.items()} == {
        WhoopExportCycle: 2,
        WhoopExportSleep: 2,
        WhoopExportWorkout: 1,
        WhoopExportJournal: 2,
    }


def test_converts_values_to_database_types():
    records = read_export([upload("export.zip", make_zip())])

    current, previous = records[WhoopExportCycle]
    assert current.cycle_start == datetime(2026, 1, 2, 22, 0, tzinfo=timezone.utc)
    assert current.timestamp == current.cycle_start
    assert current.cycle_end is None
    assert current.strain is None
    assert current.timezone_offset == "+01:00"
    assert current.recovery_score == 61
    assert current.asleep_ms == 450 * 60_000
    assert previous.strain == 12.4
    assert previous.consistency_perc == 78

    main_sleep, nap = records[WhoopExportSleep]
    assert (main_sleep.nap, nap.nap) == (False, True)
    assert nap.cycle_start == previous.cycle_start

    (workout,) = records[WhoopExportWorkout]
    assert workout.sport_name == "Running"
    assert workout.duration_ms == 45 * 60_000
    assert workout.gps_enabled is False


def test_collapses_duplicate_journal_answers_and_keeps_quoted_notes():
    records = read_export([upload("journal_entries.csv", JOURNAL_CSV)])

    answers = {entry.question: entry for entry in records[WhoopExportJournal]}
    assert set(answers) == {"Have any alcoholic drinks?", "Consumed caffeine?"}
    assert answers["Have any alcoholic drinks?"].answered_yes is True
    assert answers["Have any alcoholic drinks?"].notes == "Wine, two glasses"
    assert answers["Consumed caffeine?"].notes is None


def test_accepts_single_csv_files_and_ignores_unrelated_ones():
    records = read_export(
        [upload("sleeps.csv", SLEEPS_CSV), upload("journal_entries.xlsx", b"\x00binary")]
    )

    assert list(records) == [WhoopExportSleep]


@pytest.mark.parametrize(
    ("value", "offset", "hour"),
    [("UTCZ", "+00:00", 23), ("UTC-05:00", "-05:00", 4), ("UTC+05:30", "+05:30", 17)],
)
def test_parses_timezone_variants(value, offset, hour):
    csv = JOURNAL_CSV.replace("UTC+01:00", value)

    entry = read_export([upload("journal_entries.csv", csv)])[WhoopExportJournal][0]

    assert entry.timezone_offset == offset
    assert entry.cycle_start.hour == hour


def test_rejects_file_resaved_by_a_spreadsheet_app():
    resaved = (
        "Cycle start time;Cycle end time;Cycle timezone;Question text;Answered yes;Notes\r\n"
        "09/02/2026 22:12;;UTC+01:00;Felt Irritable?;false;\r\n"
    )

    with pytest.raises(ExportFormatError, match="re-saved by a spreadsheet app"):
        read_export([upload("journal_entries.csv", resaved)])


def test_reports_file_line_and_column_of_invalid_values():
    broken = JOURNAL_CSV.replace("2026-01-02 23:00:00,,UTC+01:00,Consumed", "09/02/2026 22:12,,UTC+01:00,Consumed", 1)

    with pytest.raises(ExportFormatError, match=r"journal_entries.csv line 3: column 'Cycle start time'"):
        read_export([upload("journal_entries.csv", broken)])


def test_rejects_upload_without_export_files():
    with pytest.raises(ExportFormatError, match="No Whoop export file found"):
        read_export([upload("notes.txt", "hello")])
