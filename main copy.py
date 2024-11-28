from models.user import User
from models.terminal2 import PortfolioApp

if __name__ == "__main__":
    user = User()
    app = PortfolioApp(user)
    app.run()