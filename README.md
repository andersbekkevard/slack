# Indøk Finance Club Slack Bot & Message Generator

A comprehensive system for generating and delivering educational content to Indøk Finance club members through both automated daily posts and AI-powered content generation.

## System Components

### 1. Slack Bot (`slack_bot.py`)
Automated daily messaging bot that delivers scheduled content to Slack channels.

### 2. Message Generator (`message_generator.py`) 
AI-powered tool that generates educational content proposals using OpenAI's API for review and scheduling.

### 3. Testing Utilities (`testing.py`)
Development tools for testing OpenAI API connectivity and streaming functionality.

## How It Works

### Automated Message Delivery
- Messages are stored as individual `.md` files in the `messages/` directory
- Files are named using European date format: `DD.MM.YY.md`
- The bot runs daily at 08:00 UTC and checks for files matching today's date
- Channel selection per message folder:
  - If a subfolder contains a file named `SLACK_CHANNEL_ID`, its first non-empty line is used as the channel ID for messages in that folder
  - Otherwise, the bot uses the default from environment: `SLACK_CHANNEL_ID` or `CHANNEL_ID`

### AI Content Generation
- Configure topics, style, and parameters in `message_generator.py`
- Generates multiple content proposals using OpenAI API
- Outputs markdown files to `inbox/` directory for review
- Includes context from previous messages and message ideas for consistency

### File Structure
```
messages/
├── misc/           # Miscellaneous messages (holidays, special events)
│   ├── 24.12.25.md # Christmas message
│   └── 31.12.25.md # New Year message
└── multippel/      # Educational content about financial multiples
    ├── 01.09.25.md # P/E ratio explanation
    ├── 08.09.25.md # EV/EBIT analysis
    └── ...         # Additional educational content

inbox/              # Generated content proposals for review
├── multippel-proposal-1-20250901-231420.md
├── multippel-proposal-2-20250901-231453.md
└── multippel-proposal-3-20250901-231531.md
```

To target a specific Slack channel for all messages in a folder, add a file named `SLACK_CHANNEL_ID` in that folder containing the channel ID (e.g. `C0123456789`). The bot will use this value for messages in that folder.

## Content Creation Workflow

### Option 1: AI-Generated Content
1. **Configure the generator**: Edit the `CONFIG` section in `message_generator.py`
   - Set `PROMPT_TITLE` and `PROMPT_BODY` for your topic
   - Adjust `NUM_PROPOSALS`, `TARGET_LENGTH`, and `TEMPERATURE`
   - Configure `CATEGORY_HINT` for organized filenames
2. **Generate proposals**: Run `python3 message_generator.py`
3. **Review output**: Check generated files in the `inbox/` directory
4. **Select and schedule**: Move chosen content to `messages/` with proper date naming

### Option 2: Manual Content Creation
1. **Create a new file** in the appropriate `messages/` subdirectory
2. **Name the file** using the target date format: `DD.MM.YY.md`
3. **Write your message** in the file
4. **Upload to GitHub** via pull request or direct commit

Optional: To send to a specific channel for that folder, create `SLACK_CHANNEL_ID` in the folder with the desired channel ID.

### Message Examples

**Educational Content** (`messages/multippel/01.09.25.md`):
```markdown
# Mandagens Multippel

P/E er et kjent konsept i finansverden. Du tar Price, altså prisen på en aksje, og deler den på Earnings, som er det årlige resultatet pr. aksje.

[Les mer](https://corporatefinanceinstitute.com/resources/valuation/price-earnings-ratio/)
```

## Technical Setup

### Required Environment Variables
```bash
# For Slack bot functionality
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_ID=C0123456789  # Default channel (optional if using folder-specific channels)

# For AI content generation
OPENAI_API_KEY=sk-your-openai-api-key
```

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run the message generator
python3 message_generator.py

# Test OpenAI connectivity
python3 testing.py "Test message"
```

### Automation
- **Platform**: GitHub Actions
- **Schedule**: Daily at 08:00 UTC
- **Language**: Python with Slack SDK and OpenAI API
- **Storage**: File-based system in Git repository
- **Channel resolution order**: folder `SLACK_CHANNEL_ID` file → env `SLACK_CHANNEL_ID` → env `CHANNEL_ID`

### Message Format
- **File Type**: Markdown (`.md`)
- **Content**: Supports Slack formatting and markdown syntax
- **Links**: Can include clickable links and references

## Current Content Categories

### Educational Series
- **Financial Multiples**: P/E, EV/EBIT, EV/EBITDA, P/B, P/NAV, EV/S
- **Industry-Specific Metrics**: EV/kg for seafood companies
- **Growth Metrics**: Rule of 40 for software companies

### Special Messages
- **Holiday Greetings**: Christmas, New Year
- **Market Commentary**: Warren Buffett-style insights

### AI Generation Configuration

Key configuration options in `message_generator.py`:

```python
CONFIG = {
    "MODEL": "gpt-4o",              # OpenAI model to use
    "TEMPERATURE": 1,               # Creativity level (0-2)
    "NUM_PROPOSALS": 3,             # Number of alternatives to generate
    "TARGET_LENGTH": "medium",      # short (~60-120), medium (~120-220), long (~220-400)
    "LANGUAGE": "Norwegian",        # Output language
    "CATEGORY_HINT": "multippel",   # Used in generated filenames
    "INCLUDE_PREVIOUS_MESSAGES": True,  # Use previous messages as context
    "INCLUDE_MESSAGE_IDEAS": True,  # Use message-ideas.md as context
}
```

## Best Practices

### AI-Generated Content
- Review all generated proposals before scheduling
- Edit content to match your voice and style
- Verify factual accuracy of financial information
- Test different temperature settings for creativity vs accuracy

### Message Creation
- Keep content educational and relevant to finance students
- Include practical examples and real-world applications
- Provide links to additional resources when appropriate

### Content Quality
- Fact-check all financial information
- Cite sources for data and quotes
- Ensure compliance with financial regulations

## Monitoring & Troubleshooting

### Daily Operations
- Check GitHub Actions logs for successful message delivery
- Monitor Slack channel for member engagement
- Review any error messages or failed deliveries

### Common Issues
- **Invalid OpenAI model**: Update `MODEL` in CONFIG to a valid model name
- **API key errors**: Verify `OPENAI_API_KEY` environment variable
- **Empty generated content**: Check API quotas and model availability
- **Channel not found**: Verify channel IDs and bot permissions
test-commit