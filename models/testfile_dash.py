import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

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
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
        self.data = pd.read_csv(stock_data_path)
        self.selected_stocks = []
        self.excluded_sectors = []
        self.risk_aversion = 5
        self.max_investment = 0
        self._setup_layout()

    def _setup_layout(self):
        """Set up the layout of the dashboard."""
        self.app.layout = dbc.Container([
            dcc.Location(id="url", refresh=True),  # URL management
            html.Div(id="page-content")
        ], fluid=True, style={"padding": "20px", "backgroundColor": "#f8f9fa"})

        # Define main page layout
        self.index_page = html.Div([
            dbc.Row([
                dbc.Col(html.H1("Portfolio Builder Dashboard", className="text-center text-primary mb-4"), width=12)
            ]),
            
            # Step 1: Choose stocks
            dbc.Row([
                dbc.Col([
                    html.H3("Step 1: Select Stocks to Include", className="mb-2"),
                    dcc.Dropdown(
                        id="stock-selector",
                        options=[{"label": stock, "value": stock} for stock in self.data['Ticker'].unique()],
                        multi=True,
                        placeholder="Select stocks...",
                    )
                ], width=6)
            ], className="mb-4"),

            # Step 2: Exclude sectors
            dbc.Row([
                dbc.Col([
                    html.H3("Step 2: Select Sectors to Exclude", className="mb-2"),
                    dcc.Dropdown(
                        id="sector-selector",
                        options=[{"label": sector, "value": sector} for sector in self.data['sector'].unique()],
                        multi=True,
                        placeholder="Select sectors to exclude...",
                    )
                ], width=6)
            ], className="mb-4"),

            # Step 3: Risk aversion
            dbc.Row([
                dbc.Col([
                    html.H3("Step 3: Select Your Risk Aversion Level", className="mb-2"),
                    dcc.Slider(
                        id="risk-slider",
                        min=1, max=10, step=1,
                        marks={i: str(i) for i in range(1, 11)},
                        value=5,
                    )
                ], width=6)
            ], className="mb-4"),

            # Step 4: Max investment per stock
            dbc.Row([
                dbc.Col([
                    html.H3("Step 4: Enter Maximum Investment Per Stock", className="mb-2"),
                    dcc.Input(
                        id="max-investment",
                        type="number",
                        placeholder="Enter amount in $",
                        className="form-control",
                        value=0
                    )
                ], width=6)
            ], className="mb-4"),

            # Create Portfolio Button
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Button("Create Portfolio", id="create-portfolio-button", n_clicks=0, 
                                    className="btn btn-primary btn-lg")
                    ], className="text-center")
                ], width=12)
            ])
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
                    dbc.Row([
                        dbc.Col(html.H1("Your Portfolio Summary", className="text-center text-primary mb-4"), width=12)
                    ]),
                    html.P(f"Risk Aversion Level: {self.risk_aversion}", className="mb-2"),
                    html.P(f"Maximum Investment Per Stock: ${self.max_investment}", className="mb-4"),
                    dcc.Graph(figure=self._create_portfolio_treemap(filtered_data))
                ], style={"padding": "20px", "backgroundColor": "#ffffff", "borderRadius": "10px"})

    def _create_portfolio_treemap(self, filtered_data):
        """Create a Treemap of the filtered portfolio data."""
        fig = go.Figure(go.Treemap(
            labels=filtered_data['Name'],
            parents=filtered_data['Parent'],
            values=filtered_data['Weight_n'],
            textinfo="label+value+percent parent",
            root_color="lightgrey"
        ))
        fig.update_layout(title="Filtered Portfolio Treemap", 
                          paper_bgcolor="#ffffff", 
                          margin=dict(t=50, l=25, r=25, b=25))
        return fig

    def run(self):
        """Run the Dash app."""
        self._run_callbacks()
        self.app.run_server(port = 8051, debug=False)


if __name__ == "__main__":
    static = 'static/ticker_data.csv'
    dashboard = PortfolioDashboard(static)
    dashboard.run()
