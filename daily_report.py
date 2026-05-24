import os
import requests

from bs4 import BeautifulSoup
from openai import OpenAI
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")

DEFAULT_MODEL = "gpt-4o-mini"

if not API_KEY or not BASE_URL:
    raise RuntimeError("Missing API_KEY environment variable.")


def fetch_trending():
    url = "https://github.com/trending?since=daily"
    # Simulate a browser request to avoid being blocked by GitHub
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    # Raise an exception if the request fails (e.g. 404, 500)
    response.raise_for_status()
    return response.text


def parse_repos(html):
    soup = BeautifulSoup(html, "html.parser")
    repos = []
    for article in soup.select("article.Box-row"):
        # Repository name (owner/repo format)
        link = article.select_one("h2 a")
        name = link["href"].strip("/") if link else "unknown"

        # Repository description
        desc_tag = article.select_one("p.col-9")
        desc = desc_tag.text.strip() if desc_tag else "无描述"

        # Programming language
        lang_tag = article.select_one('span[itemprop="programmingLanguage"]')
        lang = lang_tag.text.strip() if lang_tag else ""

        # Stars gained today
        stars_tag = article.select_one("span.d-inline-block.float-sm-right")
        stars = stars_tag.text.strip() if stars_tag else ""

        repos.append(f"- {name} ({lang}) {stars}\n  {desc}")
    return repos


def summarize(repos):
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    # Only use the top 15 repositories to avoid excessive token usage
    repo_text = "\n".join(repos[:15])
    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {
                "role": "user",
                "content": f"下面是今天 GitHub Trending 的熱門專案列表，"
                f"請用繁體中文寫一份簡短的日報摘要，"
                f"挑出最值得關注的 5 個專案，"
                f"簡要說明每個專案是做什麼的、為什麼值得關注。"
                f"\n\n{repo_text}",
            }
        ],
    )
    return response.choices[0].message.content


def save_report(summary):
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    filename = output_dir / f"trending_{date.today()}.md"
    with open(filename, "w") as f:
        f.write(f"# GitHub Trending 日报 ({date.today()})\n\n")
        f.write(summary)
    print(f"日報已儲存至 {filename}")


# ---  Workflow ---
html = fetch_trending()
repos = parse_repos(html)
summary = summarize(repos)
save_report(summary)
