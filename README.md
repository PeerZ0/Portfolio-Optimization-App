# Portfolio Optimization

A Python-based portfolio optimization system with a terminal user interface and interactive dashboard visualization.

## How to use
1. Run the main.py file
2. Select if you want to update the stock data (this will take a while and can be limited due to yfinance restrictions)
3. Enter any tickers that you want to include in the optimization (those will not be filtered out later)
4. Select/Deselect any sector you want to avoid to invest in
5. Select the investment constraints (minimum and maximum investment per stock)
6. Wait for the data to be pulled and the optimization to run
7. Click on open dashboard to see the results

## Requirements

- Python 11.x or 12.x
- Dependencies listed in [requirements.txt](requirements.txt)

## Installation

1. Clone the repository
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

## Features
- 

## Project Structure

```plaintext
.
├── main.py          # Application entry point
├── models/           # Core classes and data structures
├── services/         # Data retrieval and processing services
├── static/           # Stock data storage
└── requirements.txt # Project dependencies
```

## Dependencies

Main dependencies include:

- yfinance: Stock data retrieval
- pandas: Data manipulation
- plotly: Interactive visualization
- textual: Terminal user interface
- scipy: Optimization algorithms
