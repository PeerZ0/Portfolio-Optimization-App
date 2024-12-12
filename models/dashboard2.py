import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
from portfolio import Portfolio


app = dash.Dash(__name__)
app.title = "Portfolio Optimization Dashboard"

def create_dashboard(tickers, min_weight, max_weight):
    portfolio = Portfolio(tickers=tickers, min_weight=min_weight, max_weight=max_weight)

    # Initialize the portfolio weights
    min_variance_weights = portfolio.min_variance_portfolio()
    equal_weights = portfolio.equal_weight_portfolio()
    max_sharpe_weights = portfolio.max_sharpe_ratio_portfolio()

    # Layout of the dashboard
    app.layout = html.Div([
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

    # Callbacks for interactivity
    @app.callback(
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
            portfolio_weights = min_variance_weights
        elif selected_strategy == 'equal_weight':
            portfolio_weights = equal_weights
        elif selected_strategy == 'max_sharpe':
            portfolio_weights = max_sharpe_weights

        # Get summary statistics
        summary_df = portfolio.get_summary_statistics_table(portfolio_weights)

        # Create a table for summary statistics
        summary_table = html.Table([
            html.Thead(html.Tr([html.Th(col) for col in summary_df.columns])),
            html.Tbody([
                html.Tr([html.Td(summary_df.iloc[i][col]) for col in summary_df.columns])
                for i in range(len(summary_df))
            ])
        ], style={'width': '100%', 'text-align': 'center', 'margin-bottom': '20px'})

        # Plot cumulative returns
        cumulative_returns_fig = portfolio.plot_cumulative_returns(portfolio_weights)

        # Plot portfolio allocation
        portfolio_allocation_fig = portfolio.plot_portfolio_allocation(portfolio_weights)

        # Plot annualized returns
        annualized_returns_fig = portfolio.plot_annualized_returns(portfolio_weights)

        return summary_table, cumulative_returns_fig, portfolio_allocation_fig, annualized_returns_fig

    return app