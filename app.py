from flask import Flask, jsonify, request
import requests, time, os, json, csv

app = Flask(__name__)

OUTPUT_FILE = "top_github_users.json"
CSV_FILE = "top_github_users.csv"

# -------- Helper Functions --------
def load_existing_users():
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and all(isinstance(u, dict) and "login" in u for u in data):
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

# -------- Main Scraper Function --------
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
            return [], 0

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

# -------- Flask Routes --------
@app.route('/')
def home():
    return jsonify({"message": "Welcome to GitHub User Scraper API"})

@app.route('/scrape', methods=['GET'])
def scrape():
    min_followers = int(request.args.get("min_followers", 100))
    start_page = int(request.args.get("start_page", 1))
    max_pages = int(request.args.get("max_pages", 3))
    location = request.args.get("location")
    min_repos = request.args.get("min_repos")
    min_repos = int(min_repos) if min_repos else None

    users, added = get_github_users(min_followers, start_page, max_pages, location, min_repos)
    return jsonify({"total": len(users), "new_added": added, "users": users})

@app.route('/download/json')
def download_json():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    return jsonify({"error": "JSON file not found"}), 404

@app.route('/download/csv')
def download_csv():
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/csv'}
    return jsonify({"error": "CSV file not found"}), 404

@app.route('/clear', methods=['POST'])
def clear_data():
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
    return jsonify({"message": "Files cleared successfully!"})

# -------- Run Locally --------
if __name__ == '__main__':
    app.run(debug=True, port=5000)
