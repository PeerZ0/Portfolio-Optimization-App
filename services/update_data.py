# services/update_data.py
# Update stock data by fetching ticker symbols and company information from Wikipedia and yfinance.

import requests
import pandas as pd
from bs4 import BeautifulSoup
import yfinance as yf
import os

def get_wikipedia_tickers():
    """
    Scrape Wikipedia pages for lists of major stock indices and gather ticker symbols.

    Returns
    -------
    list of dict
        A list of dictionaries, each containing stock ticker data.
    """
    tickers = []
    urls = [
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        "https://en.wikipedia.org/wiki/FTSE_100_Index",
        "https://en.wikipedia.org/wiki/DAX",
        "https://en.wikipedia.org/wiki/Nikkei_225",
        "https://en.wikipedia.org/wiki/EURO_STOXX_50",
        "https://en.wikipedia.org/wiki/Swiss_Market_Index"
    ]
    
    for url in urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                tables = pd.read_html(response.text)
                
                for table in tables:
                    if "Symbol" in table.columns:
                        tickers += table["Symbol"].to_list()
                    elif "Ticker" in table.columns:
                        tickers += table["Ticker"].to_list()
                    elif "Code" in table.columns:
                        tickers += table["Code"].to_list()
        except Exception as e:
            print(f"Error scraping {url}: {e}")
    
    tickers = [ticker.strip().upper() for ticker in tickers if isinstance(ticker, str)]
    tickers = list(set(tickers))
    return [{'ticker': ticker} for ticker in tickers]

def fetch_ticker_data(tickers):
    """
    Fetch detailed information for each ticker using the yfinance API.

    Parameters
    ----------
    tickers : list of dict
        A list of ticker symbols to fetch data for.

    Returns
    -------
    list of dict
        A list of dictionaries containing ticker data, including company information and market details.
    """
    data = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker['ticker'])
            info = stock.info
            data.append({
                'Ticker': ticker['ticker'],
                **info
            })
        except Exception as e:
            print(f"Error fetching data for {ticker['ticker']}: {e}")
    return data

def update_data(response: str = "no"):
    """
    Update stock data by fetching ticker symbols and company information from Wikipedia.
    """
    try:
        if response == "yes":
            os.makedirs('static', exist_ok=True)

            print("Fetching tickers from Wikipedia...")
            wikipedia_tickers = get_wikipedia_tickers()
            ticker_data = fetch_ticker_data(wikipedia_tickers)
            df = pd.DataFrame(ticker_data)
            df = df.dropna(subset=['longName'])
            df = df.dropna(subset=['sector'])

            df.to_csv('static/ticker_data.csv', index=False)
            print("Data successfully saved to 'ticker_data.csv'")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    update_data()