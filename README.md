# Portfolio Optimization App

A simple Python-based Dash app that runs several optimization algorithms to find the best investment portfolio allocation based on the user's preferences and then visualizes the results in a dashboard. The app currently covers around 620 tickers, webscraped from the largest indices around the world.

Due to yFinance rate limiting being more strict lately, we had to remove an automatic update of the stock data. Furthermore, due to cross-platform issues, we had to move all frontend to Dash and Plotly.

WARNING: Calculations are hardware intensive and can take a while to run, especially when updating the stock data, optimizing the portfolio, or loading the dashboard. The app is not optimized for performance and should be used for educational purposes only.

## How to use

1. Install the applications as instructed below.
2. Run the application at http://127.0.0.1:8060
3. Select any constraints to the optimization on the Dash page (sectors to avoid, max investment per stock, risk tolerance etc.)
4. Wait for the optimization to finish (can take a while)
5. View the results on the dashboard
6. (Optional) Download the results as a CSV file or go back to the Dash page to set different constraints

## Requirements

- Python 11.x or 12.x
- Dependencies listed in [requirements.txt](requirements.txt)

## Installation

1. Clone the repository
```bash
git clone git@github.com:PeerZ0/Portfolio-Optimization-App.git
cd Portfolio-Optimization-App
````
2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
````
3. Install the dependencies:
```bash
pip install -r requirements.txt
````
4. Run the system:
```bash
python main.py
````
5. Visit the dashboard at http://127.0.0.1:8060/

## Project Structure

```plaintext
.
├── main.py           # Application entry point
├── state.py          # Global state management
├── assets/           # CSS stylesheet
├── models/           # Core classes and data structures
├── pages/            # Dash web application pages
├── services/         # Data processing services
├── static/           # Stock data storage
└── requirements.txt  # Project dependencies
```

## Dependencies

Main dependencies include:

- yfinance: Stock data retrieval
- pandas: Data manipulation
- plotly & Dash: Interactive visualization
- scipy: Optimization algorithms

## Literature

This application builds on foundational research in portfolio optimization, a critical field within financial economics. Below is a summary of the key literature informing this work:

1. **Modern Portfolio Theory (MPT)**:
   - Markowitz, H. (1952). "Portfolio Selection." *The Journal of Finance*, 7(1), 77-91.
     - This seminal work introduced the concept of mean-variance optimization, laying the groundwork for constructing efficient portfolios that minimize risk for a given level of return. This directly informs the "minimum variance" and "maximum Sharpe ratio" optimization strategies implemented in this application.
    - DOI: [10.1111/j.1540-6261.1952.tb01525.x](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x)

2. **Equal-Weight Portfolios**:
   - DeMiguel, V., Garlappi, L., & Uppal, R. (2007). "Optimal Versus Naive Diversification: How Inefficient is the 1/N Portfolio Strategy?" *The Review of Financial Studies*, 22(5), 1915-1953.
     - This research evaluates the performance of equal-weight (1/N) portfolios against optimized portfolios, highlighting their robustness and simplicity in various market conditions.
   - DOI: [10.1093/rfs/hhm075](https://doi.org/10.1093/rfs/hhm075)

3. **Sharpe Ratio Maximization**:
   - Sharpe, W. F. (1966). "Mutual Fund Performance." *The Journal of Business*, 39(1), 119-138.
     - The Sharpe ratio, a measure of risk-adjusted return, is a cornerstone metric for portfolio performance evaluation and is extensively applied in this application for optimization.
   - DOI: [10.1086/294846](https://doi.org/10.1086/294846)

By integrating these theoretical underpinnings, this application provides users with robust tools for portfolio construction and optimization.
