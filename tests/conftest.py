import io
import zipfile

import pytest
from flask import Flask

from src.ext import database, webui

# Headers are copied verbatim from a real export, rows are made up.
CYCLES_CSV = """\
Cycle start time,Cycle end time,Cycle timezone,Recovery score %,Resting heart rate (bpm),Heart rate variability (ms),Skin temp (celsius),Blood oxygen %,Day Strain,Energy burned (cal),Max HR (bpm),Average HR (bpm),Sleep onset,Wake onset,Sleep performance %,Respiratory rate (rpm),Asleep duration (min),In bed duration (min),Light sleep duration (min),Deep (SWS) duration (min),REM duration (min),Awake duration (min),Sleep need (min),Sleep debt (min),Sleep efficiency %,Sleep consistency %
2026-01-02 23:00:00,,UTC+01:00,61,50,48,34.5,97.5,,,,,2026-01-02 23:00:00,2026-01-03 07:00:00,95,14.2,450,480,220,90,140,30,470,10,94,
2026-01-01 22:30:00,2026-01-02 23:00:00,UTC+01:00,40,55,39,34.9,98.1,12.4,2400,160,70,2026-01-01 22:30:00,2026-01-02 06:15:00,80,14.8,400,465,200,80,120,65,500,35,86,78
"""

SLEEPS_CSV = """\
Cycle start time,Cycle end time,Cycle timezone,Sleep onset,Wake onset,Sleep performance %,Respiratory rate (rpm),Asleep duration (min),In bed duration (min),Light sleep duration (min),Deep (SWS) duration (min),REM duration (min),Awake duration (min),Sleep need (min),Sleep debt (min),Sleep efficiency %,Sleep consistency %,Nap
2026-01-02 23:00:00,,UTC+01:00,2026-01-02 23:00:00,2026-01-03 07:00:00,95,14.2,450,480,220,90,140,30,470,10,94,,false
2026-01-01 22:30:00,2026-01-02 23:00:00,UTC+01:00,2026-01-02 14:00:00,2026-01-02 14:25:00,30,15.0,22,25,10,12,0,3,500,35,88,,true
"""

WORKOUTS_CSV = """\
Cycle start time,Cycle end time,Cycle timezone,Workout start time,Workout end time,Duration (min),Activity name,Activity Strain,Energy burned (cal),Max HR (bpm),Average HR (bpm),HR Zone 1 %,HR Zone 2 %,HR Zone 3 %,HR Zone 4 %,HR Zone 5 %,GPS enabled
2026-01-01 22:30:00,2026-01-02 23:00:00,UTC+01:00,2026-01-02 18:00:00,2026-01-02 18:45:00,45,Running,11.2,520.0,172,148,10,25,40,20,5,false
"""

JOURNAL_CSV = """\
Cycle start time,Cycle end time,Cycle timezone,Question text,Answered yes,Notes
2026-01-02 23:00:00,,UTC+01:00,Have any alcoholic drinks?,true,"Wine, two glasses"
2026-01-02 23:00:00,,UTC+01:00,Consumed caffeine?,false,
2026-01-02 23:00:00,,UTC+01:00,Consumed caffeine?,false,
"""

EXPORT_FILES = {
    "physiological_cycles.csv": CYCLES_CSV,
    "sleeps.csv": SLEEPS_CSV,
    "workouts.csv": WORKOUTS_CSV,
    "journal_entries.csv": JOURNAL_CSV,
}


def make_zip(files=EXPORT_FILES) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    database.init_app(app)
    webui.init_app(app)
    return app


@pytest.fixture
def client(app):
    return app.test_client()
