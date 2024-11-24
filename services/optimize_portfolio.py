from models.portfolio import Portfolio

def optimize_portfolio(available_tickers, user):
    print("Pulling data for portfolio optimization...")
    portfolio = Portfolio(available_tickers, user)
    print("Data pulled successfully.")
    print("Please select the optimization method:")
    print("1. Minimum Variance Portfolio")
    print("2. Maximum Sharpe Ratio Portfolio")
    print("3. Black-Litterman Model")
    print("4 Auto-Optimize (may take a while)")
    input_optimization = input("Enter the number of the optimization method: ")
    try:
        if input_optimization == "1":
            print("Calculating minimum variance portfolio...")
            weights = portfolio.min_variance_portfolio()
            print("Minimum variance portfolio calculated successfully.")
        elif input_optimization == "2":
            print("Calculating maximum Sharpe ratio portfolio...")
            weights = portfolio.max_sharpe_ratio_portfolio()
            print("Maximum Sharpe ratio portfolio calculated successfully.")
        elif input_optimization == "3":
            print("Calculating Black-Litterman model...")
            P = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            Q = [0.02, 0.03, 0.04]
            weights = portfolio.black_litterman_model(P, Q)
            print("Black-Litterman model calculated successfully.")
        elif input_optimization == "4":
            print("Auto-optimizing portfolio...")
            weights = portfolio.auto_optimize()
            print("Portfolio auto-optimized successfully.")
        else:
            raise ValueError("Invalid input. Please enter a number between 1 and 4.")
    except ValueError as e:
        print(e)
        return
    
    return weights