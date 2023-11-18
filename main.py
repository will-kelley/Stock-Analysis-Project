from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime
import plotly.graph_objects as go
import pandas as pd

stock_client = StockHistoricalDataClient("PKIMCNYABPKFSLDLQF1W", "SkEf5wljoJAdrvI55IIFL2VIphVpdXjLGXtRE7Pa")

request_parameter = StockBarsRequest(symbol_or_symbols="AMZN",
                                     timeframe=TimeFrame.Day,
                                     start=datetime(2023, 1, 1),
                                     end=datetime(2023, 11, 16))
bars = stock_client.get_stock_bars(request_parameter).df.reset_index()

fig = go.Figure(data=[go.Candlestick(x=bars["timestamp"],
                                     open=bars["open"],
                                     high=bars["high"],
                                     low=bars["low"],
                                     close=bars["close"])])

fig.show()
