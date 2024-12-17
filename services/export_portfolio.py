# services/export_portfolio.py
"""
Service to export the optimized portfolio to a CSV file with additional information for each ticker
such as company name, sector, industry, website, and country.
"""

import pandas as pd

def export_portfolio(weights, strategy_name, output_file='static/portfolio_export.csv'):
    """
    Exports a portfolio of stocks with additional information from a static ticker file.

    Parameters
    ----------
    weights : dict
        Dictionary containing tickers as keys and weights as values.
    strategy_name : str
        Name of the strategy used for optimization.
    output_file : str, optional
        Path to save the resulting CSV file (default is 'static/portfolio_export.csv').

    Returns
    -------
    str
        Path to the saved CSV file.
    """
    # Load ticker data
    try:
        df = pd.read_csv('static/ticker_data.csv')
    except FileNotFoundError:
        raise FileNotFoundError("The static/ticker_data.csv file could not be found.")
    
    # Ensure 'Ticker' column exists
    if 'Ticker' not in df.columns:
        raise ValueError("The input CSV must contain a 'Ticker' column.")

    # Convert weights dictionary to a DataFrame
    weights_df = pd.DataFrame(weights.items(), columns=['Ticker', 'Weight'])

    # Merge weights with ticker data
    portfolio_df = pd.merge(weights_df, df, on='Ticker', how='left')

    # Check for missing tickers
    missing_tickers = portfolio_df[portfolio_df.isnull().any(axis=1)]['Ticker'].tolist()
    # Print warning if missing tickers
    if missing_tickers:
        print(f"Warning: The following tickers were not found in the ticker_data file: {missing_tickers}")

    # Select relevant columns for the export
    export_columns = [
        'Ticker','Weight', 'longName', 'sector', 'industry', 'website', 'country'
    ]
    
    # Filter to keep only relevant columns (some might be missing in data)
    export_columns = [col for col in export_columns if col in portfolio_df.columns]
    portfolio_df = portfolio_df[export_columns]

    # Sort by Weight in descending order
    portfolio_df = portfolio_df.sort_values(by='Weight', ascending=False)

    # Round Weight to three decimal places
    portfolio_df['Weight'] = portfolio_df['Weight'].round(3)
    portfolio_df = portfolio_df[portfolio_df['Weight'] > 0]
    # Rename columns
    portfolio_df.rename(columns={'longName': 'Company Name'}, inplace=True)
    portfolio_df.rename(columns={'sector': 'Sector'}, inplace=True)
    portfolio_df.rename(columns={'industry': 'Industry'}, inplace=True)
    portfolio_df.rename(columns={'website': 'Website'}, inplace=True)
    portfolio_df.rename(columns={'country': 'Country'}, inplace=True)

    # Write header and DataFrame to CSV
    with open(output_file, 'w') as f:
        f.write(f"Optimized Portfolio Weights according to {strategy_name}\n")
        portfolio_df.to_csv(f, index=False)

    return output_file

if __name__ == "__main__":
    # Testing usage
    weights = {
        'AAPL': 0.5,
        'MSFT': 0.3,
        'GOOGL': 0.2
    }
    # Run the export function
    export_portfolio(weights, "Example Strategy")