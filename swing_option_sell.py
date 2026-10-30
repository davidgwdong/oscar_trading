import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

def compute_rsi(series, period=14):
    """Calculates the Relative Strength Index (RSI) for a given price series."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / (loss + 1e-10)  # Avoid division by zero
    return 100 - (100 / (1 + rs))

def calculate_support_resistance(df, window=20):
    """
    Identifies recent key Support and Resistance boundaries 
    using local rolling extrema over a specified trading window.
    """
    recent_data = df.tail(60) # Review the last 2-3 months of action
    resistance = recent_data['High'].rolling(window=window, center=True).max().dropna().iloc[-1]
    support = recent_data['Low'].rolling(window=window, center=True).min().dropna().iloc[-1]
    return support, resistance

def monitor_advanced_short_option(ticker_symbol, entry_date_str, entry_credit, dte_at_entry, option_type="PUT"):
    """
    Monitors short options portfolios by checking Premium Targets, 
    Gamma Risk (21-DTE), Stop Losses, and Technical Overbought/Oversold thresholds.
    """
    print(f"=== Monitoring Active Short Position: {ticker_symbol} ({option_type}) ===")
    
    # 1. Temporal Clock Calculations
    entry_date = datetime.strptime(entry_date_str, "%Y-%m-%d").date()
    current_date = datetime.now().date()
    days_elapsed = (current_date - entry_date).days
    remaining_dte = dte_at_entry - days_elapsed
    
    # 2. Fetch Extended Data for Indicator Context
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="6mo") # Need historical depth for RSI & Levels
    
    if df.empty or len(df) < 30:
        print(f"Error: Insufficient data found for {ticker_symbol}.")
        return

    # Filter data matching specifically from your entry window forward
    df_since_entry = df.loc[entry_date_str:]
    if df_since_entry.empty:
        initial_stock_price = df['Close'].iloc[-1]
    else:
        initial_stock_price = df_since_entry['Close'].iloc[0]
        
    current_stock_price = df['Close'].iloc[-1]
    
    # 3. Calculate Technical Indicators
    df['RSI'] = compute_rsi(df['Close'], period=14)
    current_rsi = df['RSI'].iloc[-1]
    
    support_level, resistance_level = calculate_support_resistance(df)
    
    # Check proximity (within 1% threshold of a structural level breakout/touch)
    near_resistance = current_stock_price >= (resistance_level * 0.99)
    near_support = current_stock_price <= (support_level * 1.01)

    # 4. Simulate Options Decay & Intrinsic Pricing Impact (Proxy)
    estimated_delta = 0.25 if option_type == "PUT" else -0.25
    price_change = current_stock_price - initial_stock_price
    
    # For puts, stock price rallies drop premium. For calls, stock drops drop premium.
    underlying_impact = price_change * estimated_delta
    time_decay_factor = remaining_dte / dte_at_entry if dte_at_entry > 0 else 0
    
    estimated_current_premium = (entry_credit * time_decay_factor) - underlying_impact
    estimated_current_premium = max(0.01, estimated_current_premium)
    
    current_profit_pct = ((entry_credit - estimated_current_premium) / entry_credit) * 100
    profit_target_value = entry_credit * 0.50
    stop_loss_value = entry_credit * 2.00

    # 5. Print Performance Dashboard
    print(f"Stock Metrics: Price: ${current_stock_price:.2f} | RSI: {current_rsi:.1f}")
    print(f"Chart Levels:  Support Zone: ${support_level:.2f} | Resistance Zone: ${resistance_level:.2f}")
    print(f"Options Track: Collected: ${entry_credit:.2f} ➔ Est. Value: ${estimated_current_premium:.2f} ({current_profit_pct:.1f}% captured)")
    print(f"Time Matrix:   {remaining_dte} DTE remaining ({days_elapsed} days in trade)")
    print("-" * 75)

    # 6. Advanced Priority Signal Routing Engine
    # Tier 1 Risks: Absolute Violations
    if estimated_current_premium >= stop_loss_value:
        print("🔴 SIGNAL: EMERGENCY RISK EXIT (200% Capital Risk Stop Loss)")
        print(f"   Action: Buy back contract immediately at ${estimated_current_premium:.2f} to protect core account capital.")
        return
        
    if remaining_dte <= 21:
        print("🟡 SIGNAL: TIME LIMIT EXIT (21-DTE Rule Breached)")
        print(f"   Action: Buy back option now. Gamma risk is accelerating under 3 weeks to expiration.")
        return

    # Tier 2 Targets: Profit Locking
    if current_profit_pct >= 50.0:
        print("🟢 SIGNAL: BUY TO CLOSE (50% Standard Profit Target Filled)")
        print(f"   Action: Route a market-neutral limit order at ${estimated_current_premium:.2f} to secure gains.")
        return

    # Tier 3: Technical Overbought / Oversold Target Touch Rules
    if option_type == "PUT":
        # Short Puts profit when stock moves up. Take profits early if stock hits a wall.
        if near_resistance or current_rsi >= 70.0:
            print("🟢 SIGNAL: TECHNICAL EXIT - TAKE PROFIT EARLY (Short Put Target)")
            print(f"   Rationale: Stock is overbought (RSI: {current_rsi:.1f}) or touching historical Resistance (${resistance_level:.2f}).")
            print(f"   Action: Buy back the option early at ${estimated_current_premium:.2f} before a technical pullback occurs.")
            return
            
    elif option_type == "CALL":
        # Short Calls profit when stock moves down. Take profits early if stock hits a floor.
        if near_support or current_rsi <= 30.0:
            print("🟢 SIGNAL: TECHNICAL EXIT - TAKE PROFIT EARLY (Short Call Target)")
            print(f"   Rationale: Stock is oversold (RSI: {current_rsi:.1f}) or anchoring on key Support (${support_level:.2f}).")
            print(f"   Action: Buy back the option early at ${estimated_current_premium:.2f} before a technical bounce occurs.")
            return

    # Safe Zone
    print("⚪ SIGNAL: HOLD POSITION (No Action Required)")
    print("   Status: Equity trend and options mechanics are performing safely inside specified bounds.")

if __name__ == '__main__':
    # Test Scenario: Monitoring a Short Put on Apple sold 10 days ago.
    monitor_advanced_short_option(
        ticker_symbol="AAPL", 
        entry_date_str="2026-10-20", 
        entry_credit=2.50, 
        dte_at_entry=45,
        option_type="PUT"
    )

