# models/user.py
# User model, storing user data

class User:
    """
    User class to store and manage user-specific data for portfolio optimization.

    Attributes
    ----------
    data : dict
        A dictionary containing user preferences and constraints, including:
        - preferred_stocks : list of str
            A list of tickers the user prefers to include in their portfolio.
        - sectors_to_avoid : list of str
            A list of sectors that the user wishes to avoid investing in.
        - risk_tolerance : int
            The user's risk tolerance level on a scale from 1 to 10, where 1 is low risk and 10 is high risk.
            Defaults to 5 if not provided.
        - max_equity_investment : float, optional
            The maximum percentage of the total portfolio that the user is willing to invest in a single equity.
            Defaults to None until specified.
        - min_equity_investment : float, optional
            The minimum percentage of the total portfolio that the user wants to invest in a single equity.
            Defaults to None until specified.
    """
    def __init__(self):
        # Initialize user preferences and constraints in a dictionary
        self.data = {
            "preferred_stocks": [],  # List of stock tickers the user wants in their portfolio
            "available_stocks": [],  # List of stock tickers available for investment
            "sectors_to_avoid": [],  # List of sectors the user wishes to avoid investing in
            "risk_tolerance": 5,  # Risk tolerance level on a scale of 1 to 10, default is 5 (medium risk)
            "max_equity_investment": 5,  # Maximum allowable investment in a single equity (in percentage), default is None
            "min_equity_investment": 30,  # Minimum allowable investment in a single equity (in percentage), default is None
        }