from flask import Flask, render_template, request
from stock_analysis import fetch_stock_data, calculate_moving_averages, plot_stock_data
from datetime import datetime

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    plot_html = None  # Initialize plot_html to None
    if request.method == 'POST':
        # Extract form data
        ticker = request.form['ticker']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        include_ma = 'include_ma' in request.form
        include_volume = 'include_volume' in request.form

        # Convert dates from string to datetime
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Call your stock analysis functions
        bars = fetch_stock_data(ticker, start_date, end_date)
        if include_ma:
            bars = calculate_moving_averages(bars)

        # Generate plot and store its HTML in plot_html
        plot_html = plot_stock_data(bars, ticker, include_ma, include_volume)

    # Pass plot_html to the template, which will be None if no POST request is made
    return render_template('index.html', plot_html=plot_html)


if __name__ == '__main__':
    app.run(debug=True)
