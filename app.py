from flask import Flask, render_template, request, send_file
import requests
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    all_users = []

    if request.method == 'POST':
        min_followers = int(request.form['min_followers'])
        start_page = int(request.form['start_page'])
        max_pages = int(request.form['max_pages'])
        location = request.form.get('location', '').strip()
        min_repos = request.form.get('min_repos', '').strip()
        min_repos = int(min_repos) if min_repos.isdigit() else None

        headers = {'Accept': 'application/vnd.github.v3+json'}
        base_url = 'https://api.github.com/search/users'

        for page in range(start_page, max_pages + 1):
            query = f"followers:>={min_followers}"
            if location:
                query += f" location:{location}"
            if min_repos is not None:
                query += f" repos:>={min_repos}"

            params = {'q': query, 'page': page, 'per_page': 100}
            response = requests.get(base_url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                all_users.extend(data.get('items', []))
            else:
                print(f"Error on page {page}: {response.status_code}")
                break

        # JSON फाइल में सेव करें
        with open('users_data.json', 'w', encoding='utf-8') as file:
            json.dump(all_users, file, ensure_ascii=False, indent=2)

    return render_template('index.html', users=all_users, year=datetime.now().year)

@app.route('/download')
def download_csv():
    import csv

    try:
        with open('users_data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        csv_file = 'github_users.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Username', 'Profile URL'])
            for user in data:
                writer.writerow([user['login'], user['html_url']])

        return send_file(csv_file, as_attachment=True)
    
    except FileNotFoundError:
        return "कोई डाटा नहीं मिला, कृपया पहले स्क्रैपिंग करें।"

if __name__ == '__main__':
    app.run(debug=True)
