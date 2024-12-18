# models/user.py
"""
User Model

This module implements the User class that manages user preferences and portfolio settings.
It provides a centralized way to store and access:
1. Portfolio preferences (preferred stocks, sectors to avoid)
2. Risk parameters (risk tolerance, maximum investment per equity)
3. Portfolio state (available stocks, current portfolio)
"""

import pandas as pd

class User:
    """
    User class to store and manage user-specific data for portfolio optimization.

    This class serves as a central repository for all user-related data including
    preferences, constraints, and the current portfolio state. It maintains consistency
    across the application by providing a single source of truth for user settings.

    Attributes
    ----------
    data : dict
        Dictionary containing user preferences and constraints:
        - preferred_stocks : list[str]
            Tickers that should always be included in optimization
        - available_stocks : list[str]
            All tickers available for portfolio construction
        - sectors_to_avoid : list[str]
            Sectors to exclude from optimization
        - risk_tolerance : int
            Risk level (1-10, default=3)
        - max_equity_investment : float
            Maximum allocation per stock (percentage, default=5)
    static_data : pd.DataFrame
        Reference data for all available stocks loaded from CSV
    portfolio : Portfolio, optional
        Current portfolio instance if one exists
    """
    def __init__(self):
        """Initialize a new User instance with default preferences."""
        # Initialize user preferences with default values
        self.data = {
            "preferred_stocks": [],     # Must-include stocks
            "available_stocks": [],     # All available stocks
            "sectors_to_avoid": [],     # Excluded sectors
            "risk_tolerance": 3,        # Default to conservative risk level
            "max_equity_investment": 5, # Default to 5% max per stock
        }
        
        # Load static reference data
        self.static_data = pd.read_csv("static/ticker_data.csv")
        
        # Portfolio will be initialized later
        self.portfolio = None