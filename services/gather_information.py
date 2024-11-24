from typing import Set, List
import pandas as pd

def validate_percentage(value: float) -> bool:
    """
    Validate that the provided value is a percentage between 0 and 100.

    Parameters
    ----------
    value : float
        The percentage value to validate.

    Returns
    -------
    bool
        True if the value is between 0 and 100, inclusive. False otherwise.
    """
    # Ensure the percentage value is between 0 and 100 (inclusive)
    return 0 <= value <= 100

def get_input(prompt: str, validation_func=None, error_message: str = "Invalid input."):
    """
    Continuously prompt the user for input until valid input is provided.

    Parameters
    ----------
    prompt : str
        The message displayed to the user for input.
    validation_func : callable, optional
        A function that validates the user input.
    error_message : str
        The message displayed when the user input is invalid.

    Returns
    -------
    str
        The valid user input.
    """
    while True:
        try:
            value = input(prompt).strip()
            # Validate the input if a validation function is provided
            if validation_func is None or validation_func(value):
                return value
            # Raise an error if validation fails
            raise ValueError(error_message)
        except ValueError as e:
            # Print the error message and prompt the user again
            print(f"Error: {e}")

def get_basic_info(user) -> None:
    """
    Get basic information from the user, including risk tolerance.

    Parameters
    ----------
    user : object
        An object that stores user information.

    Modifies
    --------
    user.data : dict
        Updates the user's data dictionary with risk tolerance.
    """
    # Get user's risk tolerance level    
    risk_tolerance = int(get_input("On a scale of 1-10, what is your risk tolerance? (1=low, 10=high): ",
                                  lambda x: x.isdigit() and 1 <= int(x) <= 10, "Risk tolerance must be between 1 and 10."))
    user.data["risk_tolerance"] = risk_tolerance

def get_preferred_stocks(available_tickers: Set[str], max_attempts: int = 3) -> List[str]:
    """
    Allow the user to specify preferred stocks to include in their portfolio, with a limited number of attempts.

    Parameters
    ----------
    available_tickers : set of str
        A set of valid ticker symbols that the user can choose from.
    max_attempts : int
        The maximum number of attempts allowed to input valid tickers.

    Returns
    -------
    list of str
        A list of valid tickers specified by the user.
    """
    # Allow the user to specify preferred stocks within a limited number of attempts
    for attempt in range(max_attempts):
        stocks = input("Enter the stocks you want in your portfolio (comma-separated list with tickers): ").strip()
        if not stocks:
            # Ensure user provides at least one ticker
            print("Please enter at least one stock ticker.")
            continue

        # Parse the input and clean up the tickers
        input_tickers = {ticker.strip().upper() for ticker in stocks.split(",") if ticker.strip()}
        if not input_tickers:
            # Handle invalid input format
            print("Invalid input format. Please use comma-separated tickers.")
            continue

        # Check which tickers are valid and which are not
        valid_tickers = [ticker for ticker in input_tickers if ticker in available_tickers]
        invalid_tickers = [ticker for ticker in input_tickers if ticker not in available_tickers]
        
        # Print which tickers were successfully added and which were invalid
        if valid_tickers:
            print(f"Added tickers: {', '.join(valid_tickers)}")

        if invalid_tickers:
            # Notify the user about invalid tickers and give them a chance to try again
            print(f"Invalid tickers: {', '.join(invalid_tickers)}. Please enter valid tickers from the available list.")
            if attempt < max_attempts - 1:
                print(f"Please try again. {max_attempts - attempt - 1} attempts remaining.")
            continue
        
        # Return the list of valid tickers
        print(f"Preferred tickers: {', '.join(valid_tickers)}")
        return valid_tickers

    # If maximum attempts are reached, proceed without preferred stocks
    print("Max attempts reached. Proceeding without preferred stocks.")
    return []

def get_sector_preferences(user, df) -> None:
    """
    Ask the user if they want to avoid investing in any specific sectors and update user preferences accordingly.

    Parameters
    ----------
    user : object
        An object that stores user information.
    df : DataFrame
        A dataframe containing available sectors.

    Modifies
    --------
    user.data : dict
        Updates the user's data dictionary with sectors to avoid.
    """
    # Ask the user if they want to avoid investing in specific sectors
    sector_avoid = get_input("Do you want to avoid investing in any specific sectors? (yes/no): ", lambda x: x.lower() in ["yes", "no"], "Please enter 'yes' or 'no'.").lower()
    if sector_avoid == "yes":
        # Get available sectors from the dataframe
        df['sector'] = df['sector'].fillna('Unknown').astype(str)
        available_sectors = sorted(df['sector'].unique())
        print(f"Available sectors: {', '.join(available_sectors)}")
        # Ask user for sectors they want to avoid
        sectors_to_avoid = get_input("Enter the sectors you want to avoid (comma-separated list): ").strip()
        sectors_to_avoid_list = [sector.strip() for sector in sectors_to_avoid.split(",") if sector.strip()]
        invalid_sectors = [sector for sector in sectors_to_avoid_list if sector not in available_sectors]

        if invalid_sectors:
            # Notify user of invalid sectors
            print(f"Invalid sectors: {', '.join(invalid_sectors)}. Please enter valid sectors from the available list.")
            # Filter out invalid sectors
            sectors_to_avoid_list = [sector for sector in sectors_to_avoid_list if sector in available_sectors]

        # Update user data with sectors to avoid
        user.data["sectors_to_avoid"] = sectors_to_avoid_list
        print("Sectors to avoid:", user.data["sectors_to_avoid"])
    else:
        # If user doesn't want to avoid any sectors, set it to an empty list
        user.data["sectors_to_avoid"] = []

def get_portfolio_constraints(user) -> None:
    """
    Ask the user if they want to set minimum and maximum weights for individual equities in the portfolio.

    Parameters
    ----------
    user : object
        An object that stores user information.

    Modifies
    --------
    user.data : dict
        Updates the user's data dictionary with equity investment constraints.
    """
    # Ask the user if they want to set constraints on individual equity weights
    set_constraints = get_input("Do you want to set minimum and maximum weights for individual equities? (yes/no): ", lambda x: x.lower() in ["yes", "no"], "Please enter 'yes' or 'no'.").lower()
    if set_constraints == "yes":
        while True:
            try:
                # Get maximum and minimum equity percentages from the user
                max_equity = float(get_input("What is the maximum you want to invest in a single equity? (in percent): ",
                                            lambda x: x.replace('.', '', 1).isdigit() and validate_percentage(float(x)), "Max equity investment must be between 0 and 100."))
                min_equity = float(get_input("What is the minimum you want to invest in a single equity? (in percent): ",
                                            lambda x: x.replace('.', '', 1).isdigit() and validate_percentage(float(x)), "Min equity investment must be between 0 and 100."))

                if min_equity >= max_equity:
                    # Ensure that minimum investment is less than maximum investment
                    raise ValueError("Minimum investment must be less than maximum investment.")

                # Update user data with equity investment constraints
                user.data["max_equity_investment"] = max_equity
                user.data["min_equity_investment"] = min_equity
                break

            except ValueError as e:
                # Print the error and prompt the user to try again
                print(f"Error: {e}. Please enter valid percentages for maximum and minimum equity investments.")

def gather_information(user) -> None:
    """
    Gather all necessary information from the user, including basic info, preferred stocks, sector preferences, and portfolio constraints.

    Parameters
    ----------
    user : object
        An object that stores user information.

    Modifies
    --------
    user.data : dict
        Updates the user's data dictionary with all collected information.
    """
    try:
        # Collect basic user information like age and risk tolerance
        get_basic_info(user)

        # Ask if the user has preferred stocks they want in their portfolio
        if get_input("Do you have any stocks that you definitely want in your portfolio? (yes/no): ", lambda x: x.lower() in ["yes", "no"], "Please enter 'yes' or 'no'.").lower() == "yes":
            try:
                # Load available stocks from CSV
                df = pd.read_csv('static/ticker_data.csv')
                print("The list of available stocks is saved in 'static/ticker_data.html'.")
                available_tickers = set(df['Ticker'].values)
                # Get preferred stocks from the user
                user.data["preferred_stocks"] = get_preferred_stocks(available_tickers)
            except FileNotFoundError:
                # Handle the case where the stock data file is not found
                print("Error: Stock data file not found. Proceeding without preferred stocks.")
                user.data["preferred_stocks"] = []
        else:
            user.data["preferred_stocks"] = []

        # Load available sectors and collect sector preferences
        df = pd.read_csv('static/ticker_data.csv')
        get_sector_preferences(user, df)
        # Collect portfolio constraints if applicable
        get_portfolio_constraints(user)

    except Exception as e:
        # Handle any unexpected errors during the information gathering process
        print(f"An unexpected error occurred: {e}")
