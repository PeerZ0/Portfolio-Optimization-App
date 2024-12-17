import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
from state import user

# Load stock data
data = pd.read_csv("static/ticker_data.csv")

dash.register_page(__name__, path="/")

layout = dbc.Container([
    html.H1("Portfolio Builder", className="text-center text-primary mb-4"),
    dcc.Store(id="user-store"),  # Store inputs temporarily

    dcc.Location(id="url", refresh=True),  # Location component for navigation

    # Inputs
    dbc.Row([
        dbc.Col([
            html.H5("Select Preferred Stocks"),
            dcc.Dropdown(
                id="preferred-stocks",
                options=[{"label": stock, "value": stock} for stock in data['Ticker'].unique()],
                multi=True
            )
        ], width=6),
        dbc.Col([
            html.H5("Select Sectors to Avoid"),
            dcc.Dropdown(
                id="avoid-sectors",
                options=[{"label": sector, "value": sector} for sector in data['sector'].unique()],
                multi=True
            )
        ], width=6)
    ]),

    dbc.Row([
        dbc.Col([
            html.H5("Risk Tolerance (1-10)"),
            dcc.Slider(id="risk-slider", min=1, max=10, step=1)  # Set default value
        ], width=6),
        dbc.Col([
            html.H5("Max Equity Investment (%)"),
            dcc.Input(id="max-investment", type="number", className="form-control")
        ], width=6)
    ]),

    dbc.Button("Create Portfolio", id="create-btn", n_clicks=0, className="btn btn-primary mt-3"),
])

@callback(
    Output("preferred-stocks", "value"),
    Output("avoid-sectors", "value"),
    Output("risk-slider", "value"),
    Output("max-investment", "value"),
    Input("url", "pathname")
)
def update_inputs_on_load(pathname):
    if pathname == "/":
        preferred_stocks = user.data.get("preferred_stocks", [])
        avoided_sectors = user.data.get("sectors_to_avoid", [])
        risk_tolerance = user.data.get("risk_tolerance", 5)
        max_investment = user.data.get("max_equity_investment", 30)
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
