import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

def fetch_data_from_api(url):
    """
    Fetches stock data from a given API URL.
    :param url: API URL.
    :return: List of dictionaries with stock data.
    """
    try:
        response = requests.get(url)
        data = response.json()
        print("Data fetched from API")
        
        if not isinstance(data, dict):
            print(f"Unexpected response format from {url}. Expected dictionary, got {type(data)}")
            return []
            
        if 'data' not in data:
            print(f"Response missing 'data' key from {url}. Available keys: {list(data.keys())}")
            return []
            
        if not isinstance(data['data'], dict):
            print(f"'data' is not a dictionary in response from {url}. Got {type(data['data'])}")
            return []
            
        if 'rows' not in data['data']:
            print(f"Response missing 'rows' key in data from {url}. Available keys: {list(data['data'].keys())}")
            return []

        return data['data']['rows']

    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return []
    except ValueError as e:
        print(f"Error parsing JSON from {url}: {e}")
        return []

def get_wikipedia_tickers():
    """
    Scrapes Wikipedia pages for lists of major indices and gathers ticker symbols.
    Returns a list of dictionaries with stock data.
    """
    tickers = []

    # List of Wikipedia URLs for major indices
    urls = [
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        "https://en.wikipedia.org/wiki/FTSE_100_Index",
        "https://en.wikipedia.org/wiki/DAX",
        "https://en.wikipedia.org/wiki/Nikkei_225",
        "https://en.wikipedia.org/wiki/EURO_STOXX_50",
        "https://en.wikipedia.org/wiki/Swiss_Market_Index"
    ]

    # Loop through each URL and extract tickers
    for url in tqdm(urls, desc="Fetching Wikipedia tickers", unit="page"):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                tables = pd.read_html(response.text)

                # Each Wikipedia page may have different structures, so adjust accordingly
                for table in tables:
                    if "Symbol" in table.columns or "Ticker" in table.columns:
                        # Extract the ticker column based on its label
                        if "Symbol" in table.columns:
                            tickers += table["Symbol"].to_list()
                        elif "Ticker" in table.columns:
                            tickers += table["Ticker"].to_list()
                    elif "Code" in table.columns:
                        # For some indices like ASX 200, the column might be labeled "Code"
                        tickers += table["Code"].to_list()
        except Exception as e:
            print(f"Error scraping {url}: {e}")

    # Clean and standardize tickers
    tickers = [ticker.strip().upper() for ticker in tickers if isinstance(ticker, str)]
    tickers = list(set(tickers))  # Remove duplicates

    return [{'symbol': ticker} for ticker in tickers]

def update_data():
    """
    Fetches stock symbols and company names using NASDAQ, NYSE APIs, and Wikipedia, then stores it in a CSV file.
    Fetches about 2000 of the largest stocks from NASDAQ, NYSE, and Wikipedia indices.
    """
    bool_update_data = input("Do you want to update the data? (yes/no): ").strip().lower()

    if bool_update_data == "yes":
        # URLs for NASDAQ API
        nasdaq_url = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&download=true"

        # Fetch stock data from NASDAQ API
        print("Fetching NASDAQ stock data...")
        # nasdaq_stocks = fetch_data_from_api(nasdaq_url)

        # Fetch Wikipedia tickers
        print("Fetching tickers from Wikipedia...")
        wikipedia_tickers = get_wikipedia_tickers()

        # Combine NASDAQ and Wikipedia data
        all_stocks = wikipedia_tickers

        # Clean and prepare the data for use with Polars
        # Extract relevant information (Symbol, Name, Sector, etc.)
        stock_data = []

        # Use tqdm to show the progress of processing the combined stock data
        for stock in tqdm(all_stocks, desc="Processing stock data", unit="stock"):
            stock_data.append({
                'Symbol': stock.get('symbol', 'N/A'),
                'Company Name': stock.get('name', 'N/A'),
                'Sector': stock.get('sector', 'N/A'),
                'Industry': stock.get('industry', 'N/A'),
                'Country': stock.get('country', 'N/A'),
                'Market Cap': stock.get('marketCap', 'N/A')
            })

        # Convert to a Polars DataFrame and save as CSV
        df = pd.DataFrame(stock_data)

        # Save the data to a CSV file
        df.to_csv('static/stocks_data.csv', index=False)

        print("Data successfully saved to 'stocks_data.csv'.")
    else:
        pass

update_data()
