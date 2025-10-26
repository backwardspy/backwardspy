import json
import os
from pathlib import Path
from typing import Any

import httpx
import jinja2
import pendulum
import spotipy
from spotipy.oauth2 import SpotifyOAuth

DATA_PATH = Path("data")
GITHUB_DATA = DATA_PATH / "github.json"
SPOTIFY_DATA = DATA_PATH / "spotify.json"
README = Path("README.md")


TEMPLATE_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader("templates"),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


def write(data: Any, path: Path):
    if DATA_PATH not in path.parents:
        raise ValueError(f"invalid path: {path} - must be a child of {DATA_PATH}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    print(f" - wrote {path}")


def github_public_events(username: str) -> list[dict[str, Any]]:
    resp = httpx.get(
        f"https://api.github.com/users/{username}/events/public",
        params={"per_page": 100},
    )
    resp.raise_for_status()
    events = [e for e in resp.json() if e["repo"]["name"] != "backwardspy/backwardspy"]
    return events[:25]


def spotify_recently_played() -> list[Any]:
    if cache_value := os.getenv("SPOTIPY_CACHE"):
        print(" - using preset cache data for spotify client")
        Path(".cache").write_text(cache_value)
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id="71dc5b9ac29444dcae88b8a5ccb4b8ab",
            scope="user-read-recently-played",
            redirect_uri="http://localhost:6502",
        ),
    )
    return sp.current_user_recently_played(limit=10)


def fetch_all():
    if not GITHUB_DATA.exists():
        write(github_public_events("backwardspy"), GITHUB_DATA)
    else:
        print(f" - skipping {GITHUB_DATA} - already exists")

    if not SPOTIFY_DATA.exists():
        write(spotify_recently_played(), SPOTIFY_DATA)
    else:
        print(f" - skipping {SPOTIFY_DATA} - already exists")


def replace_readme_section(key: str, contents: str):
    readme = README.read_text()
    marker = f"<!-- SCRIPT:REPLACE:{key} -->"
    start = readme.index(marker) + len(marker)
    end = readme.index(marker, start)
    result = readme[:start] + "\n" + contents + "\n" + readme[end:]
    README.write_text(result)


def linkify(text: str, url: str) -> str:
    return f"[{text}]({url})"


def repo_linkify(repo: dict[str, Any]) -> str:
    return linkify(repo["name"], f"https://github.com/{repo['name']}")


def issue_linkify(issue: dict[str, Any]) -> str:
    if title := issue.get("title"):
        title = title
        html_url = issue["html_url"]
    else:
        url = issue["url"]
        resp = httpx.get(url)
        resp.raise_for_status()
        issue_data = resp.json()
        title = issue_data["title"]
        html_url = issue_data["html_url"]

    return linkify(f"#{issue['number']}: {title}", html_url)


def dateify(date: str) -> str:
    dt = pendulum.parse(date)
    assert isinstance(dt, pendulum.DateTime)
    return f"<span title='{dt.to_rfc3339_string()}'>{dt.format('MMM Do HH:mm')}</span>"


def generate_github_section() -> str:
    with (DATA_PATH / "github.json").open() as f:
        data = json.load(f)

    entries: list[tuple[str, str, str]] = []

    # grab interesting bits for events we care about
    for event in data:
        repo = event["repo"]
        payload = event["payload"]

        if repo["name"] == "backwardspy/backwardspy":
            continue

        def enter(entry: str):
            entries.append((dateify(event["created_at"]), entry, repo_linkify(repo)))

        match event["type"]:
            case "CreateEvent":  # a git branch or tag is created
                if payload["ref_type"] == "repository":
                    enter("🪄 created repository")
            case (
                "IssueCommentEvent"
            ):  # activity related to an issue or pull request comment
                link = issue_linkify(payload["issue"])
                if payload["action"] == "created":
                    enter(f"💬 commented on {link}")
            case "IssuesEvent":  # activity related to an issue
                link = issue_linkify(payload["issue"])
                if payload["action"] == "opened":
                    enter(f"📢 opened {link}")
                elif payload["action"] == "closed":
                    enter(f"✅ closed {link}")
            case "PullRequestEvent":  # activity related to pull requests
                link = issue_linkify(payload["pull_request"])
                if payload["action"] == "opened":
                    enter(f"🚀 opened {link}")
                elif payload["action"] == "closed":
                    enter(f"🎉 closed {link}")
            case "PullRequestReviewEvent":  # activity related to pull request reviews
                link = issue_linkify(payload["pull_request"])
                enter(f"🔍 reviewed {link}")
            case (
                "PushEvent"
            ):  # one or more commits are pushed to a repository branch or tag.
                size: int = payload.get("size", 1)
                commits = "commits" if size > 1 else "commit"
                ref = payload["ref"].removeprefix("refs/heads/")
                enter(f"🚢 pushed {size} {commits} to `{ref}`")
            case "ReleaseEvent":  # activity related to a release
                enter(f"📦 released {payload['release']['tag_name']}")
            case "WatchEvent":  # when someone stars a repository
                enter("⭐ starred a repository")
            case _:
                pass

    template = TEMPLATE_ENV.get_template("activity_table.md")
    return template.render(entries=entries)


def generate_spotify_section() -> str:
    with (DATA_PATH / "spotify.json").open() as f:
        data = json.load(f)
    template = TEMPLATE_ENV.get_template("recently_played.md")
    return template.render(entries=[item["track"] for item in data["items"]])


if __name__ == "__main__":
    print("fetch...")
    fetch_all()

    print("generate...")
    replace_readme_section("GITHUB", generate_github_section())
    replace_readme_section("SPOTIFY", generate_spotify_section())

    print("done!")
