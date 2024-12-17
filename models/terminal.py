# models/terminal.py
"""
Terminal-based Portfolio Optimization Application

This module implements a TUI (Text User Interface) application for portfolio optimization
using the Textual framework. It provides a step-by-step wizard interface for users to:
1. Update market data
2. Select preferred stocks
3. Exclude sectors
4. Set risk tolerance
5. Define investment constraints
6. View optimization results in a dashboard
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Header, Footer, Input, Label, Select, Static
from textual.screen import Screen
import pandas as pd
import os
import asyncio
import webbrowser
import time
import threading
from models.portfolio import Portfolio
from models.user import User
from services.build_list import build_available_tickers
from models.dashboard import PortfolioOptimizationDashboard

class BaseScreen(Screen):
    """Base screen class that provides common header and footer for all screens."""
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

class StocksScreen(BaseScreen):
    """
    Screen for stock selection where users can input their preferred stock tickers.
    Validates input against available stocks in the database and provides immediate feedback.
    """
    def compose(self) -> ComposeResult:
        with Container(classes="container"):
            # Display the stock selection screen with input field for stock tickers
            yield Label("Select Preferred Stocks", classes="heading")
            try:
                df = pd.read_csv('static/ticker_data.csv')
                total_stocks = len(df)
                
                yield Label(f"Total available stocks: {total_stocks}")
                yield Label(f"Please add your preferred stocks as a comma-separated list. (e.g., AAPL, MSFT)")
                yield Input(placeholder="Enter stock tickers (comma-separated)", id="stocks")
                yield Label("", id="status")
                with Horizontal(classes="button-group"):
                    yield Button("Back", id="back")
                    yield Button("Continue", id="continue", variant="primary")
            except FileNotFoundError:
                yield Label("Stock data not found. Please update data first.", classes="error")
                with Horizontal(classes="button-group"):
                    yield Button("Back", id="back")
            yield Footer()

    # Handle input change events
    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "stocks":
            stocks = [s.strip().upper() for s in event.value.split(",") if s.strip()]
            df = pd.read_csv('static/ticker_data.csv')
            valid_stocks = [s for s in stocks if s in df['Ticker'].values]
            invalid_stocks = [s for s in stocks if s not in df['Ticker'].values]
            
            status = self.query_one("#status")
            if valid_stocks:
                self.app.user.data["preferred_stocks"] = valid_stocks
                status.remove_class("error")
                status.add_class("success")
                status.update(f"Valid stocks: {', '.join(valid_stocks)}")
            if invalid_stocks:
                status.remove_class("success")
                status.add_class("error")
                status.update(f"Invalid tickers: {', '.join(invalid_stocks)}")
            self.app.user.data["preferred_stocks"] = valid_stocks
    
    # Handle button press events
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "continue":
            self.app.push_screen(SectorsScreen())
        elif event.button.id == "back":
            self.app.pop_screen()

class SectorsScreen(BaseScreen):
    """
    Screen for sector exclusion where users can select sectors they want to avoid.
    Implements a toggle mechanism for sector selection/deselection with real-time updates.
    """
    def compose(self) -> ComposeResult:
        with Container(classes="container"):
            # Display the sector exclusion screen with a list of sectors
            yield Label("Exclude Sectors", classes="heading")
            try:
                df = pd.read_csv('static/ticker_data.csv')
                df['sector'] = df['sector'].fillna('Unknown')
                sectors = list(df['sector'].unique())
                
                yield Label("Select/deselect sectors to exclude:")
                yield Select(
                    [(sector, sector) for sector in sectors],
                    id="sectors"
                )
                yield Static("Selected sectors to exclude:", classes="label")
                yield Static("None", id="selected_sectors", classes="selected-sectors")
                with Horizontal(classes="button-group"):
                    yield Button("Back", id="back")
                    yield Button("Continue", id="continue", variant="primary")
            # Display an error message if the sector data is not found
            except FileNotFoundError:
                yield Label("Sector data not found. Please update data first.", classes="error")
                with Horizontal(classes="button-group"):
                    yield Button("Back", id="back", variant="primary")
            yield Footer()

    # Handle sector selection/deselection events
    def on_select_changed(self, event: Select.Changed) -> None:
        selected_sector = event.value
        if selected_sector:
            # Update the user data with the selected sectors to avoid
            if "sectors_to_avoid" not in self.app.user.data:
                self.app.user.data["sectors_to_avoid"] = []
            
            # Toggle the selected sector in the list
            if selected_sector in self.app.user.data["sectors_to_avoid"]:
                self.app.user.data["sectors_to_avoid"].remove(selected_sector)
            else:
                self.app.user.data["sectors_to_avoid"].append(selected_sector)
            
            # Update the selected sectors display
            sectors_text = ", ".join(self.app.user.data["sectors_to_avoid"])
            if not sectors_text:
                sectors_text = "None"
            self.query_one("#selected_sectors").update(sectors_text)

    # Handle button press events
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "continue":
            self.app.push_screen("risk")
        elif event.button.id == "back":
            self.app.pop_screen()

class RiskScreen(BaseScreen):
    """
    Screen for setting risk tolerance level on a scale of 1-10.
    Provides input validation and immediate feedback on the selected risk level.
    """
    def compose(self) -> ComposeResult:
        with Container(classes="container"):
            # Display the risk tolerance screen with input field for risk level
            yield Label("Risk Tolerance", classes="heading")
            yield Label("Please indicate your risk tolerance (1-10):")
            yield Label("1 = Low Risk, 10 = High Risk")
            yield Input(placeholder="Enter risk level", id="risk")
            yield Label("", id="status")
            with Horizontal(classes="button-group"):
                yield Button("Back", id="back")
                yield Button("Continue", id="continue")
            yield Footer()

    # Validate the input risk level and update user data
    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "risk":
            try:
                # Get the risk level from the input field
                risk = int(event.value)
                # Update the user data with the risk tolerance level
                if 1 <= risk <= 10:
                    self.app.user.data["risk_tolerance"] = risk
                    self.query_one("#status").remove_class("error")
                    self.query_one("#status").update("Valid risk level")
                else:
                    self.query_one("#status").add_class("error")
                    self.query_one("#status").update("Risk level must be between 1 and 10")
            # Display an error message if the input is invalid
            except ValueError:
                self.query_one("#status").add_class("error")
                self.query_one("#status").update("Please enter a valid number")
    
    # Handle button press events
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "continue" and self.app.user.data.get("risk_tolerance"):
            self.app.push_screen(ConstraintsScreen())
        elif event.button.id == "back":
            self.app.pop_screen()

class ConstraintsScreen(BaseScreen):
    """
    Screen for setting investment constraints including maximum investment per stock.
    Implements real-time validation of input values and constraint rules.
    """
    def compose(self) -> ComposeResult:
        with Container(classes="container"):
            # Display the constraints screen with input fields for maximum investment
            yield Label("Investment Constraints", classes="heading")
            yield Label("Enter investment constraints (0-100%):")
            yield Input(placeholder="Maximum investment per stock in %", id="max")
            yield Label("", id="status")
            with Horizontal(classes="button-group"):
                yield Button("Back", id="back")
                yield Button("Continue", id="continue")
            yield Footer()

    # Validate the input constraints and update user data
    def validate_constraints(self) -> bool:
        # Get the maximum investment value from the input field
        max_input = self.query_one("#max").value
        status = self.query_one("#status")

        try:
            # Convert the input to a float value
            max_equity = float(max_input)

            if 0 < max_equity <= 100:
                # Update the user data with the maximum equity investment
                self.app.user.data.update({
                    "max_equity_investment": max_equity
                })
                # Display a success message if the input is valid
                status.remove_class("error")
                status.update("Valid constraints")
                return True
            else:
                # Display an error message if the input is invalid
                status.add_class("error")
                status.update("Invalid constraints: Min must be less than Max (0-100)")
                return False
        except ValueError:
            status.add_class("error")
            status.update("Please enter valid numbers")
            return False

    # Handle input change events
    def on_input_changed(self, event: Input.Changed) -> None:
        self.validate_constraints()

    # Handle button press events
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "continue" and self.validate_constraints():
            self.app.pop_screen()
            self.app.push_screen("data_pulling")
        elif event.button.id == "back":
            self.app.pop_screen()

class DataPullingScreen(BaseScreen):
    """
    Screen shown during portfolio initialization and data processing.
    Handles asynchronous data loading and portfolio setup with progress feedback.
    """
    def compose(self) -> ComposeResult:
        with Container(classes="container"):
            yield Label("Initializing Portfolio...", classes="heading")
            yield Static("Please wait while we prepare your portfolio.", id="status", classes="status-message")
            yield Static("This may take a few seconds... (data is pulled from YahooFinance)", 
                       id="loading", classes="status-message")
            with Container(classes="button-container bottom-space"):
                yield Button("Exit", id="exit", variant="error")
            yield Footer()

    async def on_mount(self) -> None:
        # Wait for the screen to load
        await asyncio.sleep(0.1)
        # Initialize the portfolio and redirect to the optimization screen
        asyncio.create_task(self.initialize_and_redirect())

    # Asynchronously initialize the portfolio and redirect to the optimization screen
    async def initialize_and_redirect(self) -> None:
        """
        Asynchronously initializes the portfolio and handles any errors during setup.
        Uses threading to prevent UI blocking during data processing.
        """
        try:
            # Initialize the portfolio in a separate thread
            await asyncio.to_thread(self.perform_initialization)
            # Redirect to the optimization screen
            self.app.push_screen("optimization")
        except Exception as e:
            # Display error message if initialization fails
            self.query_one("#status").update(f"[red]Error: {str(e)}[/red]")
    
    # Initialize the portfolio with user preferences through the Portfolio class
    def perform_initialization(self) -> None:
        # Build the list of available tickers based on user preferences
        available_tickers = build_available_tickers(self.app.user)
        # Update the user data with available tickers
        self.app.user.data["available_stocks"] = available_tickers
        # Raise an error if no tickers match the criteria
        if not available_tickers:
            raise ValueError("No tickers match your criteria")
        # Initialize the portfolio with the user's preferences
        self.app.portfolio = Portfolio(self.app.user)
    
    # Handle exit button press
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.app.exit()

class PortfolioOptimizationScreen(BaseScreen):
    """
    Final screen that launches the optimization dashboard.
    Manages the dashboard process in a separate thread and provides browser integration.
    """
    def compose(self) -> ComposeResult:
        with Container(classes="container"):
            # Display the final screen with a message and buttons to launch the dashboard or exit
            yield Label("Portfolio Optimization", classes="header centered")
            yield Static("Please click 'Open Dashboard' to see the optimized portfolios")
            yield Static("Hint: Depending on your hardware, you may need to wait a few seconds for the dashboard to load.")
            with Horizontal(classes="button-group"):
                yield Button("Open Dashboard", id="dashboard", variant="primary")
                yield Button("Exit", id="exit", variant="error")
            yield Footer()
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handles dashboard launch and application exit.
        
        For dashboard launch:
        1. Creates a new thread for the dashboard
        2. Waits for server initialization
        3. Opens the dashboard in the default browser
        """
        if event.button.id == "dashboard":
            # Define a function to run the dashboard
            def run_dashboard():
                # Run the dashboard through the PortfolioOptimizationDashboard class
                PortfolioOptimizationDashboard(self.app.portfolio).run()
            
            # Start the dashboard in a separate thread
            dashboard_thread = threading.Thread(target=run_dashboard)
            dashboard_thread.daemon = True
            dashboard_thread.start()

            # Wait for the server to start
            time.sleep(2)
            # Open the dashboard in the default browser
            webbrowser.open("http://127.0.0.1:8509")

        if event.button.id == "exit":
            self.app.exit()
            
class PortfolioApp(App):
    """
    Main application class that manages the screen workflow and global state.
    
    Features:
    ----------
    - Implements a wizard-like interface with multiple screens
    - Maintains user preferences and portfolio data
    - Provides keyboard shortcuts for navigation
    - Custom styling for consistent UI appearance
    """
    # Custom CSS styling for the application
    CSS = """
    Screen {
        background: #1f1f1f;
        color: #ffffff;
        align: center middle;
    }

    .container {
        width: 80%;
        height: auto;
        background: #2d2d2d;
        border: solid #4a4a4a;
        padding: 2;
        margin: 1;
        align: center middle;
    }

    .heading {
        text-align: center;
        text-style: bold;
        padding: 2;
        margin-bottom: 1;
        color: #69db7c;
    }
    
    .header {
        text-align: center !important;
        text-style: bold;
        padding: 2;
        margin-bottom: 1;
        color: #69db7c;
    }   

    .centered {
        align: center middle;
    }

    .subtitle {
        text-align: center;
        margin: 1 0 0 2;
    }

    .button-group {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
        margin-bottom: 1;
    }
    
    .button-container {
        width: 100%;
        height: auto;
        display: block;
        align: center middle;
        margin: 1;
    }

    .bottom-space {
        margin-bottom: 2;
    }

    Button#exit {
        min-width: 16;
        margin: 1;
        background: $error;
    }

    Button {
        margin: 1;
        min-width: 16;
    }

    Button#continue {
        background: $primary;
    }

    Button#back {
        background: $surface;
    }

    .selected-sectors {
        margin: 1;
        padding: 1;
        height: auto;
        min-height: 3;
        border: solid #4a4a4a;
        width: 100%;
        text-align: left;
        overflow: auto;
    }

    Select {
        width: 100%;
        margin: 1;
    }

    Input {
        width: 100%;
        margin: 1;
    }
    
    Label {
        margin: 0 0 0 2;
    }
    
    Static {
        margin: 0 0 0 2;
    }
    
    .label {
        margin: 1 0 0 2;
        text-align: left;
    }
    """
    
    # Keyboard shortcuts for navigation
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "pop_screen", "Back"),
    ]
    
    # Mapping of screen names to screen classes
    SCREENS = {
        "stocks": StocksScreen,        # Stock selection screen
        "sectors": SectorsScreen,      # Sector exclusion screen
        "risk": RiskScreen,            # Risk tolerance screen
        "constraints": ConstraintsScreen,  # Investment constraints screen
        "data_pulling": DataPullingScreen, # Data processing screen
        "optimization": PortfolioOptimizationScreen  # Final dashboard screen
    }

    def __init__(self):
        super().__init__()
        # Create an internal user object to store user preferences
        self.user = User()

    def on_mount(self) -> None:
        """Called when app starts"""
        # Initialize screen stack with the first screen
        self.push_screen("stocks")

    def action_pop_screen(self) -> None:
        """Handle going back to previous screen"""
        # Pop the current screen from the stack
        if len(self.screen_stack) > 1:
            self.pop_screen()
