import sys
from importlib import import_module
from dash import Dash, html, dcc
from dash.dependencies import Input, Output
from flask_caching import Cache
import subprocess


class PortfolioOptimizationDashboard:
    def __init__(self, portfolio):
        """
        Initializes the Portfolio Optimization Dashboard.

        Args:
            portfolio (Portfolio): An instance of the Portfolio class.
        """
        self.app = Dash(__name__)
        self.app.title = "Portfolio Optimization Dashboard"

        # Initialize cache
        self.cache = Cache(self.app.server, config={
            'CACHE_TYPE': 'simple'
        })

        # Clear cache (useful during development to reset cached data)
        self.cache.clear()

        # Store portfolio instance
        self.portfolio = portfolio

        # Example portfolio weights
        self.min_variance_weights = self.portfolio.min_variance_portfolio()
        self.equal_weights = self.portfolio.equal_weight_portfolio()
        self.max_sharpe_weights = self.portfolio.max_sharpe_ratio_portfolio()

        # Initialize layout
        self._initialize_layout()
        
        # Set up callbacks
        self._initialize_callbacks()

    def _initialize_layout(self):
        """Defines the layout of the dashboard."""
        self.app.layout = html.Div([
            # Header section
            html.Div([
                html.H1("Portfolio Optimization Dashboard", style={'text-align': 'center'}),

                html.Div([
                    html.Label("Select Portfolio Strategy:"),
                    dcc.Dropdown(
                        id='portfolio-strategy-dropdown',
                        options=[
                            {'label': 'Minimum Variance Portfolio', 'value': 'min_variance'},
                            {'label': 'Equal Weight Portfolio', 'value': 'equal_weight'},
                            {'label': 'Maximum Sharpe Ratio Portfolio', 'value': 'max_sharpe'}
                        ],
                        value='min_variance',
                        style={'width': '50%', 'margin': 'auto'}
                    )
                ], style={'text-align': 'center'})
            ]),

            html.Br(),

            # First row: Summary statistics
            html.Div([
                html.H2("Summary Statistics", style={'text-align': 'center'}),
                html.Div(id='summary-statistics-table', style={'width': '70%', 'margin': 'auto', 'margin-bottom': '30px'})
            ]),

            html.Br(),

            # Second row: Plots
            html.Div([
                html.H2("Portfolio Visualization", style={'text-align': 'center'}),
                html.Div([
                    dcc.Graph(id='cumulative-returns-plot', style={'margin-bottom': '30px'}),
                ], style={'width': '85%', 'margin': 'auto'}),

                html.Div([
                    dcc.Graph(id='portfolio-allocation-plot', style={'margin-bottom': '30px'}),
                ], style={'width': '85%', 'margin': 'auto'}),

                html.Div([
                    dcc.Graph(id='annualized-returns-plot')
                ], style={'width': '85%', 'margin': 'auto'})
            ]),

            html.Div("Dashboard created using Dash & Plotly", style={'text-align': 'center', 'margin-top': '50px'})
        ])

    def _initialize_callbacks(self):
        """Sets up the callbacks for the dashboard."""
        @self.app.callback(
            [
                Output('summary-statistics-table', 'children'),
                Output('cumulative-returns-plot', 'figure'),
                Output('portfolio-allocation-plot', 'figure'),
                Output('annualized-returns-plot', 'figure')
            ],
            [Input('portfolio-strategy-dropdown', 'value')]
        )
        def update_dashboard(selected_strategy):
            # Select portfolio weights based on the dropdown
            if selected_strategy == 'min_variance':
                portfolio_weights = self.min_variance_weights
            elif selected_strategy == 'equal_weight':
                portfolio_weights = self.equal_weights
            elif selected_strategy == 'max_sharpe':
                portfolio_weights = self.max_sharpe_weights

            # Get summary statistics
            summary_df = self.portfolio.get_summary_statistics_table(portfolio_weights)

            # Create a table for summary statistics
            summary_table = html.Table([
                html.Thead(html.Tr([html.Th(col) for col in summary_df.columns])),
                html.Tbody([
                    html.Tr([html.Td(summary_df.iloc[i][col]) for col in summary_df.columns])
                    for i in range(len(summary_df))
                ])
            ], style={'width': '100%', 'text-align': 'center', 'margin-bottom': '20px'})

            # Plot cumulative returns
            cumulative_returns_fig = self.portfolio.plot_cumulative_returns(portfolio_weights)
            if not cumulative_returns_fig:
                cumulative_returns_fig = {
                    "data": [],
                    "layout": {"title": "No data available for cumulative returns"}
                }

            # Plot portfolio allocation
            portfolio_allocation_fig = self.portfolio.plot_portfolio_allocation(portfolio_weights)
            if not portfolio_allocation_fig:
                portfolio_allocation_fig = {
                    "data": [],
                    "layout": {"title": "No data available for portfolio allocation"}
                }

            # Plot annualized returns
            annualized_returns_fig = self.portfolio.plot_annualized_returns(portfolio_weights)
            if not annualized_returns_fig:
                annualized_returns_fig = {
                    "data": [],
                    "layout": {"title": "No data available for annualized returns"}
                }
            print(f"update_dashboard called with strategy: {selected_strategy}")
            return summary_table, cumulative_returns_fig, portfolio_allocation_fig, annualized_returns_fig

    def run(self):
        """Runs the Dash application."""
        self.app.run_server(debug=False, port=8509)

if __name__ == '__main__':
    from portfolio import Portfolio  # Replace with the actual module containing the Portfolio class

    # Initialize Portfolio object
    from user import User
    user = User()
    user.data = {
            "preferred_stocks": ['AAPL', 'MSFT'], 
            "available_stocks": ['AAPL', 'MSFT'],  # List of stock tickers available for investment
            "sectors_to_avoid": [],  # List of sectors the user wishes to avoid investing in
            "risk_tolerance": 5,  # Risk tolerance level on a scale of 1 to 10, default is 5 (medium risk)
            "max_equity_investment": 30,  # Maximum allowable investment in a single equity (in percentage), default is None
            "min_equity_investment": 5,  # Minimum allowable investment in a single equity (in percentage), default is None
        }
    portfolio = Portfolio(user)

    # Initialize and run the dashboard
    dashboard = PortfolioOptimizationDashboard(portfolio)
    dashboard.run()