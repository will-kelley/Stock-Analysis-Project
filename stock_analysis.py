from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from config import API_KEY, SEC_KEY


def fetch_stock_data(ticker, start_date, end_date):
    # Initialize the stock data client with API credentials
    stock_client = StockHistoricalDataClient(API_KEY, SEC_KEY)

    # Set up request parameters for the stock data (ticker, timeframe, start and end dates)
    request_parameter = StockBarsRequest(symbol_or_symbols=ticker,
                                         timeframe=TimeFrame.Day,
                                         start=start_date,
                                         end=end_date)

    # Fetch stock data and reset index for easier handling
    bars = stock_client.get_stock_bars(request_parameter).df.reset_index()
    return bars


def calculate_moving_averages(data, window_sizes=[20, 50, 100]):
    # Calculate moving averages for specified window sizes
    for window in window_sizes:
        data[f'SMA_{window}'] = data['close'].rolling(window=window).mean()
    return data


def plot_stock_data(data, ticker, include_ma=False, include_volume=False):
    # Create a Plotly figure for candlestick chart
    fig = go.Figure(data=[go.Candlestick(x=data["timestamp"],
                                         open=data["open"],
                                         high=data["high"],
                                         low=data["low"],
                                         close=data["close"])])

    # Add moving average lines to the candlestick chart if selected
    if include_ma:
        for window in [20, 50, 100]:
            if f'SMA_{window}' in data.columns:
                fig.add_trace(go.Scatter(x=data['timestamp'], y=data[f'SMA_{window}'],
                                         mode='lines', name=f'SMA {window}'))

    # Add volume bars to the chart if selected
    if include_volume:
        fig.add_trace(go.Bar(x=data["timestamp"], y=data["volume"], name='Volume', yaxis='y2'))

    # Configure the layout for the chart, including secondary y-axis for volume if selected
    yaxis2_config = dict(overlaying='y', side='right', title='Volume') if include_volume else None

    fig.update_layout(
        title=f'Stock Data for {ticker}',
        yaxis2=yaxis2_config,
        xaxis_rangeslider_visible=False
    )

    # Display the chart
    fig.show()

