import pandas as pd
from typing import List, Dict
from models.user import User

def filter_by_user_preferences(df: pd.DataFrame, user: User) -> pd.DataFrame:
    """
    (No changes needed to this helper function.)
    """
    if user.data["sectors_to_avoid"]:
        df = df[~df['sector'].isin(user.data["sectors_to_avoid"])]
    if user.data["risk_tolerance"]:
        risk_tolerance = user.data["risk_tolerance"]
        min_risk = max(1, risk_tolerance)
        max_risk = min(10, risk_tolerance)
        df = df[(df['overallRisk'] >= min_risk) & (df['overallRisk'] <= max_risk)]
    return df

def build_available_tickers(user: User) -> List[Dict]:
    """
    Build a list of available tickers based on user preferences.

    Parameters
    ----------
    user : User
        The user object containing preferences such as sectors to avoid, preferred stocks, and risk tolerance.

    Returns
    -------
    list of dict
        A list of tickers available to the user based on their preferences.
    """
    try:
        # Read the CSV file
        df = pd.read_csv('static/ticker_data.csv')

        # Check for required columns
        required_columns = ['Ticker', 'sector', 'marketCap', 'currentPrice', 'overallRisk']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Missing required columns in ticker_data.csv")

        # Fill missing values
        df['sector'] = df['sector'].fillna('Unknown')
        df['overallRisk'] = df['overallRisk'].fillna(5)

        # Handle preferred stocks
        preferred_stocks = set(user.data["preferred_stocks"])
        preferred_df = df[df['Ticker'].isin(preferred_stocks)]

        # Filter based on user preferences
        available_df = filter_by_user_preferences(df[~df['Ticker'].isin(preferred_stocks)], user)

        # Combine preferred and filtered stocks
        final_df = pd.concat([preferred_df, available_df])

        # Convert the DataFrame to a list of tickers
        result = final_df.to_dict('records')
        return [ticker['Ticker'] for ticker in result]

    except FileNotFoundError:
        print("Error: ticker_data.csv not found. Please run update_data first.")
        return []
    except Exception as e:
        print(f"Error building available tickers: {e}")
        return []
