import sys
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

def fetch_live_contract_liquidity(ticker_symbol, target_strike, option_type):
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
        #today = datetime.now()
        today = datetime(2026, 10, 30)

        print(today)
        target_date = today + relativedelta(months=1)  # Target is one month away
        print(target_date)

        # 2. Convert strings to datetime objects
        parsed_dates = [datetime.strptime(d, "%Y-%m-%d") for d in expirations]

        # 3. Find the date with the minimum absolute time difference
        target_expiration = min(parsed_dates, key=lambda d: abs(d - target_date))

        print(target_expiration)
        # Pull the front-month chain (typically closest standard monthly option)
        chain = ticker.option_chain(target_expiration)
        chain_df = chain.puts if option_type.upper() == "PUT" else chain.calls
        
        print(chain_df);
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

if __name__ == '__main__':
    # Test Scenario: Monitoring a Short Put on Apple (Highly Liquid, should PASS liquidity gates)
    liq = fetch_live_contract_liquidity(
        ticker_symbol="AAPL", 
        target_strike=210.0,
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
