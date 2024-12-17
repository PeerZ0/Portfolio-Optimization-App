import dash
from dash import html, dcc, callback, Input, Output
import time
from state import user
from services.build_list import build_available_tickers
from models.portfolio import Portfolio

dash.register_page(__name__, path="/loading")

layout = html.Div([
    html.H2("Processing Your Portfolio...", className="text-center mt-5"),
    dcc.Loading(
        type="circle",
        children=html.Div(id="loading-output", style={"display": "none"})
    ),
    dcc.Location(id="redirect", refresh=True)  # For automatic redirect
])


@callback(
    Output("redirect", "href"),
    Input("loading-output", "children")
)
def process_portfolio(_):
    # Simulate processing
    time.sleep(3)

    # Build portfolio
    available_stocks = build_available_tickers(user)
    user.data["available_stocks"] = available_stocks
    user.portfolio = Portfolio(user)

    # Redirect to portfolio results
    return "/portfolio"
