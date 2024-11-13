from rapidfuzz import process

def map_preferred_stocks(user, stock_dict, threshold=70):
    """
    Maps the user's preferred stocks to a given stock dictionary.
    :param user: User data containing preferred stocks.
    :param stock_dict: Dictionary containing stock information with stock names as keys.
    :param threshold: Minimum match score to consider for fuzzy matching (default is 70).
    :return: Dictionary with matched preferred stocks and their details.
    """
    mapped_stocks = {}

    # Assuming `user` contains a key `preferred_stocks`
    preferred_stocks = user.get("preferred_stocks", [])

    for stock in preferred_stocks:
        # If the exact stock name is found in stock_dict
        if stock in stock_dict:
            mapped_stocks[stock] = stock_dict[stock]
        else:
            # Use fuzzy matching to find the closest match
            best_match = process.extractOne(stock, stock_dict.keys(), score_cutoff=threshold)
            if best_match:
                best_match_name, score = best_match
                mapped_stocks[best_match_name] = stock_dict[best_match_name]
                print(f"Note: Stock '{stock}' not found. Closest match '{best_match_name}' with score {score} was used.")
            else:
                print(f"Warning: Stock '{stock}' not found in the given stock dictionary, and no close match was found.")

    return mapped_stocks