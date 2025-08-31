#!/usr/bin/env python3

import glob
import logging
import os
import sys
from datetime import datetime, timezone
from typing import List

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def setup_logging():
    """Configure logging for GitHub Actions output."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_messages_for_today() -> List[str]:
    """Load all messages that match today's date from messages/ folder and subdirectories."""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%d.%m.%y")  # European format: DD.MM.YY

    messages = []
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
                    messages.append(content)
                    logging.info(f"Loaded message from {file_path}")
                else:
                    logging.warning(f"Empty message file: {file_path}")
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
            continue

    logging.info(f"Found {len(messages)} messages for {today_str}")
    return messages


def get_today_messages() -> List[str]:
    """Get all messages for today's date."""
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
    slack_channel = os.getenv("SLACK_CHANNEL_ID")

    if not slack_token:
        logging.error("SLACK_BOT_TOKEN environment variable is required")
        sys.exit(1)

    if not slack_channel:
        logging.error("SLACK_CHANNEL_ID environment variable is required")
        sys.exit(1)

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
    for i, message in enumerate(messages, 1):
        logging.info(
            f"Posting message {i} of {len(messages)}: {message[:100]}{'...' if len(message) > 100 else ''}"
        )
        success = post_to_slack(message, slack_token, slack_channel)

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
