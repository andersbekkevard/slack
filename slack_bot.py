#!/usr/bin/env python3

import glob
import logging
import os
import sys
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def setup_logging():
    """Configure logging for GitHub Actions output."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _read_channel_id_from_directory(directory_path: str) -> Optional[str]:
    """Return channel ID from a `SLACK_CHANNEL_ID` file inside the given directory if present."""
    try:
        candidate_path = os.path.join(directory_path, "SLACK_CHANNEL_ID")
        if os.path.exists(candidate_path) and os.path.isfile(candidate_path):
            with open(candidate_path, "r", encoding="utf-8") as f:
                # Use the first non-empty line as the channel id
                for line in f:
                    channel_id = line.strip()
                    if channel_id:
                        return channel_id
    except Exception as e:
        logging.warning(f"Failed reading SLACK_CHANNEL_ID in {directory_path}: {e}")
    return None


def load_messages_for_today() -> List[Tuple[str, Optional[str], str]]:
    """Load all messages for today's date along with per-folder channel overrides.

    Returns list of tuples: (message_text, channel_id_override, source_file_path)
    """
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%d.%m.%y")  # European format: DD.MM.YY

    messages: List[Tuple[str, Optional[str], str]] = []
    # Use recursive glob pattern to search in all subdirectories
    pattern = f"messages/**/{today_str}.md"

    matching_files = glob.glob(pattern, recursive=True)

    if not matching_files:
        logging.info(f"No messages found for today ({today_str})")
        return []

    for file_path in matching_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    # Determine channel override from the message's directory
                    directory = os.path.dirname(file_path)
                    channel_override = _read_channel_id_from_directory(directory)
                    messages.append((content, channel_override, file_path))
                    if channel_override:
                        logging.info(
                            f"Loaded message from {file_path} with folder-specific channel override"
                        )
                    else:
                        logging.info(f"Loaded message from {file_path}")
                else:
                    logging.warning(f"Empty message file: {file_path}")
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
            continue

    logging.info(f"Found {len(messages)} messages for {today_str}")
    return messages


def get_today_messages() -> List[Tuple[str, Optional[str], str]]:
    """Get all messages for today's date with potential channel overrides and source file path."""
    return load_messages_for_today()


def post_to_slack(message: str, token: str, channel_id: str) -> bool:
    """Post message to Slack channel."""
    client = WebClient(token=token)

    try:
        response = client.chat_postMessage(channel=channel_id, text=message)

        if response["ok"]:
            logging.info(f"Message posted successfully to channel {channel_id}")
            logging.info(f"Message timestamp: {response['ts']}")
            return True
        else:
            logging.error(f"Slack API returned ok=False: {response}")
            return False

    except SlackApiError as e:
        logging.error(f"Slack API error: {e.response['error']}")
        if e.response.get("error") == "channel_not_found":
            logging.error(
                "Check that the bot is added to the channel and channel ID is correct"
            )
        elif e.response.get("error") == "not_authed":
            logging.error("Check that SLACK_BOT_TOKEN is valid")
        return False
    except Exception as e:
        logging.error(f"Unexpected error posting to Slack: {e}")
        return False


def main():
    """Main execution function."""
    setup_logging()
    logging.info("Starting daily Slack bot")

    # Get environment variables
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    # Default channel ID can be provided via either environment variable for convenience
    # Prefer CHANNEL_ID, fallback to SLACK_CHANNEL_ID for backward compatibility
    slack_channel = os.getenv("CHANNEL_ID") or os.getenv("SLACK_CHANNEL_ID")

    if not slack_token:
        logging.error("SLACK_BOT_TOKEN environment variable is required")
        sys.exit(1)

    if not slack_channel:
        logging.warning(
            "No default channel set (SLACK_CHANNEL_ID/CHANNEL_ID). "
            "Messages must specify a folder-level SLACK_CHANNEL_ID file."
        )

    # Load messages for today
    messages = get_today_messages()

    if not messages:
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%d.%m.%y")
        logging.info(
            f"No messages scheduled for today ({today_str}). Bot completed successfully with no action."
        )
        sys.exit(0)

    # Post all messages for today
    all_success = True
    for i, (message_text, channel_override, source_path) in enumerate(messages, 1):
        channel_to_use = channel_override or slack_channel
        preview = message_text[:100] + ("..." if len(message_text) > 100 else "")
        if channel_override:
            logging.info(
                f"Posting message {i} of {len(messages)} (override from folder): {preview}"
            )
        else:
            logging.info(
                f"Posting message {i} of {len(messages)} (default channel): {preview}"
            )

        if not channel_to_use:
            logging.error(
                f"No channel ID available for message {i} from {source_path}. "
                f"Provide SLACK_CHANNEL_ID/CHANNEL_ID env or a folder-level SLACK_CHANNEL_ID file."
            )
            all_success = False
            continue

        success = post_to_slack(message_text, slack_token, channel_to_use)

        if not success:
            all_success = False
            logging.error(f"Failed to post message {i}")
        else:
            logging.info(f"Successfully posted message {i}")

    if all_success:
        logging.info(
            f"Daily Slack bot completed successfully - posted {len(messages)} message(s)"
        )
        sys.exit(0)
    else:
        logging.error("Daily Slack bot completed with some failures")
        sys.exit(1)


if __name__ == "__main__":
    main()
