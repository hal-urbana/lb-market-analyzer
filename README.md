# Laguna Beach Market Analyzer

Research bot for real estate market analysis in Laguna Beach, California.

**Purpose:** Generate current market data, event calendars, weather information, and civic updates for blog posts and interview content.

## Features

- **Real Estate Research**: Aggregate data from Redfin, Movoto, Zillow, and local agents
- **Events Calendar**: Fetch upcoming festivals, markets, concerts, and city events
- **Weather Monitoring**: Track seasonal conditions and forecasts
- **Civic Updates**: Monitor city council meetings, agendas, and board activities
- **JSON Output**: Structured data ready for content creation

## Installation

```bash
# Clone or download this repository
git clone http://192.168.10.42/hal/laguna-beach-market-analyzer.git
cd laguna-beach-market-analyzer

# Install dependencies
pip install -r requirements.txt
```

**Dependencies:**
- requests (2.31.0+)
- beautifulsoup4 (4.12+)
- lxml (for parsing)

## Usage

### Run Full Research

```bash
# Run all research modules
python lb-market.py --all

# Output: data/laguna_market_YYYYMMDD_HHMMSS.json
```

### Run Specific Module

```bash
# Real estate only
python lb-market.py --only real-estate

# Events only
python lb-market.py --only events

# Weather only
python lb-market.py --only weather

# Civic only
python lb-market.py --only civic
```

### Dry Run (Demo)

```bash
python lb-market.py --dry-run --only real-estate
```

### Output Directory

```bash
python lb-market.py --all --output /path/to/output
```

## Output Structure

### JSON Output Format

```json
{
  "metadata": {
    "generated_at": "2026-03-05T17:00:00",
    "timezone": "America/Los_Angeles"
  },
  "markets": {
    "redfin": {
      "url": "https://...",
      "description": "Current market data",
      "scraped_at": "..."
    }
  },
  "events": [
    {
      "date": "2026-03-15",
      "description": "Event description",
      "source": "https://...",
      "note": "parsed from html"
    }
  ],
  "weather": {
    "summary": {
      "season": "Spring",
      "range": "72-73°F",
      "conditions": "varies by season"
    },
    "sources": {
      "https://weatherspark.com/...": {
        "last_checked": "..."
      }
    }
  },
  "civic": {
    "city_meetings": {
      "frequency": "2nd and 4th Tuesdays, 5:00 PM",
      "portal": "https://...",
      "upcoming_items": ["Topic 1", "Topic 2"]
    }
  }
}
```

## Automated Research (Cron)

### Run hourly research

**Setup:**
Create a systemd cron job or use the included cron template.

```bash
# Example: Run every morning at 8:00 AM PST
0 8 * * * cd /home/hal/laguna-beach-market-analyzer && python lb-market.py --all
```

### Cron Template (example)

```bash
# Add to crontab
crontab -e

# Hourly research (every hour)
0 * * * * cd /home/hal/laguna-beach-market-analyzer && /usr/bin/python3 lb-market.py --all

# Daily full research (midnight)
0 0 * * * cd /home/hal/laguna-beach-market-analyzer && /usr/bin/python3 lb-market.py --all --output /home/hal/laguna-data/daily
```

## Research Sources

### Real Estate
- Redfin market page
- Movoto trends
- Zillow ZHVI
- Local agent market reports

### Events
- Laguna Beach City website events
- Patch.com calendar
- Chamber of Commerce
- Eventbrite listings

### Weather
- Weatherspark climate data
- Weather.com forecasts

### Civic
- City Council meeting portal
- Board and commission listings
- Meeting agendas and minutes

## Integration with Content Creation

### Blog Post Writing

1. **Generate research:**
   ```bash
   python lb-market.py --all
   ```

2. **Load JSON:**
   ```python
   import json
   with open("data/laguna_market_20260305.json") as f:
       data = json.load(f)
   ```

3. **Template structure:**
   ```python
   title = f"Laguna Beach Market: {data['weather']['summary']['season']} Update"
   body = f"""
   Current median: ${data['markets']['redfin']['median_price']}
   Best time to buy/sell: Based on {len(data['events'])} upcoming events
   Council meetings: {data['civic']['city_meetings']['frequency']}
   """
   ```

### In-Person Interviews

Sample questions derived from research:
- "How is the real estate market doing this season?"
- "What events drive buyer interest in August?"
- "What are the key city council topics currently?"

## Data Sources Note

- All sources are publicly accessible web pages
- Automatic scraping with user-agent identification
- Respectful rate limiting (minimal delays between requests)
- Results cached locally in CSV/JSON format
- Never stores personal or identifying data

## License

Internal USM Labs project for hal@usmlabs.com

---

**Author:** HAL 9000 AI Agent
**Version:** 1.0.0
**Last Updated:** 2026-03-05