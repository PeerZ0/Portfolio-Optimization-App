# services/gather_information.py
from typing import Set, List
import pandas as pd

def validate_age(age: int) -> bool:
    """Validate if age is positive."""
    return age > 0

def validate_percentage(value: float) -> bool:
    """Validate if percentage is between 0 and 100."""
    return 0 <= value <= 100

def get_basic_info(user) -> None:
    """Gather basic user information like age and investment style."""
    while True:
        try:
            age = int(input("How old are you?: ").strip())
            if validate_age(age):
                user.data["age"] = age
                break
            raise ValueError("Age must be a positive integer.")
        except ValueError as e:
            print(f"Error: {e}")
    
    while True:
        try:
            risk_tolerance = int(input("On a scale of 1-10, what is your risk tolerance? (1=low, 10=high): ").strip())
            if 1 <= risk_tolerance <= 10:
                user.data["risk_tolerance"] = risk_tolerance
                break
            raise ValueError("Risk tolerance must be between 1 and 10.")
        except ValueError as e:
            print(f"Error: {e}")
    
def get_preferred_stocks(available_tickers: Set[str], max_attempts: int = 3) -> List[str]:
    """Get and validate preferred stocks from user input."""
    attempt = 0
    while attempt < max_attempts:
        stocks = input("Enter the stocks you want in your portfolio (comma-separated list with tickers): ").strip()
        if not stocks:
            print("Please enter at least one stock ticker.")
            continue
            
        input_tickers = {ticker.strip().upper() for ticker in stocks.split(",") if ticker.strip()}
        if not input_tickers:
            print("Invalid input format. Please use comma-separated tickers.")
            continue
        
        valid_tickers = []
        invalid_tickers = []
        
        for ticker in input_tickers:
            if ticker in available_tickers:
                valid_tickers.append(ticker)
            else:
                invalid_tickers.append(ticker)
        
        if invalid_tickers:
            print(f"Invalid tickers: {', '.join(invalid_tickers)}")
            attempt += 1
            if attempt < max_attempts:
                print(f"Please try again. {max_attempts - attempt} attempts remaining.")
            continue
        
        return valid_tickers
    
    return []

def get_sector_preferences(user) -> None:
    """Gather user's investment preferences for sectors and geography."""
    df = pd.read_csv('static/ticker_data.csv')
    df['sector'] = df['sector'].fillna('Unknown').astype(str)
    print(f"Available sectors: {', '.join(df['sector'].unique())}")
    sectors_to_avoid = input("Are there any sectors you do not want to invest in? (comma-separated list): ").strip()
    user.data["sectors_to_avoid"] = [sector.strip() for sector in sectors_to_avoid.split(",") if sector.strip()]
    print("Sectors to avoid:", user.data["sectors_to_avoid"])
    
def get_portfolio_constraints(user) -> None:
    """Gather portfolio constraints and limitations."""
    user.data["invest_in_penny_stocks"] = input("Do you want to invest in penny stocks? (yes/no): ").strip().lower() == "yes"
    
    while True:
        try:
            max_equity = float(input("What is the maximum you want to invest in a single equity? (in percent): ").strip())
            if not validate_percentage(max_equity):
                raise ValueError("Max equity investment must be between 0 and 100.")
            
            min_equity = float(input("What is the minimum you want to invest in a single equity? (in percent): ").strip())
            if not validate_percentage(min_equity):
                raise ValueError("Min equity investment must be between 0 and 100.")
            
            if min_equity >= max_equity:
                raise ValueError("Minimum investment must be less than maximum investment.")
            
            user.data["max_equity_investment"] = max_equity
            user.data["min_equity_investment"] = min_equity
            break
            
        except ValueError as e:
            print(f"Error: {e}")

def gather_information(user) -> None:
    """Main function to gather all user information."""
    try:
        # Get basic information
        get_basic_info(user)
        
        # Handle preferred stocks
        preferred_stocks = input("Do you have any stocks that you definitely want in your portfolio? (yes/no): ")
        if preferred_stocks.lower() == "yes":
            try:
                df = pd.read_csv('static/ticker_data.csv')
                print("The list of available stocks is saved in 'static/ticker_data.html'.")
                available_tickers = set(df['Ticker'].values)
                user.data["preferred_stocks"] = get_preferred_stocks(available_tickers)
            except FileNotFoundError:
                print("Error: Stock data file not found. Proceeding without preferred stocks.")
                user.data["preferred_stocks"] = []
        else:
            user.data["preferred_stocks"] = []
        
        # Get other preferences
        get_sector_preferences(user)
        get_portfolio_constraints(user)
        
        # Get additional information
        existing_assets = input("Short info about assets currently in the portfolio (comma-separated list): ").strip()
        user.data["existing_assets_info"] = [asset.strip() for asset in existing_assets.split(",") if asset.strip()]
        
        expectations = input("Do you have any expectations for the assets in your portfolio? (comma-separated list): ").strip()
        user.data["asset_expectations"] = [exp.strip() for exp in expectations.split(",") if exp.strip()]
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        gather_information(user)