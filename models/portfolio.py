import numpy as np
import pandas as pd
from scipy.optimize import minimize
import yfinance as yf
import quantstats as qs
import datetime
#from models.user import User

class Portfolio:
    def __init__(self, tickers: list, min_weight: float = 0.0, start_date = '2020-01-01', end_date = datetime.date.today()):
        """
        Initialize the MinVariancePortfolio with stock ticker data and calculate mean returns and covariance matrix.
        
        Parameters:
        tickers (list): A list of stock ticker symbols.
        start_date (str): The start date for fetching historical data in 'YYYY-MM-DD' format.
        end_date (str): The end date for fetching historical data in 'YYYY-MM-DD' format.
        """
        #self.user = User()
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.data = self._get_data()
        self.returns = self.calculate_returns()
        self.mean_returns = self.returns.mean()
        self.cov_matrix = self.returns.cov()
        self.bounds = tuple((0,0.4) for _ in range(len(tickers)))
        #self.bounds = tuple((self.user.data['min_equity_investment'], self.user.data['max_equity_investment']) for _ in range(len(tickers)))
        self.constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}, {'type': 'ineq', 'fun': lambda x: np.sum(x) - len(self.tickers) * min_weight}]

    def _get_data(self):
        """
        Fetch historical stock price data from Yahoo Finance.
        
        Returns:
        pd.DataFrame: A DataFrame containing historical stock prices of the assets.
        """
        data_dict = {}
        for ticker in self.tickers:
            try:
                df = yf.download(ticker, self.start_date, self.end_date)['Adj Close']
                data_dict[ticker] = df
            except KeyError as e:
                print("1")
        data = pd.DataFrame(data_dict)
        data = data.sort_index()
        data = data.dropna(axis = 1, how = 'all')
        data = data.ffill()
        for column in data.columns:
            max_nan_streak = (data[column].isna().groupby(data[column].notna().cumsum()).cumsum()).max()
            if max_nan_streak >= 4:
                data = data.drop(columns=[column])
            else:
                data[column] = data[column].fillna(method='ffill')
        if pd.isna(data[column].iloc[0]) and len(data[column]) > 1:
            data[column].iloc[0] = data[column].iloc[1]
        return data
        
    

    def calculate_returns(self):
        """
        Calculate daily returns from stock price data.
        
        Returns:
        pd.DataFrame: A DataFrame containing daily returns of the assets.
        """
        return self.data.pct_change().dropna()

    def min_variance_portfolio(self):
        """
        Find the portfolio with the minimum possible variance.
        
        Returns:
        dict: A dictionary containing the optimized weights for each ticker.
        """
        num_assets = len(self.tickers)
        initial_weights = np.ones(num_assets) / num_assets
        #constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

        def portfolio_volatility(weights):
            return np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))

        result = minimize(portfolio_volatility, initial_weights, method='SLSQP', bounds=self.bounds, constraints=self.constraints)
        return dict(zip(self.tickers, result.x))

    def equal_weight_portfolio(self):
        """
        Create an equally weighted portfolio.
        
        Returns:
        dict: A dictionary containing equal weights for each ticker.
        """
        num_assets = len(self.tickers)
        weights = np.ones(num_assets) / num_assets
        return dict(zip(self.tickers, weights))

    def max_sharpe_ratio_portfolio(self, risk_free_rate=0.01):
        """
        Find the portfolio that maximizes the Sharpe ratio.
        
        Parameters:
        risk_free_rate (float): The risk-free rate used to calculate the Sharpe ratio.
        
        Returns:
        dict: A dictionary containing the optimized weights for each ticker.
        """
        num_assets = len(self.tickers)
        initial_weights = np.ones(num_assets) / num_assets
        #constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

        def negative_sharpe_ratio(weights):
            portfolio_return = np.sum(weights * self.mean_returns)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
            sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
            return -sharpe_ratio

        result = minimize(negative_sharpe_ratio, initial_weights, method='SLSQP', bounds=self.bounds, constraints=self.constraints)
        return dict(zip(self.tickers, result.x))

    def black_litterman_model(self, P, Q, omega=None, tau=0.025):
        """
        Black-Litterman model for portfolio optimization.
        
        Parameters:
        P (np.array): The matrix representing the views.
        Q (np.array): The vector representing the expected returns based on the views.
        omega (np.array or None): The uncertainty matrix for the views. If None, defaults to a diagonal matrix.
        tau (float): Scalar representing the uncertainty of the prior.
        
        Returns:
        pd.Series: The adjusted expected returns.
        """
        # Calculate the equilibrium excess returns (pi)
        pi = tau * np.dot(self.cov_matrix, self.mean_returns)
        
        # If omega is not provided, use a diagonal matrix with small uncertainty
        if omega is None:
            omega = np.diag(np.diag(np.dot(np.dot(P, self.cov_matrix), P.T)))
        
        # Calculate Black-Litterman expected returns
        M_inverse = np.linalg.inv(np.dot(np.dot(P, tau * self.cov_matrix), P.T) + omega)
        adjusted_returns = self.mean_returns + np.dot(np.dot(tau * self.cov_matrix, P.T), np.dot(M_inverse, (Q - np.dot(P, pi))))
        
        return pd.Series(adjusted_returns, index=self.tickers)

    def choose_best_sharpe_portfolio(self, risk_free_rate=0.01):
        """
        Choose the portfolio with the highest Sharpe ratio.
        
        Parameters:
        risk_free_rate (float): The risk-free rate used to calculate the Sharpe ratio.
        
        Returns:
        dict: A dictionary containing the optimized weights for the portfolio with the highest Sharpe ratio.
        """
        portfolios = {
            'min_variance': self.min_variance_portfolio(),
            'equal_weight': self.equal_weight_portfolio(),
            'max_sharpe': self.max_sharpe_ratio_portfolio(risk_free_rate)
        }
        
        best_sharpe = -np.inf
        best_portfolio = None

        for name, weights in portfolios.items():
            weighted_returns = self.returns.dot(pd.Series(weights))
            sharpe_ratio = qs.stats.sharpe(weighted_returns, rf=risk_free_rate)
            if sharpe_ratio > best_sharpe:
                best_sharpe = sharpe_ratio
                best_portfolio = weights

        return best_portfolio

    def calculate_max_drawdowns(self, returns):
        """
        Calculate the maximum drawdown of a returns series.
        
        Parameters:
        returns (pd.Series): The returns series.
        
        Returns:
        float: The maximum drawdown.
        """
        cumulative = (1 + returns).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        return drawdown.min()

    def plot_full_performance(self, returns, weights, benchmark=None, figsize=(10, 6)):
        """
        Plot the cumulative returns, drawdown, and comparison with benchmark (if provided).
        
        Parameters:
        returns (pd.Series): The portfolio returns series.
        benchmark (pd.Series or None): Benchmark returns for comparison.
        figsize (tuple): Figure size for plots.
        """
        import matplotlib.pyplot as plt

        cumulative_returns = (1 + returns).cumprod()
        peak = cumulative_returns.cummax()
        drawdown = (cumulative_returns - peak) / peak

        fig, ax = plt.subplots(3, 1, figsize=figsize)
        
        # Plot cumulative returns
        ax[0].plot(cumulative_returns, label='Portfolio Cumulative Returns', color='blue')
        if benchmark is not None:
            cumulative_benchmark = (1 + benchmark).cumprod()
            ax[0].plot(cumulative_benchmark, label='Benchmark Cumulative Returns', color='green')
        ax[0].set_title('Cumulative Returns')
        ax[0].set_ylabel('Cumulative Value')
        ax[0].legend()
        
        # Plot drawdown
        ax[1].plot(drawdown, label='Drawdown', color='red')
        ax[1].set_title('Drawdown')
        ax[1].set_ylabel('Drawdown')
        ax[1].legend()

        # Plot returns comparison if benchmark is provided
        if benchmark is not None:
            ax[2].plot(returns.index, returns, label='Portfolio Returns', color='blue')
            ax[2].plot(benchmark.index, benchmark, label='Benchmark Returns', color='green')
            ax[2].set_title('Portfolio vs. Benchmark Returns')
            ax[2].set_ylabel('Returns')
            ax[2].legend()

        plt.tight_layout()
        plt.show()
        weighted_returns = self.returns.dot(pd.Series(weights))
        weighted_returns.name = 'Portfolio'
        
        # Calculate performance metrics
        total_return = (1 + weighted_returns).prod() - 1
        annualized_return = weighted_returns.mean() * 252
        annualized_volatility = weighted_returns.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / annualized_volatility
        max_drawdown = self.calculate_max_drawdowns(weighted_returns)
        
        print("[Performance Metrics]")
        print(f"Total Return: {total_return:.2%}")
        print(f"Annualized Return: {annualized_return:.2%}")
        print(f"Annualized Volatility: {annualized_volatility:.2%}")
        print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"Max Drawdown: {max_drawdown:.2%}")

        # Display worst 5 drawdowns
        print("[Worst 5 Drawdowns]")
        drawdowns = self.calculate_max_drawdowns(weighted_returns)
        worst_drawdowns = drawdowns.sort_values(by='Drawdown', ascending=True).head(5)
        if worst_drawdowns.empty:
            print("(no drawdowns)")
        else:
            print(worst_drawdowns)

        # Plot performance
        print("[Strategy Visualization]")
        self.plot_performance(weighted_returns)


