# build_list.py
from typing import List, Dict
import pandas as pd
from models.user import User

def filter_by_user_preferences(df: pd.DataFrame, user: User) -> pd.DataFrame:
    """Filter DataFrame based on user preferences"""
    # Remove sectors user wants to avoid
    if user.data["sectors_to_avoid"]:
        df = df[~df['sector'].isin(user.data["sectors_to_avoid"])]
    
    # Filter by risk tolerance with ±2 range
    if user.data["risk_tolerance"]:
        risk_tolerance = user.data["risk_tolerance"]
        min_risk = max(1, risk_tolerance)
        max_risk = min(10, risk_tolerance)
        df = df[(df['overallRisk'] >= min_risk) & (df['overallRisk'] <= max_risk)]
        
    return df

def build_available_tickers(user: User) -> List[Dict]:
    """Build list of available tickers based on user preferences"""
    try:
        # Read ticker data
        df = pd.read_csv('static/ticker_data.csv')
        
        # Ensure required columns exist
        required_columns = ['Ticker', 'sector', 'marketCap', 'currentPrice', 'overallRisk']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Missing required columns in ticker_data.csv")
        
        # Fill NaN values
        df['sector'] = df['sector'].fillna('Unknown')
        df['overallRisk'] = df['overallRisk'].fillna(5)  # Default to medium risk (5 on 1-10 scale)
        
        # Add preferred stocks regardless of filters
        preferred_stocks = set(user.data["preferred_stocks"])
        preferred_df = df[df['Ticker'].isin(preferred_stocks)]
        
        # Filter remaining stocks based on preferences
        available_df = filter_by_user_preferences(df[~df['Ticker'].isin(preferred_stocks)], user)
        
        # Combine preferred and filtered stocks
        final_df = pd.concat([preferred_df, available_df])
        
        # Convert to list of dictionaries
        result = final_df.to_dict('records')
        
        print(f"Found {len(result)} available tickers matching your criteria")
        if len(result) == 0:
            print("Warning: No tickers match your criteria. Consider relaxing some constraints.")
        
        # return list only containing tickers
        result = [ticker['Ticker'] for ticker in result]
        return result
        
    except FileNotFoundError:
        print("Error: ticker_data.csv not found. Please run update_data first.")
        return []
    except Exception as e:
        print(f"Error building available tickers: {e}")
        return []
