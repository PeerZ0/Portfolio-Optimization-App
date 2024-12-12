# models/terminal.py
# Terminal-based application for portfolio optimization

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Header, Footer, Input, Label, Select, Static
from textual.screen import Screen
import pandas as pd
import os
import asyncio
import subprocess
import webbrowser
import time

from models.portfolio import Portfolio
from models.user import User
from services.build_list import build_available_tickers
from models.dashboard2 import PortfolioOptimizationDashboard

class BaseScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

class UpdateDataScreen(BaseScreen):
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
            # save the valid stocks to the user data
            self.app.user.data["preferred_stocks"] = valid_stocks

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "continue":
            self.app.push_screen(SectorsScreen())
        elif event.button.id == "back":
            self.app.pop_screen()

class SectorsScreen(BaseScreen):
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

            # Toggle sector selection
            if selected_sector in self.app.user.data["sectors_to_avoid"]:
                self.app.user.data["sectors_to_avoid"].remove(selected_sector)
            else:
                self.app.user.data["sectors_to_avoid"].append(selected_sector)

            # Update display
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
    def compose(self) -> ComposeResult:
        with Container(classes="container"):
            yield Label("Investment Constraints", classes="heading")
            yield Label("Enter investment constraints (0-100%):")
            yield Input(placeholder="Minimum investment %", id="min")
            yield Input(placeholder="Maximum investment %", id="max")
            yield Label("", id="status")
            with Horizontal(classes="button-group"):
                yield Button("Back", id="back")
                yield Button("Continue", id="continue")
            yield Footer()

    def validate_constraints(self) -> bool:
        min_input = self.query_one("#min").value
        max_input = self.query_one("#max").value
        status = self.query_one("#status")

        try:
            min_equity = float(min_input) / 100
            max_equity = float(max_input) / 100

            if 0 <= min_equity <= max_equity <= 1:
                self.app.user.data.update({
                    "min_equity_investment": min_equity,
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
            self.app.pop_screen()  # Remove current screen
            self.app.push_screen("data_pulling")  # Push new screen
        elif event.button.id == "back":
            self.app.pop_screen()

class DataPullingScreen(BaseScreen):
    """Screen for data pulling and portfolio initialization."""

    def compose(self) -> ComposeResult:
        with Container(classes="container"):
            yield Label("Initializing Portfolio...", classes="heading")
            yield Static("Please wait while we prepare your portfolio.", id="status")
            yield Static("This may take a few seconds... (data is pulled from YahooFinance)", id="loading")
            with Horizontal(classes="button-group"):
                yield Button("Exit", id="exit", variant="error")
            yield Footer()

    async def on_mount(self) -> None:
        """Start the initialization process immediately after mounting the screen."""
        await asyncio.sleep(0.1)  # Yield to allow the screen to render
        asyncio.create_task(self.initialize_and_redirect())

    async def initialize_and_redirect(self) -> None:
        """Perform initialization and redirect to the next screen."""
        try:
            # Perform portfolio initialization
            await asyncio.to_thread(self.perform_initialization)
            # Redirect to the next screen after successful initialization
            self.app.push_screen("optimization")
        except Exception as e:
            # If an error occurs, display it on the screen
            self.query_one("#status").update(f"[red]Error: {str(e)}[/red]")

    def perform_initialization(self) -> None:
        """Blocking initialization logic moved to a thread."""
        available_tickers = build_available_tickers(self.app.user)
        # save the available tickers to the user data
        self.app.user.data["available_stocks"] = available_tickers
        if not available_tickers:
            raise ValueError("No tickers match your criteria")
        self.app.portfolio = Portfolio(self.app.user)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.app.exit()

class PortfolioOptimizationScreen(BaseScreen):
    """Screen for selecting and running optimizations"""
    
    def compose(self) -> ComposeResult:
        with Container(classes="container"):
            yield Label("Portfolio Optimization", classes="heading")
            yield Button("Open Dashboard", id="dashboard")
            yield Button("Exit", id="exit", variant="error")
            yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        
        if event.button.id == "dashboard":
            # Suppress logs and open browser
            PortfolioOptimizationDashboard(self.app.portfolio).run()
            time.sleep(2)
            webbrowser.open("http://127.0.0.1:8059")

        if event.button.id == "exit":
            self.app.exit()
            
class PortfolioApp(App):
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

    .subtitle {
        text-align: center;
        margin: 1 0 0 2;
    }

    .button-group {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
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
        "update": UpdateDataScreen,
        "stocks": StocksScreen, 
        "sectors": SectorsScreen,
        "risk": RiskScreen,
        "constraints": ConstraintsScreen,
        "data_pulling": DataPullingScreen,
        "optimization": PortfolioOptimizationScreen
    }

    def __init__(self):
        super().__init__()
        self.user = User()

    def on_mount(self) -> None:
        """Called when app starts"""
        # Push the first screen
        self.push_screen("update")  # Start with update screen

    def action_pop_screen(self) -> None:
        """Handle going back to previous screen"""
        if len(self.screen_stack) > 1:  # Ensure we don't pop the last screen
            self.pop_screen()
