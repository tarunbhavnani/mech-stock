# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 10:26:33 2026

@author: Tarun
"""

from gnews import get_indian_market_news


API_KEY = "d4aee2f59ab42a4338ca9042dd66a316"

articles = get_indian_market_news(
    api_key=API_KEY,
    max_articles_per_category=10
)


for article in articles:

    print("=" * 80)

    print(article["category"])
    print(article["title"])
    print(article["source"]["name"])
    print(article["publishedAt"])
    print(article["url"])
    


