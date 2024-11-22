import numpy as np
import pandas as pd
from scipy.optimize import minimize
import yfinance as yf
from models.user import User

class Portfolio:
    def __init__(self, tickers: list, start_date: str, end_date: str, min_weight: float = 0.0):
        """
        Initialize the MinVariancePortfolio with stock ticker data and calculate mean returns and covariance matrix.
        
        Parameters:
        tickers (list): A list of stock ticker symbols.
        start_date (str): The start date for fetching historical data in 'YYYY-MM-DD' format.
        end_date (str): The end date for fetching historical data in 'YYYY-MM-DD' format.
        """
        self.user = User()
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.data = self._get_data()
        self.returns = self.calculate_returns()
        self.mean_returns = self.returns.mean()
        self.cov_matrix = self.returns.cov()
        self.bounds = tuple((self.user.data['min_equity_investment'], self.user.data['max_equity_investment']) for _ in range(len(tickers)))
        self.constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}, {'type': 'ineq', 'fun': lambda x: np.sum(x) - len(self.tickers) * min_weight}]

    def _get_data(self):
        """
        Fetch historical stock price data from Yahoo Finance.
        
        Returns:
        pd.DataFrame: A DataFrame containing historical stock prices of the assets.
        """
        data = yf.download(self.tickers, start=self.start_date, end=self.end_date)['Adj Close']
        return data.dropna()

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


if __name__ == "__main__":
    cl = Portfolio(['AAPL', 'MSFT', 'GOOGL'], '2020-02-01', '2023-01-01', 0.2)
    print(cl.bounds)
