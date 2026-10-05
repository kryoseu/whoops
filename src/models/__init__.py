from typing import TypeVar

from .cycle import WhoopCycle
from .export import (
    WhoopExportCycle,
    WhoopExportJournal,
    WhoopExportSleep,
    WhoopExportWorkout,
)
from .recovery import WhoopRecovery
from .sleep import WhoopSleep
from .workout import WhoopWorkout

Model = TypeVar("Model", WhoopCycle, WhoopRecovery, WhoopSleep, WhoopWorkout)


def from_path(path: str):
    if "cycle" in path:
        return WhoopCycle
    elif "recovery" in path:
        return WhoopRecovery
    elif "sleep" in path:
        return WhoopSleep
    elif "workout" in path:
        return WhoopWorkout
    else:
        raise ValueError(f"Unknown model for path: {path}")
