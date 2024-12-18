import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
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
                        min=1,
                        max=100,
                        className="form-control terminal-input",
                        placeholder="Enter value between 1-100"
                    ),
                    html.Small(
                        "Value must be between 1 and 100",
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

    # 3D Plot Section
    dbc.Row([
        dbc.Col([
            html.H5("Asset Universe", className="text-info text-center mt-4"),
            dcc.Graph(id="preferred-assets-plot", style={"height": "500px"})
        ], width=12)
    ], className="mt-4"),

    dcc.Store(id="user-store"),
    dcc.Location(id="url", refresh=True)
], fluid=True, className="py-5 terminal-container")


# Callbacks
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


@callback(
    Output("preferred-assets-plot", "figure"),
    Input("preferred-stocks", "value"),
    Input("avoid-sectors", "value"),
    Input("risk-slider", "value"),
    Input("max-investment", "value")
)
def update_3d_plot(preferred_stocks, avoided_sectors, risk_tolerance, max_investment):
    plot_data = {
        "preferred_stocks": preferred_stocks,
        "available_stocks": [],
        "sectors_to_avoid": avoided_sectors,
        "risk_tolerance": risk_tolerance,
        "max_equity_investment": max_investment,
    }

    # Fetch data for the preferred tickers
    def filter_by_user_preferences(df: pd.DataFrame, user) -> pd.DataFrame:
        if user["sectors_to_avoid"]:
            df = df[~df['sector'].isin(user["sectors_to_avoid"])]
        if user["risk_tolerance"]:
            max_risk = user["risk_tolerance"]
            df = df[df['overallRisk'] <= max_risk]
        return df

    def build_available_tickers(user):
        df = pd.read_csv('static/ticker_data.csv')
        required_columns = ['Ticker', 'sector', 'marketCap', 'currentPrice', 'overallRisk']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Missing required columns in ticker_data.csv")
        df['sector'] = df['sector'].fillna('Unknown')
        df['overallRisk'] = df['overallRisk'].fillna(5)
        preferred_stocks = set(user["preferred_stocks"])
        preferred_df = df[df['Ticker'].isin(preferred_stocks)]
        available_df = filter_by_user_preferences(df[~df['Ticker'].isin(preferred_stocks)], user)
        final_df = pd.concat([preferred_df, available_df])
        return final_df

    # Build dataset
    available_data = build_available_tickers(plot_data)
    tickers = list(available_data['Ticker'])
    sectors = available_data['sector']

    # Assign unique colors to sectors
    unique_sectors = sectors.unique()
    sector_color_map = {sector: i for i, sector in enumerate(unique_sectors)}
    colors = [sector_color_map[sector] for sector in sectors]

    # Generate random positions for the 3D scatter plot
    num_stocks = len(available_data)
    x = np.random.uniform(0, 100, num_stocks)
    y = np.random.uniform(0, 100, num_stocks)
    z = np.random.uniform(0, 100, num_stocks)

    # Create the 3D scatter plot
    fig = go.Figure(data=[go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode='markers',
        text=tickers,  # Ticker names for hover text
        hovertemplate='%{text}<extra></extra>',  # Show only the ticker name on hover
        marker=dict(
            size=10,
            color=colors,  # Assign colors based on sector
            colorscale='Viridis',  # Color scale for sectors
            opacity=0.8
        )
    )])

    # Apply dark theme
    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),
        scene=dict(
            xaxis_title='',
            yaxis_title='',
            zaxis_title='',
            xaxis=dict(backgroundcolor='black', gridcolor='gray', showbackground=True),
            yaxis=dict(backgroundcolor='black', gridcolor='gray', showbackground=True),
            zaxis=dict(backgroundcolor='black', gridcolor='gray', showbackground=True),
        ),
        paper_bgcolor='black',  # Background of the entire figure
        font=dict(color='white'),  # Text color
        coloraxis_colorbar=dict(
            title="Sector",
            tickvals=list(sector_color_map.values()),
            ticktext=list(sector_color_map.keys())
        )
    )
    return fig
