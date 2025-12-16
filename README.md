# Daily News Analyst - Local Bot

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent news analysis bot that collects, analyzes, and delivers business intelligence reports via Telegram.

## Features

- **Multi-Source Intelligence**: Brave Search API + Industry-specific RSS feeds
- **AI-Powered Analysis**: Google Gemini for intelligent content analysis
- **Content Enrichment**: Jina AI Reader for full article extraction
- **Telegram Integration**: Direct messaging with custom topic support
- **Business Intelligence Focus**: Recycling industry in developing markets

## Quick Start

### Web Interface (Streamlit)

For a visual, interactive experience, you can run the web interface:

```bash
streamlit run streamlit_app.py
```

This will open the application in your browser where you can:

- **Run Custom Analyses**: Enter specific topics (e.g., "Tire Recycling in Iran")
- **View Real-time Progress**: Monitor each step of the intelligence collection
- **Interact with Results**: Expand and read AI-generated summaries
- **Track Statistics**: View processed article counts and priority scores

### Telegram Bot

For automated daily reporting and mobile access:

### Prerequisites

- Python 3.10+
- Telegram Bot Token ([Get from @BotFather](https://t.me/botfather))
- API Keys:
  - [Google Gemini API](https://makersuite.google.com/app/apikey)
  - [Brave Search API](https://brave.com/search/api/)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
# Required API Keys
GEMINI_API_KEY=your_gemini_api_key_here
BRAVE_API_KEY=your_brave_api_key_here
TELEGRAM_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Optional Settings
NEWS_COUNT=5
ENABLE_BRAVE_SEARCH=true
ENABLE_RSS=true
ENABLE_JINA_READER=true
DEBUG_MODE=false
```

**Finding Your Chat ID:**

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy the `Id` number it sends you

### Run the Bot

```bash
python run_local_bot.py
```

The bot will start polling for Telegram messages. Keep this terminal window open.

## Usage

### Commands

- `/news` - Get latest business intelligence (default topics)
- `/news [topic]` - Get news about a specific topic

**Examples:**

```
/news
/news MLOps
/news blockchain
/news renewable energy
```

### How It Works

1. **Message Received**: Bot receives your command via Telegram
2. **Data Collection**: Searches Brave API and RSS feeds
3. **Content Enrichment**: Extracts full article content with Jina Reader
4. **AI Analysis**: Gemini analyzes and categorizes each article
5. **Report Delivery**: Formatted reports sent to your Telegram

## Default Configuration

### Business Intelligence Sources

- **Target Markets**: Iran, China, CIS countries, Middle East
- **Industry Keywords**: Recycling, waste management, circular economy
- **RSS Feeds**: Industry-specific sources (see `app/config.py`)

### Custom Topics

When you provide a custom topic (e.g., `/news blockchain`):

- Overrides default keywords with your topic
- Clears target markets and RSS feeds
- Searches the past month (instead of past week) for better results

## Project Structure

```
daily-news-analyst/
├── app/
│   ├── config.py          # Configuration and settings
│   ├── models.py          # Data models
│   └── services/
│       ├── ai.py          # Gemini AI service
│       ├── brave_search.py # Brave Search integration
│       ├── jina_reader.py  # Content extraction
│       ├── rss.py         # RSS feed parser
│       └── telegram.py    # Telegram messaging
├── main.py                # Core analysis logic
├── run_local_bot.py       # Local bot runner
├── requirements.txt       # Python dependencies
├── .env                   # Your configuration (not in git)
└── README.md              # This file
```

## Troubleshooting

### Bot Not Responding

1. Ensure the bot is running: `python run_local_bot.py`
2. Verify your `.env` file has correct API keys
3. Check the terminal for error messages

### No Results for Custom Topics

- The bot searches the past month for custom topics
- Try broader keywords (e.g., "AI" instead of "specific AI framework")
- Check Brave Search API quota/limits

### API Rate Limits

- **Brave Search**: 429 errors indicate rate limiting
- **Gemini**: 429 errors indicate quota exceeded
- Wait a few minutes and try again

### Multiple Duplicate Messages

- Stop the bot with `Ctrl+C`
- Restart: `python run_local_bot.py`

## Advanced Configuration

Edit `app/config.py` to customize:

- Target markets
- Industry keywords
- RSS feed sources
- AI prompt template
- Alert thresholds

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.
