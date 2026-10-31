import sys
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def liquidation_check(symbol="SCHD", option_type="PUT"):
  # Initialize Ticker
  tk = yf.Ticker(symbol)
  expirations = tk.options

  if not expirations:
    print(f"No option expiration dates found for {symbol}.")
    return

  # Target expiration date roughly 30 days (1 month) from today
  target_date = datetime.now() + timedelta(days=30)
  target_str = target_date.strftime("%Y-%m-%d")

  # Find the closest expiration date to 30 days out
  exp_dates_dt = [datetime.strptime(d, "%Y-%m-%d") for d in expirations]
  closest_exp = min(exp_dates_dt, key=lambda d: abs(d - target_date)).strftime(
      "%Y-%m-%d"
  )

  print(
      f"Target expiration (~1 month): {target_str} | Using closest available:"
      f" {closest_exp}"
  )

  # Fetch option chain
  opt_chain = tk.option_chain(closest_exp)
  calls = opt_chain.calls
  puts = opt_chain.puts

  # Combine calls and puts with a type label
  calls["type"] = "CALL"
  puts["type"] = "PUT"
  df = pd.concat([calls, puts], ignore_index=True)
  if option_type == "CALL":
    df = calls
  else:
    df = puts


  # Fill NaN values in volume and openInterest with 0
  df["volume"] = df["volume"].fillna(0).astype(int)
  df["openInterest"] = df["openInterest"].fillna(0).astype(int)

  # Find strike with highest volume
  max_vol_row = df.loc[df["volume"].idxmax()]
  # Find strike with highest open interest
  max_oi_row = df.loc[df["openInterest"].idxmax()]

  print("\n--- Results ---")
  print(
      f"Highest Volume: Strike {max_vol_row['strike']} ({max_vol_row['type']})"
      f" | Volume: {max_vol_row['volume']}"
  )
  print(
      f"Highest Open Interest: Strike {max_oi_row['strike']}"
      f" ({max_oi_row['type']}) | Open Interest:"
      f" {max_oi_row['openInterest']}"
  )

  return df

def get_top_options_strikes(symbol="AAPL"):
  # Initialize Ticker
  tk = yf.Ticker(symbol)
  expirations = tk.options

  if not expirations:
    print(f"No option expiration dates found for {symbol}.")
    return

  # Target expiration date roughly 30 days (1 month) from today
  target_date = datetime.now() + timedelta(days=30)
  target_str = target_date.strftime("%Y-%m-%d")

  # Find the closest expiration date to 30 days out
  exp_dates_dt = [datetime.strptime(d, "%Y-%m-%d") for d in expirations]
  closest_exp = min(exp_dates_dt, key=lambda d: abs(d - target_date)).strftime(
      "%Y-%m-%d"
  )

  print(
      f"Target expiration (~1 month): {target_str} | Using closest available:"
      f" {closest_exp}"
  )

  # Fetch option chain
  opt_chain = tk.option_chain(closest_exp)
  calls = opt_chain.calls
  puts = opt_chain.puts

  # Combine calls and puts with a type label
  calls["type"] = "CALL"
  puts["type"] = "PUT"
  df = pd.concat([calls, puts], ignore_index=True)

  # Fill NaN values in volume and openInterest with 0
  df["volume"] = df["volume"].fillna(0).astype(int)
  df["openInterest"] = df["openInterest"].fillna(0).astype(int)

  # Find strike with highest volume
  max_vol_row = df.loc[df["volume"].idxmax()]
  # Find strike with highest open interest
  max_oi_row = df.loc[df["openInterest"].idxmax()]

  print("\n--- Results ---")
  print(
      f"Highest Volume: Strike {max_vol_row['strike']} ({max_vol_row['type']})"
      f" | Volume: {max_vol_row['volume']}"
  )
  print(
      f"Highest Open Interest: Strike {max_oi_row['strike']}"
      f" ({max_oi_row['type']}) | Open Interest:"
      f" {max_oi_row['openInterest']}"
  )

  return df



def fetch_live_contract_liquidity(ticker_symbol, option_type):
    """
    Scrapes the live options chain via Yahoo Finance to pull exact 
    real-time Bid, Ask, Spread, and Open Interest data for the contract.
    """
    ticker = yf.Ticker(ticker_symbol)
    target_strike = ticker.info.get("currentPrice")
    print(target_strike)
    
    try:
        # Pull the closest standard near-term expiration dates array
        expirations = ticker.options
        if not expirations:
            return None
        
        #find the expirations in one month
        today = datetime.now()

        target_date = today + relativedelta(months=1)  # Target is one month away

        # 2. Convert strings to datetime objects
        parsed_dates = [datetime.strptime(d, "%Y-%m-%d") for d in expirations]

        # 3. Find the date with the minimum absolute time difference
        target_expiration = min(parsed_dates, key=lambda d: abs(d - target_date))

        # Pull the front-month chain (typically closest standard monthly option)
        chain = ticker.option_chain(target_expiration.strftime("%Y-%m-%d"))
        chain_df = chain.puts if option_type.upper() == "PUT" else chain.calls
        
        # Find the row closest matching our targeted strike boundary
        matching_strike = chain_df.iloc[(chain_df['strike'] - target_strike).abs().argsort()[:1]]
        
        if matching_strike.empty:
            return None
            
        contract = matching_strike.iloc[0]
        bid = contract['bid']
        ask = contract['ask']
        open_interest = contract['openInterest']
        volume = contract['volume']
        
        # Avoid division-by-zero on illiquid unquoted bid-asks
        mid_price = (bid + ask) / 2
        spread = ask - bid
        spread_pct = (spread / mid_price) * 100 if mid_price > 0 else 999.0
        
        return {
            "bid": bid, "ask": ask, "spread_dollars": spread,
            "spread_pct": spread_pct, "open_interest": open_interest, "volume": volume
        }
    except Exception as e:
        print(e)
        # Fallback safeguard structure if options chain formatting blocks the query
        return None

def check_contract_liquidity(ticker_symbol, option_type):
    """
    Scrapes the live options chain via Yahoo Finance to pull exact 
    real-time Bid, Ask, Spread, and Open Interest data for the contract.
    """
    ticker = yf.Ticker(ticker_symbol)
    
    try:
        # Pull the closest standard near-term expiration dates array
        expirations = ticker.options
        if not expirations:
            return None
        
        #find the expirations in one month
        today = datetime.now()

        target_date = today + relativedelta(months=1)  # Target is one month away

        # 2. Convert strings to datetime objects
        parsed_dates = [datetime.strptime(d, "%Y-%m-%d") for d in expirations]

        # 3. Find the date with the minimum absolute time difference
        target_expiration = min(parsed_dates, key=lambda d: abs(d - target_date))

        # Pull the front-month chain (typically closest standard monthly option)
        chain = ticker.option_chain(target_expiration.strftime("%Y-%m-%d"))
        if option_type.upper() == "PUT":
           otm_chain_df = chain.puts[chain.puts['inTheMoney'] == False].tail(10)
        else:
           otm_chain_df = chain.calls[chain.calls['inTheMoney'] == False].head(10)
        #chain_df = chain.puts if option_type.upper() == "PUT" else chain.calls
        
        #otm_chain_df = chain_df[chain_df['inTheMoney'] == False]

        print(f'\n--- Out-of-the-Money {option_type} Strikes ---')
        print(otm_chain_df[['strike', 'lastPrice', 'bid', 'ask', 'volume', 'openInterest']])

    except Exception as e:
        print(e)

if __name__ == '__main__':
    check_contract_liquidity(
        ticker_symbol="AAPL", 
        option_type="PUT"
    )
    # Test Scenario: Monitoring a Short Put on Apple (Highly Liquid, should PASS liquidity gates)
    liq = fetch_live_contract_liquidity(
        ticker_symbol="AAPL", 
        option_type="PUT"
    )

    # Define Institutional Suitability Targets
    MIN_OPEN_INTEREST = 500       # Floor requirement for baseline structural interest
    MAX_SPREAD_PERCENTAGE = 10.0  # Bid-Ask width cannot bleed out past 10% of total option premium value
    
    if liq is None:
        print("❌ CRITICAL REJECTION: Live Option Chain Data Unreachable or Strike Unavailable.")
        print("👉 Execution Status: HALTED. Do not trade due to absolute data blindness risk.")
        sys.exit(0)
        
    print(f"-> Contract Metrics | Open Interest: {liq['open_interest']:,} | Daily Volume: {liq['volume']:,}")
    print(f"-> Bid: ${liq['bid']:.2f} | Ask: ${liq['ask']:.2f} | Spread: ${liq['spread_dollars']:.2f} ({liq['spread_pct']:.1f}%)")
    
    # Liquidity Rule Violations Checks
    if liq['open_interest'] < MIN_OPEN_INTEREST:
        print(f"❌ CRITICAL REJECTION: Illiquid Contract. Open Interest ({liq['open_interest']:,}) is below floor threshold ({MIN_OPEN_INTEREST:,}).")
        print("👉 Market Maker Trap: Bid-Ask execution slippage risks are completely unacceptable for premium sellers.")
        sys.exit(0)
        
    if liq['spread_pct'] > MAX_SPREAD_PERCENTAGE:
        print(f"❌ CRITICAL REJECTION: Spread Bleed. Bid-Ask Spread width ({liq['spread_pct']:.1f}%) exceeds maximum tolerance threshold ({MAX_SPREAD_PERCENTAGE}%).")
        print("👉 Friction Risk: The entry/exit friction costs will destroy your mathematical edge.")
        sys.exit(0)
        
    print("✅ LIQUIDITY STATUS: PASSED. Proceeding to Advanced Portfolio Analysis Framework...\n")
    print("-" * 75)
