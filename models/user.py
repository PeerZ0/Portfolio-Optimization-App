# models/user.py
# User model, storing user data


class User:
    def __init__(self):
        self.data = {
            "new_portfolio": None,
            "age": None,
            "investment_style": None,
            "preferred_stocks": [],
            "interested_sectors": [],
            "sectors_to_avoid": [],
            "geographical_preference": None,
            "invest_in_crypto": {
                "invest": False,
                "percentage": 0
            },
            "invest_in_penny_stocks": False,
            "number_of_equities": 0,
            "invest_in_commodities": False,
            "max_equity_investment": 0,
            "existing_assets_info": [],
            "asset_expectations": []
        }
    
    def optimize_portfolio(self):
        pass

    def display_information(self):
        print("\nPortfolio Information Collected:")
        for key, value in self.data.items():
            print(f"{key}: {value}")
