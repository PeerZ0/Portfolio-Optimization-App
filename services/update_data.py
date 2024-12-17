# services/update_data.py
"""
Service function to update stock data by fetching ticker symbols and company information from Wikipedia.

This script is used to update the stock data used in the application by fetching ticker symbols and company information
from Wikipedia and saving the data to a CSV file stored in the 'static' directory.
The process is as follows:
1. Scrape Wikipedia pages for lists of major stock indices and gather ticker symbols.
2. Fetch detailed information for each ticker using the yfinance API.
3. Save the data to a CSV file for use in the application.
"""

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
            # Send a request to the Wikipedia page
            response = requests.get(url)
            if response.status_code == 200:
                # Parse the HTML content of the page
                soup = BeautifulSoup(response.text, 'html.parser')
                # Extract tables from the page using pandas
                tables = pd.read_html(response.text)
                
                for table in tables:
                    # Identify the column containing ticker symbols based on its header
                    if "Symbol" in table.columns:
                        tickers += table["Symbol"].to_list()
                    elif "Ticker" in table.columns:
                        tickers += table["Ticker"].to_list()
                    elif "Code" in table.columns:
                        tickers += table["Code"].to_list()
        except Exception as e:
            # Log an error if scraping fails for a URL
            print(f"Error scraping {url}: {e}")
    
    # Clean up and standardize ticker symbols
    tickers = [ticker.strip().upper() for ticker in tickers if isinstance(ticker, str)]
    tickers = list(set(tickers))  # Remove duplicates
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
            # Use yfinance to fetch ticker information
            stock = yf.Ticker(ticker['ticker'])
            info = stock.info  # Extract detailed information about the stock
            data.append({
                'Ticker': ticker['ticker'],  # Add ticker symbol
                **info  # Include all available information from yfinance
            })
        except Exception as e:
            # Log an error if data fetching fails for a specific ticker
            print(f"Error fetching data for {ticker['ticker']}: {e}")
    return data

def update_data(response: str = "no"):
    """
    Update stock data by fetching ticker symbols and company information from Wikipedia.
    
    Parameters
    ----------
    response : str
        User response to confirm whether data should be updated. "yes" triggers the update process.
    """
    try:
        if response == "yes":
            # Ensure the static directory exists
            os.makedirs('static', exist_ok=True)

            print("Fetching tickers from Wikipedia...")
            # Scrape ticker symbols from Wikipedia
            wikipedia_tickers = get_wikipedia_tickers()
            # Fetch detailed stock data for each ticker
            ticker_data = fetch_ticker_data(wikipedia_tickers)
            
            # Create a DataFrame from the fetched data
            df = pd.DataFrame(ticker_data)
            # Drop rows with missing values in critical columns
            df = df.dropna(subset=['longName'])
            df = df.dropna(subset=['sector'])

            # Save the data to a CSV file
            df.to_csv('static/ticker_data.csv', index=False)
            print("Data successfully saved to 'ticker_data.csv'")
            
    except Exception as e:
        # Log any errors that occur during the update process
        print(f"An error occurred: {str(e)}")
        raise