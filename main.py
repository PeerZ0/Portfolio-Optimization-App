# main.py
"""
Main Application

This is the entry point of the application. It initializes the Dash app
with the required configuration and starts the server.
"""

import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import webbrowser

# Initialize Dash app with multi-page support and Bootstrap theme
app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define root layout
app.layout = html.Div([
    dcc.Location(id="url", refresh=True),
    dash.page_container
])

if __name__ == "__main__":
    # Open browser automatically when app starts
    webbrowser.open("http://127.0.0.1:8060/")
    # Run server
    app.run(port='8060', debug=False)
