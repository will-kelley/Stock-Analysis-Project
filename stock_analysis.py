from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import numpy as np
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


def check_trend_line(support: bool, pivot: int, slope: float, y: np.array):
    # compute sum of differences between line and prices,
    # return negative val if invalid

    # Find the intercept of the line going through pivot point with given slope
    intercept = -slope * pivot + y[pivot]
    line_vals = slope * np.arange(len(y)) + intercept

    diffs = line_vals - y

    # Check to see if the line is valid, return -1 if it is not valid.
    if support and diffs.max() > 1e-5:
        return -1.0
    elif not support and diffs.min() < -1e-5:
        return -1.0

    # Squared sum of diffs between data and line
    err = (diffs ** 2.0).sum()
    return err;


def optimize_slope(support: bool, pivot: int, init_slope: float, y: np.array):
    # Amount to change slope by. Multiplyed by opt_step
    slope_unit = (y.max() - y.min()) / len(y)

    # Optmization variables
    opt_step = 1.0
    min_step = 0.0001
    curr_step = opt_step  # current step

    # Initiate at the slope of the line of best fit
    best_slope = init_slope
    best_err = check_trend_line(support, pivot, init_slope, y)
    assert (best_err >= 0.0)  # Shouldn't ever fail with initial slope

    get_derivative = True
    derivative = None
    while curr_step > min_step:

        if get_derivative:
            # Numerical differentiation, increase slope by very small amount
            # to see if error increases/decreases.
            # Gives us the direction to change slope.
            slope_change = best_slope + slope_unit * min_step
            test_err = check_trend_line(support, pivot, slope_change, y)
            derivative = test_err - best_err;

            # If increasing by a small amount fails,
            # try decreasing by a small amount
            if test_err < 0.0:
                slope_change = best_slope - slope_unit * min_step
                test_err = check_trend_line(support, pivot, slope_change, y)
                derivative = best_err - test_err

            if test_err < 0.0:  # Derivative failed, give up
                raise Exception("Derivative failed. Check your data. ")

            get_derivative = False

        if derivative > 0.0:  # Increasing slope increased error
            test_slope = best_slope - slope_unit * curr_step
        else:  # Increasing slope decreased error
            test_slope = best_slope + slope_unit * curr_step

        test_err = check_trend_line(support, pivot, test_slope, y)
        if test_err < 0 or test_err >= best_err:
            # slope failed/didn't reduce error
            curr_step *= 0.5  # Reduce step size
        else:  # test slope reduced error
            best_err = test_err
            best_slope = test_slope
            get_derivative = True  # Recompute derivative

    # Optimize done, return best slope and intercept
    return best_slope, -best_slope * pivot + y[pivot]


def fit_trendlines_single(data: np.array):
    # find line of best fit (least squared)
    # coefs[0] = slope,  coefs[1] = intercept
    x = np.arange(len(data))
    coefs = np.polyfit(x, data, 1)

    # Get points of line.
    line_points = coefs[0] * x + coefs[1]

    # Find upper and lower pivot points
    upper_pivot = (data - line_points).argmax()
    lower_pivot = (data - line_points).argmin()

    # Optimize the slope for both trend lines
    support_coefs = optimize_slope(True, lower_pivot, coefs[0], data)
    resist_coefs = optimize_slope(False, upper_pivot, coefs[0], data)

    return support_coefs, resist_coefs


def fit_trendlines_high_low(high: np.array, low: np.array, close: np.array):
    x = np.arange(len(close))
    coefs = np.polyfit(x, close, 1)
    # coefs[0] = slope,  coefs[1] = intercept
    line_points = coefs[0] * x + coefs[1]
    upper_pivot = (high - line_points).argmax()
    lower_pivot = (low - line_points).argmin()

    support_coefs = optimize_slope(True, lower_pivot, coefs[0], low)
    resist_coefs = optimize_slope(False, upper_pivot, coefs[0], high)

    return support_coefs, resist_coefs


def plot_stock_data(data, ticker, include_ma=False, include_volume=False, trend_lines=None):
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

    if trend_lines:
        # Plot support line
        if 'support' in trend_lines and trend_lines['support']:
            slope, intercept = trend_lines['support']
            y_values = slope * np.arange(len(data)) + intercept
            fig.add_trace(go.Scatter(x=data['timestamp'], y=y_values, mode='lines', name='Support Line'))

        # Plot resistance line
        if 'resistance' in trend_lines and trend_lines['resistance']:
            slope, intercept = trend_lines['resistance']
            y_values = slope * np.arange(len(data)) + intercept
            fig.add_trace(go.Scatter(x=data['timestamp'], y=y_values, mode='lines', name='Resistance Line'))

    # Configure the layout for the chart, including secondary y-axis for volume if selected
    yaxis2_config = dict(overlaying='y', side='right', title='Volume') if include_volume else None

    fig.update_layout(
        title=f'Stock Data for {ticker}',
        yaxis2=yaxis2_config,
        xaxis_rangeslider_visible=False
    )

    # Display the chart
    fig.show()

