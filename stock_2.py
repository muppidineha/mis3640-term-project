# Compare button

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
from pull_compare import structure


def get_stock_price_fig(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(mode="lines", x=df["Date"], y=df["Close"]))
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
                html.P("Select the company", className="start"),
                # try these two lines:
                # dcc.Input(id="dropdown_tickers", value = "", placeholder = "please enter the symbol", type = "text"),
                # html.Button("Submit", id="button")
                #     dcc.Dropdown("dropdown_tickers", options=[
                #     {"label":"Adobe", "value":"ADBE"},
                #     {"label":"Apple", "value":"AAPL"},
                #     {"label":"AT&T", "value":"T"},
                #     {"label":"Facebook", "value":"FB"},
                #     {"label":"Microsoft", "value":"MSFT"},
                #     {"label":"Tesla", "value":"TSLA"}, #change these part to include more symbols
                # ]),
                dcc.Dropdown("dropdown_tickers", placeholder="Please select a stock"),
                # html.Div([html.Button("Search", className="search-btn", id="search"),], className="Search")
                html.Div(
                    [
                        html.Button(
                            "Historical Price", className="stock-btn", id="stock"
                        ),
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
                # Dashboard Title
                html.Div(
                    [
                        html.H1(children="Stock Price Dashboard"),
                    ],
                    className="button2",
                ),
                # DropDown
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
                            min_date_allowed=dt(2015, 1, 1),
                            max_date_allowed=dt.today().date() - timedelta(days=1),
                            initial_visible_month=dt.today().date() - timedelta(days=1),
                            end_date=dt.today().date() - timedelta(days=1),
                        ),
                        html.Button(id="update-button", n_clicks=0, children="Submit"),
                    ],
                    className="button2",
                ),
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
                        # html.Div([],id = "candle-graph"), #new add for compare
                        # html.Div([],id ="news-content"),
                        # html.Div([],id='news_content'),  #new added for news
                        # html.Div([],id ="news-content", className="new_ticker"),
                    ],
                    id="main-content",
                ),
                html.Div([], id="news-content", className="new_ticker"),
                html.Div(id="compare-content", className="compare_ticker"),
                dcc.Graph(
                    id="my_graph",
                    figure={
                        "data": [{"x": [1, 2], "y": [3, 1]}],
                        "layout": {"title": "Default Title"},
                    },
                ),
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


# # Custom Error Classes


# class StartDateError(Exception):
#     pass


# class NoneValueError(Exception):
#     pass


# class StocksSelectedError(Exception):
#     pass


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


@app.callback(
    Output("my_graph", "figure"),
    [Input("update-button", "n_clicks")],
    [
        State("dropdown_tickers_1", "value"),
        State("date-picker-range", "start_date"),
        State("date-picker-range", "end_date"),
    ],
)
def graph_callback(n_clicks, selected_symbols, start_date, end_date):
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

    traces = []
    IEX_API_KEY = "pk_0340abbe62c04378a334752d0519e345"
    df_list = [
        web.DataReader(
            symbol, token="IEX_API_KEY", start_date=start_date, end_date=end_date
        )
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
    dates = [i for i in df_list[0].index]

    # Creating the graph objects
    data = [
        go.Scatter(x=dates, y=df["close"], mode="lines", name=df.name) for df in df_list
    ]
    fig = dict(data=data)
    return fig


if __name__ == "__main__":
    app.run_server(debug=True, port=8055)

    # if n_clicks ==0:
    #     return PreventUpdate
    # else:
    #     IEX_API_KEY = "pk_0340abbe62c04378a334752d0519e345"
    #     df_list = [web.DataReader(symbol, 'IEX_API_KEY', start_date, end_date) for symbol in selected_symbols]

    #     # df_list = [web.DataReader(symbol, 'iex', start_date, end_date) for symbol in selected_symbols]

    #         # Naming the DataFrames
    #     for i in range(0, len(df_list)):
    #         df_list[i].name = selected_symbols[i]

    #         # Formatting a graph title
    #     symbols = ""
    #     for symbol in selected_symbols:
    #         symbols = symbols + "'" + symbol + "', "
    #     symbols = symbols[:-2]

    #         # Making a list of all the available dates in the range selected
    #     dates = [i for i in df_list[0].index]

    #     data = [go.Scatter(x=dates, y=df['close'], mode='lines', name=df.name) for df in df_list]
    #     layout = go.Layout(title='{} closing prices'.format(symbols),
    #                         xaxis={'title': 'Date'},
    #                         yaxis={'title': 'Closing Price'},
    #                         font={'family': 'verdana', 'size': 15, 'color': '#606060'})
    #     fig = dict(data=data, layout=layout)
    #     return fig

    # # Defining an empty layout
    # empty_layout = dict(data=[], layout=go.Layout(title=f' Closing Prices',
    #                                               xaxis={'title': 'Date'},
    #                                               yaxis={'title': 'Closing Price'},
    #                                               font={'family': 'verdana', 'size': 15, 'color': '#606060'}))

    # # If already initialized
    # try:
    #         # Error Checking on Inputs
    #     if start_date is None or end_date is None or selected_symbols is None:
    #         raise NoneValueError("ERROR : Start/End date or selected symbols is None!")
    #     if start_date > end_date:
    #         raise StartDateError("ERROR : Start date is greater than End date!")
    #     if len(selected_symbols) == 0:
    #         raise StocksSelectedError("ERROR : No stocks selected!")

    #         # Getting the stock data
    #     IEX_API_KEY = "pk_0340abbe62c04378a334752d0519e345"
    #     df_list = [web.DataReader(symbol, 'IEX_API_KEY', start_date, end_date) for symbol in selected_symbols]

    #         # Naming the DataFrames
    #     for i in range(0, len(df_list)):
    #         df_list[i].name = selected_symbols[i]

    #         # Formatting a graph title
    #     symbols = ""
    #     for symbol in selected_symbols:
    #         symbols = symbols + "'" + symbol + "', "
    #     symbols = symbols[:-2]

    #         # Making a list of all the available dates in the range selected
    #     dates = [i for i in df_list[0].index]

    #         # Creating the graph objects
    #     data = [go.Scatter(x=dates, y=df['close'], mode='lines', name=df.name) for df in df_list]
    #     layout = go.Layout(title=f'{symbols} Closing Prices', xaxis={'title': 'Date'}, yaxis={'title': 'Closing Price'}, font={'family': 'verdana', 'size': 15, 'color': '#606060'})
    #     fig = dict(data=data, layout=layout)

    #     # layout = go.Layout(title=f'{symbols} Closing Prices', xaxis={'title': 'Date'}, yaxis={'title': 'Closing Price'}, font={'family': 'verdana', 'size': 15, 'color': '#606060'})
    #     fig = dict(data=data)
    #     return fig

    #     # Exception Handling
    # except StartDateError as e:
    #     print(e)
    #     return empty_layout
    # except NoneValueError as e:
    #     print(e)
    #     return empty_layout
    # except StocksSelectedError as e:
    #     print(e)
    #     return empty_layout
    # except Exception as e:
    #     print(e)

# Running the server
# if __name__ == '__main__':
#     # app.run_server(debug=False, port=5000, host='0.0.0.0')
#     # app.run_server(debug=True)
#     app.run_server(debug=True, port=5000)


# app.run_server(debug=True, port=8055)
