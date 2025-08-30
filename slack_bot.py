#!/usr/bin/env python3

import json
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
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_messages() -> List[str]:
    """Load messages from messages.json file."""
    try:
        with open('messages.json', 'r', encoding='utf-8') as f:
            messages = json.load(f)
        
        if not isinstance(messages, list) or not messages:
            raise ValueError("messages.json must contain a non-empty array of strings")
        
        logging.info(f"Loaded {len(messages)} messages from messages.json")
        return messages
    
    except FileNotFoundError:
        logging.error("messages.json file not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in messages.json: {e}")
        sys.exit(1)
    except ValueError as e:
        logging.error(f"Invalid message format: {e}")
        sys.exit(1)


def get_week_message(messages: List[str]) -> str:
    """Select message based on ISO week number (rotating)."""
    now = datetime.now(timezone.utc)
    week_number = now.isocalendar()[1]  # ISO week number (1-53)
    
    message_index = (week_number - 1) % len(messages)
    selected_message = messages[message_index]
    
    logging.info(f"Week {week_number}: Selected message {message_index + 1} of {len(messages)}")
    return selected_message


def post_to_slack(message: str, token: str, channel_id: str) -> bool:
    """Post message to Slack channel."""
    client = WebClient(token=token)
    
    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=message
        )
        
        if response["ok"]:
            logging.info(f"Message posted successfully to channel {channel_id}")
            logging.info(f"Message timestamp: {response['ts']}")
            return True
        else:
            logging.error(f"Slack API returned ok=False: {response}")
            return False
            
    except SlackApiError as e:
        logging.error(f"Slack API error: {e.response['error']}")
        if e.response.get('error') == 'channel_not_found':
            logging.error("Check that the bot is added to the channel and channel ID is correct")
        elif e.response.get('error') == 'not_authed':
            logging.error("Check that SLACK_BOT_TOKEN is valid")
        return False
    except Exception as e:
        logging.error(f"Unexpected error posting to Slack: {e}")
        return False


def main():
    """Main execution function."""
    setup_logging()
    logging.info("Starting weekly Slack bot")
    
    # Get environment variables
    slack_token = os.getenv('SLACK_BOT_TOKEN')
    slack_channel = os.getenv('SLACK_CHANNEL_ID')
    
    if not slack_token:
        logging.error("SLACK_BOT_TOKEN environment variable is required")
        sys.exit(1)
    
    if not slack_channel:
        logging.error("SLACK_CHANNEL_ID environment variable is required")
        sys.exit(1)
    
    # Load and select message
    messages = load_messages()
    message = get_week_message(messages)
    
    logging.info(f"Selected message: {message[:100]}{'...' if len(message) > 100 else ''}")
    
    # Post to Slack
    success = post_to_slack(message, slack_token, slack_channel)
    
    if success:
        logging.info("Weekly Slack bot completed successfully")
        sys.exit(0)
    else:
        logging.error("Weekly Slack bot failed")
        sys.exit(1)


if __name__ == "__main__":
    main()