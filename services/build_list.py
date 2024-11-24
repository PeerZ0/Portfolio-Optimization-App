# build_list.py
from typing import List, Dict
import pandas as pd
from models.user import User

def filter_by_user_preferences(df: pd.DataFrame, user: User) -> pd.DataFrame:
    """
    Filter a DataFrame of tickers based on user preferences, including sectors to avoid and risk tolerance.

    Parameters:
    df (pd.DataFrame): The DataFrame containing stock information.
    user (User): The user object containing preferences such as sectors to avoid and risk tolerance.

    Returns:
    pd.DataFrame: A filtered DataFrame that meets the user's preferences.
    """
    # Remove sectors user wants to avoid
    if user.data["sectors_to_avoid"]:
        # Filter out rows where the sector matches any sector the user wants to avoid
        df = df[~df['sector'].isin(user.data["sectors_to_avoid"])]
    
    # Filter by risk tolerance with a ±2 range
    if user.data["risk_tolerance"]:
        risk_tolerance = user.data["risk_tolerance"]
        # Define minimum and maximum risk levels based on the user's risk tolerance
        min_risk = max(1, risk_tolerance)
        max_risk = min(10, risk_tolerance)
        # Filter DataFrame to only include stocks with risk ratings within the desired range
        df = df[(df['overallRisk'] >= min_risk) & (df['overallRisk'] <= max_risk)]
        
    return df

def build_available_tickers(user: User) -> List[Dict]:
    """
    Build a list of available tickers based on user preferences, including filtering by sectors and risk tolerance.

    Parameters:
    user (User): The user object containing preferences such as sectors to avoid, preferred stocks, and risk tolerance.

    Returns:
    List[Dict]: A list of tickers available to the user based on their preferences.
    """
    try:
        # Read ticker data from the CSV file
        df = pd.read_csv('static/ticker_data.csv')
        
        # Ensure required columns exist in the DataFrame
        required_columns = ['Ticker', 'sector', 'marketCap', 'currentPrice', 'overallRisk']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Missing required columns in ticker_data.csv")
        
        # Fill NaN values in important columns
        df['sector'] = df['sector'].fillna('Unknown')
        df['overallRisk'] = df['overallRisk'].fillna(5)  # Default to medium risk (5 on a scale from 1-10)
        
        # Add preferred stocks regardless of filters
        preferred_stocks = set(user.data["preferred_stocks"])
        preferred_df = df[df['Ticker'].isin(preferred_stocks)]
        
        # Filter remaining stocks based on user preferences
        available_df = filter_by_user_preferences(df[~df['Ticker'].isin(preferred_stocks)], user)
        
        # Combine preferred stocks and filtered stocks
        final_df = pd.concat([preferred_df, available_df])
        
        # Convert the filtered DataFrame to a list of dictionaries
        result = final_df.to_dict('records')
        
        # Display the number of tickers found that match the user's criteria
        print(f"Found {len(result)} available tickers matching your criteria")
        if len(result) == 0:
            print("Warning: No tickers match your criteria. Consider relaxing some constraints.")
        
        # Return a list of tickers
        result = [ticker['Ticker'] for ticker in result]
        return result
        
    except FileNotFoundError:
        # Handle the case where the CSV file is not found
        print("Error: ticker_data.csv not found. Please run update_data first.")
        return []
    except Exception as e:
        # Handle any other unexpected errors that occur
        print(f"Error building available tickers: {e}")
        return []
