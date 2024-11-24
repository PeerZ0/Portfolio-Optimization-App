from models.user import User
from models.terminal import TerminalUI
from models.portfolio import Portfolio
from services.build_list import build_available_tickers
import curses

def terminal(user: User):
    """
    Main function to execute the portfolio optimization application.

    This function runs a loop that gathers user information, builds a list of available tickers, optimizes the portfolio,
    and provides an overview of the portfolio. Users have the option to retry different optimization methods if desired.
    
    Steps
    -----
    1. Create a user instance and gather user preferences and constraints.
    2. Update available data, such as ticker information.
    3. Filter available tickers based on user preferences.
    4. Optimize the portfolio and display the results.
    5. Allow the user to retry with a different optimization method.
    """
    def main(stdscr):
        # Start the terminal UI
        ui = TerminalUI(stdscr, user)
        
        # Gather user information
        ui.get_update_data()
        ui.get_stocks()
        ui.get_sectors()
        ui.get_risk_info()
        ui.get_constraints()
        
        # Build and filter the list of available tickers based on user preferences
        available_tickers = build_available_tickers(user)
        ui.optimize_portfolio(available_tickers)
    
    curses.wrapper(main)

if __name__ == "__main__":
    user = User()
    terminal(user)