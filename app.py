import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from dash.exceptions import PreventUpdate
import requests
from time import localtime, strftime
import numpy as np
import pandas_datareader.data as web
from datetime import datetime as dt
import os


# For historical stock price
def stock_price_figure(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(mode="lines", x=df["Date"], y=df["Close"]))
    fig.update_layout(
        title="Historical Stock Price", xaxis_title="Date", yaxis_title="Stock Price"
    )
    return fig


# For stock news
# https://developer.nytimes.com/
api_key = "PS5qFn9MAQYV3BPjSoHBx5a4UbqdmVcH"


def get_companyname(stocksymbol):
    """
    Use yahoo finance to convert symbol into company name
    """
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(
        stocksymbol
    )
    result = requests.get(url).json()
    for i in result["ResultSet"]["Result"]:
        if i["symbol"] == stocksymbol:
            return i["name"]


def pull_news(dropdown_tickers):
    """
    Pull news from New York Times
    """
    symbols = get_companyname(dropdown_tickers)
    sort = "relevance"
    url = f"https://api.nytimes.com/svc/search/v2/articlesearch.json?q={symbols}&api-key={api_key}&sort={sort}"
    request = requests.get(url).json()["response"]["docs"]
    if len(request) > 0:
        return request
    return "No News Found"


def get_news(dropdown_tickers):
    """
    Take the news pull from the New York Times and Return the abstract, lead paragraph, publication date, and website url for each news
    """
    news = pull_news(dropdown_tickers)
    news = [
        (n["abstract"], n["lead_paragraph"], n["pub_date"], n["web_url"]) for n in news
    ]
    return news


# For comparing stock
# List of IEX API KEY (in case: the API key have exceeded the allotted message quota)
# os.environ["IEX_API_KEY"]="pk_0340abbe62c04378a334752d0519e345" [USED]
# os.environ["IEX_API_KEY"]="pk_e695aedcc1574bd8931f218f8f4057a9" [USED]
os.environ["IEX_API_KEY"] = "pk_093ca3074be845c1a1186d470456dadc"
# os.environ["IEX_API_KEY"] = "pk_b21816e2e89d4e5d86834f242347d82a" [NOT USED]


# Dashboard Content and Layout:
app = dash.Dash()
server = app.server
app.layout = html.Div(
    [
        # Navigation (on the left side)
        html.Div(
            [
                html.P("Welcome to Our Financial Dashboard", className="start"),
                dcc.Dropdown("dropdown_tickers", placeholder="Please select a stock"),
                html.Div(
                    [
                        html.Button(
                            "Historical Price", className="stock-btn", id="stock"
                        ),
                        html.Button(
                            "Indicators", className="indicators-btn", id="indicators"
                        ),
                        html.Button("News", className="news-btn", id="stocknews"),
                    ],
                    className="Buttons",
                ),
                html.Div([html.P("Please refresh the dashboard", className="start2")]),
                dcc.Dropdown(
                    id="dropdown_tickers_1",
                    multi=True,
                    placeholder="Please select stocks",
                    className="thespace",
                ),
                html.Div(
                    [
                        html.H3("Select a start and end date:"),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=dt(2015, 1, 1),
                            max_date_allowed=dt.today(),
                            initial_visible_month=dt.today().date(),
                            end_date=dt.today().date(),
                        ),
                        html.Div(
                            [
                                html.Button(
                                    "Compare",
                                    className="compare-btn",
                                    n_clicks=0,
                                    id="compare",
                                )
                            ],
                            className="Buttons1",
                        ),
                    ],
                    className="row",
                ),
            ],
            className="Navigation",
        ),
        # Dashboard main content
        html.Div(
            [
                html.Div(
                    [
                        html.P(id="ticker"),
                        html.Img(id="logo"),
                    ],
                    className="header",
                ),
                html.Div(id="sector", className="sector_ticker"),
                html.Div(id="description", className="decription_ticker"),
                html.Div(
                    [
                        html.Div([], id="graphs-content"),
                        html.Div([], id="data-plot"),
                    ],
                    id="main-content",
                ),
                html.Div([], id="news-content", className="new_ticker"),
            ],
            className="content",
        ),
    ],
    className="container",
)

# Getting the stock names & symbols & remove stock with long name [more information on #https://iexcloud.io/docs/api/#symbols]
symbols = web.get_iex_symbols()
symbols_list = pd.DataFrame({"symbol": symbols["symbol"], "name": symbols["name"]})
symbols_list["name"].replace("", np.nan, inplace=True)
symbols_list["symbol"].replace("", np.nan, inplace=True)
symbols_list.dropna(inplace=True)
mask = symbols_list["name"].str.len() < 40
symbols_list = symbols_list.loc[mask]
symbols_list = symbols_list.reset_index(drop=True)


# For Part 1 dropdown
@app.callback(
    Output("dropdown_tickers", "options"), [Input("dropdown_tickers", "value")]
)
def symbols_names_callback(value):
    options_list = [
        {"label": symbols_list.iloc[i]["name"], "value": symbols_list.iloc[i]["symbol"]}
        for i in range(0, len(symbols_list))
    ]
    return options_list


# For Part 2 dropdown
@app.callback(
    Output("dropdown_tickers_1", "options"), [Input("dropdown_tickers_1", "value")]
)
def symbols_names_callback(value):
    options_list = [
        {"label": symbols_list.iloc[i]["name"], "value": symbols_list.iloc[i]["symbol"]}
        for i in range(0, len(symbols_list))
    ]
    return options_list


# For bring Yahoo Finance API and main content
@app.callback(
    [
        Output("sector", "children"),
        Output("description", "children"),
        Output("logo", "src"),
        Output("ticker", "children"),
    ],
    [Input("dropdown_tickers", "value")],
)
def basic_info(v):
    """
    Take the Input and return Business Summary from Yahoo Finance API. If there is not value inputed --> prevent update
    """
    if v == None:
        raise PreventUpdate
    else:
        ticker = yf.Ticker(v)
        inf = ticker.info

        df = pd.DataFrame.from_dict(inf, orient="index").T
        # df = df[
        #     [
        #         "sector",
        #         "logo_url",
        #         "longBusinessSummary",
        #         "shortName",
        #     ]
        # ]

        companysector = df["sector"].values[0]

        return (
            f"Sector: {companysector}",
            df["longBusinessSummary"].values[0],
            df["logo_url"].values[0],
            df["shortName"].values[0],
        )


# For Stock Historical Price Button
@app.callback(
    [Output("graphs-content", "children")],
    [Input("stock", "n_clicks")],
    [State("dropdown_tickers", "value")],
)
def stock_prices(v, v2):
    """
    use yahoo finance data to return a graph
    """
    if v == None:
        raise PreventUpdate
    if v2 == None:
        raise PreventUpdate

    df = yf.download(v2)
    df.reset_index(inplace=True)
    fig = stock_price_figure(df)
    return [dcc.Graph(figure=fig)]


# For Indicator Button
@app.callback(
    [Output("main-content", "children"), Output("stock", "n_clicks")],
    [Input("indicators", "n_clicks")],
    [State("dropdown_tickers", "value")],
)
def indicators(v, v2):
    """
    Use Yahoo Finance to return company's stock price, price to book, proft margins, book value, enterprise to EBITDA, short ratio, beta, payout ratio
    """
    if v == None:
        raise PreventUpdate
    if v2 == None:
        raise PreventUpdate
    ticker = yf.Ticker(v2)

    df_calendar = ticker.calendar.T
    df_info = pd.DataFrame.from_dict(ticker.info, orient="index").T
    # df_info = df_info[
    #     [
    #         "priceToBook",
    #         "profitMargins",
    #         "bookValue",
    #         "enterpriseToEbitda",
    #         "shortRatio",
    #         "beta",
    #         "payoutRatio",
    #         "trailingEps",
    #     ]
    # ]

    df_calendar["Earnings Date"] = pd.to_datetime(df_calendar["Earnings Date"])
    df_calendar["Earnings Date"] = df_calendar["Earnings Date"].dt.date

    ticker_yahoo = yf.Ticker(v2)
    data = ticker_yahoo.history()

    # For DATE
    tbl = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H4("Today is"),
                            html.P(strftime("%Y-%m-%d %H:%M:%S", localtime())),
                        ]
                    ),
                    html.Div(
                        [
                            html.H4("Stock Price"),
                            html.P(round(data.tail(1)["Close"].iloc[0])),
                        ]
                    ),
                ],
                className="kpi",
            )
        ]
    )

    # FOR STOCK PRICE/Statistics
    tbl2 = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H4("Profit Margins"),
                            html.P(round(df_info["profitMargins"].iloc[0])),
                        ]
                    ),
                    html.Div(
                        [
                            html.H4("Book Value"),
                            html.P(round(df_info["bookValue"].iloc[0])),
                        ]
                    ),
                    html.Div(
                        [
                            html.H4("Payout Ratio"),
                            html.P(round(df_info["payoutRatio"].iloc[0])),
                        ]
                    ),
                    html.Div(
                        [
                            html.H4("Price To Book"),
                            html.P(round(df_info["priceToBook"].iloc[0])),
                        ]
                    ),
                    html.Div(
                        [
                            html.H4("Enterprise to Ebitda"),
                            html.P(round(df_info["enterpriseToEbitda"].iloc[0])),
                        ]
                    ),
                    html.Div(
                        [
                            html.H4("Beta"),
                            html.P(round(df_info["beta"].iloc[0])),
                        ]
                    ),
                ],
                className="kpi",
            )
        ]
    )

    tickerdata = yf.Ticker(v2)
    tickerinfo = tickerdata.info
    return [html.Div([tbl, tbl2], id="graphs-content")], None


# News Button
@app.callback(
    [Output("news-content", "children"), Output("indicators", "n_clicks")],
    [Input("stocknews", "n_clicks")],
    [State("dropdown_tickers", "value")],
)
def news_search(v, v2):
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
                    html.P(n[3]),
                ]
            )
        )
    return html_string, None


# For Comparing Stocks
@app.callback(
    Output("data-plot", "children"),
    [Input("compare", "n_clicks")],
    [
        State("dropdown_tickers_1", "value"),
        State("date-range", "start_date"),
        State("date-range", "end_date"),
    ],
)
def graph_callback(n_clicks, selected_symbols, start_date, end_date):
    """
    Get stock price of each stock use iex api and return the historical stock price graph
    """
    if n_clicks == 0:
        raise PreventUpdate
    else:
        empty_layout = dict(
            data=[],
            layout=go.Layout(
                title=f" Closing Prices",
                xaxis={"title": "Date"},
                yaxis={"title": "Closing Price"},
                font={"family": "Trebuchet MS", "size": 15, "color": "#606060"},
            ),
        )

        df_list = [
            web.DataReader(symbol, "iex", start_date, end_date)
            for symbol in selected_symbols
        ]

        for i in range(0, len(df_list)):
            df_list[i].name = selected_symbols[i]

        symbols = ""
        for symbol in selected_symbols:
            symbols = symbols + "'" + symbol + "', "
        symbols = symbols[:-2]

        dates = [i for i in df_list[0].index]

        data = [
            go.Scatter(x=dates, y=df["close"], mode="lines", name=df.name)
            for df in df_list
        ]
        layout = go.Layout(
            title=f"{symbols} Closing Prices",
            xaxis={"title": "Date"},
            yaxis={"title": "Stock Closing Price"},
            font={"family": "Trebuchet MS", "size": 15, "color": "#606060"},
        )
        fig = dict(data=data, layout=layout)
        return [dcc.Graph(figure=fig)]


if __name__ == "__main__":
    app.run_server(debug=True, port=8055)