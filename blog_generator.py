#!/usr/bin/env python3
"""
Generate a daily blog post from lb-market research data using the Claude API.

Usage:
  python blog_generator.py                        # uses latest JSON in data/
  python blog_generator.py data/my_file.json      # uses specific file

Requires:
  ANTHROPIC_API_KEY environment variable

Output:
  data/blog/YYYYMMDD.json   — structured post (title, body, metadata)
"""

import json
import os
import sys
import glob
from datetime import datetime, date
import anthropic


def _load_env(path: str = ".env") -> None:
    """Load key=value pairs from a .env file into os.environ (if not already set)."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_env()


BLOG_DIR = "data/blog"
MODEL = "claude-sonnet-4-6"


def load_research(data_dir: str = "data") -> tuple[dict, str]:
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        files = sorted(glob.glob(os.path.join(data_dir, "laguna_market_*.json")), reverse=True)
        if not files:
            sample = os.path.join(data_dir, "sample_laguna_market.json")
            if os.path.exists(sample):
                files = [sample]
            else:
                raise FileNotFoundError(
                    f"No research JSON found in '{data_dir}'. Run: python lb-market.py --all"
                )
        path = files[0]

    with open(path) as f:
        return json.load(f), path


def build_prompt(data: dict) -> str:
    markets = data.get("markets", {})
    events = data.get("events", [])
    weather = data.get("weather", {}).get("summary", {})
    civic = data.get("civic", {})

    market_lines = []
    for src, info in markets.items():
        desc = info.get("description", "")
        if desc:
            market_lines.append(f"- {src.title()}: {desc}")
        for k, v in info.items():
            if k not in {"url", "scraped_at", "description"}:
                market_lines.append(f"  • {k.replace('_', ' ').title()}: {v}")

    upcoming = [e for e in events if e.get("date", "") >= date.today().isoformat()]
    event_lines = [
        f"- {e['date']}: {e['description'][:120]}"
        for e in sorted(upcoming, key=lambda x: x.get("date", ""))[:8]
    ]

    projects = civic.get("upcoming_projects", [])
    project_lines = [f"- {p}" if isinstance(p, str) else f"- {p.get('topic', '')}"
                     for p in projects[:6]]

    season = weather.get("season", "current season")
    temp = weather.get("typical_range", weather.get("range", "mild"))
    conditions = weather.get("conditions", "")
    best_time = weather.get("best_time", "")

    council_freq = civic.get("city_meetings", {}).get("frequency", "")

    week_label = date.today().strftime("the week of %B %-d, %Y")
    prompt = f"""You are writing a daily real estate market update post for Laguna Beach, California, for {week_label}.

Focus specifically on what is happening RIGHT NOW this week — specific listing counts, price movements, upcoming city meetings, and local events in the next 7–10 days. Do NOT write about seasons in general. Ground every observation in the specific numbers and dates in the data below.

Tone: direct, data-backed, conversational — like a trusted local agent giving a weekly briefing to serious buyers and sellers.
Structure: a compelling title that mentions the week/date, a one-sentence subtitle with a specific stat or event, then 5–6 body paragraphs with natural paragraph breaks (no markdown headers).
End with a "Quick Stats" bullet list of the most important specific numbers and dates.

--- RESEARCH DATA ---

MARKET DATA ({date.today().strftime("%B %d, %Y")}):
{chr(10).join(market_lines) if market_lines else "Limited market data available."}

WEATHER & SEASON:
- Season: {season}
- Typical temperature range: {temp}
{f"- Conditions: {conditions}" if conditions else ""}
{f"- Best time to visit/buy: {best_time}" if best_time else ""}

UPCOMING EVENTS:
{chr(10).join(event_lines) if event_lines else "No upcoming events found."}

CIVIC & CITY COUNCIL:
- Meeting schedule: {council_freq}
{chr(10).join(project_lines) if project_lines else ""}

--- OUTPUT FORMAT (JSON) ---

Respond with ONLY valid JSON, no markdown fences:
{{
  "title": "...",
  "subtitle": "...",
  "body": "Full blog post body as plain text with paragraph breaks (\\n\\n between paragraphs).",
  "quick_stats": ["Stat 1", "Stat 2", "Stat 3", "Stat 4"]
}}"""

    return prompt


def generate_post(data: dict, source_file: str) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set.\n"
            "Export it before running: export ANTHROPIC_API_KEY=sk-ant-..."
        )

    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_prompt(data)

    print(f"  Calling Claude ({MODEL})...")
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    # Strip accidental markdown fences if model adds them
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    post_data = json.loads(raw)
    today = date.today().isoformat()

    return {
        "date": today,
        "title": post_data["title"],
        "subtitle": post_data.get("subtitle", ""),
        "body": post_data["body"],
        "quick_stats": post_data.get("quick_stats", []),
        "generated_at": datetime.now().isoformat(),
        "source_file": os.path.basename(source_file),
        "model": MODEL,
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
    }


def save_post(post: dict) -> str:
    os.makedirs(BLOG_DIR, exist_ok=True)
    filename = os.path.join(BLOG_DIR, f"{post['date']}.json")
    with open(filename, "w") as f:
        json.dump(post, f, indent=2)
    return filename


def load_all_posts() -> list[dict]:
    """Return all saved blog posts sorted newest first."""
    files = sorted(glob.glob(os.path.join(BLOG_DIR, "*.json")), reverse=True)
    posts = []
    for f in files:
        try:
            with open(f) as fh:
                posts.append(json.load(fh))
        except Exception:
            pass
    return posts


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Loading research data...")
    data, source_file = load_research()
    print(f"  Source: {source_file}")

    today = date.today().isoformat()
    out_path = os.path.join(BLOG_DIR, f"{today}.json")
    if os.path.exists(out_path):
        print(f"  Post for {today} already exists at {out_path}")
        print("  Delete it to regenerate, or pass a different source file.")
        return

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Generating blog post...")
    post = generate_post(data, source_file)

    saved = save_post(post)
    print(f"\n✓ Blog post saved: {saved}")
    print(f"\nTitle: {post['title']}")
    print(f"Subtitle: {post['subtitle']}")
    print(f"Tokens used: {post['input_tokens']} in / {post['output_tokens']} out\n")


if __name__ == "__main__":
    main()
