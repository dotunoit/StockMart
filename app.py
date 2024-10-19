from flask import Flask, render_template, request, redirect, url_for
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.utils  # This is the missing import for using PlotlyJSONEncoder
import json

app = Flask(__name__)

# Index route
@app.route('/')
def index():
    return render_template('index.html')

# Dashboard route (handles both GET and POST)
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        # Retrieve form data from the POST request
        symbol = request.form['symbol']
        start_date = request.form['start_date']
        end_date = request.form.get('end_date', datetime.today().strftime('%Y-%m-%d'))

        # Redirect to the result page with the submitted data as query parameters
        return redirect(url_for('result', symbol=symbol, start=start_date, end=end_date))

    content = '''<p>Some dashboard content here</p>
    [yahoonews v="https://news.yahoo.com/video/yahoo-news-live-ben-carson-182500280.html"]'''
    content = replace_shortcodes(content)
    
    return render_template('dashboard.html', content=content)

# Result route to show stock data and charts (handles both GET and POST)
@app.route('/result', methods=['GET'])
def result():
    symbols = request.args.get('symbol').split(',')
    start_date = request.args.get('start')
    end_date = request.args.get('end', datetime.today().strftime('%Y-%m-%d'))
    plots = []

    for symbol in symbols:
        try:
            # Fetch stock data from yfinance (or similar API)
            stock_data = yf.download(symbol.strip(), start=start_date, end=end_date)

            # Fetch company name (this is just an example, adjust based on your API)
            company_name = fetch_company_name(symbol.strip())  # Define a function to get company name
            
            if stock_data.empty:
                continue

            stock_data['SMA_60'] = stock_data['Close'].rolling(window=60).mean()
            stock_data['Daily_Return'] = stock_data['Close'].pct_change() * 100

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], mode='lines', name=f'{symbol} Closing Price'))
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['SMA_60'], mode='lines', name=f'{symbol} 60-day SMA', line=dict(dash='dash')))

            fig.update_layout(
                title=f"{symbol} Closing Price and 60-day SMA",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                template="plotly_dark"
            )

            plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            plots.append({
                'symbol': symbol,
                'company_name': company_name,  # Add the company name to the plot data
                'plot_json': plot_json
            })

        except Exception as e:
            return f"Error fetching data for {symbol}: {e}"

    return render_template('result.html', plots=plots)

# Example function to fetch company name
def fetch_company_name(symbol):
    # You can use yfinance or another API to fetch the company name based on the stock symbol
    stock = yf.Ticker(symbol)
    return stock.info['longName']  # Assuming yfinance's longName field holds the company name


# Utility function to replace shortcodes in the content
def replace_shortcodes(content):
    if '[yahoonews' in content:
        start_idx = content.index('[yahoonews')
        end_idx = content.index('"]', start_idx) + 2
        shortcode = content[start_idx:end_idx]

        # Extract the video URL from the shortcode
        url_start = shortcode.index('v="') + 3
        url_end = shortcode.index('"', url_start)
        video_url = shortcode[url_start:url_end]

        # Replace the shortcode with an iframe embed
        iframe = f'<iframe width="560" height="315" src="{video_url}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>'
        content = content.replace(shortcode, iframe)
    return content

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)