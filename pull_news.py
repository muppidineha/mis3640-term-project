import requests
import pprint


# https://developer.nytimes.com/
api_key = "PS5qFn9MAQYV3BPjSoHBx5a4UbqdmVcH"


def pull_news(dropdown_tickers):
    url = f"https://api.nytimes.com/svc/search/v2/articlesearch.json?q={dropdown_tickers}&api-key={api_key}"
    r = requests.get(url).json()["response"]["docs"]
    if len(r) > 0:
        return r
    return "No news found"


def get_news(dropdown_tickers):
    news = pull_news(dropdown_tickers)
    news = [(n["abstract"], n["lead_paragraph"], n["pub_date"]) for n in news]
    return news


# pprint.pprint(pull_news('APLE'))