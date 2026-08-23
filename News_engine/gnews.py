# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 10:24:10 2026

@author: Tarun
"""

# gnews.py

import requests
from datetime import datetime, timedelta


GNEWS_URL = "https://gnews.io/api/v4/search"


MARKET_QUERIES = {
    "market": '"Nifty 50" OR "Sensex" OR "Indian stock market"',
    "flows": 'FII OR FPI OR DII',
    "rbi": 'RBI OR "repo rate" OR inflation',
    "global": '"US markets" OR "Asian markets" OR "Federal Reserve"',
    "commodities": '"crude oil" OR Brent OR "gold prices"',
    "currency": '"Indian rupee" OR INR',
    "regulation": 'SEBI OR NSE OR BSE',
    "economy": '"Indian economy" OR "India GDP"',
}


def get_news(query, api_key, max_articles=10, hours=48):
    """
    Pull news from GNews.

    Parameters
    ----------
    query : str
        GNews search query.
    api_key : str
        GNews API key.
    max_articles : int
        Maximum number of articles to return.
    hours : int
        Only return articles from the last N hours.

    Returns
    -------
    list
        List of news articles.
    """

    from_time = datetime.utcnow() - timedelta(hours=hours)

    params = {
        "q": query,
        "lang": "en",
        "country": "in",
        "max": max_articles,
        "sortby": "publishedAt",
        "from": from_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "apikey": api_key,
    }

    response = requests.get(
        GNEWS_URL,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    return data.get("articles", [])


def get_market_news(api_key, max_articles_per_category=10):
    """
    Pull Indian market news across all categories.

    Returns
    -------
    dict
        {
            "market": [...],
            "flows": [...],
            "rbi": [...],
            ...
        }
    """

    news = {}

    for category, query in MARKET_QUERIES.items():

        try:

            articles = get_news(
                query=query,
                api_key=api_key,
                max_articles=max_articles_per_category
            )

            news[category] = articles

        except requests.RequestException as e:

            print(f"Error getting {category} news: {e}")

            news[category] = []

    return news


def flatten_news(news):
    """
    Convert categorized news dictionary into one list.

    Adds the category to each article.
    """

    articles = []

    for category, category_articles in news.items():

        for article in category_articles:

            article = article.copy()
            article["category"] = category

            articles.append(article)

    return articles


def remove_duplicates(articles):
    """
    Remove duplicate articles based on URL.
    """

    seen = set()
    unique_articles = []

    for article in articles:

        url = article.get("url")

        if url and url not in seen:

            seen.add(url)
            unique_articles.append(article)

    return unique_articles


def get_indian_market_news(api_key, max_articles_per_category=10):
    """
    Main function.

    Returns a clean list of Indian market news articles.
    """

    news = get_market_news(
        api_key=api_key,
        max_articles_per_category=max_articles_per_category
    )

    articles = flatten_news(news)

    articles = remove_duplicates(articles)

    articles.sort(
        key=lambda x: x.get("publishedAt", ""),
        reverse=True
    )

    return articles