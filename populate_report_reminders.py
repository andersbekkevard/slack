#!/usr/bin/env python3

import json
import logging
import os
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional


# Message format (Norwegian)
# Example output:
# "Hei alle! MOWI slipper 3.kvartalsrapport 05.11.2025. Analysegruppen har analyseansvar, men alle oppfordres til å følge med."
MESSAGE_TEMPLATE = (
    "Hei alle! {selskap} slipper {kvartal}.kvartalsrapport {dato}. "
    "{gruppe} har analyseansvar, men alle oppfordres til å følge med."
)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_paths() -> Dict[str, str]:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return {
        "reports": os.path.join(root_dir, "reports.json"),
        "out_dir": os.path.join(root_dir, "messages", "diskusjon"),
    }


def load_reports(reports_path: str) -> Dict[str, Dict[str, Optional[str]]]:
    if not os.path.exists(reports_path):
        raise FileNotFoundError(f"Could not find reports.json at {reports_path}")
    with open(reports_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("reports.json must contain a top-level object mapping")
    return data


def parse_quarter_from_key(key: str) -> Optional[int]:
    # Expected format: "Q3_2025" -> 3
    try:
        if not key:
            return None
        key_upper = key.upper()
        if key_upper.startswith("Q"):
            # take characters after Q until next non-digit
            num = ""
            for ch in key_upper[1:]:
                if ch.isdigit():
                    num += ch
                else:
                    break
            return int(num) if num else None
        return None
    except Exception:
        return None


def to_date(iso_date_str: str) -> date:
    # reports.json dates are in YYYY-MM-DD
    return date.fromisoformat(iso_date_str)


def reminder_date(report_date: date) -> date:
    return report_date - timedelta(days=3)


def format_filename_date(d: date) -> str:
    # DD.MM.YY
    return d.strftime("%d.%m.%y")


def format_human_date(d: date) -> str:
    # DD.MM.YYYY for message body
    return d.strftime("%d.%m.%Y")


def ensure_out_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def build_message(
    ticker: str, quarter_num: int, report_dt: date, group_name: str
) -> str:
    return MESSAGE_TEMPLATE.format(
        selskap=ticker,
        kvartal=quarter_num,
        dato=format_human_date(report_dt),
        gruppe=group_name,
    )


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
            logging.info(f"No new reminders to add for {fname} (already up to date)")
            return fpath
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(merged)
        logging.info(f"Updated {fpath} with additional reminders")
    else:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(new_content + "\n")
        logging.info(f"Created {fpath} with {len(messages)} reminder(s)")
    return fpath


def main() -> None:
    setup_logging()
    paths = get_paths()

    group_name = os.getenv("ANALYSE_GRUPPE", "Analysegruppen")

    data = load_reports(
        paths["reports"]
    )  # { ticker: { Qx_YYYY: "YYYY-MM-DD" | null } }

    # Collect reminders grouped by reminder date
    reminders: Dict[date, List[str]] = {}

    for ticker, quarters in data.items():
        if not isinstance(quarters, dict):
            logging.warning(
                f"Skipping {ticker}: expected object of quarter->date mappings"
            )
            continue
        for qkey, iso_dt in quarters.items():
            if not iso_dt:
                continue  # skip null / missing dates
            try:
                qnum = parse_quarter_from_key(qkey)
                if qnum is None:
                    logging.warning(
                        f"Could not parse quarter from key '{qkey}' for {ticker}; skipping"
                    )
                    continue
                rpt_dt = to_date(iso_dt)
                rmd_dt = reminder_date(rpt_dt)
                msg = build_message(ticker, qnum, rpt_dt, group_name)
                reminders.setdefault(rmd_dt, []).append(msg)
            except Exception as e:
                logging.warning(f"Skipping {ticker} {qkey}='{iso_dt}': {e}")

    if not reminders:
        logging.info("No reminders to schedule (no upcoming report dates found)")
        return

    # Write/merge one file per reminder date
    written = 0
    for d, messages in sorted(reminders.items(), key=lambda kv: kv[0]):
        write_daily_file(paths["out_dir"], d, messages)
        written += 1

    logging.info(
        f"Prepared reminder files for {written} day(s) in 'messages/diskusjon'"
    )


if __name__ == "__main__":
    main()
