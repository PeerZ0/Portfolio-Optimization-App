import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from models.user import User
from models.portfolio import Portfolio
from services.build_list import build_available_tickers
from models.dashboard import PortfolioOptimizationDashboard


class PortfolioManager:
    def __init__(self, stock_data_path):
        self.stock_data_path = stock_data_path
        self.user = User()
        self.data = pd.read_csv(stock_data_path)
        self.portfolio = None
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self._setup_layout()

    def _setup_layout(self):
        """Set up the layout for the input dashboard."""
        self.app.layout = dbc.Container([
            html.H1("Portfolio Builder", className="text-center text-primary mb-4"),
            
            # Inputs
            dbc.Row([
                dbc.Col([html.H5("Select Preferred Stocks"),
                         dcc.Dropdown(
                             id="preferred-stocks",
                             options=[{"label": stock, "value": stock} for stock in self.data['Ticker'].unique()],
                             multi=True)
                ], width=6),
                dbc.Col([html.H5("Select Sectors to Avoid"),
                         dcc.Dropdown(
                             id="avoid-sectors",
                             options=[{"label": sector, "value": sector} for sector in self.data['sector'].unique()],
                             multi=True)
                ], width=6)
            ], className="mb-4"),
            
            # Risk Tolerance
            dbc.Row([
                dbc.Col([html.H5("Risk Tolerance (1-10)"),
                         dcc.Slider(id="risk-slider", min=1, max=10, step=1, value=5)
                ], width=6),
                dbc.Col([html.H5("Max Equity Investment (%)"),
                         dcc.Input(id="max-investment", type="number", value=30, className="form-control")
                ], width=6)
            ], className="mb-4"),
            
            # Submit Button
            dbc.Row([
                dbc.Col(html.Button("Create Portfolio", id="create-button", n_clicks=0, 
                                    className="btn btn-primary btn-lg"), width=12)
            ], className="text-center mb-4"),

            # Confirmation Output
            html.Div(id="confirmation-output")
        ])

    def _run_callbacks(self):
        @self.app.callback(
            Output("confirmation-output", "children"),
            Input("create-button", "n_clicks"),
            [
                State("preferred-stocks", "value"),
                State("avoid-sectors", "value"),
                State("risk-slider", "value"),
                State("max-investment", "value")
            ]
        )
        def collect_user_inputs(n_clicks, preferred_stocks, avoid_sectors, risk_tolerance, max_investment):
            if n_clicks > 0:
                # Update user inputs
                self.user.data.update({
                    "preferred_stocks": preferred_stocks or [],
                    "sectors_to_avoid": avoid_sectors or [],
                    "risk_tolerance": risk_tolerance,
                    "max_equity_investment": max_investment
                })

                # Print user inputs to terminal for verification
                print("User Inputs Collected:")
                print(self.user.data)

                # Display user inputs on the confirmation section
                confirmation_message = html.Div([
                    html.H5("User Inputs Collected Successfully:", className="text-success mb-3"),
                    html.P(f"Preferred Stocks: {', '.join(self.user.data['preferred_stocks']) or 'None'}"),
                    html.P(f"Sectors to Avoid: {', '.join(self.user.data['sectors_to_avoid']) or 'None'}"),
                    html.P(f"Risk Tolerance: {self.user.data['risk_tolerance']}"),
                    html.P(f"Max Equity Investment: {self.user.data['max_equity_investment']}%"),
                    html.Hr(),
                    html.H5("Launching Portfolio Dashboard...", className="text-primary")
                ])

                # Build the list of available tickers based on user preferences
                available_tickers = build_available_tickers(self.user)
                print('success')
                self.user.data["available_stocks"] = available_tickers
                # Raise an error if no tickers match the criteria
                print(available_tickers)
                # Initialize the portfolio with the user's preferences
                self.portfolio = Portfolio(self.user)
                portfolio_dashboard = PortfolioOptimizationDashboard(self.portfolio)
                portfolio_dashboard.run()
                return confirmation_message

    def run(self):
        self._run_callbacks()
        self.app.run_server(port = 8053, debug=False)


# Run the combined application
if __name__ == "__main__":

    static = 'static/ticker_data.csv'
    manager = PortfolioManager(static)
    manager.run()