import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import webbrowser

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dcc.Location(id="url", refresh=True),
    dash.page_container
])

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:8060/")
    app.run(port = '8060',debug=False)
