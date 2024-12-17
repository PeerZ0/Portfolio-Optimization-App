import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
from state import user  # Shared state where portfolio is already initialized
from services.export_portfolio import export_portfolio
from models.portfolio import Portfolio

# Register the page
dash.register_page(__name__, path="/portfolio")

# Layout for the portfolio dashboard
layout = html.Div([
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
                        style={'width': '50%', 'margin': 'auto'},
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

@callback(
    [
        Output('summary-statistics-table', 'children'),
        Output('cumulative-returns-plot', 'figure'),
        Output('portfolio-allocation-plot', 'figure'),
        Output('annualized-returns-plot', 'figure'),
        Output('sector-allocation-plot', 'figure')
    ],
    Input('portfolio-strategy-dropdown', 'value')
)
def update_dashboard(selected_strategy):
    """
    Update dashboard components based on the selected strategy.
    """
    # Ensure portfolio is initialized
    if not user.portfolio:
        user.portfolio = Portfolio(user)

    # Retrieve portfolio object
    portfolio = user.portfolio

    # Retrieve weights
    if selected_strategy == 'min_variance':
        portfolio_weights = portfolio.weights_min
    elif selected_strategy == 'equal_weight':
        portfolio_weights = portfolio.weights_eq
    elif selected_strategy == 'max_sharpe':
        portfolio_weights = portfolio.weights_sharpe
    else:
        return None, None, None, None, None

    # Get summary statistics
    summary_df = portfolio.get_summary_statistics_table(portfolio_weights)
    summary_table = html.Table([
        html.Thead(html.Tr([html.Th(col) for col in summary_df.columns])),
        html.Tbody([
            html.Tr([html.Td(summary_df.iloc[i][col]) for col in summary_df.columns])
            for i in range(len(summary_df))
        ])
    ])

    # Generate plots
    cumulative_returns_fig = portfolio.plot_cumulative_returns(portfolio_weights)
    portfolio_allocation_fig = portfolio.plot_portfolio_allocation(portfolio_weights, selected_strategy)
    annualized_returns_fig = portfolio.plot_annualized_returns(portfolio_weights)
    sector_allocation_fig = portfolio.create_weighted_sector_treemap(portfolio_weights)

    return summary_table, cumulative_returns_fig, portfolio_allocation_fig, annualized_returns_fig, sector_allocation_fig


@callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-download", "n_clicks"),
    State("portfolio-strategy-dropdown", "value"),
    prevent_initial_call=True
)
def download_csv(n_clicks, selected_strategy):
    """
    Export portfolio data to CSV based on selected strategy.
    """
    # Ensure portfolio is initialized
    if not user.portfolio:
        user.portfolio = Portfolio(user)

    portfolio = user.portfolio

    if selected_strategy == 'min_variance':
        portfolio_weights = portfolio.weights_min
        strategy_name = "Minimum Variance Strategy"
    elif selected_strategy == 'equal_weight':
        portfolio_weights = portfolio.weights_eq
        strategy_name = "Equal Weight Strategy"
    elif selected_strategy == 'max_sharpe':
        portfolio_weights = portfolio.weights_sharpe
        strategy_name = "Maximum Sharpe Ratio Strategy"
    else:
        return None

    # Export portfolio and return file download
    return export_portfolio(portfolio_weights, strategy_name)
