# services/export_portfolio.py
"""
Service to export the optimized portfolio to a CSV file with additional information for each ticker
such as company name, sector, industry, website, and country.
"""

import pandas as pd

def export_portfolio(weights, strategy_name):
    """
    Creates a portfolio DataFrame with additional information from a static ticker file.

    Parameters
    ----------
    weights : dict
        Dictionary containing tickers as keys and weights as values.
    strategy_name : str
        Name of the strategy used for optimization.

    Returns
    -------
    pandas.DataFrame
        Portfolio data with additional information.
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

    # Select and rename relevant columns
    columns_map = {
        'Ticker': 'Ticker',
        'Weight': 'Weight',
        'longName': 'Company Name',
        'sector': 'Sector',
        'industry': 'Industry',
        'website': 'Website',
        'country': 'Country'
    }
    
    # Filter columns that exist in the data
    available_columns = [col for col, new_name in columns_map.items() if col in portfolio_df.columns]
    portfolio_df = portfolio_df[available_columns]
    
    # Rename columns
    for col in available_columns:
        if col in columns_map:
            portfolio_df.rename(columns={col: columns_map[col]}, inplace=True)

    # Format the data
    portfolio_df['Weight'] = (portfolio_df['Weight'] * 100).round(2).astype(str) + '%'
    portfolio_df = portfolio_df.sort_values(by='Weight', ascending=False)
    
    # Filter out zero weights
    portfolio_df = portfolio_df[portfolio_df['Weight'] != '0%']

    return portfolio_df