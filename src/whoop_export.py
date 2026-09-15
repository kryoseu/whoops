import csv
import io
import posixpath
import zipfile
from typing import BinaryIO, Dict, Iterable, Iterator, List, Tuple

from src.models.export import EXPORT_MODELS

MAX_FILE_BYTES = 50 * 1024 * 1024

MODELS_BY_FILENAME = {model.FILENAME: model for model in EXPORT_MODELS}


class ExportFormatError(ValueError):
    """The uploaded content is not a readable Whoop data export."""


def read_export(uploads: Iterable[Tuple[str, BinaryIO]]) -> Dict[type, List]:
    """
    Parse the Whoop export zip and/or its CSV files into export models,
    grouped by model class. Unrelated files are ignored and rows sharing a
    primary key are collapsed, the last one winning.
    """
    records: Dict[type, Dict[tuple, object]] = {}

    for filename, content in _export_files(uploads):
        model = MODELS_BY_FILENAME[posixpath.basename(filename)]
        rows = records.setdefault(model, {})
        for instance in _parse_csv(model, filename, content):
            rows[model.primary_key_of(instance)] = instance

    if not records:
        raise ExportFormatError(
            "No Whoop export file found. Upload the export zip or any of: "
            + ", ".join(MODELS_BY_FILENAME)
        )

    return {model: list(rows.values()) for model, rows in records.items()}


def _export_files(uploads: Iterable[Tuple[str, BinaryIO]]) -> Iterator[Tuple[str, bytes]]:
    """Yield (filename, content) of every known export CSV, unpacking zips."""
    for filename, stream in uploads:
        data = stream.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise ExportFormatError(f"{filename} is larger than {MAX_FILE_BYTES // 2**20} MB")

        if not zipfile.is_zipfile(io.BytesIO(data)):
            if posixpath.basename(filename) in MODELS_BY_FILENAME:
                yield filename, data
            continue

        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for info in archive.infolist():
                    if posixpath.basename(info.filename) not in MODELS_BY_FILENAME:
                        continue
                    if info.file_size > MAX_FILE_BYTES:
                        raise ExportFormatError(f"{info.filename} is larger than {MAX_FILE_BYTES // 2**20} MB")
                    yield info.filename, archive.read(info)
        except zipfile.BadZipFile as e:
            raise ExportFormatError(f"{filename}: {e}") from None


def _parse_csv(model, filename: str, data: bytes) -> Iterator:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ExportFormatError(f"{filename}: not a UTF-8 CSV file") from None

    reader = csv.DictReader(io.StringIO(text, newline=""))
    headers = reader.fieldnames or []

    missing = [h for h in model.required_headers() if h not in headers]
    if missing:
        message = f"{filename}: missing columns {', '.join(missing)}."
        if len(headers) == 1 and ";" in headers[0]:
            message += " The file looks re-saved by a spreadsheet app, upload the original from the Whoop zip."
        raise ExportFormatError(message)

    for row in reader:
        try:
            yield model.from_csv_row(row)
        except ValueError as e:
            raise ExportFormatError(f"{filename} line {reader.line_num}: {e}") from None
