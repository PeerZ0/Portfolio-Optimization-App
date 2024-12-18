# pages/loading.py
"""
Loading Page Module

This module implements an intermediate loading screen that:
1. Displays while the portfolio is being constructed
2. Features an animated terminal-themed loading indicator
3. Handles the initialization of portfolio data
4. Redirects to the portfolio dashboard when ready

The page uses CSS animations for the loading indicator and maintains the
terminal theme consistent with the rest of the application.
"""

import dash
from dash import html, dcc, callback, Input, Output
from state import user
from services.build_list import build_available_tickers
from models.portfolio import Portfolio

# Register the page
dash.register_page(__name__, path="/loading")

# Custom loader style with terminal theme
loader_style = {
    'width': '60px',
    'aspectRatio': '2',
    'background': '''
        radial-gradient(circle closest-side,#FF8000 90%,#0000) 0% 50%,
        radial-gradient(circle closest-side,#FF8000 90%,#0000) 50% 50%,
        radial-gradient(circle closest-side,#FF8000 90%,#0000) 100% 50%
    ''',
    'backgroundSize': 'calc(100%/3) 50%',
    'backgroundRepeat': 'no-repeat',
    'animation': 'l3 1s infinite linear'
}

# Add keyframes animation for the loading dots
dash.clientside_callback(
    """
    function(trigger) {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes l3 {
                20%{background-position:0% 0%, 50% 50%,100% 50%}
                40%{background-position:0% 100%, 50% 0%,100% 50%}
                60%{background-position:0% 50%, 50% 100%,100% 0%}
                80%{background-position:0% 50%, 50% 50%,100% 100%}
            }
        `;
        document.head.appendChild(style);
        return '';
    }
    """,
    Output("loading-animation", "children"),
    Input("loading-animation", "id")
)

# Define page layout
layout = html.Div([
    html.H2("PROCESSING YOUR PORTFOLIO", 
            className="text-center mt-5 terminal-title"),
    html.Div(
        html.Div(id="loading-animation", className="loader", style=loader_style),
        className="d-flex justify-content-center mt-4"
    ),
    html.Div(id="loading-output", style={"display": "none"}),
    dcc.Location(id="redirect", refresh=True)
], className="terminal-container d-flex flex-column align-items-center")

@callback(
    Output("redirect", "href"),
    Input("loading-output", "children")
)
def process_portfolio(_):
    """
    Process and initialize the portfolio object.

    This callback function runs when the loading page is displayed. It:
    1. Builds the list of available tickers based on user preferences
    2. Initializes the portfolio object
    3. Redirects to the portfolio dashboard

    Parameters
    ----------
    _ : any
        Unused parameter required by the callback.

    Returns
    -------
    str
        Redirect URL to the portfolio dashboard.
    """
    # Build list of available stocks based on user preferences
    available_stocks = build_available_tickers(user)
    user.data["available_stocks"] = available_stocks
    
    # Initialize portfolio object
    user.portfolio = Portfolio(user)
    
    # Redirect to portfolio dashboard
    return "/portfolio"