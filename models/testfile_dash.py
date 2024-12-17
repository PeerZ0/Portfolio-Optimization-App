import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.graph_objects as go
from flask import redirect

class PortfolioDashboard:
    def __init__(self, stock_data_path):
        """
        Initialize the Portfolio Dashboard.

        Parameters
        ----------
        stock_data_path : str
            Path to the CSV file containing stock and sector data.
        """
        self.stock_data_path = stock_data_path
        self.app = dash.Dash(__name__, suppress_callback_exceptions=True)
        self.data = pd.read_csv(stock_data_path)
        self.selected_stocks = []
        self.excluded_sectors = []
        self.risk_aversion = 5
        self.max_investment = 0
        self._setup_layout()

    def _setup_layout(self):
        """Set up the layout of the dashboard."""
        self.app.layout = html.Div([
            dcc.Location(id="url", refresh=True),  # URL management
            html.Div(id="page-content")
        ])

        # Define main page layout
        self.index_page = html.Div([
            html.H1("Portfolio Builder Dashboard", style={"textAlign": "center"}),

            # Step 1: Choose stocks
            html.Div([
                html.H3("Step 1: Select Stocks to Include"),
                dcc.Dropdown(
                    id="stock-selector",
                    options=[{"label": stock, "value": stock} for stock in self.data['Ticker'].unique()],
                    multi=True,
                    placeholder="Select stocks..."
                ),
            ], style={"marginBottom": "20px"}),

            # Step 2: Exclude sectors
            html.Div([
                html.H3("Step 2: Select Sectors to Exclude"),
                dcc.Dropdown(
                    id="sector-selector",
                    options=[{"label": sector, "value": sector} for sector in self.data['Ticker'].unique()],
                    multi=True,
                    placeholder="Select sectors to exclude..."
                ),
            ], style={"marginBottom": "20px"}),

            # Step 3: Risk aversion
            html.Div([
                html.H3("Step 3: Select Your Risk Aversion Level"),
                dcc.Slider(
                    id="risk-slider",
                    min=1, max=10, step=1,
                    marks={i: str(i) for i in range(1, 11)},
                    value=5
                ),
            ], style={"marginBottom": "20px"}),

            # Step 4: Max investment per stock
            html.Div([
                html.H3("Step 4: Enter Maximum Investment Per Stock"),
                dcc.Input(
                    id="max-investment",
                    type="number",
                    placeholder="Enter amount in $",
                    value=0
                ),
            ], style={"marginBottom": "20px"}),

            # Create Portfolio Button
            html.Div([
                html.Button("Create Portfolio", id="create-portfolio-button", n_clicks=0, style={"marginTop": "10px"})
            ], style={"textAlign": "center"})
        ])

    def _create_portfolio_page(self):
        """Create the Portfolio Results Page."""
        return html.Div(id="portfolio-results")

    def _run_callbacks(self):
        """Define the callbacks for interactivity."""
        # Route pages
        @self.app.callback(
            Output("page-content", "children"),
            Input("url", "pathname")
        )
        def display_page(pathname):
            if pathname == "/portfolio":
                return self._create_portfolio_page()
            return self.index_page

        # Redirect to portfolio page
        @self.app.callback(
            Output("url", "pathname"),
            Input("create-portfolio-button", "n_clicks"),
            [
                State("stock-selector", "value"),
                State("sector-selector", "value"),
                State("risk-slider", "value"),
                State("max-investment", "value")
            ]
        )
        def redirect_to_portfolio(n_clicks, selected_stocks, excluded_sectors, risk_aversion, max_investment):
            if n_clicks > 0:
                # Update instance variables
                self.selected_stocks = selected_stocks or []
                self.excluded_sectors = excluded_sectors or []
                self.risk_aversion = risk_aversion
                self.max_investment = max_investment
                return "/portfolio"
            return dash.no_update

        # Display portfolio results
        @self.app.callback(
            Output("portfolio-results", "children"),
            Input("url", "pathname")
        )
        def display_portfolio(pathname):
            if pathname == "/portfolio":
                filtered_data = self.data.copy()
                if self.excluded_sectors:
                    filtered_data = filtered_data[~filtered_data['Parent'].isin(self.excluded_sectors)]
                if self.selected_stocks:
                    filtered_data = filtered_data[filtered_data['Name'].isin(self.selected_stocks)]

                return html.Div([
                    html.H1("Your Portfolio Summary", style={"textAlign": "center"}),
                    html.P(f"Risk Aversion Level: {self.risk_aversion}"),
                    html.P(f"Maximum Investment Per Stock: ${self.max_investment}"),
                    dcc.Graph(figure=self._create_portfolio_treemap(filtered_data))
                ])


    def run(self):
        """Run the Dash app."""
        self._run_callbacks()
        self.app.run_server(port = 8052,debug=False)

# Run the dashboard
if __name__ == "__main__":
    static = 'static/ticker_data.csv'
    dashboard = PortfolioDashboard(static)
    dashboard.run()
