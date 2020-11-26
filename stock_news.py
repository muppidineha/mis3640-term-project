import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from dash.exceptions import PreventUpdate
import dash_table
import plotly.express as px
import requests
from io import StringIO
from bs4 import BeautifulSoup
import re
import json
import csv
import datetime
from pull_news import get_news


def get_stock_price_fig(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(mode="lines", x=df["Date"], y=df["Close"]))
    return fig


def get_dounts(df, label):

    non_main = 1 - df.values[0]
    labels = ["main", label]
    values = [non_main, df.values[0]]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.499)])
    return fig


app = dash.Dash(
    external_stylesheets=[
        '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">'
    ]
)

app.layout = html.Div(
    [
        # Navigation to different tabs
        html.Div(
            [
                html.P("Search for companies", className="start"),
                # dcc.Input(id="dropdown_tickers", placeholder = "please enter the symbol", type = "text")
                dcc.Dropdown(
                    "dropdown_tickers",
                    options=[
                        {"label": "Apple", "value": "AAPL"},
                        {"label": "Tesla", "value": "TSLA"},
                        {
                            "label": "Facebook",
                            "value": "FB",
                        },  # change these part to include more symbols
                    ],
                ),
                # html.Div([html.Button("Search", className="search-btn", id="search"),], className="Search")
                html.Div(
                    [
                        html.Button("Stock Price", className="stock-btn", id="stock"),
                        html.Button(
                            "Indicators", className="indicators-btn", id="indicators"
                        ),
                        html.Button("News", className="news-btn", id="news_search"),
                        # html.Button("News", className="news-btn", id="news"),
                        # html.Button("Compare", className="compare-btn", id="compare"),
                    ],
                    className="Buttons",
                ),
                html.Div(
                    [
                        html.Button("Compare", className="compare-btn", id="compare"),
                    ],
                    className="Buttons1",
                ),
            ],
            className="Navigation",
        ),
        # content of the web page (content) - ticker/symbol, logo, and description of the company
        #     html.Div([
        #         html.Div([
        #                 html.P(id="ticker"),
        #                 html.Img(id="logo"),
        #         ], className="header"),
        #         html.Div(id="description", className="decription_ticker"),
        #         html.Div([
        #             # html.Div([],id="stock_price_today"), #new added
        #             html.Div([], id="graphs-content"),
        #             # html.Div([],id='news_content'),  #new added
        #         ], id="main-content"),
        #         html.Div([],id = "news-content"),
        #     ],className="content"),
        # ], className="container")
        html.Div(
            [
                html.Div(
                    [
                        html.P(id="ticker"),
                        html.Img(id="logo"),
                    ],
                    className="header",
                ),
                html.Div(id="description", className="decription_ticker"),
                html.Div(
                    [
                        # html.Div([],id="stock_price_today"), #new added
                        html.Div([], id="graphs-content"),
                        # html.Div([],id = "news-content"),
                        # html.Div([],id='news_content'),  #new added
                    ],
                    id="main-content",
                ),
                html.Div([], id="news-content"),
            ],
            className="content",
        ),
    ],
    className="container",
)


# create a callback - bring Yahoo Finance API
# include Output and Input
@app.callback(
    [
        Output("description", "children"),
        Output("logo", "src"),
        Output("ticker", "children"),
        Output("indicators", "n_clicks"),
    ],
    [Input("dropdown_tickers", "value")],
)

# create function that is associate with the function
# when dropdown_tickers is in action
def update_data(v):
    """Take the Input and return Business Summary from Yahoo Finance API. If there is not value inputed --> you want to prevent update"""
    if v == None:
        raise PreventUpdate

    ticker = yf.Ticker(v)
    # print(ticker.info) #select the information you want from this list
    # return '','',''
    # useful information includes: 'sector', 'longBusinessSummary'
    inf = ticker.info

    df = pd.DataFrame.from_dict(inf, orient="index").T
    df = df[
        [
            "sector",
            "fullTimeEmployees",
            "sharesOutstanding",
            "priceToBook",
            "logo_url",
            "longBusinessSummary",
            "shortName",
        ]
    ]

    return (
        df["longBusinessSummary"].values[0],
        df["logo_url"].values[0],
        df["shortName"].values[0],
        1,
    )


# @app.callback(
#             [Output("description1", "children")],
#             [Input("dropdown_tickers", "value")]
#             )

# def today_stock_price(v, v2):
#     if v==None:
#         raise PreventUpdate
#     if v2 == None:
#         raise PreventUpdate

#     tickerdata = yf.Ticker(v2)
#     tickerinfo = tickerdata.info

#     today = datetime.datetime.today().isoformat()
#     # print ("today = " + today)

#     tickerDF = tickerdata.history(period='1d', start = '2020-1-1', end=today[:10])
#     # priceLast = tickerDF['Close'].iloc[-1]
#     # print(investment + 'price last = '+ priceLast)

#     # return f"{today},{priceLast}"
#     # return priceLast
#     return tickerDF['Close'].iloc[-1]


# Stock Price Button
@app.callback(
    [Output("graphs-content", "children")],
    [Input("stock", "n_clicks")],
    [State("dropdown_tickers", "value")],
)
def stock_prices(v, v2):
    if v == None:
        raise PreventUpdate
    if v2 == None:
        raise PreventUpdate

    df = yf.download(v2)
    df.reset_index(inplace=True)

    fig = get_stock_price_fig(df)
    # print(fig)

    return [dcc.Graph(figure=fig)]


# how to get daily stock price


# Indicator Button
@app.callback(
    [Output("main-content", "children"), Output("stock", "n_clicks")],
    [Input("indicators", "n_clicks")],
    [State("dropdown_tickers", "value")],
)
def indicators(v, v2):
    if v == None:
        raise PreventUpdate
    if v2 == None:
        raise PreventUpdate
    ticker = yf.Ticker(v2)

    df_calendar = ticker.calendar.T
    df_info = pd.DataFrame.from_dict(ticker.info, orient="index").T
    df_info.to_csv("test.csv")
    df_info = df_info[
        [
            "priceToBook",
            "profitMargins",
            "bookValue",
            "enterpriseToEbitda",
            "shortRatio",
            "beta",
            "payoutRatio",
            "trailingEps",
        ]
    ]

    df_calendar["Earnings Date"] = pd.to_datetime(df_calendar["Earnings Date"])
    df_calendar["Earnings Date"] = df_calendar["Earnings Date"].dt.date

    ticker_yahoo = yf.Ticker(v2)
    data = ticker_yahoo.history()
    # last_quote = (data.tail(1)['Close'].iloc[0])

    # For DATE
    tbl = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H4("TODAY IS"),
                            html.P(datetime.datetime.today().isoformat()),
                        ]
                    ),
                ],
                className="kpi2",
            )
        ]
    )

    # FOR STOCK PRICE
    tbl1 = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [html.H4("STOCK PRICE"), html.P(data.tail(1)["Close"].iloc[0])]
                    ),
                ],
                className="kpi2",
            )
        ]
    )

    # Print out the stock price, price to book, Enterprise to EBITDA, and Beta
    tbl2 = html.Div(
        [
            html.Div(
                [
                    #    html.Div([
                    #         html.H4("Stock Price"),
                    #         html.P(round(data.tail(1)['Close'].iloc[0]))  #use round to move the decimal points
                    #         # html.P(f"{data.tail(1)['Close'].iloc[0]:02}")   #how to remove the extra 0decimals
                    #     ]),
                    html.Div(
                        [html.H4("PRICE TO BOOK"), html.P(df_info["priceToBook"])]
                    ),
                    html.Div(
                        [
                            html.H4("ENTERPRISE TO EBITDA"),
                            html.P(df_info["enterpriseToEbitda"]),
                        ]
                    ),
                    html.Div([html.H4("BETA"), html.P(df_info["beta"])]),
                ],
                className="kpi",
            )
        ]
    )

    tickerdata = yf.Ticker(v2)
    # tickerinfo = tickerdata.info

    # today = datetime.datetime.today().isoformat()

    # for the graph of PM and M/Payout
    # html.Div([
    #     dcc.Graph(figure=get_dounts(df_info["profitMargins"], "Margin")),
    #     dcc.Graph(figure=get_dounts(df_info["payoutRatio"], "Payout"))
    # ], className="dounuts")
    # ])

    # only show the statistics
    # return [html.Div([tbl], id="graphs-content")], None
    # show both the statistics and the date
    return [html.Div([tbl, tbl1, tbl2], id="graphs-content")], None


# News Button
@app.callback(
    Output("news-content", "children"),
    [Input("news_search", "n_clicks")],
    [State("dropdown_tickers", "value")],
)
def get_news_callback(v, v2):
    if v != None:
        news = get_news(v2)
    else:
        raise PreventUpdate
    # return ""
    html_string = []

    for n in news:
        html_string.append(
            html.Div(
                [
                    html.H1([n[0]], className="title"),
                    html.P(n[1], className="p"),
                    html.P(n[2]),
                ]
            )
        )
    return html_string


# app.run_server(debug=True)
app.run_server(debug=True, port=8055)