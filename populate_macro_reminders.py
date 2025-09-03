#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
import shutil
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional


# Message templates for each event type
MESSAGE_TEMPLATES = {
    "PPR": (
        "Hei alle! I dag, {dato}, publiserer Norges Bank sin pengepolitiske rapport. "
        "Dette er viktig for renteutsikter og økonomisk politikk i Norge."
    ),
    "FOMC": (
        "Hei alle! I dag, {dato}, har Fed (Den amerikanske sentralbanken) rentemøte. "
        "Dette er viktig for USD og globale renteforventninger."
    ),
    "NFP": (
        "Hei alle! I dag, {dato}, publiseres Non-Farm Payrolls. "
        "Dette er kritisk sysselsettingsdata som påvirker Fed-forventninger og USD."
    ),
}


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_paths() -> Dict[str, str]:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return {
        "macro": os.path.join(root_dir, "macro", "macro.json"),
        "out_dir": os.path.join(root_dir, "messages", "diskusjon"),
    }


def rename_macro_file_after_parsing(macro_path: str) -> str:
    """Rename the macro.json file to indicate it has been parsed."""
    if not os.path.exists(macro_path):
        return macro_path

    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = macro_path.replace(".json", f"_parsed_{timestamp}.json")

    try:
        shutil.move(macro_path, backup_path)
        logging.info(f"Renamed {macro_path} to {backup_path} after parsing")
        return backup_path
    except Exception as e:
        logging.error(f"Failed to rename macro file: {e}")
        return macro_path


def load_macro_data(macro_path: str) -> Dict[str, Dict[str, Optional[str]]]:
    if not os.path.exists(macro_path):
        raise FileNotFoundError(f"Could not find macro.json at {macro_path}")
    with open(macro_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("macro.json must contain a top-level object mapping")
    return data


def parse_period_from_key(key: str, event_type: str) -> Optional[str]:
    """Parse period information from key based on event type."""
    try:
        if not key:
            return None
        key_upper = key.upper()

        if event_type == "PPR":
            # Expected format: "Q3_2025" -> "3. kvartal 2025"
            if key_upper.startswith("Q"):
                quarter = key_upper[1]
                year = key_upper.split("_")[1] if "_" in key_upper else ""
                return (
                    f"{quarter}. kvartal {year}" if quarter.isdigit() and year else None
                )
        elif event_type in ["FOMC", "NFP"]:
            # Expected format: "Sep_2025" -> "september 2025"
            month_map = {
                "JAN": "januar",
                "FEB": "februar",
                "MAR": "mars",
                "APR": "april",
                "MAY": "mai",
                "JUN": "juni",
                "JUL": "juli",
                "AUG": "august",
                "SEP": "september",
                "OCT": "oktober",
                "NOV": "november",
                "DEC": "desember",
            }
            if "_" in key_upper:
                month_part, year_part = key_upper.split("_", 1)
                if month_part in month_map:
                    return f"{month_map[month_part]} {year_part}"
        return key  # fallback to original key if parsing fails
    except Exception:
        return key  # fallback to original key if parsing fails


def to_date(iso_date_str: str) -> date:
    # macro.json dates are in YYYY-MM-DD
    return date.fromisoformat(iso_date_str)


def safe_to_date(iso_date_str: Optional[str]) -> Optional[date]:
    """Parse a date safely; return None if invalid."""
    if not iso_date_str:
        return None
    try:
        return to_date(iso_date_str)
    except Exception:
        return None


def reminder_date(event_date: date) -> date:
    return event_date - timedelta(days=0)


def format_filename_date(d: date) -> str:
    # DD.MM.YY
    return d.strftime("%d.%m.%y")


def format_human_date(d: date) -> str:
    # DD.MM.YYYY for message body
    return d.strftime("%d.%m.%Y")


def ensure_out_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def build_message(
    event_type: str, event_date: date, period: Optional[str] = None
) -> str:
    template = MESSAGE_TEMPLATES.get(event_type, MESSAGE_TEMPLATES["PPR"])
    message = template.format(dato=format_human_date(event_date))

    if period and event_type == "PPR":
        # Add period information for PPR
        message = message.replace(
            "Pengepolitisk rapport", f"Pengepolitisk rapport for {period}"
        )

    return message


def merge_with_existing(existing: str, new_messages: List[str]) -> str:
    # Idempotent merge: only add messages that are not already present verbatim
    content = existing.strip()
    for msg in new_messages:
        if msg and msg not in content:
            content = (content + "\n\n" + msg).strip() if content else msg
    return content + "\n"


def write_daily_file(out_dir: str, d: date, messages: List[str]) -> str:
    ensure_out_dir(out_dir)
    fname = f"{format_filename_date(d)}.md"
    fpath = os.path.join(out_dir, fname)

    new_content = "\n\n".join(m.strip() for m in messages if m.strip())
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            existing = f.read()
        merged = merge_with_existing(existing, [m.strip() for m in messages])
        if merged.strip() == existing.strip():
            logging.info(
                f"No new macro reminders to add for {fname} (already up to date)"
            )
            return fpath
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(merged)
        logging.info(f"Updated {fpath} with additional macro reminders")
    else:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(new_content + "\n")
        logging.info(f"Created {fpath} with {len(messages)} macro reminder(s)")
    return fpath


def main() -> None:
    setup_logging()
    paths = get_paths()

    data = load_macro_data(
        paths["macro"]
    )  # { event_type: { period_key: "YYYY-MM-DD" | null } }

    # Collect reminders grouped by reminder date
    reminders: Dict[date, List[str]] = {}

    success_count = 0
    error_count = 0

    for event_type, periods in data.items():
        if not isinstance(periods, dict):
            logging.warning(
                f"Skipping {event_type}: expected object of period->date mappings"
            )
            continue

        if event_type not in MESSAGE_TEMPLATES:
            logging.warning(f"Unknown event type '{event_type}', skipping")
            continue

        for period_key, iso_dt in periods.items():
            if not iso_dt:
                continue  # skip null / missing dates

            period = parse_period_from_key(period_key, event_type)
            event_dt = safe_to_date(iso_dt)
            if event_dt is None:
                logging.warning(
                    f"Skipping {event_type} {period_key}: invalid date '{iso_dt}'"
                )
                error_count += 1
                continue

            try:
                rmd_dt = reminder_date(event_dt)
                msg = build_message(event_type, event_dt, period)
                reminders.setdefault(rmd_dt, []).append(msg)
                success_count += 1
                logging.debug(
                    f"Added reminder for {event_type} {period_key} on {rmd_dt}"
                )
            except Exception as e:
                logging.warning(
                    f"Skipping {event_type} {period_key}='{iso_dt}': {e}"
                )
                error_count += 1

    if not reminders:
        logging.info("No macro reminders to schedule (no upcoming event dates found)")
        return

    # Write/merge one file per reminder date
    written = 0
    for d, messages in sorted(reminders.items(), key=lambda kv: kv[0]):
        write_daily_file(paths["out_dir"], d, messages)
        written += 1

    logging.info(
        f"Prepared macro reminder files for {written} day(s) in 'messages/diskusjon'"
    )

    # Summary of processing
    logging.info(f"Successfully processed {success_count} macro events")
    if error_count > 0:
        logging.warning(f"Skipped {error_count} macro events due to errors")

    # Rename the macro.json file to indicate it has been parsed
    rename_macro_file_after_parsing(paths["macro"])


if __name__ == "__main__":
    main()
