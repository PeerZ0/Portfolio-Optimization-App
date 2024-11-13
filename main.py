from models.user import User
from services import *

def main():
    user = User()
    gather_information(user)
    user.optimize_portfolio()
    
if __name__ == "__main__":
    main()