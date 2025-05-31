from flask import Flask, request, jsonify, render_template
from scraper import get_github_users

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    min_followers = int(data.get('min_followers', 100))
    start_page = int(data.get('start_page', 1))
    max_pages = int(data.get('max_pages', 3))
    location = data.get('location')
    min_repos = data.get('min_repos')

    users, total = get_github_users(min_followers, start_page, max_pages, location, min_repos)
    return jsonify({"total_users": len(users), "new_users": total, "users": users})

if __name__ == '__main__':
    app.run(debug=True)
