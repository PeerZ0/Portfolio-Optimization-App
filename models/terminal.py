import sys
import curses
import os
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import pandas as pd
from services.update_data import update_data
from models.user import User
from models.portfolio import Portfolio

class TerminalUI:
    def __init__(self, stdscr, user):
        self.stdscr = stdscr
        self.user = user  # Store the user instance directly in the class
        self.user_data = {}  # Optionally keep a local copy
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        self.GREEN = curses.color_pair(1)
        self.RED = curses.color_pair(2)

    def update_user_data(self):
        """Synchronize user data with the user instance."""
        self.user.data.update(self.user_data)
    
    def show_prompt(self, prompt: str, y: int, exit = True) -> str:
        self.stdscr.addstr(y, 2, prompt)
        if exit:
            self.stdscr.addstr(y + 2, 2, "(type 'exit' to quit)")  # Display 'exit' message below the prompt
        self.stdscr.refresh()
        curses.echo()
        response = self.stdscr.getstr(y, len(prompt) + 3).decode('utf-8').strip()
        curses.noecho()

        # Check for the exit command
        if response.lower() == "exit":
            self.exit_program()
        
        return response

    def exit_program(self):
        """Gracefully exit the program."""
        self.stdscr.clear()
        self.stdscr.addstr(1, 2, "Exiting program. Goodbye!", curses.A_BOLD)
        self.stdscr.refresh()
        curses.napms(500)  # Display the message for 2 seconds
        sys.exit()

    def get_risk_info(self):
        """
        Prompt the user for their risk tolerance and handle invalid inputs.
        """
        self.stdscr.clear()
        
        while True:
            self.stdscr.addstr(1, 2, "Risk Information", curses.A_BOLD)
            self.stdscr.addstr(3, 2, "Please indicate the highest risk rating you want to invest in.", curses.A_NORMAL)
            self.stdscr.addstr(4, 2, "We are using YahooFinance risk ratings (1 = Low Risk, 10 = High Risk).", curses.A_NORMAL)
            
            try:
                # Prompt the user for input
                risk = int(self.show_prompt("Risk Tolerance (1-10): ", 6))
                if 1 <= risk <= 10:
                    break  # Valid input
                else:
                    # Handle out-of-range input
                    self.stdscr.addstr(8, 2, "Invalid input. Please enter a number between 1 (low risk) and 10 (high risk).", self.RED)
            except ValueError:
                # Handle non-integer input
                self.stdscr.addstr(8, 2, "Invalid input. Please enter a valid integer between 1 and 10.", self.RED)
            
            # Refresh the screen and wait for the user to acknowledge the error
            self.stdscr.refresh()
            self.stdscr.getch()
            self.stdscr.clear()

        # Store and update user data
        self.user_data["risk_tolerance"] = risk
        self.update_user_data()  # Update user data immediately

    def get_stocks(self):
        self.stdscr.clear()
        filepath = os.path.abspath('static/ticker_data.html')
        try:
            df = pd.read_csv('static/ticker_data.csv')
            total_stocks = len(df)
            
            while True:
                self.stdscr.clear()
                self.stdscr.addstr(1, 2, "Preferred Stocks Selection", curses.A_BOLD)
                self.stdscr.addstr(2, 2, f"Here you can specify if you want specific stocks to be forced to be included", curses.A_NORMAL)
                self.stdscr.addstr(4, 2, f"Total available stocks: {total_stocks}", curses.A_NORMAL)
                self.stdscr.addstr(5, 2, f"You can see all available stocks at:{filepath}", curses.A_NORMAL)


                # Show current selections if any
                if self.user.data.get('preferred_stocks'):
                    self.stdscr.addstr(7, 2, f"Current selection: {', '.join(self.user.data['preferred_stocks'])}", 
                                     curses.A_NORMAL)
                
                # Input prompt
                self.stdscr.addstr(8, 2, "Enter stock tickers (comma-separated) or 'done' to finish:", curses.A_NORMAL)
                response = self.show_prompt("Stocks: ", 9).strip()
                
                # Check for exit condition
                if response.lower() == 'done':
                    break
                
                # Handle empty input
                if not response:
                    self.stdscr.addstr(10, 2, "Please enter at least one stock ticker or type done.", self.RED)
                    self.stdscr.refresh()
                    self.stdscr.getch()
                    continue
                
                # Parse and validate input
                stocks = [s.strip().upper() for s in response.split(",") if s.strip()]
                valid_stocks = [s for s in stocks if s in df['Ticker'].values]
                invalid_stocks = [s for s in stocks if s not in df['Ticker'].values]
                
                # Display results
                y_pos = 10
                if valid_stocks:
                    # Add new valid stocks to existing selections
                    current_stocks = set(self.user.data.get('preferred_stocks', []))
                    current_stocks.update(valid_stocks)
                    self.user.data["preferred_stocks"] = list(current_stocks)
                    
                    self.stdscr.addstr(y_pos, 2, f"Added stocks: {', '.join(valid_stocks)}", self.GREEN)
                    y_pos += 1
                    
                if invalid_stocks:
                    self.stdscr.addstr(y_pos, 2, f"Invalid tickers: {', '.join(invalid_stocks)}", self.RED)
                    y_pos += 1
                    self.stdscr.addstr(y_pos, 2, "These tickers were not found in our database.", self.RED)
                    y_pos += 2
                
                # Show instructions
                self.stdscr.addstr(y_pos, 2, "Press any key to continue or enter 'done' to finish.", curses.A_NORMAL)
                self.stdscr.refresh()
                self.stdscr.getch()

        except FileNotFoundError:
            self.stdscr.addstr(7, 2, "Error: Stock data not found. Please update data first.", self.RED)
            self.stdscr.refresh()
            self.stdscr.getch()
            self.user.data["preferred_stocks"] = []
        
        self.update_user_data()

    def get_sectors(self):
        self.stdscr.clear()
        try:
            df = pd.read_csv('static/ticker_data.csv')
            df['sector'] = df['sector'].fillna('Unknown')
            sector_counts = df['sector'].value_counts()
            sectors_list = list(sector_counts.items())  # List of (sector, count) tuples

            while True:
                self.stdscr.clear()
                self.stdscr.addstr(1, 2, "Sector Selection", curses.A_BOLD)
                self.stdscr.addstr(2, 2, "Here you can specify which sectors you want to exclude from your portfolio", curses.A_NORMAL)
                
                # Display available sectors in two columns with numbers
                self.stdscr.addstr(4, 2, "Available Sectors (enter numbers to select):", curses.A_BOLD)
                max_sector_length = max(len(f"{sector} ({count} stocks)") for sector, count in sectors_list)
                column_width = max_sector_length + 10  # Add padding
                mid_point = (len(sectors_list) + 1) // 2

                # First column
                for i in range(mid_point):
                    sector, count = sectors_list[i]
                    self.stdscr.addstr(6 + i, 4, f"{i+1:2d}. {sector} ({count} stocks)")

                # Second column
                for i in range(mid_point, len(sectors_list)):
                    sector, count = sectors_list[i]
                    self.stdscr.addstr(6 + (i - mid_point), 4 + column_width, 
                                     f"{i+1:2d}. {sector} ({count} stocks)")

                # Show current selections if any
                y_pos = 6 + mid_point + 1
                if self.user.data.get('sectors_to_avoid'):
                    current_sectors = self.user.data['sectors_to_avoid']
                    self.stdscr.addstr(y_pos, 2, "Currently avoiding: ", curses.A_NORMAL)
                    self.stdscr.addstr(y_pos, 22, ', '.join(current_sectors), self.RED)
                    y_pos += 1

                # Input prompt
                self.stdscr.addstr(y_pos + 1, 2, 
                                 "Enter sector numbers to avoid (comma-separated) or 'done' to finish:", 
                                 curses.A_NORMAL)
                response = self.show_prompt("Numbers: ", y_pos + 2).strip()

                if response.lower() == 'done':
                    break

                if not response:
                    self.stdscr.addstr(y_pos + 4, 2, "Please enter at least one number or type 'done'.", self.RED)
                    self.stdscr.refresh()
                    self.stdscr.getch()
                    continue

                # Parse and validate input numbers
                try:
                    numbers = [int(n.strip()) for n in response.split(',') if n.strip()]
                    valid_numbers = [n for n in numbers if 1 <= n <= len(sectors_list)]
                    invalid_numbers = [n for n in numbers if n not in valid_numbers]

                    # Convert valid numbers to sector names
                    selected_sectors = [sectors_list[n-1][0] for n in valid_numbers]
                    
                    result_pos = y_pos + 4
                    if selected_sectors:
                        current_sectors = set(self.user.data.get('sectors_to_avoid', []))
                        current_sectors.update(selected_sectors)
                        self.user.data["sectors_to_avoid"] = list(current_sectors)
                        self.stdscr.addstr(result_pos, 2, 
                                         f"Added sectors: {', '.join(selected_sectors)}", 
                                         self.GREEN)
                        result_pos += 1

                    if invalid_numbers:
                        self.stdscr.addstr(result_pos, 2, 
                                         f"Invalid input, no Sector: {', '.join(map(str, invalid_numbers))}", 
                                         self.RED)
                        result_pos += 2

                    self.stdscr.addstr(result_pos, 2, 
                                     "Press any key to continue or enter 'done' to finish.", 
                                     curses.A_NORMAL)
                    self.stdscr.refresh()
                    self.stdscr.getch()
                except ValueError:
                    self.stdscr.addstr(y_pos + 4, 2, "Invalid input. Please enter valid numbers.", self.RED)
                    self.stdscr.refresh()
                    self.stdscr.getch()

        except FileNotFoundError:
            self.stdscr.addstr(7, 2, "Error: Stock data not found. Please update data first.", self.RED)
            self.stdscr.refresh()
            self.stdscr.getch()
            self.user.data["sectors_to_avoid"] = []

        self.update_user_data()

    def get_constraints(self):
        self.stdscr.clear()
        while True:
            self.stdscr.clear()
            self.stdscr.addstr(1, 2, "Portfolio Constraints", curses.A_BOLD)
            self.stdscr.addstr(2, 2, "Here you can specify how large/small a single position can be", curses.A_NORMAL)
            self.stdscr.addstr(3, 2, "Enter percentages between 0 and 100", curses.A_NORMAL)

            # Show current constraints if any
            y_pos = 5
            if self.user.data.get('min_equity_investment') is not None:
                self.stdscr.addstr(y_pos, 2, f"Current minimum: {self.user.data['min_equity_investment']*100}%", curses.A_NORMAL)
                self.stdscr.addstr(y_pos + 1, 2, f"Current maximum: {self.user.data['max_equity_investment']*100}%", curses.A_NORMAL)
                y_pos += 3

            # Input prompts
            self.stdscr.addstr(y_pos, 2, "Enter new constraints or 'done' to finish:", curses.A_NORMAL)
            
            # Get both inputs first
            min_response = self.show_prompt("Minimum investment per equity (%): ", y_pos + 1).strip()
            if min_response.lower() == 'done':
                break
                
            max_response = self.show_prompt("Maximum investment per equity (%): ", y_pos + 2, exit=False).strip()
            if max_response.lower() == 'done':
                break

            # Handle empty inputs
            if not min_response or not max_response:
                self.stdscr.addstr(y_pos + 4, 2, "Please enter both values or type 'done'.", self.RED)
                self.stdscr.refresh()
                self.stdscr.getch()
                continue

            # Validate inputs
            try:
                min_equity = float(min_response)/100
                max_equity = float(max_response)/100

                result_pos = y_pos + 4
                
                # Validate constraints
                if not (0 <= min_equity <= max_equity <= 100):
                    error_message = "Invalid input: "
                    if min_equity < 0 or max_equity > 100:
                        error_message += "Values must be between 0 and 100"
                    elif min_equity > 100 or max_equity < 0:
                        error_message += "Values must be between 0 and 100"
                    elif min_equity > max_equity:
                        error_message += "Minimum must be less than maximum"
                        
                    self.stdscr.addstr(result_pos, 2, error_message, self.RED)
                    self.stdscr.refresh()
                    self.stdscr.getch()
                    continue

                # Update constraints if valid
                self.user.data.update({
                    "min_equity_investment": min_equity,
                    "max_equity_investment": max_equity,
                })
                
                break
                
            except ValueError:
                self.stdscr.addstr(y_pos + 4, 2, "Invalid input. Please enter numeric values.", self.RED)
                self.stdscr.refresh()
                self.stdscr.getch()

        self.update_user_data()

    def get_update_data(self):
        self.stdscr.clear()
        # Automatically update data if ticker_data.csv is not found
        try:
            pd.read_csv('static/ticker_data.csv')
        except FileNotFoundError:
            self.stdscr.clear()
            self.stdscr.addstr(1, 2, "Ticker data file not found. Updating data automatically...", curses.A_BOLD)
            self.stdscr.refresh()
            with open(os.devnull, 'w') as fnull, redirect_stdout(fnull), redirect_stderr(fnull):
                update_data("yes")
            self.user_data["data_updated"] = "yes"
            self.update_user_data()  # Update user data immediately
        
        while True:
            if self.user.data.get("data_updated") == "yes":
                self.stdscr.clear()
                self.stdscr.addstr(1, 2, "Data already updated.", curses.A_BOLD)
                self.stdscr.refresh()
                self.stdscr.getch()
                break

            self.stdscr.addstr(1, 2, "Update Data", curses.A_BOLD)
            self.stdscr.addstr(3, 2, "Do you want to update the data (yes/no/static)", curses.A_NORMAL)
            response = self.show_prompt("Enter how you want to proceed: ", 5)
            if response in ["yes", "no", "static"]:
                break
            self.stdscr.addstr(7, 2, "Invalid response. Please enter 'yes', 'no', or 'static'.", self.RED)
            self.stdscr.refresh()
            self.stdscr.getch()
            self.stdscr.clear()

        if response == "yes":
            self.stdscr.clear()
            self.stdscr.addstr(1, 2, "Updating data, please wait...", curses.A_BOLD)
            self.stdscr.refresh()
            with open(os.devnull, 'w') as fnull, redirect_stdout(fnull), redirect_stderr(fnull):
                update_data("yes")
            self.user_data["data_updated"] = "yes"
        elif response == "static":
            self.stdscr.clear()
            self.stdscr.addstr(1, 2, "Using static data...", curses.A_BOLD)
            self.stdscr.refresh()
            with open(os.devnull, 'w') as fnull, redirect_stdout(fnull), redirect_stderr(fnull):
                update_data("static")
            self.user_data["data_updated"] = "static"
        
        self.update_user_data()  # Update user data immediately
        
    def optimize_portfolio(self, available_tickers):
        self.stdscr.clear()
        self.stdscr.refresh()
        self.stdscr.addstr(1, 2, "Portfolio Optimization", curses.A_BOLD)
        self.stdscr.addstr(3, 2, "Pulling necessary data...", curses.A_NORMAL)
        self.stdscr.refresh()
        # surpress logs
        with open(os.devnull, 'w') as fnull, redirect_stdout(fnull), redirect_stderr(fnull):
            portfolio = Portfolio(self.user, available_tickers)
        self.stdscr.refresh()
        self.stdscr.addstr(3, 2, "Finished...", curses.A_GREEN)
        self.stdscr.refresh()
        curses.napms(1000)
        self.stdscr.clear()
        self.stdscr.addstr(1, 2, "Portfolio Optimization", curses.A_BOLD)
        self.stdscr.addstr(3, 2, "Please Select:", curses.A_NORMAL)