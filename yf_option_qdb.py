import time
from datetime import datetime, timezone
import yfinance as yf
import pandas as pd
import questdb.ingress


def fetch_and_store_options(ticker_symbol: str, questdb_host: str = "localhost", questdb_port: int = 9000):
    stock = yf.Ticker(ticker_symbol)
    
    # Get available expiration dates
    expirations = stock.options
    if not expirations:
        print(f"[{datetime.now()}] No options data found for {ticker_symbol}.")
        return

    # Use the nearest expiration date (or loop through all expirations if needed)
    target_expiration = expirations[0]
    opt_chain = stock.option_chain(target_expiration)
    
    # Combine calls and puts with a type column
    calls = opt_chain.calls.copy()
    calls['option_type'] = 'CALL'
    puts = opt_chain.puts.copy()
    puts['option_type'] = 'PUT'
    
    df = pd.concat([calls, puts], ignore_index=True)
    
    # Clean up column names to be database-friendly
    df.columns = [col.lower().replace(' ', '_').replace('%', 'pct') for col in df.columns]
    
    current_time = datetime.now(timezone.utc)
    
    # Connect to QuestDB using the Ingress Sender (TCP/Line Protocol)
    # Ensure QuestDB ILP port (default 9009) or HTTP/TCP sender is configured properly
    # Using questdb.ingress.Sender.from_conf("tcp://localhost:9009")
    conf = f"tcp://{questdb_host}:9009"
    
    try:
        with questdb.ingress.Sender.from_conf(conf) as sender:
            for _, row in df.iterrows():
                sender.row(
                    'options_chain',
                    symbols={
                        'ticker': ticker_symbol.upper(),
                        'contractSymbol': str(row.get('contract_symbol', '')),
                        'optionType': str(row.get('option_type', '')),
                        'expirationDate': str(target_expiration)
                    },
                    columns={
                        'strike': float(row.get('strike', 0.0) or 0.0),
                        'lastPrice': float(row.get('last_price', 0.0) or 0.0),
                        'bid': float(row.get('bid', 0.0) or 0.0),
                        'ask': float(row.get('ask', 0.0) or 0.0),
                        'change': float(row.get('change', 0.0) or 0.0),
                        'pctChange': float(row.get('percent_change', 0.0) or 0.0),
                        'volume': int(row.get('volume', 0) or 0),
                        'openInterest': int(row.get('open_interest', 0) or 0),
                        'impliedVolatility': float(row.get('implied_volatility', 0.0) or 0.0),
                        'inTheMoney': bool(row.get('in_the_money', False))
                    },
                    at=current_time
                )
            sender.flush()
        print(f"[{current_time}] Successfully ingested {len(df)} option rows for {ticker_symbol} (expiry: {target_expiration}).")
    except Exception as e:
        print(f"Error writing to QuestDB: {e}")


def main():
    ticker = "AAPL"
    interval_seconds = 300  # 5 minutes
    
    print(f"Starting options data poller for {ticker} every 5 minutes...")
    while True:
        try:
            fetch_and_store_options(ticker)
        except Exception as e:
            print(f"Error during fetch cycle: {e}")
        
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
