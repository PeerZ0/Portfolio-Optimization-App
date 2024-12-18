# models/portfolio.py
"""
Portfolio Optimization Class

This module implements a Portfolio class that fetches historical stock data from Yahoo Finance, and
calculates optimal portfolio weights using different strategies such as:
1. Minimum variance
2. Equal weight
3. Maximum Sharpe ratio
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import yfinance as yf
import datetime
import plotly.graph_objs as go

class Portfolio:
    def __init__(self, user, min_weight: float = 0.0, start_date='2022-01-01', end_date=datetime.date.today()):
        """
        Initialize the Portfolio with historical stock data and calculate statistics.

        Parameters
        ----------
        user : object
            User data object containing available stock tickers and investment limits.
        min_weight : float, optional
            Minimum weight for each stock in the portfolio, by default 0.0.
        start_date : str, optional
            Start date for historical data in 'YYYY-MM-DD' format, by default '2023-01-01'.
        end_date : datetime.date, optional
            End date for historical data, by default today's date.
        """
        self.tickers = set(user.data['available_stocks'])
        self.start_date = start_date
        self.end_date = end_date
        self.data_retrieval_success = False
        self.data = self._get_data()
        self.returns = self.calculate_returns()
        self.mean_returns = self.returns.mean()
        self.cov_matrix = self.returns.cov()
        self.bounds = tuple((0, user.data['max_equity_investment'] / 100) for _ in range(len(self.tickers)))
        self.constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
            {'type': 'ineq', 'fun': lambda x: np.sum(x) - len(self.tickers) * min_weight}
        ]
        self.sp500 = yf.download('^GSPC', start=start_date, end=end_date)['Adj Close']
        self.sp500_returns = self.sp500.pct_change().dropna()
        self.weights_eq = self.equal_weight_portfolio()
        self.weights_min = self.min_variance_portfolio()
        self.weights_sharpe = self.max_sharpe_ratio_portfolio()
        self.plot_config = {
            "template": "plotly_dark",
            "paper_bgcolor": "#000000",
            "plot_bgcolor": "#000000",
            "font": dict(
                family="Roboto Mono",
                color="#FFFFFF"
            ),
            "title_font_color": "#FF8000"
        }

    def _apply_theme(self, fig):
        """Apply terminal theme to plot"""
        fig.update_layout(
            **self.plot_config,
            margin=dict(t=50, l=25, r=25, b=25)
        )
        return fig

    def _get_data(self):
        """
        Fetch historical stock price data from Yahoo Finance.

        Returns
        -------
        pd.DataFrame
            DataFrame containing historical adjusted close prices of the assets.
        """
        data_list = []  # List to store individual stock data
        for ticker in self.tickers:
            try:
                # Fetch Adjusted Close price data for the ticker
                df = yf.download(ticker, self.start_date, self.end_date, progress=False)['Adj Close']
                data_list.append(df)
            except KeyError as e:
                # Skip tickers with issues during data retrieval
                continue  

        self.data_retrieval_success = True  # Flag indicating successful data retrieval

        # Combine data for all tickers into a single DataFrame
        data = pd.concat(data_list, axis=1)
        data = data.sort_index()  # Ensure data is sorted by date
        data = data.dropna(axis=1, how='all')  # Remove tickers with no valid data
        data.ffill(inplace=True)  # Forward-fill missing data to ensure continuity

        # Check for and handle tickers with large missing data streaks
        for column in data.columns:
            max_nan_streak = (data[column].isna().groupby((~data[column].isna()).cumsum()).cumsum()).max()
            if max_nan_streak >= 4:  # Threshold for dropping columns with many consecutive NaNs
                data.drop(columns=[column], inplace=True)
            else:
                # Forward-fill remaining missing values within acceptable limits
                data[column].fillna(method='ffill', inplace=True)

        # Fill the first row if NaN (edge case)
        if pd.isna(data.iloc[0]).any() and len(data) > 1:
            data.iloc[0] = data.iloc[1]  # Use the second row to fill the first

        self.tickers = list(data.columns)  # Update tickers list to include only valid ones
        
        return data  # Return the cleaned DataFrame

        
    def calculate_returns(self):
        """
        Calculate daily returns from stock price data.

        Returns
        -------
        pd.DataFrame
            DataFrame containing daily returns of the assets.
        """
        return self.data.pct_change().dropna()

    def min_variance_portfolio(self):
        """
        Find the portfolio with the minimum possible variance.

        Returns
        -------
        dict
            Dictionary containing the optimized weights for each ticker.
        """
        num_assets = len(self.tickers)
        initial_weights = np.ones(num_assets) / num_assets

        def portfolio_volatility(weights):
            return np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))

        # Minimize portfolio volatility
        result = minimize(portfolio_volatility, initial_weights, method='SLSQP', bounds=self.bounds, constraints=self.constraints)
        return dict(zip(self.tickers, result.x))

    def equal_weight_portfolio(self):
        """
        Create an equally weighted portfolio.

        Returns
        -------
        dict
            Dictionary containing equal weights for each ticker.
        """
        num_assets = len(self.tickers)
        weights = np.ones(num_assets) / num_assets
        return dict(zip(self.tickers, weights))

    def max_sharpe_ratio_portfolio(self, risk_free_rate=0.01):
        """
        Find the portfolio that maximizes the Sharpe ratio.

        Parameters
        ----------
        risk_free_rate : float, optional
            The risk-free rate used to calculate the Sharpe ratio, by default 0.01.

        Returns
        -------
        dict
            Dictionary containing the optimized weights for each ticker.
        """

        num_assets = len(self.tickers)
        initial_weights = np.ones(num_assets) / num_assets

        def negative_sharpe_ratio(weights):
            portfolio_return = np.sum(weights * self.mean_returns)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
            sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
            return -sharpe_ratio

        # Maximize Sharpe ratio (minimize negative Sharpe)
        result = minimize(negative_sharpe_ratio, initial_weights, method='SLSQP', bounds=self.bounds, constraints=self.constraints)
        return dict(zip(self.tickers, result.x))

    def plot_cumulative_returns(self, portfolio_weights):
        """
        Plot cumulative returns of the given portfolio weights using Plotly.

        Parameters
        ----------
        portfolio_weights : dict
            Dictionary containing the weights of each ticker in the portfolio.
        
        Returns
        -------
        plotly.graph_objects.Figure
            Plotly figure showing the cumulative returns.
        """
        
        # Load S&P 500 returns using yfinance
        sp500_returns = self.sp500.pct_change().dropna()
        self.sp500_returns = sp500_returns

        # Calculate portfolio weighted returns
        weighted_returns = self.returns.dot(pd.Series(portfolio_weights))

        # Align dates
        aligned_data = pd.concat([weighted_returns, sp500_returns], axis=1, join="inner")
        aligned_data.columns = ["Portfolio", "S&P 500"]

        # Calculate cumulative returns
        cumulative_returns = (1 + aligned_data["Portfolio"]).cumprod()
        cumulative_sp500_returns = (1 + aligned_data["S&P 500"]).cumprod()

        # Create the plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=cumulative_returns.index, y=cumulative_returns, mode='lines', name='Portfolio'))
        fig.add_trace(go.Scatter(x=cumulative_sp500_returns.index, y=cumulative_sp500_returns, mode='lines', name='S&P 500 Benchmark'))
        
        fig.update_layout(
            title=dict(
                text="CUMULATIVE RETURNS VS BENCHMARK",
                font=dict(size=24)
            ),
            xaxis_title='Date',
            yaxis_title='Cumulative Return',
            template='plotly_white',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        return self._apply_theme(fig)

    def get_summary_statistics(self, portfolio_weights, risk_free_rate=0.01):
        """
        Get summary statistics of the given portfolio.

        Parameters
        ----------
        portfolio_weights : dict
            Dictionary containing the weights of each ticker in the portfolio.
        risk_free_rate : float, optional
            The risk-free rate used to calculate the Sharpe ratio, by default 0.01.

        Returns
        -------
        dict
            Dictionary containing summary statistics of the portfolio.
        """
        # Calculate portfolio returns
        weighted_returns = self.returns.dot(pd.Series(portfolio_weights))
        
        # Calculate cumulative return
        cumulative_return = (1 + weighted_returns).prod() - 1
        
        # Calculate annualized return
        annualized_return = weighted_returns.mean() * 252
        
        # Calculate annualized volatility
        annualized_volatility = weighted_returns.std() * np.sqrt(252)
        
        # Calculate Sharpe ratio
        sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility
                
        # Create a summary dictionary
        summary_stats = {
            'Cumulative Return': round(cumulative_return, 3),
            'Annualized Return': round(annualized_return, 3),
            'Annualized Volatility': round(annualized_volatility, 3),
            'Sharpe Ratio': round(sharpe_ratio, 3),
        }
        
        return summary_stats

    def _format_percentage(self, value):
        """Format number as percentage string"""
        return f"{value * 100:.2f}%"
    
    def _get_date_range_str(self):
        """Get formatted date range string"""
        start_date = self.returns.index[0].strftime('%Y-%m-%d')
        end_date = self.returns.index[-1].strftime('%Y-%m-%d')
        return f"{start_date} to {end_date}"

    def get_summary_statistics_table(self, weights):
        """Calculate and format summary statistics for the portfolio"""
        # Calculate portfolio returns
        portfolio_returns = np.sum(self.returns * pd.Series(weights), axis=1)
        benchmark_returns = self.sp500_returns
        
        # Align portfolio and benchmark returns
        aligned_data = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
        portfolio_returns = aligned_data.iloc[:, 0]
        benchmark_returns = aligned_data.iloc[:, 1]
        
        # Calculate metrics for both portfolio and benchmark
        def calculate_metrics(returns):
            cum_return = (1 + returns).prod() - 1
            daily_ret = returns.mean()
            monthly_ret = (1 + daily_ret)**21 - 1
            yearly_ret = (1 + daily_ret)**252 - 1
            vol = returns.std() * np.sqrt(252)
            
            # Calculate CAGR
            total_years = len(returns) / 252  # Convert trading days to years
            cagr = (1 + cum_return)**(1/total_years) - 1
            
            # Calculate downside deviation
            neg_returns = returns[returns < 0]
            down_dev = np.sqrt(np.mean(neg_returns**2)) * np.sqrt(252)
            
            # Calculate additional statistics
            sharpe = yearly_ret / vol if vol != 0 else 0
            sortino = yearly_ret / down_dev if down_dev != 0 else 0
            skew = returns.skew()
            kurt = returns.kurtosis()
            
            return {
                'cum_return': cum_return,
                'cagr': cagr,
                'daily_ret': daily_ret,
                'monthly_ret': monthly_ret,
                'yearly_ret': yearly_ret,
                'vol': vol,
                'sharpe': sharpe,
                'sortino': sortino,
                'skew': skew,
                'kurt': kurt
            }

        # Calculate metrics
        port_metrics = calculate_metrics(portfolio_returns)
        bench_metrics = calculate_metrics(benchmark_returns)
        
        # Calculate Beta
        covariance = np.cov(portfolio_returns, benchmark_returns)[0][1]
        market_variance = np.var(benchmark_returns)
        beta = covariance / market_variance if market_variance != 0 else 0

        data = {
            'Metric': [
                'Period',
                'Cumulative Return',
                'CAGR',
                'Expected Daily Return',
                'Expected Monthly Return',
                'Expected Yearly Return',
                'Annualized Volatility',
                'Beta',
                'Sharpe Ratio',
                'Sortino Ratio',
                'Skewness',
                'Kurtosis'
            ],
            'Portfolio': [
                self._get_date_range_str(),
                self._format_percentage(port_metrics['cum_return']),
                self._format_percentage(port_metrics['cagr']),
                self._format_percentage(port_metrics['daily_ret']),
                self._format_percentage(port_metrics['monthly_ret']),
                self._format_percentage(port_metrics['yearly_ret']),
                self._format_percentage(port_metrics['vol']),
                f"{beta:.2f}",
                f"{port_metrics['sharpe']:.2f}",
                f"{port_metrics['sortino']:.2f}",
                f"{port_metrics['skew']:.2f}",
                f"{port_metrics['kurt']:.2f}"
            ],
            'S&P 500': [
                self._get_date_range_str(),
                self._format_percentage(bench_metrics['cum_return']),
                self._format_percentage(bench_metrics['cagr']),
                self._format_percentage(bench_metrics['daily_ret']),
                self._format_percentage(bench_metrics['monthly_ret']),
                self._format_percentage(bench_metrics['yearly_ret']),
                self._format_percentage(bench_metrics['vol']),
                "1.00",  # Beta of market is always 1
                f"{bench_metrics['sharpe']:.2f}",
                f"{bench_metrics['sortino']:.2f}",
                f"{bench_metrics['skew']:.2f}",
                f"{bench_metrics['kurt']:.2f}"
            ]
        }
        return pd.DataFrame(data)

    def create_weighted_sector_treemap(self, weights):
        """Generate a weighted treemap of sectors for the given tickers."""
        # Check if all tickers have corresponding weights
        if set(self.tickers) - set(weights.keys()):
            raise ValueError("All tickers must have corresponding weights in the weights dictionary.")

        # Load sector data
        sector_data_raw = pd.read_csv('static/ticker_data.csv')
        sector_data = []
        missing_tickers = []

        for ticker in self.tickers:  # Iterate over tickers
            try:
                # Get sector data for the ticker
                sector = sector_data_raw.loc[sector_data_raw['Ticker'] == ticker, 'sector'].values[0]
                weight = weights.get(ticker, 0)  # Get weight, default to 0 if not found

                # Append stock-level data
                if weight >= 0.0001:  # Exclude weights smaller than 0.01%
                    sector_data.append({'Name': ticker, 'Parent': sector, 'Weight': weight})

            except Exception as e:
                print(f"Error fetching sector for {ticker}: {e}")
                missing_tickers.append(ticker)

        # Convert to DataFrame
        df = pd.DataFrame(sector_data)

        # Aggregate sector-level weights
        sector_weights = df.groupby('Parent')['Weight'].sum().reset_index()
        sector_weights = sector_weights[sector_weights['Weight'] >= 0.0001]  # Filter sectors
        sector_weights["Name"] = sector_weights["Parent"]
        sector_weights["Parent"] = "Portfolio"

        # Normalize stock weights to sum to 100% within each sector
        df['Normalized_Weight'] = df.groupby('Parent')['Weight'].transform(lambda x: 100 * x / x.sum())

        # Replace the 'Weight' column with normalized weights for the stocks
        df['Weight_n'] = df['Normalized_Weight']
        df.drop(columns=['Normalized_Weight'], inplace=True)

        # Combine sector-level and stock-level data
        combined_df = pd.concat([
            sector_weights,  # Sectors
            df  # Stocks
        ], ignore_index=True)

        # Filter combined_df to exclude weights < 0.01%
        combined_df = combined_df[combined_df['Weight'] >= 0.0001]

        # Create custom text with more detailed information and bold sector names
        def format_text(row):
            if pd.isna(row['Weight_n']):  # Sector level
                return f"<b>{row['Name']}</b><br>Sector Weight: {row['Weight']*100:.2f}%"
            else:  # Stock level
                return f"{row['Name']}<br>Portfolio Weight: {row['Weight']*100:.2f}%<br>Sector Weight: {row['Weight_n']:.1f}%"

        # Generate Treemap with updated styling and information
        fig = go.Figure(go.Treemap(
            labels=combined_df['Name'],
            parents=combined_df['Parent'],
            values=combined_df['Weight'],
            text=combined_df.apply(format_text, axis=1),
            textinfo="text",
            hovertemplate="<b>%{label}</b><br>" +
                        "Portfolio Weight: %{value:.2%}<br>" +
                        "<extra></extra>",
            marker=dict(
                colors=combined_df['Weight'],
                colorscale=[
                    [0, '#4d4d4d'],    # Dark grey for small weights
                    [0.5, '#FF8000'],   # Orange for medium weights
                    [1, '#ffd700']      # Gold for large weights
                ],
                showscale=True,
                colorbar=dict(
                    title="Weight %",
                    tickformat=".1%",
                    thickness=15,
                    len=0.85,
                    bgcolor='rgba(0,0,0,0)',
                    tickfont=dict(color='#FFFFFF'),
                    titlefont=dict(color='#FFFFFF')
                )
            ),
            root_color="rgba(0,0,0,0)",
            maxdepth=2
        ))

        # Update layout with terminal theme
        fig.update_layout(
            title=dict(
                text="SECTOR AND STOCK ALLOCATION",
                font=dict(size=24)
            ),
            margin=dict(t=50, l=25, r=25, b=25),
            treemapcolorway=['#FF8000'],  # Use the terminal orange color
            **self.plot_config
        )

        return fig

    def plot_annualized_returns(self, portfolio_weights):
        """
        Plot a bar chart showing both the annualized returns and weighted contributions of each asset.

        Parameters
        ----------
        portfolio_weights : dict
            A dictionary containing the weights of each ticker in the portfolio.

        Returns
        -------
        plotly.graph_objects.Figure
            A bar chart figure showing asset returns and contributions.
        """
        # Calculate annualized returns for each asset
        annualized_returns = self.mean_returns * 252
        
        # Calculate weighted contribution for each asset
        contributions = {ticker: weights * annualized_returns[ticker] 
                       for ticker, weights in portfolio_weights.items()}
        
        # Create DataFrame for plotting
        df = pd.DataFrame({
            'Ticker': list(portfolio_weights.keys()),
            'Weight': list(portfolio_weights.values()),
            'Return': [annualized_returns[ticker] for ticker in portfolio_weights.keys()],
            'Contribution': list(contributions.values())
        })
        
        # Sort by contribution
        df = df.sort_values('Contribution', ascending=True)
        
        # Create the plot
        fig = go.Figure()
        
        # Add bars for annualized returns
        fig.add_trace(go.Bar(
            x=df['Return'],
            y=df['Ticker'],
            name='Annualized Return',
            orientation='h',
            marker_color='#404040',
            text=[f"{x:.1%}" for x in df['Return']],
            textposition='auto',
        ))
        
        # Add bars for weighted contributions
        fig.add_trace(go.Bar(
            x=df['Contribution'],
            y=df['Ticker'],
            name='Portfolio Contribution',
            orientation='h',
            marker_color='#FF8000',
            text=[f"{x:.1%}" for x in df['Contribution']],
            textposition='auto',
        ))

        # Update layout
        fig.update_layout(
            title=dict(
                text="ASSET RETURNS AND PORTFOLIO CONTRIBUTIONS",
                font=dict(size=24)
            ),
            height=800,  # Make only this plot taller
            xaxis_title='Return',
            yaxis_title='Asset',
            xaxis=dict(
                tickformat='.1%',
                showgrid=True,
                gridcolor='#333333'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#333333'
            ),
            barmode='overlay',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return self._apply_theme(fig)

    def plot_monthly_returns_distribution(self, portfolio_weights):
        """
        Plot a bar chart showing the distribution of monthly returns.

        Parameters
        ----------
        portfolio_weights : dict
            Dictionary containing the weights of each ticker in the portfolio.

        Returns
        -------
        plotly.graph_objects.Figure
            Bar chart showing monthly returns distribution.
        """
        # Calculate portfolio daily returns
        portfolio_returns = self.returns.dot(pd.Series(portfolio_weights))
        
        # Convert to monthly returns
        monthly_returns = (portfolio_returns + 1).resample('M').prod() - 1
        
        # Create histogram using go.Bar
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly_returns.index.strftime('%Y-%m'),
            y=monthly_returns,
            marker_color=['#FF8000' if x >= 0 else '#FF4444' for x in monthly_returns],
            name='Monthly Returns'
        ))

        fig.update_layout(
            title=dict(
                text="MONTHLY RETURNS DISTRIBUTION TIMESERIES",
                font=dict(size=24)
            ),
            xaxis_title='Month',
            yaxis_title='Return',
            xaxis=dict(
                tickangle=45,
                showgrid=True,
                gridcolor='#333333'
            ),
            yaxis=dict(
                tickformat='.1%',
                showgrid=True,
                gridcolor='#333333'
            ),
            bargap=0.1
        )
        
        return self._apply_theme(fig)

    def plot_daily_returns_series(self, portfolio_weights):
        """
        Plot a time series of daily returns.

        Parameters
        ----------
        portfolio_weights : dict
            Dictionary containing the weights of each ticker in the portfolio.

        Returns
        -------
        plotly.graph_objects.Figure
            Line plot showing daily returns over time.
        """
        # Calculate portfolio daily returns
        portfolio_returns = self.returns.dot(pd.Series(portfolio_weights))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=portfolio_returns.index,
            y=portfolio_returns,
            mode='lines',
            name='Daily Returns',
            line=dict(color='#FF8000', width=1)
        ))

        # Add a horizontal line at y=0
        fig.add_hline(
            y=0, 
            line_dash="dash", 
            line_color="#FFFFFF",
            opacity=0.5
        )

        fig.update_layout(
            title=dict(
                text="DAILY RETURNS TIME SERIES",
                font=dict(size=24)
            ),
            xaxis_title='Date',
            yaxis_title='Return',
            xaxis=dict(
                showgrid=True,
                gridcolor='#333333'
            ),
            yaxis=dict(
                tickformat='.1%',
                showgrid=True,
                gridcolor='#333333'
            ),
            showlegend=False
        )
        
        return self._apply_theme(fig)

    def plot_monthly_returns_histogram(self, portfolio_weights):
        """
        Plot a histogram with density curve of monthly returns distribution.

        Parameters
        ----------
        portfolio_weights : dict
            Dictionary containing the weights of each ticker in the portfolio.

        Returns
        -------
        plotly.graph_objects.Figure
            Histogram with density plot of monthly returns distribution.
        """
        # Calculate portfolio daily returns
        portfolio_returns = self.returns.dot(pd.Series(portfolio_weights))
        
        # Convert to monthly returns
        monthly_returns = (portfolio_returns + 1).resample('M').prod() - 1
        
        # Create histogram
        fig = go.Figure()
        
        # Add histogram
        fig.add_trace(go.Histogram(
            x=monthly_returns,
            name='Monthly Returns',
            nbinsx=30,
            histnorm='probability density',
            marker_color='#FF8000',
            opacity=0.7
        ))
        
        # Add density curve using kernel density estimation
        import numpy as np
        from scipy import stats
        
        kde = stats.gaussian_kde(monthly_returns)
        x_range = np.linspace(monthly_returns.min(), monthly_returns.max(), 100)
        y_range = kde(x_range)
        
        fig.add_trace(go.Scatter(
            x=x_range,
            y=y_range,
            mode='lines',
            name='Density',
            line=dict(color='#FFFFFF', width=2)
        ))

        fig.update_layout(
            title=dict(
                text="MONTHLY RETURNS DISTRIBUTION HISTOGRAM",
                font=dict(size=24)
            ),
            xaxis_title='Monthly Return',
            yaxis_title='Density',
            xaxis=dict(
                tickformat='.1%',
                showgrid=True,
                gridcolor='#333333'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#333333'
            ),
            bargap=0.1,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return self._apply_theme(fig)

    def plot_rolling_volatility(self, portfolio_weights):
        """
        Plot rolling 3-month volatility of the portfolio compared to the S&P 500.

        Parameters
        ----------
        portfolio_weights : dict
            Dictionary containing the weights of each ticker in the portfolio.

        Returns
        -------
        plotly.graph_objects.Figure
            Line plot showing rolling volatility comparison.
        """
        # Calculate portfolio daily returns
        portfolio_returns = self.returns.dot(pd.Series(portfolio_weights))
        
        # Align portfolio and benchmark returns
        aligned_data = pd.concat([portfolio_returns, self.sp500_returns], axis=1).dropna()
        portfolio_returns = aligned_data.iloc[:, 0]
        benchmark_returns = aligned_data.iloc[:, 1]
        
        # Calculate rolling volatilities (63 trading days ≈ 3 months)
        portfolio_vol = portfolio_returns.rolling(window=63).std() * np.sqrt(252)
        benchmark_vol = benchmark_returns.rolling(window=63).std() * np.sqrt(252)

        # Create the plot
        fig = go.Figure()
        
        # Add portfolio volatility line
        fig.add_trace(go.Scatter(
            x=portfolio_vol.index,
            y=portfolio_vol,
            mode='lines',
            name='Portfolio Volatility',
            line=dict(color='#FF8000', width=2)
        ))
        
        # Add benchmark volatility line
        fig.add_trace(go.Scatter(
            x=benchmark_vol.index,
            y=benchmark_vol,
            mode='lines',
            name='S&P 500 Volatility',
            line=dict(color='#FFFFFF', width=2, dash='dash')
        ))

        fig.update_layout(
            title=dict(
                text="ROLLING 3-MONTH VOLATILITY VS BENCHMARK",
                font=dict(size=24)
            ),
            xaxis_title='Date',
            yaxis_title='Annualized Volatility',
            xaxis=dict(
                showgrid=True,
                gridcolor='#333333'
            ),
            yaxis=dict(
                tickformat='.1%',
                showgrid=True,
                gridcolor='#333333'
            ),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return self._apply_theme(fig)