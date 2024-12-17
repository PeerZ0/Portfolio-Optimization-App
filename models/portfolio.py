#%%
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
    def __init__(self, user, min_weight: float = 0.0, start_date='2023-01-01', end_date=datetime.date.today()):
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
        self.weights_eq = self.equal_weight_portfolio()
        self.weights_min = self.min_variance_portfolio()
        self.weights_sharpe = self.max_sharpe_ratio_portfolio()


    def _get_data(self):
        """
        Fetch historical stock price data from Yahoo Finance.

        Returns
        -------
        pd.DataFrame
            DataFrame containing historical adjusted close prices of the assets.
        """
        data_list = []
        for ticker in self.tickers:
            try:
                # Fetch data for each ticker
                df = yf.download(ticker, self.start_date, self.end_date, progress=False)['Adj Close']
                data_list.append(df)
            except KeyError as e:
                print(f"Error fetching data for {ticker}: {e}")

        self.data_retrieval_success = True
        data = pd.concat(data_list, axis=1)
        data = data.sort_index()
        data = data.dropna(axis=1, how='all')  # Remove columns with all NaNs
        data.ffill(inplace=True)  # Forward-fill missing data

        for column in data.columns:
            # Drop columns with large missing data streaks
            max_nan_streak = (data[column].isna().groupby((~data[column].isna()).cumsum()).cumsum()).max()
            if max_nan_streak >= 4:
                data.drop(columns=[column], inplace=True)
            else:
                data[column].fillna(method='ffill', inplace=True)

        if pd.isna(data.iloc[0]).any() and len(data) > 1:
            data.iloc[0] = data.iloc[1]  # Fill the first row if NaN

        self.tickers = list(data.columns)
        return data

        
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


    def choose_best_return_portfolio(self, yearly_rebalance='no'):
        """
        Choose the portfolio with the highest return.

        Parameters
        ----------
        yearly_rebalance : str
            Whether to rebalance the portfolio annually ('yes' or 'no').

        Returns
        -------
        dict
            A dictionary containing the optimized weights for the portfolio with the highest return.
        """
        portfolios = {
            'min_variance': self.min_variance_portfolio(),
            'equal_weight': self.equal_weight_portfolio(),
            'max_sharpe': self.max_sharpe_ratio_portfolio(0.01)
        }
        
        best_portfolio = None
        best_return = -float('inf')

        for name, weights in portfolios.items():
            if yearly_rebalance == 'yes':
                cumulative_value = 1.0  # Starting with an initial wealth of 1
                rebalanced_weights = self.yearly_rebalance(weights)
                
                # Iteratively apply yearly returns
                for year, year_weights in rebalanced_weights.items():
                    yearly_returns = self.returns[self.returns.index.year == year]
                    
                    if yearly_returns.empty:
                        continue
                    
                    # Apply the weights to the returns for the given year
                    weighted_returns = yearly_returns.dot(pd.Series(year_weights))
                    
                    # Calculate the cumulative return for the year
                    cumulative_year_return = (1 + weighted_returns).prod() - 1
                    
                    # Update the overall portfolio value based on the year's return
                    cumulative_value *= (1 + cumulative_year_return)
                    
                total_return = cumulative_value - 1  # Calculate the overall return
            else:
                # No rebalancing: calculate return using original weights across the whole period
                weighted_returns = self.returns.dot(pd.Series(weights))
                total_return = (1 + weighted_returns).prod() - 1  # Final cumulative return

            if total_return > best_return:
                best_return = total_return
                best_portfolio = weights
        
        return best_portfolio
    

    def calculate_max_drawdowns(self, returns):
        """
        Calculate the maximum drawdown of a returns series.

        Parameters
        ----------
        returns : pd.Series
            The returns series.

        Returns
        -------
        float
            The maximum drawdown.
        """
        cumulative = (1 + returns).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        return drawdown.min()


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

        # Debug output (optional)
        print("Cumulative Portfolio Returns:", cumulative_returns.head())
        print("Cumulative S&P 500 Returns:", cumulative_sp500_returns.head())

        # Create the plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=cumulative_returns.index, y=cumulative_returns, mode='lines', name='Portfolio'))
        fig.add_trace(go.Scatter(x=cumulative_sp500_returns.index, y=cumulative_sp500_returns, mode='lines', name='S&P 500 Benchmark'))
        
        fig.update_layout(
            title='Cumulative Returns of Portfolio vs S&P 500',
            xaxis_title='Date',
            yaxis_title='Cumulative Return',
            template='plotly_white'
        )
        return fig

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
        
        # Calculate maximum drawdown
        max_drawdown = self.calculate_max_drawdowns(weighted_returns)
        
        # Create a summary dictionary
        summary_stats = {
            'Cumulative Return': round(cumulative_return, 3),
            'Annualized Return': round(annualized_return, 3),
            'Annualized Volatility': round(annualized_volatility, 3),
            'Sharpe Ratio': round(sharpe_ratio, 3),
            'Maximum Drawdown': round(max_drawdown, 3),
        }
        
        return summary_stats

    def get_summary_statistics_table(self, portfolio_weights, risk_free_rate=0.01):
        """
        Get a summary statistics table of the given portfolio.

        Parameters
        ----------
        portfolio_weights : dict
            A dictionary containing the weights of each ticker in the portfolio.
        risk_free_rate : float
            The risk-free rate used to calculate the Sharpe ratio.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing summary statistics of the portfolio.
        """
        summary_stats = self.get_summary_statistics(portfolio_weights, risk_free_rate)
        summary_df = pd.DataFrame(list(summary_stats.items()), columns=['Metric', 'Value'])
        return summary_df


    def plot_portfolio_allocation(self, portfolio_weights, selected_strategy):
            """
            Plot a pie chart showing the allocation of the given portfolio weights using Plotly.

            Parameters
            ----------
            portfolio_weights : dict
                A dictionary containing the weights of each ticker in the portfolio.
            selected_strategy : str
                The strategy used to generate the portfolio (min_variance, equal_weight, or max_sharpe).

            Returns
            -------
            plotly.graph_objects.Figure
                A pie chart figure showing the portfolio allocation.
            """
            labels = list(portfolio_weights.keys())
            values = list(portfolio_weights.values())

            if selected_strategy in ['min_variance', 'max_sharpe']:
                # Sort the allocation by weight
                sorted_allocation = pd.Series(portfolio_weights).sort_values(ascending=False)
                
                # Summarize all under 0.01 as 'Others'
                other_allocation = sorted_allocation[sorted_allocation < 0.01].sum()
                sorted_allocation = sorted_allocation[sorted_allocation >= 0.01]
                
                labels = list(sorted_allocation.index) + ['Others']
                values = list(sorted_allocation.values) + [other_allocation]
                                        
            fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
            fig.update_layout(title_text=f'Portfolio Allocation', template='plotly_white')

            return fig
    
    def create_weighted_sector_treemap(self, weights):
        """
        Generate a weighted treemap of sectors for the given tickers.

        Parameters
        ----------
        weights : dict
            A dictionary mapping tickers to their respective weights.

        Returns
        -------
        plotly.graph_objects.Figure
            A treemap figure showing sectors with their respective weights.
        """
        # Check if all tickers have corresponding weights
        if set(self.tickers) - set(weights.keys()):
            raise ValueError("All tickers must have corresponding weights in the weights dictionary.")

        sector_data_raw = pd.read_csv('static/ticker_data.csv')
        sector_data = []
        missing_tickers = []
        for ticker in self.tickers:  # Iterate over tickers
            try:
                # Get sector data for the ticker
                sector = sector_data_raw.loc[sector_data_raw['Ticker'] == ticker, 'industry'].values[0]
                weight = weights.get(ticker, 0)  # Get weight, default to 0 if not found

                # Append stock-level data
                sector_data.append({'Name': ticker, 'Parent': sector, 'Weight': weight})

            except Exception as e:
                print(f"Error fetching sector for {ticker}: {e}")
                missing_tickers.append(ticker)

        # Aggregate sector-level weights
        sector_weights = sector_data_raw.groupby('industry').apply(
            lambda x: sum(weights.get(ticker, 0) for ticker in x['Ticker'])
            ).reset_index(name='Weight')

        # Create the DataFrame with hierarchical structure
        df = pd.DataFrame(sector_data)

        # Aggregate weights by sector
        sector_weights = df.groupby('Parent')['Weight'].sum().reset_index()
        sector_weights["Name"] = sector_weights["Parent"]
        sector_weights["Parent"] = "World"

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

        # Extract hierarchy information
        labels = combined_df["Name"].tolist()
        parents = combined_df["Parent"].tolist()
        values = combined_df["Weight"].round(3).tolist()

        # Build the treemap using plotly.graph_objects
        fig = go.Figure(go.Treemap(
            labels=labels,     # Names of the nodes (stocks and sectors)
            parents=parents,   # Parent-child relationships
            values=values,     # Sizes (weights) of nodes
            textinfo="label+value+percent parent",  # Display node name, value, and % of parent
            root_color="lightgrey",
        ))

        # Update layout for clean visualization
        fig.update_layout(
            title="Sectors with Stocks Treemap",
            margin=dict(t=100, l=25, r=25, b=25)
        )
        fig.show()
        # Return the treemap figure
        return fig
    
    def create_weighted_sector_treemap2(self, weights):
        """
        Generate a weighted treemap of sectors for the given tickers.

        Parameters
        ----------
        weights : dict
            A dictionary mapping tickers to their respective weights.

        Returns
        -------
        plotly.graph_objects.Figure
            A treemap figure showing sectors with their respective weights.
        """
        # Check if all tickers have corresponding weights
        if set(self.tickers) - set(weights.keys()):
            raise ValueError("All tickers must have corresponding weights in the weights dictionary.")

        sector_data_raw = pd.read_csv('static/ticker_data.csv')
        sector_data = []

        # Extract sector and stock-level data
        for ticker in self.tickers:
            try:
                sector = sector_data_raw.loc[sector_data_raw['Ticker'] == ticker, 'industry'].values[0]
                weight = weights.get(ticker, 0)
                sector_data.append({'Name': ticker, 'Parent': sector, 'Weight': weight})
            except Exception as e:
                print(f"Error fetching sector for {ticker}: {e}")

        # Create DataFrame with stock-level data
        df = pd.DataFrame(sector_data)

        # Step 1: Calculate total weight for each sector
        sector_totals = df.groupby('Parent')['Weight'].sum().reset_index()
        sector_totals.rename(columns={'Weight': 'Total_Weight'}, inplace=True)

        # Step 2: Merge sector total weights into stock-level data
        df = df.merge(sector_totals, on='Parent', how='left')

        # Step 3: Scale stock weights proportionally to sum to 100% within each sector
        df['Normalized_Weight'] = df['Weight'] / df['Total_Weight'] * 100

        # Aggregate weights at the sector level
        sector_weights = df.groupby('Parent')['Total_Weight'].first().reset_index()
        sector_weights['Name'] = sector_weights['Parent']
        sector_weights['Parent'] = 'World'

        # Add sector-level data
        combined_df = pd.concat([
            pd.DataFrame(sector_weights),  # Sectors as parents
            df[['Name', 'Parent', 'Weight', 'Normalized_Weight']]  # Stocks as children
        ], ignore_index=True)

        # Extract hierarchy and text for display
        labels = combined_df['Name'].tolist()
        parents = combined_df['Parent'].tolist()
        values = combined_df['Weight'].tolist()
        custom_text = combined_df.apply(
            lambda row: f"Original: {row['Weight']:.3f}<br>Sector %: {row['Normalized_Weight']:.1f}%",
            axis=1
        ).tolist()

        # Build the treemap using plotly.graph_objects
        fig = go.Figure(go.Treemap(
            labels=labels,
            parents=parents,
            values=values,
            text=custom_text,  # Custom text with original and normalized weights
            textinfo="label+text",
            root_color="lightgrey"
        ))

        # Update layout for clean visualization
        fig.update_layout(
            title="Sectors with Stocks Treemap (Stocks sum to 100%, display original weight)",
            margin=dict(t=100, l=25, r=25, b=25)
        )
        return fig


    def plot_annualized_returns(self, portfolio_weights):
            """
            Plot a bar chart showing the contribution of each asset's annualized returns to the portfolio's total return.

            Parameters
            ----------
            portfolio_weights : dict
                A dictionary containing the weights of each ticker in the portfolio.

            Returns
            -------
            plotly.graph_objects.Figure
                A bar chart figure showing each asset's contribution to the portfolio return.
            """
            annualized_returns = self.mean_returns * 252
            labels = self.tickers

            # Contribution of each asset to the portfolio return
            contribution_to_portfolio = [portfolio_weights[ticker] * annualized_returns[ticker] for ticker in self.tickers]

            fig = go.Figure()
            fig.add_trace(go.Bar(x=labels, y=contribution_to_portfolio, name='Contribution to Portfolio Return'))

            fig.update_layout(
                title='Contribution of Each Asset to Portfolio Return',
                xaxis_title='Asset',
                yaxis_title='Contribution to Portfolio Return',
                template='plotly_white'
            )
            return fig

if __name__ == "__main__":
    from user import User
    user = User()
    user.data = {
            "preferred_stocks": [],  # List of stock tickers the user wants in their portfolio
            "available_stocks": ["AAPL", "MSFT", 'SW', 'TSCO', 'DHL.DE', 'BNR.DE', 'DB1.DE', 'AIZ', 'DRI', 'CMS', 'WM', 'HD', 'HUM', 'ENEL.MI', 'ENI.MI', 'TMO', 'CVX', 'QIA.DE', 'MTD', 'MTD', 'NDA-FI.HE', 'AD.AS', 'EIX', 'ETN', 'MUV2.DE'],  # List of stock tickers available for investment
            "sectors_to_avoid": [],  # List of sectors the user wishes to avoid investing in
            "risk_tolerance": 5,  # Risk tolerance level on a scale of 1 to 10, default is 5 (medium risk)
            "max_equity_investment": 30,  # Maximum allowable investment in a single equity (in percentage), default is 30%
        }
    # user.data = {"available_stocks": ["AAPL", "MSFT", 'SW', 'TSCO', 'DHL.DE', 'BNR.DE', 'DB1.DE', 'AIZ', 'DRI', 'CMS', 'WM', 'HD', 'HUM', 'ENEL.MI', 'ENI.MI', 'TMO', 'CVX', 'QIA.DE', 'MTD', 'MTD', 'NDA-FI.HE', 'AD.AS', 'EIX', 'ETN', 'MUV2.DE', 'PPL', 'SOON.SW', 'FRE.DE', 'EVRG', 'CS.PA', 'ZURN.SW', 'MMC', 'C', 'UNP', 'PNC', 'AIR.PA', 'MA', 'NI', 'ZAL.DE', 'XEL', 'AI.PA', 'RSG', 'URI', 'SLB', 'PCG', 'BBVA.MC', 'GD', 'OTIS']}  # List of stock tickers available for investment}
    port = Portfolio(user)
    weights = port.equal_weight_portfolio()
    port.create_weighted_sector_treemap(weights)


