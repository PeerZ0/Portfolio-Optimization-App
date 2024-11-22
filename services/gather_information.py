from typing import Set, List
import pandas as pd

def validate_age(age: int) -> bool:
    return age > 0

def validate_percentage(value: float) -> bool:
    return 0 <= value <= 100

def get_input(prompt: str, validation_func=None, error_message: str = "Invalid input."):
    while True:
        try:
            value = input(prompt).strip()
            if validation_func is None or validation_func(value):
                return value
            raise ValueError(error_message)
        except ValueError as e:
            print(f"Error: {e}")

def get_basic_info(user) -> None:
    age = int(get_input("How old are you?: ", lambda x: x.isdigit() and validate_age(int(x)), "Age must be a positive integer."))
    user.data["age"] = age
    
    risk_tolerance = int(get_input("On a scale of 1-10, what is your risk tolerance? (1=low, 10=high): ",
                                  lambda x: x.isdigit() and 1 <= int(x) <= 10, "Risk tolerance must be between 1 and 10."))
    user.data["risk_tolerance"] = risk_tolerance

def get_preferred_stocks(available_tickers: Set[str], max_attempts: int = 3) -> List[str]:
    for attempt in range(max_attempts):
        stocks = input("Enter the stocks you want in your portfolio (comma-separated list with tickers): ").strip()
        if not stocks:
            print("Please enter at least one stock ticker.")
            continue

        input_tickers = {ticker.strip().upper() for ticker in stocks.split(",") if ticker.strip()}
        if not input_tickers:
            print("Invalid input format. Please use comma-separated tickers.")
            continue

        valid_tickers = [ticker for ticker in input_tickers if ticker in available_tickers]
        invalid_tickers = [ticker for ticker in input_tickers if ticker not in available_tickers]
        
        # print which have been added and which are invalid
        if valid_tickers:
            print(f"Added tickers: {', '.join(valid_tickers)}")

        if invalid_tickers:
            print(f"Invalid tickers: {', '.join(invalid_tickers)}. Please enter valid tickers from the available list.")
            if attempt < max_attempts - 1:
                print(f"Please try again. {max_attempts - attempt - 1} attempts remaining.")
            continue
        
        print(f"Preferred tickers: {', '.join(valid_tickers)}")
        return valid_tickers

    print("Max attempts reached. Proceeding without preferred stocks.")
    return []

def get_sector_preferences(user, df) -> None:
    sector_avoid = get_input("Do you want to avoid investing in any specific sectors? (yes/no): ", lambda x: x.lower() in ["yes", "no"], "Please enter 'yes' or 'no'.").lower()
    if sector_avoid == "yes":
        df['sector'] = df['sector'].fillna('Unknown').astype(str)
        available_sectors = sorted(df['sector'].unique())
        print(f"Available sectors: {', '.join(available_sectors)}")
        sectors_to_avoid = get_input("Enter the sectors you want to avoid (comma-separated list): ").strip()
        sectors_to_avoid_list = [sector.strip() for sector in sectors_to_avoid.split(",") if sector.strip()]
        invalid_sectors = [sector for sector in sectors_to_avoid_list if sector not in available_sectors]

        if invalid_sectors:
            print(f"Invalid sectors: {', '.join(invalid_sectors)}. Please enter valid sectors from the available list.")
            sectors_to_avoid_list = [sector for sector in sectors_to_avoid_list if sector in available_sectors]

        user.data["sectors_to_avoid"] = sectors_to_avoid_list
        print("Sectors to avoid:", user.data["sectors_to_avoid"])
    else:
        user.data["sectors_to_avoid"] = []

def get_portfolio_constraints(user) -> None:
    set_constraints = get_input("Do you want to set minimum and maximum weights for individual equities? (yes/no): ", lambda x: x.lower() in ["yes", "no"], "Please enter 'yes' or 'no'.").lower()
    if set_constraints == "yes":
        while True:
            try:
                max_equity = float(get_input("What is the maximum you want to invest in a single equity? (in percent): ",
                                            lambda x: x.replace('.', '', 1).isdigit() and validate_percentage(float(x)), "Max equity investment must be between 0 and 100."))
                min_equity = float(get_input("What is the minimum you want to invest in a single equity? (in percent): ",
                                            lambda x: x.replace('.', '', 1).isdigit() and validate_percentage(float(x)), "Min equity investment must be between 0 and 100."))

                if min_equity >= max_equity:
                    raise ValueError("Minimum investment must be less than maximum investment.")

                user.data["max_equity_investment"] = max_equity
                user.data["min_equity_investment"] = min_equity
                break

            except ValueError as e:
                print(f"Error: {e}. Please enter valid percentages for maximum and minimum equity investments.")

def gather_information(user) -> None:
    try:
        get_basic_info(user)

        if get_input("Do you have any stocks that you definitely want in your portfolio? (yes/no): ", lambda x: x.lower() in ["yes", "no"], "Please enter 'yes' or 'no'.").lower() == "yes":
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

        df = pd.read_csv('static/ticker_data.csv')
        get_sector_preferences(user, df)
        get_portfolio_constraints(user)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
