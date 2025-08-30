PRD: Weekly Slack Bot (Python + GitHub Actions)
Objective

A Slack bot that posts one message per week into a specified Slack channel. Messages are curated in the repository itself, so non-technical contributors can easily add or modify content. The bot will be triggered automatically by a GitHub Actions workflow on a schedule (cron job).

Functional Requirements
1. Message Management

Message Source:
Messages are stored in the repository. Two options must be supported:

JSON file (messages.json) containing an array of strings.

(Optional extension) Directory of Markdown/text files (/messages/) where each file contains one message.

Message Selection Strategy:

Default: Rotate by ISO week number. Example: week 1 uses message 1, week 2 uses message 2, wrapping around if messages are fewer than weeks.

Alternate: Random selection seeded by week number (so the same week always yields the same message, making runs deterministic).

2. Posting to Slack

Target Channel: Configured via an environment variable (SLACK_CHANNEL_ID).

Authentication: Uses a Slack Bot User OAuth Token (xoxb-...) stored securely as a GitHub Actions secret (SLACK_BOT_TOKEN).

Message Format:

Plain text by default.

Should be possible to extend to Slack Block Kit
 if needed.

3. Scheduling

Runs once per week via GitHub Actions.

Default schedule: Monday at 08:00 UTC (cron: "0 8 * * 1").

Workflow should also support manual dispatch for testing.

Non-Functional Requirements
1. Reliability

The workflow must fail loudly if Slack rejects the request (e.g. invalid token, missing permissions, wrong channel).

Logs must clearly show success or failure in GitHub Actions.

2. Security

No secrets are hard-coded in the repo.

All sensitive values (SLACK_BOT_TOKEN, SLACK_CHANNEL_ID) are provided through GitHub Actions secrets.

3. Maintainability

Messages live in repo so contributors can update via pull requests.

Adding a new message should not require touching bot code.

Codebase must be minimal: a single Python script and requirements file.

Dependencies
Python Libraries

slack_sdk: Official Slack SDK for Python, handles authentication and posting.

json: Standard library for reading messages.json.

datetime: Standard library for calculating week numbers.

logging: Standard library for structured logging.

(Optional) os for environment variable handling.

(Optional) random for seeded random selection.

GitHub Actions

actions/checkout: Fetches repo content.

actions/setup-python: Installs Python (3.11 preferred).

Workflow steps to install dependencies (pip install -r requirements.txt) and run the bot script.

Process Flow
1. Developer Setup

Create a Slack App in the target workspace.

Add chat:write bot scope.

Install app to workspace and invite bot to the desired channel.

Copy the Bot User OAuth Token (xoxb-...).

Find the channel ID of the target channel.

Store both in GitHub Actions secrets.

2. Weekly Execution (Automated via GitHub Actions)

Trigger: Cron job fires Monday 08:00 UTC.

Checkout: GitHub Action pulls repo.

Setup: Python is installed, dependencies resolved.

Run Script:

Script loads messages from repo.

Picks correct message based on week number or random seed.

Authenticates with Slack API using secrets.

Posts message to target channel.

Validation: Logs success/failure to GitHub Actions console.

Fallback: If it fails (invalid token, wrong channel, etc.), workflow reports failure so maintainers can investigate.

3. Manual Execution

A maintainer can trigger the workflow manually via GitHub UI (workflow_dispatch) for testing or ad-hoc posting.

Desired Behavior Summary

Once a week, the bot posts one message in the chosen Slack channel.

Messages come from a file (JSON or per-file basis).

The same message never repeats within the same cycle of the file.

GitHub Actions manages execution; no servers or cron jobs are needed by the team.

Anyone can update the content by editing the repo.