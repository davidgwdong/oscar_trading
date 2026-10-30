# I asked Gemini AI about "swing trades for selling options", it gives the operational indicators framework,
# and generated the script to give buying/selling signal according to the framework
# 
# For selling options on a swing trading horizon (holding for weeks), Implied Volatility Percentile/Rank (IVP/IVR) is your most important indicator [1].
# When you sell options, your primary goal is to collect premium and benefit from time decay (Theta) and falling volatility (Vega) [1].
# 
# The Ultimate Swing Selling Indicator: IV Rank / IV Percentile
# 
# • What it does: Tells you whether the current Implied Volatility is high or low compared to that specific stock's historical average.
# • Why it matters: Standard IV only tells you the current number, but IV Rank tells you if it's cheap or expensive. You want to sell when IV Rank is above 50%.
# • The Math: If a stock has an IV of 40%, it might look low. But if its historical IV range is 10% to 45%, an IV of 40% is actually extremely high (an IV Rank of ~85%).
# • The Strategy: High IV Rank means option premiums are heavily inflated. You sell the expensive premium, and profit as the stock stabilizes and IV reverts to its mean (called an "IV Crush").
# 
# The Operational Indicators Framework
# 
# To execute a 30-to-45-day option selling swing trade (such as a Credit Spread or Cash-Secured Put), use this multi-layered framework:
# 
# Indicator Category	Specific Indicator	Optimal Metric / Target	Actionable Purpose
# Volatility (Price/Cost)	IV Rank (IVR)	> 50%	Ensures you are getting paid maximum premium for the risk.
# Probability (Strike Selection)	Delta (Δ)	0.15 to 0.30	Gives you a statistically high probability of success (~70% to 85% chance of expiring worthless).
# Time Decay (Duration)	Days to Expiration (DTE)	30 to 45 Days	Captures the acceleration of the Theta decay curve before it drops off too sharply.
# Directional Filter	50-day / 200-day EMA	Stock above EMAs for bullish sells; below for bearish sells.	Avoids selling premium directly into a massive, runaway institutional trend.

import sys
import yfinance as yf
import pandas as pd
import numpy as np

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
        
        # Pull the front-month chain (typically closest standard monthly option)
        chain = ticker.option_chain(expirations[0])
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
        # Fallback safeguard structure if options chain formatting blocks the query
        return None

def analyze_swing_sell_framework(ticker_symbol):
    """
    Evaluates a stock against the short-option swing trading framework.
    Uses 30-day Historical Volatility Rank as a reliable, free proxy for IV Rank.
    """
    print(f"=== Analyzing {ticker_symbol} for Short Option Swing Trades ===")
    
    # 1. Fetch 1 year of historical market data
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="1y")
    
    if df.empty:
        print(f"Error: No data found for ticker '{ticker_symbol}'")
        return
        
    current_price = df['Close'].iloc[-1]
    
    # 2. Trend Filtering (Exponential Moving Averages)
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    ema_50 = df['EMA_50'].iloc[-1]
    ema_200 = df['EMA_200'].iloc[-1]
    
    # Determine the directional bias
    if current_price > ema_50 and ema_50 > ema_200:
        trend_bias = "BULLISH"
        recommended_strategy = "Sell Cash-Secured Puts or Bull Put Credit Spreads"
    elif current_price < ema_50 and ema_50 < ema_200:
        trend_bias = "BEARISH"
        recommended_strategy = "Sell Covered Calls or Bear Call Credit Spreads"
    else:
        trend_bias = "NEUTRAL / CHOPPY"
        recommended_strategy = "Sell Iron Condors (Neutral / Range-bound)"

    # 3. Volatility Rank Calculation
    # Free APIs like yfinance don't output historical Implied Volatility. 
    # This block computes 30-day Historical Volatility (HV) and ranks it over the year.
    df['Returns'] = df['Close'].pct_change()
    df['HV_30'] = df['Returns'].rolling(window=21).std() * np.sqrt(252) * 100
    
    current_hv = df['HV_30'].iloc[-1]
    min_hv = df['HV_30'].min()
    max_hv = df['HV_30'].max()
    
    # Back-solve Volatility Rank (Scale of 0 to 100)
    if max_hv != min_hv:
        vol_rank = ((current_hv - min_hv) / (max_hv - min_hv)) * 100
    else:
        vol_rank = 0
        
    # Rule Checklist
    vol_filter_passed = vol_rank >= 50.0


    # ------------------------------------------------------------------------
    # EXTRA STEP: HARD LIQUIDITY GATE FILTERS
    # ------------------------------------------------------------------------
#    liq = fetch_live_contract_liquidity(ticker_symbol, target_strike, option_type)
    
    # Define Institutional Suitability Targets
#    MIN_OPEN_INTEREST = 500       # Floor requirement for baseline structural interest
#    MAX_SPREAD_PERCENTAGE = 10.0  # Bid-Ask width cannot bleed out past 10% of total option premium value
    
#    if liq is None:
#        print("❌ CRITICAL REJECTION: Live Option Chain Data Unreachable or Strike Unavailable.")
#        print("👉 Execution Status: HALTED. Do not trade due to absolute data blindness risk.")
#        return
        
#    print(f"-> Contract Metrics | Open Interest: {liq['open_interest']:,} | Daily Volume: {liq['volume']:,}")
#   print(f"-> Bid: ${liq['bid']:.2f} | Ask: ${liq['ask']:.2f} | Spread: ${liq['spread_dollars']:.2f} ({liq['spread_pct']:.1f}%)")
#   
#   # Liquidity Rule Violations Checks
#   if liq['open_interest'] < MIN_OPEN_INTEREST:
#       print(f"❌ CRITICAL REJECTION: Illiquid Contract. Open Interest ({liq['open_interest']:,}) is below floor threshold ({MIN_OPEN_INTEREST:,}).")
#       print("👉 Market Maker Trap: Bid-Ask execution slippage risks are completely unacceptable for premium sellers.")
#       return
#       
#   if liq['spread_pct'] > MAX_SPREAD_PERCENTAGE:
#       print(f"❌ CRITICAL REJECTION: Spread Bleed. Bid-Ask Spread width ({liq['spread_pct']:.1f}%) exceeds maximum tolerance threshold ({MAX_SPREAD_PERCENTAGE}%).")
#       print("👉 Friction Risk: The entry/exit friction costs will destroy your mathematical edge.")
#       return
#       
#   print("✅ LIQUIDITY STATUS: PASSED. Proceeding to Advanced Portfolio Analysis Framework...\n")
#   print("-" * 75)


    # 4. Generate Console Output Report
    print(f"Current Stock Price: ${current_price:.2f}")
    print(f"50 EMA: ${ema_50:.2f} | 200 EMA: ${ema_200:.2f} -> Trend Bias: {trend_bias}")
    print(f"Estimated Volatility Rank: {vol_rank:.1f}% -> {'HIGH (Overpriced Premium)' if vol_filter_passed else 'LOW (Underpriced Premium)'}")
    print("-" * 60)
    
    # 5. Output Signal Execution Rules
    if vol_filter_passed:
        print(f"🟢 SIGNAL: EXECUTE SHORT OPTION SWING")
        print(f"👉 Recommended Play: {recommended_strategy}")
        print(f"🎯 Execution Checklist (30-45 Days to Expiration):")
        if trend_bias == "BULLISH":
            print("   - Target short Put strikes at the 0.15 to 0.25 Delta level.")
        elif trend_bias == "BEARISH":
            print("   - Target short Call strikes at the 0.15 to 0.25 Delta level.")
        else:
            print("   - Target an Iron Condor: Sell both a Call and Put leg at 0.15 Delta.")
    else:
        print("🔴 SIGNAL: NO TRADE (Avoid Selling Premium)")
        print("👉 Rationale: Volatility is compressed. Premium values are too cheap to justify the tail risk.")


# Execute Script
if __name__ == '__main__':
    tikers = sys.argv[1:]
    if not tikers:
        print("Please give at lease one tiker")
        sys.exit(1)
    # Dependencies: pip install yfinance pandas numpy
    # Swap out "AAPL" for any ticker symbol you wish to test (e.g., "TSLA", "NVDA", "SPY")
    analyze_swing_sell_framework(tikers[0])

