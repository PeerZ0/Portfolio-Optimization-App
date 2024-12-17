import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dcc.Location(id="url", refresh=True),  # Handles navigation
    dash.page_container  # Renders pages
])

if __name__ == "__main__":
    app.run(port = '8060',debug=False)
