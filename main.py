from models.user import User
from models.portfolio import Portfolio
from services.gather_information import gather_information
from services.update_data import update_data
from services.build_list import build_available_tickers

def main():
    user = User()
    update_data()
    gather_information(user)
    available_tickers = build_available_tickers(user)
    portfolio = Portfolio(available_tickers)
    
if __name__ == "__main__":
    main()