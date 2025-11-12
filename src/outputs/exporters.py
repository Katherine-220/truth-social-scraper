import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set

from extractors.utils_formatting import flatten_profiles_for_csv

logger = logging.getLogger(__name__)

def _ensure_output_dir(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)

def export_json(profiles: List[Dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)
    logger.info("Wrote JSON output with %d profile(s) to %s", len(profiles), path)

def export_csv(profiles: List[Dict[str, Any]], path: Path) -> None:
    rows = flatten_profiles_for_csv(profiles)
    if not rows:
        logger.warning("No rows to export to CSV at %s", path)
        return

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    logger.info("Wrote CSV output with %d row(s) to %s", len(rows), path)

def export_profiles(
    profiles: List[Dict[str, Any]],
    output_dir: Path,
    formats: Sequence[str],
) -> None:
    """
    Export profiles to the requested formats.

    Supported formats:
        - "json"
        - "csv"
    """
    if not profiles:
        logger.warning("No profiles provided to export.")
        return

    _ensure_output_dir(output_dir)

    normalized_formats: Set[str] = {fmt.lower() for fmt in formats} if formats else {"json"}

    if "json" in normalized_formats:
        json_path = output_dir / "truth_social_profiles.json"
        export_json(profiles, json_path)

    if "csv" in normalized_formats:
        csv_path = output_dir / "truth_social_profiles.csv"
        export_csv(profiles, csv_path)

    unsupported = normalized_formats.difference({"json", "csv"})
    for fmt in sorted(unsupported):
        logger.warning("Unsupported export format requested and ignored: %s", fmt)