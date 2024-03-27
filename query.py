import os
import sys
import json
from pathlib import Path

from gql.transport.httpx import HTTPXTransport
from gql import Client, gql
from httpx import Timeout

TOKEN = os.getenv("GH_TOKEN")
if not TOKEN:
    print("error: GH_TOKEN not present", file=sys.stderr)
    sys.exit(1)

transport = HTTPXTransport(
    url="https://api.github.com/graphql",
    headers={"Authorization": f"Bearer {TOKEN}"},
    timeout=Timeout(timeout=30.0),
)
client = Client(transport=transport, fetch_schema_from_transport=True)
query = gql("""
{
  viewer {
    repositories(
      first: 100
      orderBy: {field: PUSHED_AT, direction: DESC}
      isArchived: false
      visibility: PUBLIC
    ) {
      nodes {
        owner { login }
        name
        url
        releases(first: 1, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes {
            name
            url
          }
        }
      }
    }
  }
}
""")
print("querying user repos...")
result = client.execute(query)
Path("user.json").write_text(json.dumps(result))

query = gql("""
{
  organization(login: "catppuccin") {
    repositories(
      first: 100
      orderBy: {field: PUSHED_AT, direction: DESC}
      isArchived: false
      visibility: PUBLIC
    ) {
      nodes {
        owner { login }
        name
        url
        releases(first: 1, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes {
            name
            url
          }
        }
      }
    }
  }
}
""")
print("querying catppuccin repos...")
result = client.execute(query)
Path("catppuccin.json").write_text(json.dumps(result))

print("done!")
