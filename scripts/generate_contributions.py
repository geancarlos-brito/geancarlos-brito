#!/usr/bin/env python3
"""Generate a GitHub-style contribution heatmap using GitHub's GraphQL API."""
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen
import json
import os
import html

USERNAME = "geancarlos-brito"
OUTPUT = Path("assets/contributions.svg")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    raise SystemExit("GH_TOKEN or GITHUB_TOKEN is required")

query = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            weekday
          }
        }
      }
    }
  }
}
"""
payload = json.dumps({"query": query, "variables": {"login": USERNAME}}).encode()
request = Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "geancarlos-contribution-heatmap",
    },
)
with urlopen(request, timeout=30) as response:
    result = json.load(response)

if result.get("errors"):
    raise SystemExit(f"GitHub GraphQL error: {result['errors']}")
calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"]
total = calendar["totalContributions"]

cell, gap = 11, 4
left, top = 48, 43
columns = len(weeks)
width = left + columns * (cell + gap) + 8
height = 43 + 7 * (cell + gap) + 30
colors = ["#161b22", "#5c1717", "#922626", "#d43b3b", "#ff5a4e"]

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
    '<title id="title">Atividade de Gean Carlos no GitHub</title>',
    f'<desc id="desc">{total} contribuições no último ano, atualizado automaticamente.</desc>',
    '<rect width="100%" height="100%" rx="12" fill="#0d1117"/>',
    '<text x="16" y="23" fill="#f0f6fc" font-family="Segoe UI,Arial,sans-serif" font-size="14" font-weight="600">Contribuições no último ano</text>',
    f'<text x="{width-16}" y="23" text-anchor="end" fill="#ff6b61" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="700">{total:,} contribuições</text>',
]
for label, day in [("Seg", 1), ("Qua", 3), ("Sex", 5)]:
    y = top + day * (cell + gap) + 9
    parts.append(f'<text x="12" y="{y}" fill="#8b949e" font-family="Segoe UI,Arial,sans-serif" font-size="9">{label}</text>')

previous_month = None
for col, week in enumerate(weeks):
    days = week["contributionDays"]
    first = date.fromisoformat(days[0]["date"])
    if first.month != previous_month and first.day <= 7:
        x = left + col * (cell + gap)
        month = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"][first.month-1]
        parts.append(f'<text x="{x}" y="37" fill="#8b949e" font-family="Segoe UI,Arial,sans-serif" font-size="10">{month}</text>')
        previous_month = first.month
    for item in days:
        weekday = item["weekday"]
        count = item["contributionCount"]
        level = 0 if count == 0 else 1 if count < 3 else 2 if count < 6 else 3 if count < 10 else 4
        x = left + col * (cell + gap)
        y = top + weekday * (cell + gap)
        title = html.escape(f"{count} contribuições em {item['date']}")
        parts.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{colors[level]}">'
            f'<title>{title}</title></rect>'
        )

legend_y = height - 10
parts.append(f'<text x="{left}" y="{legend_y}" fill="#8b949e" font-family="Segoe UI,Arial,sans-serif" font-size="9">Menos</text>')
for i, color in enumerate(colors):
    x = left + 37 + i * 16
    parts.append(f'<rect x="{x}" y="{legend_y-9}" width="10" height="10" rx="2" fill="{color}"/>')
parts.append(f'<text x="{left+127}" y="{legend_y}" fill="#8b949e" font-family="Segoe UI,Arial,sans-serif" font-size="9">Mais</text>')
parts.append('</svg>')

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
print(f"Generated {OUTPUT} with {total} contributions.")
