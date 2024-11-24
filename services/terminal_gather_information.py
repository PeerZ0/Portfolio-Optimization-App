# services/terminal_gather_information.py
import curses
import pandas as pd
from typing import Dict, Any
from models.user import User

class TerminalUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.user_data = {}
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        self.GREEN = curses.color_pair(1)
        self.RED = curses.color_pair(2)

    def show_prompt(self, prompt: str, y: int) -> str:
        self.stdscr.addstr(y, 2, prompt)
        self.stdscr.refresh()
        curses.echo()
        response = self.stdscr.getstr(y, len(prompt) + 3).decode('utf-8')
        curses.noecho()
        return response

    def get_basic_info(self):
        self.stdscr.clear()
        self.stdscr.addstr(1, 2, "Basic Information", curses.A_BOLD)
        
        while True:
            try:
                age = int(self.show_prompt("Age: ", 3))
                if age <= 0:
                    raise ValueError
                break
            except ValueError:
                continue

        while True:
            try:
                risk = int(self.show_prompt("Risk Tolerance (1-10): ", 5))
                if 1 <= risk <= 10:
                    break
            except ValueError:
                continue

        self.user_data.update({
            "age": age,
            "risk_tolerance": risk
        })

    def get_stocks(self):
        self.stdscr.clear()
        try:
            df = pd.read_csv('static/ticker_data.csv')
            self.stdscr.addstr(1, 2, "Available Stocks", curses.A_BOLD)
            response = self.show_prompt("Enter preferred stocks (comma-separated): ", 3)
            stocks = [s.strip().upper() for s in response.split(",")]
            valid_stocks = [s for s in stocks if s in df['Ticker'].values]
            self.user_data["preferred_stocks"] = valid_stocks
        except FileNotFoundError:
            self.user_data["preferred_stocks"] = []

    def get_sectors(self):
        self.stdscr.clear()
        try:
            df = pd.read_csv('static/ticker_data.csv')
            sectors = df['sector'].unique()
            self.stdscr.addstr(1, 2, "Available Sectors", curses.A_BOLD)
            for i, sector in enumerate(sectors):
                self.stdscr.addstr(3 + i, 4, f"{sector}")
            
            response = self.show_prompt("Sectors to avoid (comma-separated): ", 3 + len(sectors) + 2)
            avoid_sectors = [s.strip() for s in response.split(",")]
            self.user_data["sectors_to_avoid"] = [s for s in avoid_sectors if s in sectors]
        except FileNotFoundError:
            self.user_data["sectors_to_avoid"] = []

    def get_constraints(self):
        self.stdscr.clear()
        self.stdscr.addstr(1, 2, "Portfolio Constraints", curses.A_BOLD)

        while True:
            try:
                min_equity = float(self.show_prompt("Minimum investment per equity (%): ", 3))
                max_equity = float(self.show_prompt("Maximum investment per equity (%): ", 5))
                if 0 <= min_equity <= max_equity <= 100:
                    break
            except ValueError:
                continue

        penny_stocks = self.show_prompt("Invest in penny stocks? (y/n): ", 7).lower() == 'y'

        self.user_data.update({
            "min_equity_investment": min_equity,
            "max_equity_investment": max_equity,
            "invest_in_penny_stocks": penny_stocks
        })

def gather_information_terminal(user: User):
    def main(stdscr):
        ui = TerminalUI(stdscr)
        ui.get_basic_info()
        ui.get_stocks()
        ui.get_sectors()
        ui.get_constraints()
        user.data.update(ui.user_data)

    curses.wrapper(main)

if __name__ == "__main__":
    user = User()
    gather_information_terminal(user)