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
from models.dashboard2 import PortfolioOptimizationDashboard

class BaseScreen(Screen):
    """Base screen class that provides common header and footer for all screens."""
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

class UpdateDataScreen(BaseScreen):
    """
    First screen in the wizard that allows users to update market data.
    Provides options to either fetch new data or use existing data.
    """
    def compose(self) -> ComposeResult:
        with Container(classes="container"):
            yield Label("Update Market Data", classes="heading")
            yield Label("Do you want to update the market data?", classes="subtitle")
            yield Label("", id="status")
            with Horizontal(classes="button-group"):
                yield Button("Yes", id="yes")
                yield Button("No", id="no", variant="primary")
            yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        status = self.query_one("#status")
        if event.button.id in ["yes", "no"]:
            self.app.user.data["data_updated"] = event.button.id
            if event.button.id in ["yes", "static"]:
                status.update("Updating data... (This may take a few minutes)")
                asyncio.create_task(self.async_update_data(event.button.id, status))
            else:
                self.app.push_screen("stocks")

    async def async_update_data(self, mode: str, status: Label) -> None:
        await asyncio.to_thread(self.update_data, mode)
        status.update("Data updated successfully!")
        self.app.push_screen("stocks")

    def update_data(self, mode: str) -> None:
        from services.update_data import update_data
        with open(os.devnull, 'w') as fnull:
            update_data(mode)

class StocksScreen(BaseScreen):
    """
    Screen for stock selection where users can input their preferred stock tickers.
    Validates input against available stocks in the database and provides immediate feedback.
    """
    def compose(self) -> ComposeResult:
        with Container(classes="container"):
            yield Label("Select Preferred Stocks", classes="heading")
            try:
                df = pd.read_csv('static/ticker_data.csv')
                total_stocks = len(df)
                
                yield Label(f"Total available stocks: {total_stocks}")
                yield Label(f"Please add your preferred stocks as a comma-separated list.")
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
            except FileNotFoundError:
                yield Label("Sector data not found. Please update data first.", classes="error")
                with Horizontal(classes="button-group"):
                    yield Button("Back", id="back", variant="primary")
            yield Footer()

    def on_select_changed(self, event: Select.Changed) -> None:
        selected_sector = event.value
        if selected_sector:
            if "sectors_to_avoid" not in self.app.user.data:
                self.app.user.data["sectors_to_avoid"] = []

            if selected_sector in self.app.user.data["sectors_to_avoid"]:
                self.app.user.data["sectors_to_avoid"].remove(selected_sector)
            else:
                self.app.user.data["sectors_to_avoid"].append(selected_sector)

            sectors_text = ", ".join(self.app.user.data["sectors_to_avoid"])
            if not sectors_text:
                sectors_text = "None"
            self.query_one("#selected_sectors").update(sectors_text)

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
            yield Label("Risk Tolerance", classes="heading")
            yield Label("Please indicate your risk tolerance (1-10):")
            yield Label("1 = Low Risk, 10 = High Risk")
            yield Input(placeholder="Enter risk level", id="risk")
            yield Label("", id="status")
            with Horizontal(classes="button-group"):
                yield Button("Back", id="back")
                yield Button("Continue", id="continue")
            yield Footer()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "risk":
            try:
                risk = int(event.value)
                if 1 <= risk <= 10:
                    self.app.user.data["risk_tolerance"] = risk
                    self.query_one("#status").remove_class("error")
                    self.query_one("#status").update("Valid risk level")
                else:
                    self.query_one("#status").add_class("error")
                    self.query_one("#status").update("Risk level must be between 1 and 10")
            except ValueError:
                self.query_one("#status").add_class("error")
                self.query_one("#status").update("Please enter a valid number")

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
            yield Label("Investment Constraints", classes="heading")
            yield Label("Enter investment constraints (0-100%):")
            yield Input(placeholder="Maximum investment per stock in %", id="max")
            yield Label("", id="status")
            with Horizontal(classes="button-group"):
                yield Button("Back", id="back")
                yield Button("Continue", id="continue")
            yield Footer()

    def validate_constraints(self) -> bool:
        max_input = self.query_one("#max").value
        status = self.query_one("#status")

        try:
            max_equity = float(max_input)

            if 0 < max_equity <= 100:
                self.app.user.data.update({
                    "max_equity_investment": max_equity
                })
                status.remove_class("error")
                status.update("Valid constraints")
                return True
            else:
                status.add_class("error")
                status.update("Invalid constraints: Min must be less than Max (0-100)")
                return False
        except ValueError:
            status.add_class("error")
            status.update("Please enter valid numbers")
            return False

    def on_input_changed(self, event: Input.Changed) -> None:
        self.validate_constraints()

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
            yield Static("Please wait while we prepare your portfolio.", id="status")
            yield Static("This may take a few seconds... (data is pulled from YahooFinance)", id="loading")
            with Horizontal(classes="button-group"):
                yield Button("Exit", id="exit", variant="error")
            yield Footer()

    async def on_mount(self) -> None:
        await asyncio.sleep(0.1)
        asyncio.create_task(self.initialize_and_redirect())

    async def initialize_and_redirect(self) -> None:
        """
        Asynchronously initializes the portfolio and handles any errors during setup.
        Uses threading to prevent UI blocking during data processing.
        """
        try:
            await asyncio.to_thread(self.perform_initialization)
            self.app.push_screen("optimization")
        except Exception as e:
            self.query_one("#status").update(f"[red]Error: {str(e)}[/red]")

    def perform_initialization(self) -> None:
        available_tickers = build_available_tickers(self.app.user)
        self.app.user.data["available_stocks"] = available_tickers
        if not available_tickers:
            raise ValueError("No tickers match your criteria")
        self.app.portfolio = Portfolio(self.app.user)

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
            yield Label("Portfolio Optimization", classes="header centered")
            yield Static("Please click 'Open Dashboard' to see the optimized portfolios", id="status")
            with Horizontal(classes="button-group"):
                yield Button("Open Dashboard", id="dashboard", variant="primary")
                yield Button("Exit", id="exit", variant="error")
            yield Footer()
    
    def perform_initialization(self) -> None:
        PortfolioOptimizationDashboard(self.app.portfolio).run()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handles dashboard launch and application exit.
        
        For dashboard launch:
        1. Creates a new thread for the dashboard
        2. Waits for server initialization
        3. Opens the dashboard in the default browser
        """
        if event.button.id == "dashboard":
            def run_dashboard():
                PortfolioOptimizationDashboard(self.app.portfolio).run()

            dashboard_thread = threading.Thread(target=run_dashboard)
            dashboard_thread.daemon = True
            dashboard_thread.start()

            time.sleep(4)
            webbrowser.open("http://127.0.0.1:8509")

        if event.button.id == "exit":
            self.app.exit()
            
class PortfolioApp(App):
    """
    Main application class that manages the screen workflow and global state.
    
    Features:
    - Implements a wizard-like interface with multiple screens
    - Maintains user preferences and portfolio data
    - Provides keyboard shortcuts for navigation
    - Custom styling for consistent UI appearance
    """
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

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "pop_screen", "Back"),
    ]

    SCREENS = {
        "update": UpdateDataScreen,    # Initial data update screen
        "stocks": StocksScreen,        # Stock selection screen
        "sectors": SectorsScreen,      # Sector exclusion screen
        "risk": RiskScreen,            # Risk tolerance screen
        "constraints": ConstraintsScreen,  # Investment constraints screen
        "data_pulling": DataPullingScreen, # Data processing screen
        "optimization": PortfolioOptimizationScreen  # Final dashboard screen
    }

    def __init__(self):
        super().__init__()
        self.user = User()

    def on_mount(self) -> None:
        """Called when app starts"""
        self.push_screen("update")

    def action_pop_screen(self) -> None:
        """Handle going back to previous screen"""
        if len(self.screen_stack) > 1:
            self.pop_screen()
