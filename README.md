# Daily Slack Bot

A GitHub Actions-powered Slack bot that posts messages daily to a specified Slack channel. Messages are scheduled by date using European format (DD.MM.YY) filenames, allowing precise control over when content is delivered.

## Features

- 📅 **Daily Scheduling**: Automatically runs every day at 08:00 UTC
- 🗓️ **Date-Based Messages**: Messages scheduled using European date format (DD.MM.YY)
- 📄 **File-Based Storage**: Each message stored as individual .txt files in messages/ folder
- 🔧 **Easy Management**: Add messages by creating date-named files via pull requests
- 🚀 **GitHub Actions**: No servers needed - runs entirely on GitHub infrastructure
- 🔐 **Secure**: All sensitive tokens stored as GitHub secrets
- 📝 **Detailed Logging**: Full visibility into success/failure in GitHub Actions
- 📬 **Multiple Messages**: Can post multiple messages on the same date

## Quick Setup

### 1. Create a Slack App

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app (e.g., "Weekly Motivation Bot") and select your workspace
4. In "OAuth & Permissions", add the `chat:write` bot scope
5. Install the app to your workspace
6. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### 2. Add Bot to Channel

1. Go to your target Slack channel
2. Type `/invite @YourBotName` to add the bot
3. Get the channel ID:
   - Right-click the channel → "View channel details"
   - Scroll down to find the Channel ID (starts with `C`)

### 3. Configure GitHub Secrets

In your GitHub repository, go to Settings → Secrets and Variables → Actions, then add:

- **`SLACK_BOT_TOKEN`**: Your bot token (xoxb-...)
- **`SLACK_CHANNEL_ID`**: Your target channel ID (C...)

### 4. Add Messages

Create message files in the `messages/` folder using European date format:
- `30.08.25.txt` - Message for August 30, 2025
- `25.12.25.txt` - Message for Christmas Day 2025
- `01.01.26.txt` - Message for New Year's Day 2026

## Usage

### Automatic Posting
The bot runs automatically every day at 08:00 UTC via GitHub Actions. It will only post messages if there are files matching today's date.

### Manual Testing
1. Go to Actions tab in your repository
2. Select "Daily Slack Bot" workflow
3. Click "Run workflow" to test immediately

### Adding New Messages
1. Create a new .txt file in `messages/` folder
2. Name it with the target date in DD.MM.YY format (e.g., `15.03.25.txt`)
3. Add your message content to the file
4. Create a pull request
5. Once merged, the bot will post the message on the specified date

## File Structure

```
├── slack_bot.py              # Main bot script
├── requirements.txt          # Python dependencies
├── messages/                 # Date-based message files
│   ├── 30.08.25.txt         # Message for Aug 30, 2025
│   ├── 01.09.25.txt         # Message for Sep 1, 2025
│   ├── 25.12.25.txt         # Message for Christmas 2025
│   └── 01.01.26.txt         # Message for New Year 2026
├── .github/workflows/
│   └── daily-slack-bot.yml  # GitHub Actions workflow
└── README.md                 # This file
```

## Message Selection Logic

The bot matches today's date with message filenames:
- Today is August 30, 2025 → Looks for `30.08.25.txt`
- Today is December 25, 2025 → Looks for `25.12.25.txt`
- Today is January 1, 2026 → Looks for `01.01.26.txt`

This ensures:
- Messages post on exact dates you specify
- No messages post unless specifically scheduled
- Multiple messages can be scheduled for the same date
- Full control over content timing

## Troubleshooting

### Bot Not Posting
1. Check GitHub Actions logs for error details
2. Verify bot is added to the target channel
3. Confirm `SLACK_BOT_TOKEN` and `SLACK_CHANNEL_ID` are correct
4. Ensure bot has `chat:write` permission

### Common Errors
- **`channel_not_found`**: Bot isn't added to channel or wrong channel ID
- **`not_authed`**: Invalid or expired bot token
- **`missing_scope`**: Bot lacks `chat:write` permission

### Testing Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Create a test message for today
date_today=$(date '+%d.%m.%y')
echo "Test message for today!" > "messages/${date_today}.txt"

# Set environment variables
export SLACK_BOT_TOKEN="xoxb-your-token"
export SLACK_CHANNEL_ID="C1234567890"

# Run the bot
python slack_bot.py
```

## Customization

### Changing Schedule
Edit `.github/workflows/daily-slack-bot.yml` and modify the cron expression:
```yaml
schedule:
  - cron: '0 8 * * *'  # Daily 08:00 UTC
  # - cron: '0 9 * * *'  # Daily 09:00 UTC
  # - cron: '0 8 * * 1-5'  # Weekdays only at 08:00 UTC
```

### Message Format
Messages support basic Slack formatting:
- `*bold*`
- `_italic_`
- `~strike~`
- `:emoji:`
- Links: `<https://example.com|Link Text>`

For advanced formatting, modify `slack_bot.py` to use Slack Block Kit.

## License

MIT License - feel free to use and modify for your team's needs!
