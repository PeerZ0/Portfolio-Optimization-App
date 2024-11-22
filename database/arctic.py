import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from arctic import Arctic, TICK_STORE


# Step 1: Connect to MongoDB and initialize Arctic
def initialize_arctic():
    # Replace with your MongoDB connection string
    mongo_uri = "mongodb://localhost:27017"
    arctic_store = Arctic(mongo_uri)
    
    # Initialize a library for storing stock data (tick-store optimized for time series)
    if "stocks" not in arctic_store.list_libraries():
        arctic_store.initialize_library("stocks", lib_type=TICK_STORE)
    
    return arctic_store["stocks"]

stocks_library = initialize_arctic()

# Step 2: Define the list of tickers and update logic
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA"]  # Example tickers

def update_stock_data(tickers, library, start_date="2023-01-01"):
    """Fetch and update stock data in Arctic DB."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    for ticker in tickers:
        try:
            print(f"Updating data for {ticker}...")
            
            # Check if the ticker already exists in the library
            if ticker in library.list_symbols():
                # Retrieve the last date of stored data
                existing_data = library.read(ticker).data
                last_date = existing_data.index[-1].strftime("%Y-%m-%d")
                start_date = (datetime.strptime(last_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                print(f"{ticker} not found in library, starting fresh...")
            
            # Fetch data from yfinance
            new_data = yf.download(ticker, start=start_date, end=today)["Adj Close"]
            
            if not new_data.empty:
                # Convert to a DataFrame if necessary
                new_data = pd.DataFrame(new_data)
                new_data.columns = ["Adj Close"]
                
                # Append new data to the Arctic DB
                library.append(ticker, new_data, upsert=True)
                print(f"Data for {ticker} updated successfully.")
            else:
                print(f"No new data found for {ticker}.")
        except Exception as e:
            print(f"Error updating {ticker}: {e}")

# Step 3: Call the update function
update_stock_data(tickers, stocks_library)
