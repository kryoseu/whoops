"""
Tables mirroring the CSV files of a Whoop data export
(Whoop app > Settings > Data Export).

The export carries data the developer API does not expose (most notably the
Journal), so it is stored beside the API-fed tables rather than merged into
them. The export has no Whoop ids: rows are keyed by their start time.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Tuple

from sqlalchemy import inspect

from src.ext.database import db

_TIMEZONE = re.compile(r"^UTC(?:(?P<sign>[+-])(?P<hours>\d{2}):?(?P<minutes>\d{2})|Z)?$")


def _timezone(value: str) -> timezone:
    """Parse the export's 'Cycle timezone' column, e.g. 'UTC+01:00' or 'UTCZ'."""
    match = _TIMEZONE.match(value.strip())
    if not match:
        raise ValueError(f"invalid timezone {value!r}")
    if not match["sign"]:
        return timezone.utc

    offset = timedelta(hours=int(match["hours"]), minutes=int(match["minutes"]))
    return timezone(-offset if match["sign"] == "-" else offset)


def _offset(tz: timezone) -> str:
    minutes = int(tz.utcoffset(None).total_seconds() // 60)
    sign = "-" if minutes < 0 else "+"
    return f"{sign}{abs(minutes) // 60:02d}:{abs(minutes) % 60:02d}"


# Converters receive a non-empty CSV value and the row's timezone.
def _datetime(value: str, tz: timezone) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=tz)
    return parsed.astimezone(timezone.utc)


def _float(value: str, _tz: timezone) -> float:
    return float(value)


def _int(value: str, _tz: timezone) -> int:
    return round(float(value))


def _minutes_to_ms(value: str, _tz: timezone) -> int:
    return round(float(value) * 60_000)


def _bool(value: str, _tz: timezone) -> bool:
    lowered = value.lower()
    if lowered not in ("true", "false"):
        raise ValueError(f"invalid boolean {value!r}")
    return lowered == "true"


def _text(value: str, _tz: timezone) -> str:
    return value


class ExportRow:
    """Builds a model from one row of its export CSV file."""

    FILENAME: str
    # model attribute -> (CSV header, converter)
    COLUMNS: Dict[str, Tuple[str, Callable]]
    # attribute copied into `timestamp`, the column dashboards filter on
    TIMESTAMP: str

    @classmethod
    def required_headers(cls) -> List[str]:
        return ["Cycle timezone"] + [header for header, _ in cls.COLUMNS.values()]

    @classmethod
    def from_csv_row(cls, row: Dict[str, str]):
        tz = _timezone(row["Cycle timezone"])

        values = {}
        for attr, (header, convert) in cls.COLUMNS.items():
            raw = (row[header] or "").strip()
            try:
                values[attr] = convert(raw, tz) if raw else None
            except ValueError as e:
                raise ValueError(f"column {header!r}: {e}") from None

        for column in inspect(cls).primary_key:
            if values[column.key] is None:
                raise ValueError(f"column {cls.COLUMNS[column.key][0]!r} is empty")

        values["timezone_offset"] = _offset(tz)
        values["timestamp"] = values[cls.TIMESTAMP]
        return cls(**values)

    @classmethod
    def primary_key_of(cls, instance) -> tuple:
        return tuple(inspect(cls).primary_key_from_instance(instance))


_CYCLE_COLUMNS = {
    "cycle_start": ("Cycle start time", _datetime),
    "cycle_end": ("Cycle end time", _datetime),
}

_SLEEP_COLUMNS = {
    "sleep_onset": ("Sleep onset", _datetime),
    "wake_onset": ("Wake onset", _datetime),
    "performance_perc": ("Sleep performance %", _int),
    "respiratory_rate": ("Respiratory rate (rpm)", _float),
    "asleep_ms": ("Asleep duration (min)", _minutes_to_ms),
    "total_in_bed_ms": ("In bed duration (min)", _minutes_to_ms),
    "total_light_sleep_ms": ("Light sleep duration (min)", _minutes_to_ms),
    "total_slow_wave_sleep_ms": ("Deep (SWS) duration (min)", _minutes_to_ms),
    "total_rem_sleep_ms": ("REM duration (min)", _minutes_to_ms),
    "total_awake_ms": ("Awake duration (min)", _minutes_to_ms),
    "sleep_need_ms": ("Sleep need (min)", _minutes_to_ms),
    "sleep_debt_ms": ("Sleep debt (min)", _minutes_to_ms),
    "efficiency_perc": ("Sleep efficiency %", _int),
    "consistency_perc": ("Sleep consistency %", _int),
}


class _SleepMetrics:
    """Sleep columns shared by physiological_cycles.csv and sleeps.csv."""

    wake_onset = db.Column(db.DateTime(timezone=True), nullable=True)
    performance_perc = db.Column(db.Integer, nullable=True)
    respiratory_rate = db.Column(db.Float, nullable=True)
    asleep_ms = db.Column(db.BigInteger, nullable=True)
    total_in_bed_ms = db.Column(db.BigInteger, nullable=True)
    total_light_sleep_ms = db.Column(db.BigInteger, nullable=True)
    total_slow_wave_sleep_ms = db.Column(db.BigInteger, nullable=True)
    total_rem_sleep_ms = db.Column(db.BigInteger, nullable=True)
    total_awake_ms = db.Column(db.BigInteger, nullable=True)
    sleep_need_ms = db.Column(db.BigInteger, nullable=True)
    sleep_debt_ms = db.Column(db.BigInteger, nullable=True)
    efficiency_perc = db.Column(db.Integer, nullable=True)
    consistency_perc = db.Column(db.Integer, nullable=True)


class WhoopExportCycle(ExportRow, _SleepMetrics, db.Model):
    __tablename__ = "whoop_export_cycle"

    FILENAME = "physiological_cycles.csv"
    TIMESTAMP = "cycle_start"
    COLUMNS = {
        **_CYCLE_COLUMNS,
        "recovery_score": ("Recovery score %", _int),
        "resting_heart_rate": ("Resting heart rate (bpm)", _int),
        "hrv_rmssd_ms": ("Heart rate variability (ms)", _float),
        "skin_temp_celsius": ("Skin temp (celsius)", _float),
        "spo2_perc": ("Blood oxygen %", _float),
        "strain": ("Day Strain", _float),
        "energy_kcal": ("Energy burned (cal)", _float),
        "max_heart_rate": ("Max HR (bpm)", _int),
        "avg_heart_rate": ("Average HR (bpm)", _int),
        **_SLEEP_COLUMNS,
    }

    cycle_start = db.Column(db.DateTime(timezone=True), primary_key=True)
    cycle_end = db.Column(db.DateTime(timezone=True), nullable=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    timezone_offset = db.Column(db.String(10), nullable=False)

    # Recovery
    recovery_score = db.Column(db.Integer, nullable=True)
    resting_heart_rate = db.Column(db.Integer, nullable=True)
    hrv_rmssd_ms = db.Column(db.Float, nullable=True)
    skin_temp_celsius = db.Column(db.Float, nullable=True)
    spo2_perc = db.Column(db.Float, nullable=True)

    # Day
    strain = db.Column(db.Float, nullable=True)
    energy_kcal = db.Column(db.Float, nullable=True)
    max_heart_rate = db.Column(db.Integer, nullable=True)
    avg_heart_rate = db.Column(db.Integer, nullable=True)

    # Main sleep of the cycle
    sleep_onset = db.Column(db.DateTime(timezone=True), nullable=True)


class WhoopExportSleep(ExportRow, _SleepMetrics, db.Model):
    __tablename__ = "whoop_export_sleep"

    FILENAME = "sleeps.csv"
    TIMESTAMP = "sleep_onset"
    COLUMNS = {
        **_CYCLE_COLUMNS,
        **_SLEEP_COLUMNS,
        "nap": ("Nap", _bool),
    }

    sleep_onset = db.Column(db.DateTime(timezone=True), primary_key=True)
    cycle_start = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    cycle_end = db.Column(db.DateTime(timezone=True), nullable=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    timezone_offset = db.Column(db.String(10), nullable=False)
    nap = db.Column(db.Boolean, nullable=True)


class WhoopExportWorkout(ExportRow, db.Model):
    __tablename__ = "whoop_export_workout"

    FILENAME = "workouts.csv"
    TIMESTAMP = "workout_start"
    COLUMNS = {
        **_CYCLE_COLUMNS,
        "workout_start": ("Workout start time", _datetime),
        "workout_end": ("Workout end time", _datetime),
        "duration_ms": ("Duration (min)", _minutes_to_ms),
        "sport_name": ("Activity name", _text),
        "strain": ("Activity Strain", _float),
        "energy_kcal": ("Energy burned (cal)", _float),
        "max_heart_rate": ("Max HR (bpm)", _int),
        "avg_heart_rate": ("Average HR (bpm)", _int),
        "zone_one_perc": ("HR Zone 1 %", _float),
        "zone_two_perc": ("HR Zone 2 %", _float),
        "zone_three_perc": ("HR Zone 3 %", _float),
        "zone_four_perc": ("HR Zone 4 %", _float),
        "zone_five_perc": ("HR Zone 5 %", _float),
        "gps_enabled": ("GPS enabled", _bool),
    }

    workout_start = db.Column(db.DateTime(timezone=True), primary_key=True)
    cycle_start = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    cycle_end = db.Column(db.DateTime(timezone=True), nullable=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    timezone_offset = db.Column(db.String(10), nullable=False)
    workout_end = db.Column(db.DateTime(timezone=True), nullable=True)
    duration_ms = db.Column(db.BigInteger, nullable=True)
    sport_name = db.Column(db.String(64), nullable=True)

    strain = db.Column(db.Float, nullable=True)
    energy_kcal = db.Column(db.Float, nullable=True)
    max_heart_rate = db.Column(db.Integer, nullable=True)
    avg_heart_rate = db.Column(db.Integer, nullable=True)
    zone_one_perc = db.Column(db.Float, nullable=True)
    zone_two_perc = db.Column(db.Float, nullable=True)
    zone_three_perc = db.Column(db.Float, nullable=True)
    zone_four_perc = db.Column(db.Float, nullable=True)
    zone_five_perc = db.Column(db.Float, nullable=True)
    gps_enabled = db.Column(db.Boolean, nullable=True)


class WhoopExportJournal(ExportRow, db.Model):
    """
    One Journal answer. Whoop attaches the answers given on waking to the cycle
    that starts with that night's sleep, so an entry relates to the recovery
    of the same cycle (join on cycle_start).
    """

    __tablename__ = "whoop_export_journal"

    FILENAME = "journal_entries.csv"
    TIMESTAMP = "cycle_start"
    COLUMNS = {
        **_CYCLE_COLUMNS,
        "question": ("Question text", _text),
        "answered_yes": ("Answered yes", _bool),
        "notes": ("Notes", _text),
    }

    cycle_start = db.Column(db.DateTime(timezone=True), primary_key=True)
    question = db.Column(db.String(255), primary_key=True)
    cycle_end = db.Column(db.DateTime(timezone=True), nullable=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    timezone_offset = db.Column(db.String(10), nullable=False)
    answered_yes = db.Column(db.Boolean, nullable=True)
    notes = db.Column(db.Text, nullable=True)


EXPORT_MODELS = [
    WhoopExportCycle,
    WhoopExportSleep,
    WhoopExportWorkout,
    WhoopExportJournal,
]
