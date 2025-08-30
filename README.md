# Weekly Slack Bot

A GitHub Actions-powered Slack bot that posts one message per week to a specified Slack channel. Messages rotate based on ISO week number, ensuring consistent weekly motivation for your team.

## Features

- 📅 **Weekly Scheduling**: Automatically posts every Monday at 08:00 UTC
- 🔄 **Message Rotation**: Cycles through messages based on ISO week number
- 🔧 **Easy Management**: Messages stored in repository for easy editing via pull requests
- 🚀 **GitHub Actions**: No servers needed - runs entirely on GitHub infrastructure
- 🔐 **Secure**: All sensitive tokens stored as GitHub secrets
- 📝 **Detailed Logging**: Full visibility into success/failure in GitHub Actions

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

### 4. Customize Messages

Edit `messages.json` to add your own motivational messages. The bot will rotate through them based on the week number.

## Usage

### Automatic Posting
The bot runs automatically every Monday at 08:00 UTC via GitHub Actions.

### Manual Testing
1. Go to Actions tab in your repository
2. Select "Weekly Slack Bot" workflow
3. Click "Run workflow" to test immediately

### Adding New Messages
1. Edit `messages.json` 
2. Add your message to the array
3. Create a pull request
4. Once merged, the bot will include the new message in rotation

## File Structure

```
├── slack_bot.py              # Main bot script
├── requirements.txt          # Python dependencies
├── messages.json             # Weekly messages (edit this!)
├── .github/workflows/
│   └── weekly-slack-bot.yml  # GitHub Actions workflow
└── README.md                 # This file
```

## Message Selection Logic

The bot uses ISO week numbers (1-53) to select messages:
- Week 1 → Message 1
- Week 2 → Message 2
- Week 53 → Message 1 (if only 52 messages exist)

This ensures:
- Same message never repeats consecutively
- Predictable rotation cycle
- Deterministic selection (same week = same message)

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

# Set environment variables
export SLACK_BOT_TOKEN="xoxb-your-token"
export SLACK_CHANNEL_ID="C1234567890"

# Run the bot
python slack_bot.py
```

## Customization

### Changing Schedule
Edit `.github/workflows/weekly-slack-bot.yml` and modify the cron expression:
```yaml
schedule:
  - cron: '0 8 * * 1'  # Monday 08:00 UTC
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
