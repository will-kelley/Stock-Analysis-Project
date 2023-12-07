import sys
from stock_analysis import (fetch_stock_data, calculate_moving_averages,
                            plot_stock_data, fit_trendlines_single, fit_trendlines_high_low)
from datetime import datetime


def main():
    # User input for ticker symbol and date range
    ticker = input("Enter the ticker symbol: ")
    start_year, start_month, start_day = map(int, input("Enter start date (YYYY MM DD): ").split())
    end_year, end_month, end_day = map(int, input("Enter end date (YYYY MM DD): ").split())

    # Fetch stock data for the given ticker and date range
    bars = fetch_stock_data(ticker, datetime(start_year, start_month, start_day),
                            datetime(end_year, end_month, end_day))

    # Ask user if they want to include moving averages and volume bars
    include_ma = input("Include Moving Averages? (yes/no): ").lower() == 'yes'
    include_volume = input("Include Volume Bars? (yes/no): ").lower() == 'yes'

    # Ask user if they want to include trend line analysis
    include_trend_lines = input("Include Trend Line Analysis? (yes/no): ").lower() == 'yes'

    # Calculate moving averages for the stock data if selected
    if include_ma:
        bars = calculate_moving_averages(bars)

    # Perform trend line analysis if selected
    if include_trend_lines:
        support_coefs, resist_coefs = fit_trendlines_single(bars['close'].to_numpy())
        # Add code here to use these coefficients in your plot, if needed

    # Plot the stock data along with selected features
    plot_stock_data(bars, ticker, include_ma, include_volume)


if __name__ == "__main__":
    main()
