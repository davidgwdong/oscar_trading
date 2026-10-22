import pandas as pd
import yfinance as yf


def get_options_data(ticker_symbol, expiration_date=None):
    """Fetches option chain data for a given ticker and expiration date."""
    # Initialize the ticker object
    ticker = yf.Ticker(ticker_symbol)

    # Fetch available expiration dates
    try:
        expirations = ticker.options
    except Exception as e:
        print(f"Error fetching data for {ticker_symbol}: {e}")
        return None, None

    if not expirations:
        print(f"No options data available for ticker: {ticker_symbol}")
        return None, None

    # If no date is specified, default to the closest upcoming expiration date
    if expiration_date is None:
        expiration_date = expirations[0]
        print(f"No date specified. Using closest expiration: {expiration_date}")
    elif expiration_date not in expirations:
        print(f"Error: '{expiration_date}' is not a valid expiration date.")
        print(f"Available dates: {expirations}")
        return None, None

    print(
        f"\nFetching options chain for {ticker_symbol.upper()} expiring on {expiration_date}..."
    )

    # Get the complete option chain for the specified date
    opt_chain = ticker.option_chain(expiration_date)

    # Separate into Calls and Puts DataFrames
    calls_df = opt_chain.calls
    puts_df = opt_chain.puts

    return calls_df, puts_df


if __name__ == "__main__":
    # Example: Pull options for Apple Inc. (AAPL)
    ticker = "AAPL"

    # Step 1: Initialize ticker to see available dates first
    yf_ticker = yf.Ticker(ticker)
    available_dates = yf_ticker.options

    if available_dates:
        print(f"Available Expiration Dates for {ticker}: {available_dates[:5]}...")

        # Step 2: Fetch data for the nearest expiration date
        # You can replace None with a specific string from available_dates, e.g., '2026-11-20'
        calls, puts = get_options_data(ticker, expiration_date=None)

        if calls is not None and not calls.empty:
            # Display the first few rows of the Calls DataFrame
            print("\n--- CALLS (First 5 Rows) ---")
            print(
                calls[
                    [
                        "contractSymbol",
                        "strike",
                        "lastPrice",
                        "bid",
                        "ask",
                        "volume",
                        "openInterest",
                        "impliedVolatility",
                    ]
                ].head()
            )

        if puts is not None and not puts.empty:
            # Display the first few rows of the Puts DataFrame
            print("\n--- PUTS (First 5 Rows) ---")
            print(
                puts[
                    [
                        "contractSymbol",
                        "strike",
                        "lastPrice",
                        "bid",
                        "ask",
                        "volume",
                        "openInterest",
                        "impliedVolatility",
                    ]
                ].head()
            )

