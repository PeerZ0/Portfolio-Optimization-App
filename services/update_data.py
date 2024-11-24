import requests
import pandas as pd
from bs4 import BeautifulSoup
import yfinance as yf
from datetime import datetime
import os

def generate_html_wrapper(content, title):
    """
    Generate styled HTML content with a consistent layout for display.

    Parameters
    ----------
    content : str
        The HTML content to embed within the wrapper.
    title : str
        The title of the HTML document.

    Returns
    -------
    str
        A complete HTML document with specified content and title.
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                margin: 2rem;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 2rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .table {{
                width: 100%;
                border-collapse: collapse;
                margin: 1rem 0;
            }}
            .table th, .table td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            .table th {{
                background-color: #f8f9fa;
                font-weight: 600;
            }}
            .table-striped tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            .table tr:hover {{
                background-color: #f2f2f2;
            }}
            .metadata {{
                color: #666;
                font-size: 0.9rem;
                margin-bottom: 1rem;
            }}
            .search {{
                width: 100%;
                padding: 8px;
                margin: 1rem 0;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
        </style>
        <script>
            function searchTable(inputId, tableId) {{
                // Function to search through the HTML table based on user input
                const input = document.getElementById(inputId);
                const filter = input.value.toUpperCase();
                const table = document.getElementById(tableId);
                const rows = table.getElementsByTagName('tr');

                // Loop through all table rows, and hide those that don't match the search query
                for (let i = 1; i < rows.length; i++) {{
                    const cells = rows[i].getElementsByTagName('td');
                    let found = false;
                    for (let j = 0; j < cells.length; j++) {{
                        const cell = cells[j];
                        if (cell) {{
                            const text = cell.textContent || cell.innerText;
                            if (text.toUpperCase().indexOf(filter) > -1) {{
                                found = true;
                                break;
                            }}
                        }}
                    }}
                    rows[i].style.display = found ? '' : 'none';
                }}
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="metadata">
                Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
            {content}
        </div>
    </body>
    </html>
    """

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
            # Request the page content
            response = requests.get(url)
            if response.status_code == 200:
                # Parse the page content using BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                # Extract tables using pandas read_html
                tables = pd.read_html(response.text)
                
                # Loop through tables to find relevant columns containing ticker symbols
                for table in tables:
                    if "Symbol" in table.columns:
                        tickers += table["Symbol"].to_list()
                    elif "Ticker" in table.columns:
                        tickers += table["Ticker"].to_list()
                    elif "Code" in table.columns:
                        tickers += table["Code"].to_list()
        except Exception as e:
            # Print any error that occurs while scraping a particular URL
            print(f"Error scraping {url}: {e}")
    
    # Clean up the ticker list by stripping whitespace and converting to uppercase
    tickers = [ticker.strip().upper() for ticker in tickers if isinstance(ticker, str)]
    # Remove duplicate tickers
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
            # Use yfinance to get the stock information
            stock = yf.Ticker(ticker['ticker'])
            info = stock.info
            # Append the fetched data to the data list
            data.append({
                'Ticker': ticker['ticker'],
                **info
            })
        except Exception as e:
            # Print any error that occurs while fetching data for a particular ticker
            print(f"Error fetching data for {ticker['ticker']}: {e}")
    return data

def static_data():
    """
    Generate static HTML and CSV files using the previously saved stock data.
    Generates a sector overview and a detailed stock list as HTML tables.
    """
    try:
        # Read the CSV file containing ticker data
        df = pd.read_csv('static/ticker_data.csv')
        # Fill missing sectors with 'Unknown' and convert to string type
        df['sector'] = df['sector'].fillna('Unknown').astype(str)
        # Group by sector to get count of tickers and sum of market cap
        sector_groups = df.groupby('sector').agg({
            'Ticker': 'count',
            'marketCap': 'sum'
        }).reset_index()
        # Sort by market cap in descending order
        sector_groups = sector_groups.sort_values('marketCap', ascending=False)
        
        # Generate HTML for sector overview
        sector_html = f"""
            <h1>Sector Overview</h1>
            <input type="text" id="sectorSearch" class="search" 
                    onkeyup="searchTable('sectorSearch', 'sectorTable')" 
                    placeholder="Search for sectors...">
            {sector_groups.to_html(
                index=False,
                classes='table table-striped',
                table_id='sectorTable',
                float_format=lambda x: '{:,.0f}'.format(x) if pd.notnull(x) else ''
            )}
        """
        
        # Save the sector overview HTML file
        with open('static/sector_data.html', 'w') as f:
            f.write(generate_html_wrapper(sector_html, "Sector Overview"))

        # Generate HTML for stock list
        stocks_html = f"""
            <h1>Stock List</h1>
            <input type="text" id="stockSearch" class="search" 
                    onkeyup="searchTable('stockSearch', 'stockTable')" 
                    placeholder="Search for stocks...">
            {df[['Ticker', 'longName', 'sector', 'marketCap']].to_html(
                index=False,
                classes='table table-striped',
                table_id='stockTable',
                float_format=lambda x: '{:,.0f}'.format(x) if pd.notnull(x) else ''
            )}
        """
        
        # Save the stock list HTML file
        with open('static/ticker_data.html', 'w') as f:
            f.write(generate_html_wrapper(stocks_html, "Stock List"))

        print("HTML files generated successfully in the static directory")
        return
        
    except FileNotFoundError:
        # Handle the case where the CSV file is not found
        print("Error: ticker_data.csv not found. Please run a full update first.")
        return

def update_data():
    """
    Update stock data by fetching ticker symbols and company information from Wikipedia.
    Saves the data in CSV and HTML formats for offline viewing.
    """
    try:
        while True:
            # Prompt user input for updating data
            user_input = input("Do you want to update the data? (yes/no/static): ").strip().lower()
            
            if user_input == "static":
                # Generate static data if user selects 'static'
                static_data()
                break
                            
            elif user_input == "yes":
                # Create a directory for storing static files if it doesn't exist
                os.makedirs('static', exist_ok=True)

                # Fetch and process data
                print("Fetching tickers from Wikipedia...")
                wikipedia_tickers = get_wikipedia_tickers()
                ticker_data = fetch_ticker_data(wikipedia_tickers)
                df = pd.DataFrame(ticker_data)
                # Drop rows where 'longName' or 'sector' is missing
                df = df.dropna(subset=['longName']) 
                df = df.dropna(subset=['sector']) 

                # Save raw data to CSV
                df.to_csv('static/ticker_data.csv', index=False)
                print("Data successfully saved to 'ticker_data.csv'")

                # Generate static HTML files
                static_data()
                break

            elif user_input == "no":
                # Exit if user selects 'no'
                break

            else:
                # Handle invalid input
                print("Invalid input. Please enter 'yes', 'no', or 'static'.")
            
    except Exception as e:
        # Print any unexpected errors that occur during the update process
        print(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    # Start the data update process when the script is executed
    update_data()
