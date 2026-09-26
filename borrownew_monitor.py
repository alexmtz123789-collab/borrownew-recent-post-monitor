"""
BorrowNew Recent Post Monitor

Read-only Reddit API utility that retrieves recent public submissions
from r/BorrowNew and keeps only posts created within the previous hour.

This application does not post, comment, vote, message users, or modify
Reddit content.
"""

import os
import time
import requests

SUBREDDIT = "BorrowNew"
WINDOW_SECONDS = 60 * 60
USER_AGENT = "borrownew-recent-post-monitor/1.0 (personal read-only utility)"


def get_access_token():
    client_id = os.environ["REDDIT_CLIENT_ID"]
    client_secret = os.environ["REDDIT_CLIENT_SECRET"]

    response = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=(client_id, client_secret),
        data={"grant_type": "client_credentials"},
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )

    response.raise_for_status()
    return response.json()["access_token"]


def get_recent_posts(access_token):
    response = requests.get(
        f"https://oauth.reddit.com/r/{SUBREDDIT}/new",
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": USER_AGENT,
        },
        params={
            "limit": 100,
            "raw_json": 1,
        },
        timeout=20,
    )

    response.raise_for_status()

    now = time.time()
    recent_posts = []

    for child in response.json()["data"]["children"]:
        post = child["data"]
        created_utc = float(post["created_utc"])
        age_seconds = now - created_utc

        # Strict rolling 60-minute freshness requirement.
        if 0 <= age_seconds <= WINDOW_SECONDS:
            recent_posts.append(
                {
                    "id": post["id"],
                    "author": post.get("author"),
                    "title": post.get("title"),
                    "created_utc": created_utc,
                    "age_minutes": round(age_seconds / 60, 1),
                    "flair": post.get("link_flair_text"),
                    "permalink": "https://www.reddit.com"
                    + post["permalink"],
                }
            )

    return recent_posts


def main():
    access_token = get_access_token()
    posts = get_recent_posts(access_token)

    print(
        f"Found {len(posts)} r/{SUBREDDIT} submissions "
        "created within the previous 60 minutes."
    )

    for post in posts:
        print()
        print(f"Age: {post['age_minutes']} minutes")
        print(f"Author: u/{post['author']}")
        print(f"Title: {post['title']}")
        print(f"Flair: {post['flair']}")
        print(f"Created UTC: {post['created_utc']}")
        print(f"URL: {post['permalink']}")


if __name__ == "__main__":
    main()
