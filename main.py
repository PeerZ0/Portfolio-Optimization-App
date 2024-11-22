from models.user import User
from services.gather_information import gather_information
from services.update_data import update_data

def main():
    user = User()
    update_data()
    gather_information(user)
    user.optimize_portfolio()
    
if __name__ == "__main__":
    main()