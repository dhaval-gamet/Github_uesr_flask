import requests
import json
import time
import os
import csv

OUTPUT_FILE = "top_github_users.json"
CSV_FILE = "top_github_users.csv"

def load_existing_users():
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except json.JSONDecodeError:
            pass
    return []

def save_users(users):
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def save_csv(users):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Username", "Profile URL"])
        for user in users:
            writer.writerow([user["login"], user["html_url"]])

def get_github_users(min_followers=100, start_page=1, max_pages=3, location=None, min_repos=None):
    all_users = load_existing_users()
    seen_logins = set(user["login"] for user in all_users)
    collected = 0

    for page in range(start_page, start_page + max_pages):
        query = f"followers:>={min_followers}"
        if location:
            query += f" location:{location}"
        if min_repos:
            query += f" repos:>={min_repos}"

        url = f"https://api.github.com/search/users?q={query}&per_page=100&page={page}"
        headers = {"Accept": "application/vnd.github.v3+json"}

        response = requests.get(url, headers=headers)

        if response.status_code == 403:
            reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait_time = max(reset_time - int(time.time()), 1)
            time.sleep(wait_time)
            continue

        if response.status_code != 200:
            break

        data = response.json()
        items = data.get("items", [])

        new_users = [
            {"login": item["login"], "html_url": item["html_url"]}
            for item in items if item["login"] not in seen_logins
        ]

        all_users.extend(new_users)
        seen_logins.update(u["login"] for u in new_users)

        collected += len(new_users)
        save_users(all_users)
        time.sleep(1)

        if len(items) == 0:
            break

    save_csv(all_users)
    return all_users, collected
