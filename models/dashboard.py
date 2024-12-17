# models/dashboard.py
"""
Dashboard class for interactive visualization of portfolio optimization results.

This module defines the PortfolioOptimizationDashboard class, which is used to create an 
interactive dashboard for visualizing the results of portfolio optimization.
"""

from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State
from flask_caching import Cache
from services.export_portfolio import export_portfolio

class PortfolioOptimizationDashboard:
    def __init__(self, portfolio):
        """
        Initializes the Portfolio Optimization Dashboard.

        Parameters
        ----------
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
        self.min_variance_weights = portfolio.weights_min
        self.equal_weights = portfolio.weights_eq
        self.max_sharpe_weights = portfolio.weights_sharpe

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
                ], style={'text-align': 'center'}),

                # Add Download Button after dropdown
                html.Div([
                    html.Button(
                        "Download Portfolio Data",
                        id="btn-download",
                        style={
                            'margin': '20px',
                            'padding': '10px 20px',
                            'backgroundColor': '#4CAF50',
                            'color': 'white',
                            'border': 'none',
                            'borderRadius': '4px',
                            'cursor': 'pointer'
                        }
                    ),
                    dcc.Download(id="download-dataframe-csv"),
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
                ], style={'width': '85%', 'margin': 'auto'}),

                #new test plot 
                html.Div([
                    dcc.Graph(id='sector-allocation-plot')
                ], style={'width': '85%', 'margin': 'auto'}),
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
                Output('annualized-returns-plot', 'figure'),
                # new plot test
                Output('sector-allocation-plot', 'figure')
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
            portfolio_allocation_fig = self.portfolio.plot_portfolio_allocation(portfolio_weights, selected_strategy)
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
            
            # Plot sector allocation
            sector_allocation_fig = self.portfolio.create_weighted_sector_treemap(portfolio_weights)
            if not annualized_returns_fig:
                annualized_returns_fig = {
                    "data": [],
                    "layout": {"title": "No data available for annualized returns"}
                }
            print(f"update_dashboard called with strategy: {selected_strategy}")
            return summary_table, cumulative_returns_fig, portfolio_allocation_fig, annualized_returns_fig, sector_allocation_fig

        @self.app.callback(
            Output("download-dataframe-csv", "data"),
            [Input("btn-download", "n_clicks"),
             Input("portfolio-strategy-dropdown", "value")],
            prevent_initial_call=True
        )
        def download_csv(n_clicks, selected_strategy):
            if n_clicks is None:
                return None
            
            # Select portfolio weights based on strategy
            if selected_strategy == 'min_variance':
                portfolio_weights = self.min_variance_weights
                strategy_name = "Minimum Variance Strategy"
            elif selected_strategy == 'equal_weight':
                portfolio_weights = self.equal_weights
                strategy_name = "Equal Weight Strategy"
            elif selected_strategy == 'max_sharpe':
                portfolio_weights = self.max_sharpe_weights
                strategy_name = "Maximum Sharpe Ratio Strategy"

            # Export portfolio and get file path
            output_file = export_portfolio(portfolio_weights, strategy_name)
            
            # Return the file as a download
            return dcc.send_file(output_file)

    def run(self):
        """Runs the Dash application."""
        self.app.run_server(debug=False, port=8509)

if __name__ == "__main__":
    from user import User
    from portfolio import Portfolio
    
    user = User()
    user.data = {
            "preferred_stocks": [],  # List of stock tickers the user wants in their portfolio
            "available_stocks": ["AAPL", "MSFT", 'SW', 'TSCO', 'DHL.DE', 'BNR.DE', 'DB1.DE', 'AIZ', 'DRI', 'CMS', 'WM', 'HD', 'HUM', 'ENEL.MI', 'ENI.MI', 'TMO', 'CVX', 'QIA.DE', 'MTD', 'MTD', 'NDA-FI.HE', 'AD.AS', 'EIX', 'ETN', 'MUV2.DE'],  # List of stock tickers available for investment
            "sectors_to_avoid": [],  # List of sectors the user wishes to avoid investing in
            "risk_tolerance": 5,  # Risk tolerance level on a scale of 1 to 10, default is 5 (medium risk)
            "max_equity_investment": 30,  # Maximum allowable investment in a single equity (in percentage), default is 30%
        }
    # user.data = {"available_stocks": ["AAPL", "MSFT", 'SW', 'TSCO', 'DHL.DE', 'BNR.DE', 'DB1.DE', 'AIZ', 'DRI', 'CMS', 'WM', 'HD', 'HUM', 'ENEL.MI', 'ENI.MI', 'TMO', 'CVX', 'QIA.DE', 'MTD', 'MTD', 'NDA-FI.HE', 'AD.AS', 'EIX', 'ETN', 'MUV2.DE', 'PPL', 'SOON.SW', 'FRE.DE', 'EVRG', 'CS.PA', 'ZURN.SW', 'MMC', 'C', 'UNP', 'PNC', 'AIR.PA', 'MA', 'NI', 'ZAL.DE', 'XEL', 'AI.PA', 'RSG', 'URI', 'SLB', 'PCG', 'BBVA.MC', 'GD', 'OTIS']}  # List of stock tickers available for investment}
    port = Portfolio(user)
    PortfolioOptimizationDashboard(port).run()
