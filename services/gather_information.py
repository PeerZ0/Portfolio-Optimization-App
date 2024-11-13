# services/gather_information.py
# Gathers information from the user

from services.map_stocks import map_preferred_stocks

def gather_information(user):
    try:
        user.data["age"] = int(input("How old are you?: ").strip())
        if user.data["age"] <= 0:
            raise ValueError("Age must be a positive integer.")

        user.data["investment_style"] = input("What is your investment style?: ").strip()
        
        preferred_stocks = input("Do you have any stocks that you definitely want in your portfolio? (yes/no): ")
        if preferred_stocks == "yes":
            stocks = input("Enter the stocks you want in your portfolio (comma-separated list): ").strip()
            mapped_stocks = []
            for stock in stocks.split(","):
                try:
                    mapped_stocks.append(map_preferred_stocks(stock))
                except ValueError as e:
                    print(f"Error: {e}")
            user.data["preferred_stocks"] = mapped_stocks
        else:
            user.data["preferred_stocks"] = []
        
        interested_sectors = input("Are you interested in certain sectors? (comma-separated list): ").strip()
        user.data["interested_sectors"] = [sector.strip() for sector in interested_sectors.split(",") if sector.strip()]
        
        sectors_to_avoid = input("Which sectors do you not want to invest in? (comma-separated list): ").strip()
        user.data["sectors_to_avoid"] = [sector.strip() for sector in sectors_to_avoid.split(",") if sector.strip()]
        
        user.data["geographical_preference"] = input("Do you have preferences in geographical asset allocation?: ").strip()
        
        invest_in_crypto = input("Do you want to invest in crypto? (yes/no): ").strip().lower() == "yes"
        if invest_in_crypto:
            crypto_percentage = float(input("If yes, how much (in percent)?: ").strip())
            if crypto_percentage < 0 or crypto_percentage > 100:
                raise ValueError("Crypto percentage must be between 0 and 100.")
            user.data["invest_in_crypto"] = {"invest": True, "percentage": crypto_percentage}
        else:
            user.data["invest_in_crypto"] = {"invest": False, "percentage": 0}
        
        user.data["invest_in_penny_stocks"] = input("Do you want to invest in penny stocks? (yes/no): ").strip().lower() == "yes"
        
        user.data["number_of_equities"] = int(input("How many equities do you want in your portfolio?: ").strip())
        if user.data["number_of_equities"] <= 0:
            raise ValueError("Number of equities must be a positive integer.")

        user.data["invest_in_commodities"] = input("Do you want to invest in commodities? (yes/no): ").strip().lower() == "yes"
        
        user.data["max_equity_investment"] = float(input("What is the maximum you want to invest in a single equity? (in percent): ").strip())
        if user.data["max_equity_investment"] < 0 or user.data["max_equity_investment"] > 100:
            raise ValueError("Max equity investment must be between 0 and 100.")

        existing_assets_info = input("Short info about assets currently in the portfolio (comma-separated list): ").strip()
        user.data["existing_assets_info"] = [asset.strip() for asset in existing_assets_info.split(",") if asset.strip()]
        
        asset_expectations = input("Do you have any expectations for the assets in your portfolio? (comma-separated list): ").strip()
        user.data["asset_expectations"] = [expectation.strip() for expectation in asset_expectations.split(",") if expectation.strip()]
    
    except ValueError as e:
        print(f"Error: {e}")
        gather_information(user)
