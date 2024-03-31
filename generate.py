import json
from pathlib import Path
from typing import Any

import httpx
import pendulum

DATA_PATH = Path("data")
GITHUB_DATA = DATA_PATH / "github.json"
README = Path("README.md")


def write(data: dict[str, Any], path: Path):
    if path.exists():
        print(f"skipping {path} - already exists")
        return

    if DATA_PATH not in path.parents:
        raise ValueError(f"invalid path: {path} - must be a child of {DATA_PATH}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    print(f"wrote {path}")


def github_public_events(username: str) -> dict[str, Any]:
    resp = httpx.get(f"https://api.github.com/users/{username}/events/public")
    resp.raise_for_status()
    return resp.json()


def fetch_all():
    write(github_public_events("backwardspy"), GITHUB_DATA)


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
    return linkify(f"#{issue['number']}: {issue['title']}", issue["html_url"])


def dateify(date: str) -> str:
    dt = pendulum.parse(date)
    return f"<span title='{dt.to_rfc3339_string()}'>{dt.diff_for_humans()}</span>"


def generate_github_section() -> str:
    with (DATA_PATH / "github.json").open() as f:
        data = json.load(f)

    entries = []

    # grab interesting bits for events we care about
    for event in data:
        repo = event["repo"]
        payload = event["payload"]

        def enter(entry: str):
            entries.append((event["created_at"], entry, repo))

        match event["type"]:
            case "CreateEvent":  # a git branch or tag is created
                if payload["ref_type"] == "repository":
                    enter("🪄 created repository")
            case "IssueCommentEvent":  # activity related to an issue or pull request comment
                link = issue_linkify(payload["issue"])
                if payload["action"] == "created":
                    enter(f"💬 commented on issue {link}")
            case "IssuesEvent":  # activity related to an issue
                link = issue_linkify(payload["issue"])
                if payload["action"] == "opened":
                    enter(f"📢 opened issue {link}")
                elif payload["action"] == "closed":
                    enter(f"✅ closed issue {link}")
            case "PullRequestEvent":  # activity related to pull requests
                link = issue_linkify(payload["pull_request"])
                if payload["action"] == "opened":
                    enter(f"🚀 opened pull request {link}")
                elif payload["action"] == "closed":
                    enter(f"🎉 closed pull request {link}")
            case "PullRequestReviewEvent":  # activity related to pull request reviews
                link = issue_linkify(payload["pull_request"])
                enter(f"🔍 reviewed pull request {link}")
            case "PushEvent":  # one or more commits are pushed to a repository branch or tag.
                enter(f"🚢 pushed {payload['size']} commits to `{payload['ref']}`")
            case "ReleaseEvent":  # activity related to a release
                enter(f"📦 released {payload['release']['tag_name']}")
            case "WatchEvent":  # when someone stars a repository
                enter("⭐ starred a repository")

    def format_entries(entries: list[tuple[str, str, dict[str, Any]]]) -> str:
        return "\n".join(
            f"| {dateify(dt)} | {entry} | {repo_linkify(repo)} |"
            for (dt, entry, repo) in entries
        )

    heading = "## recent github activity"

    thead = "| date | event | repo |"
    sep = "|" + "|".join(" - " for _ in entries[0]) + "|"

    first = format_entries(entries[:5])
    more_open = """<details>
<summary>show more...</summary>"""
    remaining = format_entries(entries[5:])
    more_close = "</details>"

    table = "\n".join([heading, thead, sep, first])
    if remaining:
        table += "\n".join(["", "", more_open, "", thead, sep, remaining, "", more_close])

    return table


if __name__ == "__main__":
    print("fetch...")
    fetch_all()
    print()

    print("generate...")
    replace_readme_section("GITHUB", generate_github_section())
    print()

    print("done!")
