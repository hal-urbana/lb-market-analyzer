#!/usr/bin/env python3
"""
Generate an HTML dashboard from the latest lb-market JSON output.
Usage: python dashboard.py [path/to/file.json]
Output: data/dashboard.html
"""

import json
import os
import sys
import glob
from datetime import datetime, date


def load_latest(data_dir: str = "data") -> tuple[dict, str]:
    """Return (data, filepath) for the most recent JSON file in data_dir."""
    pattern = os.path.join(data_dir, "laguna_market_*.json")
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        # Fall back to sample
        sample = os.path.join(data_dir, "sample_laguna_market.json")
        if os.path.exists(sample):
            files = [sample]
        else:
            raise FileNotFoundError(
                f"No JSON files found in '{data_dir}'. Run: python lb-market.py --all"
            )
    path = files[0]
    with open(path) as f:
        return json.load(f), path


def _badge(text: str, color: str) -> str:
    return f'<span class="badge" style="background:{color}">{text}</span>'


def _fmt_ts(ts: str) -> str:
    """Format an ISO timestamp to a short human-readable form."""
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%b %d %I:%M %p")
    except Exception:
        return ts


def _pct_color(pct_str: str) -> str:
    """Return green for positive, red for negative change strings."""
    s = pct_str.strip().lstrip("(").rstrip(")")
    if s.startswith("+") or (s[0].isdigit() and "+" in s):
        return "#27ae60"
    if s.startswith("-"):
        return "#e74c3c"
    return "#7f8c8d"


def load_blog_posts(blog_dir: str = "data/blog") -> list[dict]:
    """Return all saved blog posts sorted newest first."""
    files = sorted(glob.glob(os.path.join(blog_dir, "*.json")), reverse=True)
    posts = []
    for f in files:
        try:
            with open(f) as fh:
                posts.append(json.load(fh))
        except Exception:
            pass
    return posts


def render_blog_today(post: dict) -> str:
    """Render today's blog post as the hero section."""
    title = post.get("title", "Today's Market Update")
    subtitle = post.get("subtitle", "")
    body = post.get("body", "")
    stats = post.get("quick_stats", [])
    generated_at = _fmt_ts(post.get("generated_at", ""))
    model = post.get("model", "")

    # Convert plain-text paragraphs to <p> tags
    paragraphs = "".join(
        f"<p>{p.strip()}</p>" for p in body.split("\n\n") if p.strip()
    )

    stats_html = ""
    if stats:
        items = "".join(f"<li>{s}</li>" for s in stats)
        stats_html = f'<ul class="blog-stats">{items}</ul>'

    meta = f'Generated {generated_at} · {model}' if generated_at else ""

    return f"""
    <div class="blog-today">
      <div class="blog-today-label">Today&#39;s Blog Post</div>
      <h2 class="blog-title">{title}</h2>
      {f'<p class="blog-subtitle">{subtitle}</p>' if subtitle else ''}
      <div class="blog-body">{paragraphs}</div>
      {stats_html}
      {f'<p class="blog-meta">{meta}</p>' if meta else ''}
    </div>"""


def render_blog_history(posts: list[dict]) -> str:
    """Render past blog posts as an expandable archive list."""
    today = date.today().isoformat()
    past = [p for p in posts if p.get("date", "") != today]
    if not past:
        return "<p class='empty'>No previous posts yet. Run blog_generator.py daily to build history.</p>"

    items = ""
    for post in past:
        post_date = post.get("date", "")
        try:
            label = datetime.fromisoformat(post_date).strftime("%B %d, %Y")
        except Exception:
            label = post_date
        title = post.get("title", "Market Update")
        subtitle = post.get("subtitle", "")
        body = post.get("body", "")
        preview = body[:280].rsplit(" ", 1)[0] + "…" if len(body) > 280 else body
        stats = post.get("quick_stats", [])
        stats_html = "".join(f"<li>{s}</li>" for s in stats)
        paragraphs = "".join(
            f"<p>{p.strip()}</p>" for p in body.split("\n\n") if p.strip()
        )

        items += f"""
        <details class="history-entry">
          <summary>
            <span class="history-date">{label}</span>
            <span class="history-title">{title}</span>
            <span class="history-preview">{preview}</span>
          </summary>
          <div class="history-body">
            {f'<p class="blog-subtitle">{subtitle}</p>' if subtitle else ''}
            {paragraphs}
            {f'<ul class="blog-stats">{stats_html}</ul>' if stats_html else ''}
          </div>
        </details>"""

    return f'<div class="history-list">{items}</div>'


def render_markets(markets: dict) -> str:
    if not markets:
        return "<p class='empty'>No market data collected.</p>"
    cards = []
    for source, info in markets.items():
        rows = ""
        skip = {"url", "scraped_at", "description"}
        desc = info.get("description", "")
        scraped_at = info.get("scraped_at", "")
        for k, v in info.items():
            if k in skip:
                continue
            label = k.replace("_", " ").title()
            color = _pct_color(str(v)) if "change" in k or "%" in str(v) else "#2c3e50"
            rows += f'<tr><td>{label}</td><td style="color:{color};font-weight:600">{v}</td></tr>'
        url = info.get("url", "#")
        ts_html = f'<span class="ts">scraped {_fmt_ts(scraped_at)}</span>' if scraped_at else ""
        cards.append(f"""
        <div class="card">
          <div class="card-header">
            <span class="source-name">{source.title()}</span>
            <a href="{url}" target="_blank" class="source-link">View Source &rarr;</a>
          </div>
          {f'<p class="desc">{desc}</p>' if desc else ''}
          <table class="stat-table">{rows}</table>
          {ts_html}
        </div>""")
    return "\n".join(cards)


def render_sources(data: dict) -> str:
    """Render a full sources log: every URL fetched, its timestamp, and status."""
    rows = ""

    def _row(module: str, url: str, ts: str, note: str = ""):
        status_dot = '<span style="color:#27ae60;font-size:1.1em">&#9679;</span>' if ts else \
                     '<span style="color:#e74c3c;font-size:1.1em">&#9679;</span>'
        ts_fmt = _fmt_ts(ts) if ts else "not fetched"
        note_cell = f'<span style="color:#7f8c8d">{note}</span>' if note else ""
        rows_ref = []
        rows_ref.append(
            f'<tr><td>{status_dot}</td><td class="mod-badge mod-{module.lower()}">{module}</td>'
            f'<td><a href="{url}" target="_blank">{url}</a></td>'
            f'<td>{ts_fmt}</td><td>{note_cell}</td></tr>'
        )
        return rows_ref[0]

    # Markets
    for src, info in data.get("markets", {}).items():
        rows += _row("Markets", info.get("url", ""), info.get("scraped_at", ""),
                     info.get("description", "")[:80])

    # Events sources
    events = data.get("events", [])
    seen_event_srcs = {}
    for ev in events:
        src = ev.get("source", "")
        if src and src not in seen_event_srcs:
            seen_event_srcs[src] = ev.get("date", "")
    for src, _ in seen_event_srcs.items():
        rows += _row("Events", src, "", f"{sum(1 for e in events if e.get('source')==src)} event(s) parsed")

    # Weather sources
    for url, meta in data.get("weather", {}).get("sources", {}).items():
        rows += _row("Weather", url, meta.get("last_checked", ""))

    # Civic
    civic = data.get("civic", {})
    portal = civic.get("city_meetings", {}).get("portal", "")
    if portal:
        rows += _row("Civic", portal, "")

    if not rows:
        return "<p class='empty'>No source data recorded.</p>"

    return f"""
    <table class="event-table">
      <thead><tr>
        <th style="width:30px"></th>
        <th style="width:80px">Module</th>
        <th>URL</th>
        <th style="width:160px">Fetched At</th>
        <th>Note</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def render_events(events: list) -> str:
    if not events:
        return "<p class='empty'>No events collected.</p>"
    today = datetime.now().strftime("%Y-%m-%d")
    rows = ""
    for ev in sorted(events, key=lambda x: x.get("date", "")):
        date = ev.get("date", "?")
        desc = ev.get("description", "")[:120]
        src = ev.get("source", "#")
        past = date < today
        row_class = "past" if past else ""
        rows += f"""
        <tr class="{row_class}">
          <td class="event-date">{date}</td>
          <td>{desc}</td>
          <td><a href="{src}" target="_blank">source</a></td>
        </tr>"""
    return f'<table class="event-table"><thead><tr><th>Date</th><th>Description</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table>'


def render_weather(weather: dict) -> str:
    s = weather.get("summary", {})
    if not s:
        return "<p class='empty'>No weather data collected.</p>"
    season = s.get("season", "N/A")
    rng = s.get("typical_range", s.get("range", "N/A"))
    cond = s.get("conditions", "N/A")
    best = s.get("best_time", "")
    season_icons = {"Spring": "🌸", "Summer": "☀️", "Fall": "🍂", "Winter": "❄️"}
    icon = season_icons.get(season, "")
    best_row = f"<tr><td>Best Time to Visit</td><td>{best}</td></tr>" if best else ""
    return f"""
    <div class="card">
      <div class="card-header"><span class="source-name">{icon} {season} Conditions</span></div>
      <table class="stat-table">
        <tr><td>Typical Range</td><td style="font-weight:600">{rng}</td></tr>
        <tr><td>Conditions</td><td>{cond}</td></tr>
        {best_row}
      </table>
    </div>"""


def render_civic(civic: dict) -> str:
    if not civic:
        return "<p class='empty'>No civic data collected.</p>"
    cm = civic.get("city_meetings", {})
    freq = cm.get("frequency", "N/A")
    portal = cm.get("portal", "#")
    deadline = cm.get("online_comments_deadline", "")
    boards = civic.get("boards_commissions", [])
    projects = civic.get("upcoming_projects", [])

    board_items = "".join(f"<li>{b}</li>" for b in boards)
    project_items = "".join(f"<li>{p}</li>" for p in projects)

    deadline_row = f"<tr><td>Comment Deadline</td><td>{deadline}</td></tr>" if deadline else ""
    return f"""
    <div class="card">
      <div class="card-header"><span class="source-name">City Council</span>
        <a href="{portal}" target="_blank" class="source-link">Meeting Portal &rarr;</a>
      </div>
      <table class="stat-table">
        <tr><td>Schedule</td><td style="font-weight:600">{freq}</td></tr>
        {deadline_row}
      </table>
    </div>
    <div class="card" style="margin-top:16px">
      <div class="card-header"><span class="source-name">Boards &amp; Commissions</span></div>
      <ul class="simple-list">{board_items}</ul>
    </div>
    <div class="card" style="margin-top:16px">
      <div class="card-header"><span class="source-name">Upcoming Projects</span></div>
      <ul class="simple-list">{project_items}</ul>
    </div>"""


def build_html(data: dict, source_file: str, blog_posts: list[dict] = None) -> str:
    generated = data.get("metadata", {}).get("generated_at", "unknown")
    try:
        dt = datetime.fromisoformat(generated)
        generated_fmt = dt.strftime("%B %d, %Y at %I:%M %p")
    except Exception:
        generated_fmt = generated

    now_fmt = datetime.now().strftime("%B %d, %Y %I:%M %p")
    markets_html = render_markets(data.get("markets", {}))
    events_html = render_events(data.get("events", []))
    weather_html = render_weather(data.get("weather", {}))
    civic_html = render_civic(data.get("civic", {}))
    sources_html = render_sources(data)

    if blog_posts is None:
        blog_posts = []
    today_str = date.today().isoformat()
    today_post = next((p for p in blog_posts if p.get("date") == today_str), None)
    blog_today_html = render_blog_today(today_post) if today_post else ""
    blog_history_html = render_blog_history(blog_posts)
    blog_count = len(blog_posts)

    market_count = len(data.get("markets", {}))
    event_count = len(data.get("events", []))
    season = data.get("weather", {}).get("summary", {}).get("season", "")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Laguna Beach Market Intelligence &mdash; Marcus Skenderian</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #f0f2f5;
      color: #2c3e50;
      min-height: 100vh;
    }}
    /* ── Header / branding ── */
    header {{
      background: linear-gradient(135deg, #1a3a5c 0%, #2e86ab 100%);
      color: white;
      padding: 24px 40px 20px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .header-brand h1 {{ font-size: 1.65rem; font-weight: 700; letter-spacing: -0.5px; }}
    .header-brand p {{ opacity: 0.75; font-size: 0.85rem; margin-top: 3px; }}
    .header-agent {{
      text-align: right;
      font-size: 0.85rem;
      opacity: 0.9;
      line-height: 1.5;
    }}
    .header-agent strong {{ font-size: 1rem; display: block; }}
    .header-agent a {{ color: #a8d8f0; text-decoration: none; }}
    .header-agent a:hover {{ text-decoration: underline; }}
    .header-logo {{
      height: 52px;
      width: auto;
      display: block;
      filter: brightness(0) invert(1);
      opacity: 0.92;
    }}
    .stat-bar {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      padding: 12px 40px;
      background: #1a3a5c;
      border-top: 1px solid rgba(255,255,255,0.1);
    }}
    .stat-pill {{
      background: rgba(255,255,255,0.15);
      color: white;
      padding: 5px 14px;
      border-radius: 20px;
      font-size: 0.82rem;
      font-weight: 500;
    }}
    main {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}
    .section-title {{
      font-size: 1.05rem;
      font-weight: 700;
      color: #1a3a5c;
      margin: 32px 0 12px;
      padding-bottom: 8px;
      border-bottom: 2px solid #2e86ab;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .section-title:first-child {{ margin-top: 0; }}
    /* ── Blog hero ── */
    .blog-today {{
      background: white;
      border-radius: 12px;
      padding: 32px 36px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
      border-left: 5px solid #2e86ab;
      margin-bottom: 8px;
    }}
    .blog-today-label {{
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #2e86ab;
      margin-bottom: 10px;
    }}
    .blog-title {{
      font-size: 1.7rem;
      font-weight: 800;
      color: #1a3a5c;
      line-height: 1.25;
      margin-bottom: 8px;
    }}
    .blog-subtitle {{
      font-size: 1.05rem;
      color: #555;
      margin-bottom: 20px;
      font-style: italic;
    }}
    .blog-body p {{
      line-height: 1.75;
      color: #2c3e50;
      margin-bottom: 14px;
      font-size: 0.97rem;
    }}
    .blog-body p:last-child {{ margin-bottom: 0; }}
    .blog-stats {{
      list-style: none;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 20px;
      padding: 16px;
      background: #f0f6fb;
      border-radius: 8px;
    }}
    .blog-stats li {{
      font-size: 0.85rem;
      font-weight: 600;
      color: #1a3a5c;
      background: white;
      padding: 5px 14px;
      border-radius: 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.07);
    }}
    .blog-meta {{
      margin-top: 16px;
      font-size: 0.78rem;
      color: #aaa;
    }}
    /* ── Blog history ── */
    .history-list {{ display: flex; flex-direction: column; gap: 8px; }}
    .history-entry {{
      background: white;
      border-radius: 10px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.07);
      overflow: hidden;
    }}
    .history-entry summary {{
      display: grid;
      grid-template-columns: 120px 1fr;
      grid-template-rows: auto auto;
      gap: 2px 12px;
      padding: 14px 18px;
      cursor: pointer;
      user-select: none;
      list-style: none;
    }}
    .history-entry summary::-webkit-details-marker {{ display: none; }}
    .history-entry summary::after {{
      content: "▸";
      grid-row: 1 / 3;
      grid-column: 3;
      color: #2e86ab;
      align-self: center;
      font-size: 1rem;
      margin-left: auto;
    }}
    details[open] summary::after {{ content: "▾"; }}
    .history-date {{
      grid-row: 1; grid-column: 1;
      font-size: 0.8rem;
      font-weight: 700;
      color: #2e86ab;
      align-self: center;
    }}
    .history-title {{
      grid-row: 1; grid-column: 2;
      font-weight: 700;
      font-size: 0.95rem;
      color: #1a3a5c;
    }}
    .history-preview {{
      grid-row: 2; grid-column: 2;
      font-size: 0.83rem;
      color: #7f8c8d;
      line-height: 1.4;
    }}
    .history-body {{
      padding: 0 18px 18px;
      border-top: 1px solid #f0f2f5;
    }}
    .history-body p {{
      font-size: 0.9rem;
      line-height: 1.7;
      margin-bottom: 10px;
      margin-top: 14px;
      color: #2c3e50;
    }}
    /* ── Market cards ── */
    .cards-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
    }}
    .card {{
      background: white;
      border-radius: 10px;
      padding: 18px 20px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }}
    .source-name {{ font-weight: 700; font-size: 1rem; }}
    .source-link {{ font-size: 0.8rem; color: #2e86ab; text-decoration: none; }}
    .source-link:hover {{ text-decoration: underline; }}
    .desc {{ font-size: 0.85rem; color: #555; margin-bottom: 10px; }}
    .stat-table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
    .stat-table td {{ padding: 5px 0; }}
    .stat-table td:first-child {{ color: #7f8c8d; width: 55%; }}
    .stat-table tr + tr td {{ border-top: 1px solid #f0f2f5; }}
    /* ── Events / sources table ── */
    .event-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
      background: white;
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }}
    .event-table th {{
      background: #1a3a5c;
      color: white;
      padding: 10px 14px;
      text-align: left;
      font-weight: 600;
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }}
    .event-table td {{ padding: 9px 14px; border-bottom: 1px solid #f0f2f5; }}
    .event-table tr:last-child td {{ border-bottom: none; }}
    .event-table tr.past {{ opacity: 0.45; }}
    .event-date {{ font-weight: 600; white-space: nowrap; color: #2e86ab; }}
    .event-table a {{ color: #2e86ab; font-size: 0.8rem; text-decoration: none; }}
    .event-table a:hover {{ text-decoration: underline; }}
    /* ── Misc ── */
    .simple-list {{ list-style: none; padding: 0; }}
    .simple-list li {{ padding: 6px 0; border-bottom: 1px solid #f0f2f5; font-size: 0.88rem; }}
    .simple-list li:last-child {{ border-bottom: none; }}
    .simple-list li::before {{ content: "•"; color: #2e86ab; margin-right: 8px; }}
    .badge {{
      display: inline-block; padding: 2px 10px; border-radius: 12px;
      color: white; font-size: 0.78rem; font-weight: 600;
    }}
    .empty {{ color: #aaa; font-size: 0.9rem; font-style: italic; }}
    .ts {{ display: block; margin-top: 8px; font-size: 0.78rem; color: #aaa; }}
    .mod-badge {{
      display: inline-block; padding: 2px 8px; border-radius: 10px;
      font-size: 0.75rem; font-weight: 600; color: white; white-space: nowrap;
    }}
    .mod-markets {{ background: #2e86ab; }}
    .mod-events  {{ background: #e67e22; }}
    .mod-weather {{ background: #27ae60; }}
    .mod-civic   {{ background: #8e44ad; }}
    footer {{
      text-align: center;
      padding: 24px;
      color: #aaa;
      font-size: 0.8rem;
      border-top: 1px solid #e0e0e0;
      margin-top: 40px;
    }}
    footer a {{ color: #2e86ab; text-decoration: none; }}
    footer a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <header>
    <div class="header-brand">
      <h1>Laguna Beach Market Intelligence</h1>
      <p>Data generated: {generated_fmt} &nbsp;|&nbsp; Dashboard built: {now_fmt}</p>
    </div>
    <div class="header-agent">
      <a href="https://marcusskenderian.com/" target="_blank">
        <img class="header-logo"
             src="https://media-production.lp-cdn.com/cdn-cgi/image/format=auto,quality=85/https://media-production.lp-cdn.com/media/211ab4c3-5a78-41a6-8001-ac430ffa495b"
             alt="Marcus Skenderian Real Estate">
      </a>
      <a href="https://marcusskenderian.com/" target="_blank" style="font-size:0.78rem;margin-top:4px;display:block">marcusskenderian.com</a>
    </div>
  </header>
  <div class="stat-bar">
    <span class="stat-pill">{market_count} Market Sources</span>
    <span class="stat-pill">{event_count} Events</span>
    {f'<span class="stat-pill">{season} Season</span>' if season else ''}
    {f'<span class="stat-pill">{blog_count} Blog Post{"s" if blog_count != 1 else ""}</span>' if blog_count else ''}
    <span class="stat-pill">Laguna Beach, CA</span>
  </div>

  <main>
    {f'<div class="section-title">Today\'s Blog Post</div>{blog_today_html}' if blog_today_html else ''}

    <div class="section-title">Real Estate Markets</div>
    <div class="cards-grid">
      {markets_html}
    </div>

    <div class="section-title">Upcoming Events</div>
    {events_html}

    <div class="section-title">Weather &amp; Seasonal Conditions</div>
    {weather_html}

    <div class="section-title">Civic &amp; City Council</div>
    {civic_html}

    <div class="section-title">Sources &amp; Run Log</div>
    {sources_html}

    <div class="section-title">Blog History</div>
    {blog_history_html}
  </main>

  <footer>
    <strong><a href="https://marcusskenderian.com/">Marcus Skenderian</a></strong> &nbsp;&middot;&nbsp;
    Laguna Beach Real Estate &nbsp;&middot;&nbsp;
    Research data: {os.path.basename(source_file)}
  </footer>
</body>
</html>"""


def main():
    data_dir = "data"
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path) as f:
            data = json.load(f)
    else:
        data, path = load_latest(data_dir)

    blog_posts = load_blog_posts()
    html = build_html(data, path, blog_posts)
    out = os.path.join(data_dir, "dashboard.html")
    os.makedirs(data_dir, exist_ok=True)
    with open(out, "w") as f:
        f.write(html)

    print(f"Dashboard written to: {out}")
    print(f"Open with: xdg-open {out}")


if __name__ == "__main__":
    main()
