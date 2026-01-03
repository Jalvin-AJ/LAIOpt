import csv
import io
from typing import List, Any, TextIO, Union

from laiopt.backend.core.models import Block, Net, Die


def _open_csv(csvfile: Union[str, TextIO]) -> TextIO:
    """
    Open a CSV file in text mode.

    Supports:
    - File paths (str)
    - Streamlit UploadedFile (binary)
    - Already-open text file objects
    """
    if isinstance(csvfile, str):
        return open(csvfile, newline="", encoding="utf-8")

    # Streamlit UploadedFile or binary file-like
    if hasattr(csvfile, "read"):
        # If file returns bytes, wrap it
        sample = csvfile.read(0)
        if isinstance(sample, bytes):
            return io.TextIOWrapper(csvfile, encoding="utf-8", newline="")
        return csvfile

    raise ValueError("Unsupported CSV input type")


def load_blocks_csv(csvfile: Union[str, TextIO]) -> List[Block]:
    """
    Load macro block definitions from a CSV file.

    Required columns: id, width, height, power, heat
    """
    required_columns = ["id", "width", "height", "power", "heat"]

    f = _open_csv(csvfile)
    close_file = isinstance(csvfile, str)

    try:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("Blocks CSV is empty or missing headers.")

        missing = [c for c in required_columns if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"Missing required block columns: {missing}")

        blocks: List[Block] = []
        for lineno, row in enumerate(reader, start=2):
            try:
                blocks.append(
                    Block(
                        id=row["id"],
                        width=float(row["width"]),
                        height=float(row["height"]),
                        power=float(row["power"]),
                        heat=float(row["heat"]),
                    )
                )
            except Exception as e:
                raise ValueError(f"Invalid block data at row {lineno}: {e}")

        return blocks
    finally:
        if close_file:
            f.close()


def load_nets_csv(csvfile: Union[str, TextIO]) -> List[Net]:
    """
    Load net/connectivity definitions from a CSV file.

    Required columns: name, blocks, weight
    """
    required_columns = ["name", "blocks", "weight"]

    f = _open_csv(csvfile)
    close_file = isinstance(csvfile, str)

    try:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("Nets CSV is empty or missing headers.")

        missing = [c for c in required_columns if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"Missing required net columns: {missing}")

        nets: List[Net] = []
        for lineno, row in enumerate(reader, start=2):
            try:
                name = row["name"].strip()
                if not name:
                    raise ValueError("Empty net name")

                block_ids = [b.strip() for b in row["blocks"].split(",") if b.strip()]
                if not block_ids:
                    raise ValueError("Net has no connected blocks")

                nets.append(
                    Net(
                        name=name,
                        blocks=block_ids,
                        weight=float(row["weight"]),
                    )
                )
            except Exception as e:
                raise ValueError(f"Invalid net data at row {lineno}: {e}")

        return nets
    finally:
        if close_file:
            f.close()


def load_die_from_params(width: Any, height: Any) -> Die:
    """
    Create Die object from explicit width and height parameters.
    """
    try:
        return Die(width=float(width), height=float(height))
    except Exception as e:
        raise ValueError(f"Invalid die dimensions: {e}")
