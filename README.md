MIS3640 term project
Term Project - Neha and Yuwei
Our Project
For this project, we created a financial dashboard drawing data from Yahoo Finance and the New York Times websites. We are essentially addressing the problem of making it easier to compare the financial performance of various stocks in a single location without having to switch back and forth between different sources.

Development Components
We created our financial dashboard utilizing dash, yahoo finance, New York Time API, IEX API.

Requirement:

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
The code can be run in the terminal: python app.py

Functionality & Features
Our financial dashboard consists of two main components - a single stock analysis, and a multiple stock comparison tool.

Single Stock Analysis:

For the single stock analysis component of our dashboard, users can essentially select the stock they are interested in from a dropdown list. THey then have the option of selecting from one of three buttons: “historical price” which would lead them to a  dynamic graph depicting the historical price of the stock over time, “Indicators” which  would lead to a screen presenting metrics like the stock’s price and beta and book value, and “News” which would lead to a screen presenting the headings and subheadings of ten of the most recent articles discussing the stock. All of these pages, in addition to presenting the stated information, would also present a brief description of the stock company as well as it’s sector at the top of the page. All of these single stock analysis features make it an easy and streamlined process for a user to quickly study summarized information regarding a stock all through the single platform of our dashboard.

Multiple Stock Comparison:

For the multiple stock analysis component of our dashboard, users must refresh the dashboard prior to use. Then, they may select as many stocks as they like from the provided dropdown list. After selecting the stocks, they may select a date range through the date section provided. The default end date is the current day (though the user may change this), and the user can select any start date they would like. Finally, they can click the “Compare” button and will be led to a dynamic graph depicting the historical price of the selected stocks over the selected period of time, making it very easy for the user to quickly and easily compare the stocks relative to each other. If the user would like to learn more about any one of the specific stocks they had analyzed in this section, they can simply refresh the dashboard and use the single stock analysis feature to study that specific stock.
