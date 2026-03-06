"""
Content templates for Laguna Beach market analysis
"""
import json
from datetime import datetime


def generate_blog_post_title(data: dict, category: str = "market") -> str:
    """Generate a compelling blog post title based on research data"""

    season = data.get("weather", {}).get("summary", {}).get("season", "current")
    events_count = len(data.get("events", []))
    market_summary = data.get("markets", {}).get("redfin", {}).get("median_price", "")

    templates = {
        "real-estate": [
            f"Laguna Beach Real Estate: {season} Market Update ({events_count} Key Events)",
            f"Housing Boom or Bust? Laguna Beach Market Analysis for {season}",
            f"Median Price Breakdown: Laguna Beach Real Estate Trends in {season}",
            f"Is {season} the Right Time to Buy in Laguna Beach?",
            f"Market Pulse: {len(data.get('markets', {}))} Data Points on Laguna Beach Homes",
        ],
        "events": [
            f"{season} in Laguna Beach: {events_count} Events You Can't Miss",
            f"Events Driving Real Estate Interest in {season}: Laguna Beach Edition",
            f"From Beach Markets to Art Festivals: {season} Calendar Highlights",
            f"Plan Your {season} Move: {events_count} Laguna Beach Events to Know",
        ],
        "civic": [
            f"City Council Update: What's Happening in {season} in Laguna Beach",
            f"New Developments: Laguna Beach Civic News for {season}",
            f"Beach Safety and Zoning: Recent City Council Topics in {season}",
        ]
    }

    category_key = category if category in templates else "real-estate"
    return templates.get(category_key, templates["real-estate"])[0]


def generate_content_outline(data: dict, post_type: str = "blog") -> list:

    sections = {
        "blog": [
            "# {title}\n\n",
            "## Executive Summary\n",
            "Key takeaways in 2-3 short paragraphs.\n\n",
            "## Market Overview\n",
            "- Price trends and sales activity\n",
            "- Inventory levels\n",
            "- Days on market\n\n",
            "## Seasonal Context\n",
            "Based on current weather and conditions\n\n",
            "## Event Impact\n",
            "How {events_count} upcoming events may affect buyer/seller behavior\n\n",
            "## Civic Update\n",
            "Recent council decisions and board activity\n\n",
            "## Expert Take\n",
            "What trends mean for {season}-season buyers/sellers\n\n",
            "## Quick Stats\n",
            "1. Median price: ${avg_price:,}\n",
            "2. Market days: {doym}\n",
            "3. Events coming: {events_count}\n",
            "4. Interest rate context: {rate_context}\n\n",
            "# Sources\n",
            "Data from Redfin, Movoto, Zillow, LC Chamber, City Council..."
        ],
        "interview": [
            "### Opening Question: {season} Market Assessment\n",
            "{exper_summary}\n\n",
            "### Real Estate Trends\n",
            "Follow up with market stats and trends from research data.\n\n",
            "### Seasonal Nuances\n",
            "Discuss weather and seasonal conditions and how they impact real estate.\n\n",
            "### Event Influence\n",
            "Ask about upcoming events and their market impact.\n\n",
            "### Civic & Planning\n",
            "Discuss development projects and city council decisions.\n\n",
            "### Conclusion\n",
            "Summary for prospective buyers/sellers."
        ]
    }

    season = data.get("weather", {}).get("summary", {}).get("season", "N/A")
    events_count = len(data.get("events", []))
    markets = data.get("markets", {})
    avg_price = markets.get("redfin", {}).get("median_price", "$0")
    doym = "114 days"  # Example from search results

    outline = sections.get(post_type, sections["blog"])[:]

    return outline.format(
        title=generate_blog_post_title(data),
        season=season,
        events_count=events_count,
        avg_price=avg_price,
        doym=doym,
        exper_summary="Share expert perspective based on 15 years in the Laguna Beach market.",
        rate_context="Assume current interest rates per market conditions."
    )


def generate_question_bank(data: dict) -> list:

    return [
        "How has the real estate market shifted this {season} compared to last year?",
        "What are the biggest opportunities for buyers this {season}?",
        "How do upcoming events affect home prices in Laguna Beach?",
        "What are the top city council priorities impacting property values?",
        "Is this the right time to sell a second home, given seasonal conditions?",
        "How are inventory levels affecting buyer competition?",
        "What's driving the median price trends in the {neighborhood} area?",
        "How do local events and civic decisions impact long-term property appreciation?",
    ]


def load_research_file(filepath: str) -> dict:
    """Load research data from JSON file"""

    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filepath} not found. Please run lb-market.py --all first.")
        return {}


# Template usage examples
# title = generate_blog_post_title(data)
# outline = generate_content_outline(data, "blog")
# questions = generate_question_bank(data)