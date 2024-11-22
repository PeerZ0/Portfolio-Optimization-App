import requests
import pandas as pd
from bs4 import BeautifulSoup
import yfinance as yf
from datetime import datetime
import os

def generate_html_wrapper(content, title):
    """Generate styled HTML with consistent layout"""
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
                const input = document.getElementById(inputId);
                const filter = input.value.toUpperCase();
                const table = document.getElementById(tableId);
                const rows = table.getElementsByTagName('tr');

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
    Scrapes Wikipedia pages for lists of major indices and gathers ticker symbols.
    Returns a list of dictionaries with stock data.
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
    tickers = list(set(tickers))  # Remove duplicates
    return [{'ticker': ticker} for ticker in tickers]

def fetch_ticker_data(tickers):
    """
    Fetches detailed information for each ticker using yfinance.
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

def static_data():
    try:
        df = pd.read_csv('static/ticker_data.csv')
        # Generate sector overview
        df['sector'] = df['sector'].fillna('Unknown').astype(str)
        sector_groups = df.groupby('sector').agg({
            'Ticker': 'count',
            'marketCap': 'sum'
        }).reset_index()
        sector_groups = sector_groups.sort_values('marketCap', ascending=False)
        
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
        
        with open('static/sector_data.html', 'w') as f:
            f.write(generate_html_wrapper(sector_html, "Sector Overview"))

        # Generate stock list
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
        
        with open('static/ticker_data.html', 'w') as f:
            f.write(generate_html_wrapper(stocks_html, "Stock List"))

        print("HTML files generated successfully in the static directory")
        return
        
    except FileNotFoundError:
        print("Error: ticker_data.csv not found. Please run a full update first.")
        return


def update_data():
    """
    Fetches stock symbols and company names using Wikipedia indices, then stores it in CSV and HTML files.
    """
    try:
        user_input = input("Do you want to update the data? (yes/no/static): ").strip().lower()
        
        if user_input == "static":
            static_data()
                            
        elif user_input == "yes":
            # Create static directory if it doesn't exist
            os.makedirs('static', exist_ok=True)

            # Fetch and process data
            print("Fetching tickers from Wikipedia...")
            wikipedia_tickers = get_wikipedia_tickers()
            ticker_data = fetch_ticker_data(wikipedia_tickers)
            df = pd.DataFrame(ticker_data)
            df = df.dropna(subset=['longName'])

            # Save raw data to CSV
            df.to_csv('static/ticker_data.csv', index=False)
            print("Data successfully saved to 'ticker_data.csv'")

            # Generate static HTML files
            static_data()            
        else:
            pass
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    update_data()