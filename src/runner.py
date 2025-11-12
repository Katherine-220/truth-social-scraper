import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from extractors.truth_profile_parser import build_profile
from extractors.utils_formatting import normalize_identifier
from outputs.exporters import export_profiles

DEFAULT_CONFIG: Dict[str, Any] = {
    "truth_base_url": "https://truthsocial.com",
    "output": {
        "directory": "data",
        "formats": ["json", "csv"],
    },
    "scraper": {
        "mode": "mock",
        "max_profiles": 100,
    },
    "logging": {
        "level": "INFO",
    },
}

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Truth Social Scraper - mock implementation for structured profile + post data."
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Path to identifiers JSON file (defaults to data/identifiers.sample.json).",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to settings JSON (defaults to src/config/settings.example.json).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Directory where outputs will be written (overrides config).",
    )
    parser.add_argument(
        "--output-formats",
        type=str,
        help="Comma-separated list of output formats, e.g. 'json,csv' (overrides config).",
    )
    return parser.parse_args()

def load_config(config_path: Path, base_dir: Path, logger: logging.Logger) -> Dict[str, Any]:
    config: Dict[str, Any] = dict(DEFAULT_CONFIG)
    if config_path.is_file():
        try:
            with config_path.open("r", encoding="utf-8") as f:
                file_cfg = json.load(f)
            if isinstance(file_cfg, dict):
                for key, value in file_cfg.items():
                    config[key] = value
            logger.info("Loaded configuration from %s", config_path)
        except Exception as exc:
            logger.warning("Failed to load config from %s: %s. Using defaults.", config_path, exc)
    else:
        logger.warning("Config file %s not found. Using default configuration.", config_path)

    # Normalise output directory to be relative to repo root if not absolute
    output_cfg = config.get("output", {})
    dir_value = output_cfg.get("directory", "data")
    if not isinstance(dir_value, str):
        dir_value = "data"
    if Path(dir_value).is_absolute():
        output_dir = Path(dir_value)
    else:
        output_dir = base_dir / dir_value
    output_cfg["directory"] = str(output_dir)
    config["output"] = output_cfg

    # Normalise formats
    formats = output_cfg.get("formats") or ["json"]
    if isinstance(formats, str):
        formats = [fmt.strip() for fmt in formats.split(",") if fmt.strip()]
    output_cfg["formats"] = formats
    config["output"] = output_cfg

    return config

def configure_logging(config: Dict[str, Any]) -> logging.Logger:
    logging_cfg = config.get("logging", {}) or {}
    level_name = str(logging_cfg.get("level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    return logging.getLogger("truth_social_scraper")

def load_identifiers(path: Path, logger: logging.Logger) -> List[str]:
    if not path.is_file():
        logger.error("Identifiers file %s does not exist.", path)
        raise SystemExit(1)

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        logger.error("Failed to read identifiers from %s: %s", path, exc)
        raise SystemExit(1)

    identifiers: List[str] = []
    if isinstance(data, dict) and "identifiers" in data:
        raw_list = data["identifiers"]
    elif isinstance(data, list):
        raw_list = data
    else:
        logger.error(
            "Unsupported identifiers JSON structure in %s. "
            "Use either an array or {\"identifiers\": [...]}.",
            path,
        )
        raise SystemExit(1)

    for item in raw_list:
        if not isinstance(item, str):
            logger.warning("Skipping non-string identifier entry: %r", item)
            continue
        value = item.strip()
        if not value:
            continue
        identifiers.append(value)

    if not identifiers:
        logger.error("No valid identifiers found in %s.", path)
        raise SystemExit(1)

    logger.info("Loaded %d identifiers from %s", len(identifiers), path)
    return identifiers

def build_profiles(
    identifiers: List[str],
    max_profiles: int,
    logger: logging.Logger,
) -> List[Dict[str, Any]]:
    profiles: List[Dict[str, Any]] = []
    for index, raw in enumerate(identifiers):
        if index >= max_profiles:
            logger.info(
                "Reached max_profiles limit (%d). Remaining identifiers will be skipped.",
                max_profiles,
            )
            break

        try:
            normalized, id_type = normalize_identifier(raw)
        except ValueError as exc:
            logger.warning("Skipping invalid identifier '%s': %s", raw, exc)
            continue

        logger.info("Processing identifier '%s' (type=%s)", normalized, id_type)
        profile = build_profile(normalized, id_type=id_type)
        profiles.append(profile)

    if not profiles:
        logger.error("No profiles were successfully built from the provided identifiers.")
        raise SystemExit(1)

    logger.info("Successfully built %d profile payload(s).", len(profiles))
    return profiles

def main() -> None:
    args = parse_args()

    base_dir = Path(__file__).resolve().parents[1]

    default_input = base_dir / "data" / "identifiers.sample.json"
    default_config = base_dir / "src" / "config" / "settings.example.json"

    # Temporary logger before config is loaded
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    bootstrap_logger = logging.getLogger("truth_social_scraper.bootstrap")

    input_path = Path(args.input) if args.input else default_input
    config_path = Path(args.config) if args.config else default_config

    config = load_config(config_path, base_dir=base_dir, logger=bootstrap_logger)
    logger = configure_logging(config)

    # Resolve overrides from CLI
    output_cfg = config.get("output", {})
    if args.output_dir:
        out_dir = Path(args.output_dir)
        output_cfg["directory"] = str(out_dir)
    if args.output_formats:
        formats = [fmt.strip() for fmt in args.output_formats.split(",") if fmt.strip()]
        if formats:
            output_cfg["formats"] = formats
    config["output"] = output_cfg

    identifiers = load_identifiers(input_path, logger=logger)

    scraper_cfg = config.get("scraper", {}) or {}
    max_profiles = int(scraper_cfg.get("max_profiles", 100))

    profiles = build_profiles(identifiers, max_profiles=max_profiles, logger=logger)

    output_dir = Path(config["output"]["directory"])
    formats = config["output"]["formats"]

    export_profiles(profiles, output_dir=output_dir, formats=formats)
    logger.info("Scraping run completed. Output written to %s", output_dir)

if __name__ == "__main__":
    main()