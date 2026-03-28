import requests
from bs4 import BeautifulSoup
from collections import Counter
import csv
import os
from flask import Flask, render_template_string, redirect, url_for

app = Flask(__name__)

CSV_FILE = 'news_articles.csv'

def scrape_news_links():
    url = "https://news.google.com/home?hl=en-PK&gl=PK&ceid=PK%3Aen"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('a', {'class': 'gPFEn'})

        if not articles:
            print("No news articles found. The HTML structure might have changed.")
            return []

        # Extract links
        links = []
        for article in articles:
            title = article.text.strip() or "No Title"
            link = article['href']
            if link.startswith('./'):
                link = 'https://news.google.com' + link[1:]
            links.append((title, link))

        return links
    else:
        print(f"Failed to fetch Google News. Status code: {response.status_code}")
        return []

def read_news_from_csv():
    articles = []
    if os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, mode='r', encoding='utf-8-sig', errors='replace') as file:
                reader = csv.reader(file)
                next(reader, None)  # Skip header
                articles = [(row[0], row[1], int(row[2])) for row in reader if len(row) >= 3]
        except Exception as e:
            print(f"Error reading CSV: {e}")
    return articles

def append_new_articles_to_csv(new_articles):
    existing_articles = set(title for title, _, _ in read_news_from_csv())

    # Append only new articles with default clicks = 0
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for title, link in new_articles:
            if title not in existing_articles:
                writer.writerow([title, link, 0])  # Default clicks = 0
                print(f"Appended: {title}")

def calculate_trending(articles):
    # Sort by clicks (descending)
    trending_scores = sorted(articles, key=lambda x: x[2], reverse=True)
    return trending_scores

def refresh_logic():
    # Fetch fresh articles and append only new ones
    new_articles = scrape_news_links()
    if new_articles:
        append_new_articles_to_csv(new_articles)

@app.route("/click/<int:article_id>")
def record_click(article_id):
    articles = read_news_from_csv()

    # Increment the click count for the selected article
    if 0 <= article_id < len(articles):
        title, link, clicks = articles[article_id]
        articles[article_id] = (title, link, clicks + 1)

        # Update the CSV file with the new click count
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Title', 'Link', 'Clicks'])
            writer.writerows(articles)

    
   

    # Redirect the user to the actual article link
    return redirect(articles[article_id][1])
    

@app.route("/")
def display_trending_news():
    articles = read_news_from_csv()
    if not articles:
        print("Fetching fresh data as no articles were found in CSV.")
        new_articles = scrape_news_links()
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Title', 'Link', 'Clicks'])  # Write header
            for title, link in new_articles:
                writer.writerow([title, link, 0])
        articles = read_news_from_csv()

    trending_articles = calculate_trending(articles)

    # Pass articles with indices (enumerated)
    enumerated_articles = list(enumerate(trending_articles))

    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trending News</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {
            font-family: 'Poppins', Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f8f9fa;
            color: #333;
        }

        /* Sidebar */
        .sidebar {
            background-color: #2c3e50;
            color: #ecf0f1;
            width: 300px;
            position: fixed;
            height: 100%;
            padding: 20px;
            overflow-y: auto;
        }
        .sidebar h2 {
            text-align: center;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 2px solid #7f8c8d;
            padding-bottom: 10px;
        }
        .sidebar button {
            display: block;
            width: 100%;
            padding: 10px;
            background-color: #27ae60;
            color: white;
            border: none;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 1em;
            cursor: pointer;
        }
        .sidebar button:hover {
            background-color: #219150;
        }
        .trending-article {
            margin: 15px 0;
        }
        .trending-article a {
            color: #ecf0f1;
            text-decoration: none;
            font-size: 1.1em;
        }
        .trending-article a:hover {
            text-decoration: underline;
        }
        .trending-article .score {
            font-size: 0.9em;
            color: #bdc3c7;
        }

        /* Main Content */
        .main-content {
            margin-left: 320px;
            padding: 20px;
        }
        .main-content h1 {
            font-size: 2.2em;
            color: #2c3e50;
            margin-bottom: 20px;
        }
        .article {
            margin-bottom: 15px;
            padding: 10px 0;
            border-bottom: 1px solid #ddd;
        }
        .article a {
            color: #2980b9;
            text-decoration: none;
            font-size: 1.3em;
        }
        .article a:hover {
            text-decoration: underline;
        }
        .score {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <!-- Sidebar -->
    <div class="sidebar">
        <h2><i class="fa-solid fa-fire"></i> Trending News</h2>
         <meta http-equiv="refresh" content="5"> <!-- Refresh every 5 seconds -->
        <form action="{{ url_for('refresh_news') }}" method="post">
            <button type="submit"><i class="fa-solid fa-rotate-right"></i> Refresh</button>
        </form>
        <!-- Trending Articles -->
        {% for idx, (title, link, score) in articles[:5] %}
        <div class="trending-article">
            <a href="{{ url_for('record_click', article_id=idx) }}" target="_blank">
                <i class="fa-solid fa-link"></i> {{ title }}
            </a>
            <div class="score">Clicks: {{ score }}</div>
        </div>
        {% endfor %}
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <h1><i class="fa-solid fa-newspaper"></i> All News Articles</h1>
        {% for idx, (title, link, score) in articles %}
        <div class="article">
            <a href="{{ url_for('record_click', article_id=idx) }}" target="_blank">{{ title }}</a>
            <div class="score">Clicks: {{ score }}</div>
        </div>
        {% endfor %}
    </div>
</body>
</html>

    """
    return render_template_string(html_template, articles=enumerated_articles)

@app.route("/refresh", methods=["POST", "GET"])
def refresh_news():
    refresh_logic()
    return redirect(url_for('display_trending_news'))

if __name__ == "__main__":
    app.run(app.run(host="0.0.0.0", port=5000, debug=True))
