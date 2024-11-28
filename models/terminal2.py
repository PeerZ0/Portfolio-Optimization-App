from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Header, Footer, Input, Label, Select, Static
from textual.screen import Screen
from textual.message import Message
import pandas as pd
import os
import asyncio
from typing import List
from models.portfolio import Portfolio

class BaseScreen(Screen):
    """Base screen class with common functionality"""
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

class UpdateDataScreen(BaseScreen):
    """Screen for updating market data"""
    def compose(self) -> ComposeResult:
        with Container(classes="container"):
            yield Label("Update Market Data", classes="heading")
            yield Label("Do you want to update the market data?", classes="subtitle")
            yield Label("", id="status")
            with Horizontal(classes="button-group"):
                yield Button("Yes", id="yes", variant="primary")
                yield Button("No", id="no")
                yield Button("Static", id="static")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        status = self.query_one("#status")
        if event.button.id in ["yes", "no", "static"]:
            self.app.user.data["data_updated"] = event.button.id
            if event.button.id in ["yes", "static"]:
                status.update("Updating data...")
                self.update_data(event.button.id)
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
                filepath = os.path.abspath('static/ticker_data.html')
                
                yield Label(f"Total available stocks: {total_stocks}")
                yield Label(f"[Click here to view stocks](file://{filepath})", classes="link", markup=True)
                yield Input(placeholder="Enter stock tickers (comma-separated)", id="stocks")
                yield Label("", id="status")
                yield Button("Continue", id="continue", variant="primary")
            except FileNotFoundError:
                yield Label("Stock data not found. Please update data first.", classes="error")
                yield Button("Back", id="back", variant="primary")
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "continue":
            self.app.push_screen(SectorsScreen())
        elif event.button.id == "back":
            self.app.pop_screen()

# Remaining screens would similarly have button groups adjusted to horizontal layouts where appropriate,
# clickable links for HTML files, and overall better alignment and consistency in element sizes.

# Note: Only part of the application has been improved here for brevity. The same principles can be applied
# to other screens like SectorsScreen, RiskScreen, ConstraintsScreen, and OptimizationScreen to further enhance UI/UX.



class SectorsScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        with Container(classes="container"):
            yield Label("Exclude Sectors", classes="heading")
            try:
                df = pd.read_csv('static/ticker_data.csv')
                df['sector'] = df['sector'].fillna('Unknown')
                sectors = list(df['sector'].unique())
                
                yield Label("Select a sector to exclude:")
                yield Select(
                    [(sector, sector) for sector in sectors],
                    id="sectors"
                )
                with Horizontal(classes="button-group"):
                    yield Button("Add to exclusion list", id="add_sector")
                    yield Button("Continue", id="continue")
                yield Label("Selected sectors to exclude:", id="selected_sectors")
            except FileNotFoundError:
                yield Label("Sector data not found. Please update data first.", classes="error")
                yield Button("Back", id="back", variant="primary")
            yield Footer()

    def on_select_changed(self, event: Select.Changed) -> None:
        selected_sector = event.value
        if selected_sector:
            if "sectors_to_avoid" not in self.app.user.data:
                self.app.user.data["sectors_to_avoid"] = []

            if selected_sector not in self.app.user.data["sectors_to_avoid"]:
                self.app.user.data["sectors_to_avoid"].append(selected_sector)

            self.query_one("#selected_sectors").update(
                "Selected sectors to exclude: " + ", ".join(self.app.user.data["sectors_to_avoid"])
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_sector":
            # Explicitly handle adding sector selection to the user's list
            sector_select = self.query_one("#sectors")
            selected_sector = sector_select.value

            if selected_sector:
                if "sectors_to_avoid" not in self.app.user.data:
                    self.app.user.data["sectors_to_avoid"] = []

                if selected_sector not in self.app.user.data["sectors_to_avoid"]:
                    self.app.user.data["sectors_to_avoid"].append(selected_sector)
                    self.query_one("#selected_sectors").update(
                        "Selected sectors to exclude: " + ", ".join(self.app.user.data["sectors_to_avoid"])
                    )

        elif event.button.id == "continue":
            self.app.push_screen(RiskScreen())
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
                yield Button("Continue", id="continue")
                yield Button("Back", id="back")
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
                yield Button("Continue", id="continue")
                yield Button("Back", id="back")
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
            self.app.push_screen("data_pulling")  # Changed from OptimizationScreen
        elif event.button.id == "back":
            self.app.pop_screen()

class DataPullingScreen(BaseScreen):
    """Screen for data pulling and portfolio initialization"""

    def compose(self) -> ComposeResult:
        with Container(classes="container"):
            yield Label("Initializing Portfolio", classes="heading")
            yield Static("Starting data collection...", id="status")
            yield Static("", id="progress", classes="progress")
            yield Button("Back", id="back", classes="hidden")

    async def on_mount(self) -> None:
        """Start data collection when screen mounts"""
        self.initialize_portfolio()

    async def initialize_portfolio(self) -> None:
        status = self.query_one("#status")
        progress = self.query_one("#progress")
        back_button = self.query_one("#back")
        
        try:
            # Build ticker list
            status.update("Building available tickers list...")
            from services.build_list import build_available_tickers
            available_tickers = build_available_tickers(self.app.user)
            
            if not available_tickers:
                status.update("[red]No tickers match your criteria[/red]")
                back_button.remove_class("hidden")
                return
            
            # Initialize portfolio
            total_tickers = len(available_tickers)
            status.update(f"Initializing portfolio with {total_tickers} tickers...")
            progress.update("Fetching market data (this may take a few minutes)...")
            
            # Store portfolio in app for access across screens
            self.app.portfolio = Portfolio(available_tickers, self.app.user)
            
            # Success - proceed to optimization
            await asyncio.sleep(1)  # Brief pause to show success
            status.update("[green]Portfolio initialized successfully![/green]")
            await asyncio.sleep(1)  # Brief pause before transition
            self.app.push_screen("optimization")
            
        except Exception as e:
            status.update(f"[red]Error initializing portfolio: {str(e)}[/red]")
            progress.update("Please try again or adjust your preferences")
            back_button.remove_class("hidden")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()

class PortfolioOptimizationScreen(BaseScreen):
    """Screen for selecting and running optimizations"""
    
    def compose(self) -> ComposeResult:
        with Container(classes="container"):
            yield Label("Portfolio Optimization", classes="heading")
            yield Static("Select optimization method:", classes="subtitle")
            with Vertical():
                yield Button("Minimum Variance Portfolio", id="min_var")
                yield Button("Maximum Sharpe Ratio", id="max_sharpe")
                yield Button("Black-Litterman Model", id="black_litterman")
                yield Button("Auto-Optimize", id="auto")
            yield Static("", id="results", classes="results")
            yield Button("Back", id="back")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
            
        results = self.query_one("#results")
        try:
            results.update("Optimizing portfolio...")
            weights = None
            
            if event.button.id == "min_var":
                weights = self.app.portfolio.min_variance_portfolio()
                method = "Minimum Variance"
            elif event.button.id == "max_sharpe":
                weights = self.app.portfolio.max_sharpe_ratio_portfolio()
                method = "Maximum Sharpe Ratio"
            elif event.button.id == "black_litterman":
                weights = self.app.portfolio.black_litterman_model()
                method = "Black-Litterman"
            elif event.button.id == "auto":
                weights = self.app.portfolio.auto_optimize()
                method = "Auto-Optimize"
            
            if weights is not None:
                result_text = f"\n{method} Portfolio Weights:\n"
                for ticker, weight in zip(self.app.portfolio.tickers, weights):
                    result_text += f"{ticker}: {weight:.2%}\n"
                results.update(result_text)
            
        except Exception as e:
            results.update(f"[red]Optimization failed: {str(e)}[/red]")

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
        margin: 1;
    }

    .button-group {
        width: 100%;
        height: auto;
        align: center middle;
    }

    Button {
        margin: 1;
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

    def __init__(self, user):
        super().__init__()
        self.user = user

    def on_mount(self) -> None:
        """Called when app starts"""
        # Push the first screen
        self.push_screen("update")  # Start with update screen

    def action_pop_screen(self) -> None:
        """Handle going back to previous screen"""
        if len(self.screen_stack) > 1:  # Ensure we don't pop the last screen
            self.pop_screen()
