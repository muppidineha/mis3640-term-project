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
from time import localtime, strftime
from pull_news import get_news
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.timeseries import TimeSeries
import numpy as np
import pandas as pd
import pandas_datareader.data as web
from datetime import datetime as dt, timedelta
from datetime import datetime
import os


def get_stock_price_fig(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(mode="lines", x=df["Date"], y=df["Close"]))
    return fig


# os.environ["IEX_API_KEY"]="pk_0340abbe62c04378a334752d0519e345"  #need a new one (bc it have exceeded the allotted message quota)
os.environ["IEX_API_KEY"] = "pk_e695aedcc1574bd8931f218f8f4057a9"

app = dash.Dash(
    external_stylesheets=[
        '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">'
    ]
)
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

app.layout = html.Div(
    [
        # Navigation to different tabs
        html.Div(
            [
                html.P("Select the company", className="start"),
                dcc.Dropdown("dropdown_tickers", placeholder="Please select a stock"),
                html.Div(
                    [
                        html.Button(
                            "Historical Price", className="stock-btn", id="stock"
                        ),
                        html.Button(
                            "Indicators", className="indicators-btn", id="indicators"
                        ),
                        html.Button("News", className="news-btn", id="news_search"),
                    ],
                    className="Buttons",
                ),
                html.Div(
                    [
                        html.Button("Compare", className="compare-btn", id="compare"),
                    ],
                    className="Buttons1",
                ),
                # Dashboard Title
                html.Div(
                    [
                        html.H1(children="Stock Price Dashboard"),
                    ],
                    className="button2",
                ),
                dcc.Dropdown(
                    id="dropdown_tickers_1",
                    multi=True,
                    placeholder="Please Select Stocks",
                ),
                html.Div(
                    [
                        html.H3("Select a start and end date:"),
                        dcc.DatePickerRange(
                            id="date-picker-range",
                            # min_date_allowed=dt(2015, 1, 1),
                            # max_date_allowed=dt.today().date() - timedelta(days=1),
                            # initial_visible_month=dt.today().date() - timedelta(days=1),
                            # end_date=dt.today().date() - timedelta(days=1)),
                            min_date_allowed=dt(2015, 1, 1),
                            max_date_allowed=dt.today(),
                            initial_visible_month=dt.today().date(),
                            end_date=dt.today().date(),
                        ),
                        html.Button(id="update-button", n_clicks=0, children="Submit"),
                    ],
                    className="row",
                ),
                # html.Div([dcc.Graph(id='data-plot')], className='row')
            ],
            className="Navigation",
        ),
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
                        html.Div([], id="graphs-content"),
                    ],
                    id="main-content",
                ),
                html.Div([], id="news-content", className="new_ticker"),
                html.Div(
                    [
                        html.Div([dcc.Graph(id="data-plot")], className="row"),
                    ],
                    id="compare-content",
                ),
                # html.Div(id ="compare-content", className="compare_ticker"),
                # html.Div([dcc.Graph(id='data-plot')], className='row'),
            ],
            className="content",
        ),
    ],
    className="container",
)

# Getting the stock names & symbols and also cleaning the data
symbols = (
    web.get_iex_symbols()
)  # TODO: EXPLORE THIS API TO REMOVE STOCK THAT IS LESS WELL KNOWN #https://iexcloud.io/docs/api/#symbols
symbols_list = pd.DataFrame({"symbol": symbols["symbol"], "name": symbols["name"]})
symbols_list["name"].replace("", np.nan, inplace=True)
symbols_list["symbol"].replace("", np.nan, inplace=True)
symbols_list.dropna(inplace=True)

# Removing stocks with very long names
mask = symbols_list["name"].str.len() < 40
symbols_list = symbols_list.loc[mask]
symbols_list = symbols_list.reset_index(drop=True)


@app.callback(
    Output("dropdown_tickers", "options"), [Input("dropdown_tickers", "value")]
)
def symbols_names_callback(value):
    options_list = [
        {"label": symbols_list.iloc[i]["name"], "value": symbols_list.iloc[i]["symbol"]}
        for i in range(0, len(symbols_list))
    ]

    return options_list


# Callback functions for updating the dashboard components
@app.callback(
    Output("dropdown_tickers_1", "options"), [Input("dropdown_tickers_1", "value")]
)
def symbols_names_callback(value):
    options_list = [
        {"label": symbols_list.iloc[i]["name"], "value": symbols_list.iloc[i]["symbol"]}
        for i in range(0, len(symbols_list))
    ]

    return options_list


# create a callback - bring Yahoo Finance API
# include Output and Input
@app.callback(
    [
        Output("description", "children"),
        Output("logo", "src"),
        Output("ticker", "children"),
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
    )


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

    # For DATE
    tbl = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H4("Today is"),
                            # html.P(datetime.datetime.today().isoformat())
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

    # FOR STOCK PRICE
    # Print out the stock price, price to book, Enterprise to EBITDA, and Beta
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
    [Input("news_search", "n_clicks")],
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
                    # html.P(n[2])
                ]
            )
        )
    return html_string, None


# Comparing Stocks
# Custom Error Classes
class StartDateError(Exception):
    pass


class NoneValueError(Exception):
    pass


class StocksSelectedError(Exception):
    pass


@app.callback(
    Output("data-plot", "figure"),
    [Input("update-button", "n_clicks")],
    [
        State("dropdown_tickers_1", "value"),
        State("date-picker-range", "start_date"),
        State("date-picker-range", "end_date"),
    ],
)
def graph_callback(n_clicks, selected_symbols, start_date, end_date):
    # Defining an empty layout
    # empty_layout = dict(data=[], layout=go.Layout(title=f' closing prices',
    #                                               xaxis={'title': 'Date'},
    #                                               yaxis={'title': 'Closing Price'},
    #                                               font={'family': 'verdana', 'size': 15, 'color': '#606060'}))

    if n_clicks == None:
        raise PreventUpdate
    else:
        empty_layout = dict(
            data=[],
            layout=go.Layout(
                title=f" closing prices",
                xaxis={"title": "Date"},
                yaxis={"title": "Closing Price"},
                font={"family": "verdana", "size": 15, "color": "#606060"},
            ),
        )

        # # If already initialized
        # if n_clicks > 0:
        try:
            # Error Checking on Inputs
            if start_date is None or end_date is None or selected_symbols is None:
                raise NoneValueError(
                    "ERROR : Start/End date or selected symbols is None!"
                )
            if start_date > end_date:
                raise StartDateError("ERROR : Start date is greater than End date!")
            if len(selected_symbols) == 0:
                raise StocksSelectedError("ERROR : No stocks selected!")

            # Getting the stock data
            df_list = [
                web.DataReader(symbol, "iex", start_date, end_date)
                for symbol in selected_symbols
            ]

            # Naming the DataFrames
            for i in range(0, len(df_list)):
                df_list[i].name = selected_symbols[i]

            # Formatting a graph title
            symbols = ""
            for symbol in selected_symbols:
                symbols = symbols + "'" + symbol + "', "
            symbols = symbols[:-2]

            # Making a list of all the available dates in the range selected
            dates = [i for i in df_list[0].index]

            # Creating the graph objects
            data = [
                go.Scatter(x=dates, y=df["close"], mode="lines", name=df.name)
                for df in df_list
            ]
            layout = go.Layout(
                title=f"{symbols} Closing Prices",
                xaxis={"title": "Date"},
                yaxis={"title": "Stock Closing Price"},
                font={"family": "verdana", "size": 15, "color": "#606060"},
            )
            fig = dict(data=data, layout=layout)
            return fig

        # Exception Handling
        except StartDateError as e:
            print(e)
            return empty_layout
        except NoneValueError as e:
            print(e)
            return empty_layout
        except StocksSelectedError as e:
            print(e)
            return empty_layout
        except Exception as e:
            print(e)

        else:
            return empty_layout

    # start = datetime.strptime(start_date[:10],'%Y-%m-%d')
    # end = datetime.strptime(end_date[:10],'%Y-%m-%d')
    # traces = []
    # iex = "pk_0340abbe62c04378a334752d0519e345"
    # df = [web.DataReader(symbol, 'iex', start_date, end_date) for symbol in selected_symbols]

    # for i in selected_symbols:
    #     traces.append({'x':df.index,'y':df['close'],'name':i})
    # fig = {
    #     'data':traces,
    #     'layout':{'title':selected_symbols}
    # }
    # return fig

    # start = datetime(start_date[:10],'%Y-%m-%d')
    # end = datetime(end_date[:10],'%Y-%m-%d')


if __name__ == "__main__":
    app.run_server(debug=True, port=8055)