# pages/dashboard.py
"""
Portfolio Builder Dashboard

This module implements the main dashboard page where users can set their portfolio
preferences including preferred stocks, sectors to avoid, risk tolerance, and
maximum investment per equity.
"""

import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
from state import user

# Load stock data
data = pd.read_csv("static/ticker_data.csv")

# Add custom CSS for animations
external_stylesheets = [
    dbc.themes.DARKLY,
    "https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap"
]

dash.register_page(__name__, path="/")

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("PORTFOLIO BUILDER", 
                className="text-center mb-4 terminal-title")
        ], width=12)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("PREFERRED STOCKS", className="text-info"),
                    dcc.Dropdown(
                        id="preferred-stocks",
                        options=[{"label": stock, "value": stock} for stock in data['Ticker'].unique()],
                        multi=True,
                        className="dash-dropdown-modern terminal-input"
                    )
                ])
            ], className="h-100 terminal-card animate__animated animate__fadeInLeft")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("SECTORS TO AVOID", className="text-info"),
                    dcc.Dropdown(
                        id="avoid-sectors",
                        options=[{"label": sector, "value": sector} for sector in data['sector'].unique()],
                        multi=True,
                        className="dash-dropdown-modern terminal-input"
                    )
                ])
            ], className="h-100 terminal-card animate__animated animate__fadeInRight")
        ], width=6)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("RISK TOLERANCE", className="text-info"),
                    html.P("1 = LOW RISK; 10 = HIGH RISK", 
                          className="small mb-2",
                          style={
                              "fontFamily": "Roboto Mono",
                              "color": "#aaa"
                          }),
                    dcc.Slider(
                        id="risk-slider",
                        min=1,
                        max=10,
                        step=1,
                        marks={i: str(i) for i in range(1, 11)},
                        className="mt-3",
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ])
            ], className="h-100 terminal-card animate__animated animate__fadeInLeft")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("MAX EQUITY INVESTMENT (%)", className="text-info"),
                    dcc.Input(
                        id="max-investment",
                        type="number",
                        min=0,
                        max=100,
                        className="form-control terminal-input",
                        placeholder="Enter value between 0-100"
                    ),
                    html.Small(
                        "Value must be between 0 and 100",
                        className="small mb-2",
                        style={"fontFamily": "Roboto Mono",
                                "color": "#aaa"}
                    )
                ])
            ], className="h-100 terminal-card animate__animated animate__fadeInRight")
        ], width=6)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Button(
                "CREATE PORTFOLIO",
                id="create-btn",
                n_clicks=0,
                className="btn btn-lg w-100 terminal-button"
            )
        ], width={"size": 6, "offset": 3})
    ]),

    dcc.Store(id="user-store"),
    dcc.Location(id="url", refresh=True)
], fluid=True, className="py-5 terminal-container")

@callback(
    Output("preferred-stocks", "value"),
    Output("avoid-sectors", "value"),
    Output("risk-slider", "value"),
    Output("max-investment", "value"),
    Input("url", "pathname")
)
def update_inputs_on_load(pathname):
    """
    Update input fields with user's saved preferences when page loads.

    Parameters
    ----------
    pathname : str
        Current URL pathname.

    Returns
    -------
    tuple
        Tuple containing (preferred_stocks, avoided_sectors, risk_tolerance, max_investment).
    """
    if pathname == "/":
        preferred_stocks = user.data.get("preferred_stocks", [])
        avoided_sectors = user.data.get("sectors_to_avoid", [])
        risk_tolerance = user.data.get("risk_tolerance", 5)
        max_investment = user.data.get("max_equity_investment", 5)
        return preferred_stocks, avoided_sectors, risk_tolerance, max_investment
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

@callback(
    Output("url", "pathname"),  # Update the pathname of the dcc.Location
    Input("create-btn", "n_clicks"),
    State("preferred-stocks", "value"),
    State("avoid-sectors", "value"),
    State("risk-slider", "value"),
    State("max-investment", "value")
)
def handle_inputs(n_clicks, preferred, avoid, risk, max_inv):
    """
    Handle form submission and update user preferences.

    Parameters
    ----------
    n_clicks : int
        Number of times the create button has been clicked.
    preferred : list
        List of preferred stock tickers.
    avoid : list
        List of sectors to avoid.
    risk : int
        Risk tolerance level (1-10).
    max_inv : float
        Maximum investment percentage per equity.

    Returns
    -------
    str
        Redirect URL path.
    """
    if n_clicks > 0:
        # Update user data
        user.data.update({
            "preferred_stocks": preferred or [],
            "sectors_to_avoid": avoid or [],
            "risk_tolerance": risk,
            "max_equity_investment": max_inv
        })

        # Redirect to the loading page
        return "/loading"
