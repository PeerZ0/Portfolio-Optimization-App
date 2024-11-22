# models/user.py
# User model, storing user data


class User:
    def __init__(self):
        self.data = {
            "age": None,
            "preferred_stocks": [],
            "sectors_to_avoid": [],
            "risk_tolerance": 5,
            "invest_in_penny_stocks": False,
            "max_equity_investment": 0,
            "min_equity_investment": 0,
            "existing_assets_info": [],
            "asset_expectations": []
        }
    
    def display_information(self):
        print("\nPortfolio Information Collected:")
        for key, value in self.data.items():
            print(f"{key}: {value}")
