from models.user import User
from services.gather_information import gather_information
from services.update_data import update_data
from services.build_list import build_available_tickers
from services.optimize_portfolio import optimize_portfolio
from services.build_overview import build_overview

def main():
    """
    Main function to execute the portfolio optimization application.

    This function runs a loop that gathers user information, builds a list of available tickers, optimizes the portfolio,
    and provides an overview of the portfolio. Users have the option to retry different optimization methods if desired.
    
    Steps:
    1. Create a user instance and gather user preferences and constraints.
    2. Update available data, such as ticker information.
    3. Filter available tickers based on user preferences.
    4. Optimize the portfolio and display the results.
    5. Allow the user to retry with a different optimization method.
    """
    # Create a new User instance to store user preferences and constraints
    user = User()
    
    # Update the ticker data to make sure the latest data is used
    update_data()
    
    # Gather user preferences, such as age, risk tolerance, and preferred sectors or stocks
    gather_information(user)
    
    # Build a list of available tickers based on the user's preferences
    available_tickers = build_available_tickers(user)
    
    print(f"{len(available_tickers)} tickers available based on your preferences.")
    
    while True:
        # Optimize the portfolio based on available tickers and user preferences
        weights = optimize_portfolio(available_tickers, user)
        
        # Generate and display a detailed overview of the portfolio
        build_overview(weights)
        
        # Ask the user if they want to try a different optimization method
        retry = input("Would you like to try a different optimization method? (yes/no): ").strip().lower()
        
        # Handle user input for retrying optimization
        if retry not in ('yes', 'y', 'no', 'n'):
            print("Invalid input. Please enter 'yes' or 'no'.")
        elif retry in ('no', 'n'):
            # Exit the loop and end the program if the user does not want to retry
            print("Exiting the application. Goodbye!")
            break

if __name__ == "__main__":
    main()
