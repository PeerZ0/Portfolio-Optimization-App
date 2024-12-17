# main.py
"""
Main file to run the application
"""

from models.terminal import PortfolioApp
from models.testfile_dash1 import PortfolioManager

if __name__ == "__main__":
    # Run the PortfolioApp
    static = 'static/ticker_data.csv'
    manager = PortfolioManager(static)
    manager.run()