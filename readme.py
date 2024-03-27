import io
import re
import json
from pathlib import Path

REPLACE = "<!-- SCRIPT:REPLACE -->"
REPLACE_PAT = re.compile(f"{REPLACE}.*{REPLACE}", re.M | re.S)
README = Path("README.md")
ROWS = 5

user = json.loads(Path("user.json").read_text())
catppuccin = json.loads(Path("catppuccin.json").read_text())

user = user["viewer"]["repositories"]["nodes"][:ROWS]
catppuccin = catppuccin["organization"]["repositories"]["nodes"][:ROWS]


def format_repo(repo):
    s = "[{}/{}]({})".format(repo["owner"]["login"], repo["name"], repo["url"])
    if r := repo["releases"]["nodes"]:
        r = r[0]
        s += " ([{}]({}))".format(r["name"], r["url"])
    return s


buf = io.StringIO()
print(REPLACE, file=buf)
print("| me | catppuccin |", file=buf)
print("| -- | ---------- |", file=buf)
for u, c in zip(user, catppuccin):
    print(f"| {format_repo(u)} | {format_repo(c)} |", file=buf)
print(REPLACE, file=buf, end="")

contents = README.read_text()
result = REPLACE_PAT.sub(buf.getvalue(), contents)
README.write_text(result)
