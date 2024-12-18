# services/build_list.py
"""
Portfolio Stock Selection Service

This module implements the logic for filtering and selecting stocks based on user
preferences. It takes into account:
1. Preferred stocks (always included)
2. Sectors to avoid
3. Risk tolerance levels
4. Market capitalization requirements

The module provides functions to filter stocks and build the final list of
available tickers for portfolio optimization.
"""

import pandas as pd
from typing import List, Dict

def filter_by_user_preferences(df: pd.DataFrame, user) -> pd.DataFrame:
    """
    Filter the stock universe based on user preferences.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing stock data with columns for sector, risk, etc.
    user : User
        User object containing preference attributes:
        - sectors_to_avoid: List of sectors to exclude
        - risk_tolerance: Integer 1-10 indicating max acceptable risk
    
    Returns
    -------
    pd.DataFrame
        Filtered DataFrame containing only stocks matching user preferences.
    """
    if user.data["sectors_to_avoid"]:
        # Remove rows corresponding to sectors the user wants to avoid
        df = df[~df['sector'].isin(user.data["sectors_to_avoid"])]
    if user.data["risk_tolerance"]:
        # Filter stocks by risk tolerance
        max_risk = user.data["risk_tolerance"]
        df = df[df['overallRisk'] <= max_risk]
    
    return df

def build_available_tickers(user) -> List[Dict]:
    """
    Build list of available tickers based on user preferences.

    This function:
    1. Loads the stock universe from ticker_data.csv
    2. Applies user preferences to filter stocks
    3. Ensures preferred stocks are included regardless of filters
    4. Validates data quality and handles missing values

    Parameters
    ----------
    user : User
        User object containing:
        - preferred_stocks: List of tickers to always include
        - sectors_to_avoid: List of sectors to exclude
        - risk_tolerance: Integer 1-10 for max risk level

    Returns
    -------
    list of str
        List of ticker symbols available for portfolio optimization.

    Raises
    ------
    ValueError
        If required columns are missing from ticker_data.csv.
    """
    try:
        # Read the CSV file containing ticker data
        df = pd.read_csv('static/ticker_data.csv')

        # Check for required columns in the data
        required_columns = ['Ticker', 'sector', 'marketCap', 'currentPrice', 'overallRisk']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Missing required columns in ticker_data.csv")

        # Fill missing values for specific columns
        df['sector'] = df['sector'].fillna('Unknown')
        df['overallRisk'] = df['overallRisk'].fillna(5)  # Assume a default risk level if missing

        # Handle the user's preferred stocks
        preferred_stocks = set(user.data["preferred_stocks"])
        preferred_df = df[df['Ticker'].isin(preferred_stocks)]

        # Filter the remaining stocks based on user preferences
        available_df = filter_by_user_preferences(df[~df['Ticker'].isin(preferred_stocks)], user)

        # Combine preferred stocks with filtered stocks
        final_df = pd.concat([preferred_df, available_df])

        # Convert the DataFrame to a list of dictionaries for the result
        result = final_df.to_dict('records')
        
        return [ticker['Ticker'] for ticker in result]

    except FileNotFoundError:
        # Handle the case where the CSV file is not found
        print("Error: ticker_data.csv not found. Please run update_data first.")
        return []
    except Exception as e:
        # Handle any other errors that occur during the process
        print(f"Error building available tickers: {e}")
        return []
