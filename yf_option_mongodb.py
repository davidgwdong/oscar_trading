import sys
import datetime
import time
import pymongo
import yfinance as yf

# --- CONFIGURATION ---
MONGODB_URI = "mongodb://localhost:27017/"  # Change to your MongoDB URI if remote
DB_NAME_EXT = "options_data_db"
COLLECTION_NAME = "options_snapshots"
INTERVAL_SECONDS = 900  # 15 minutes
MARKET_OPEN_TIME = "9:30"
MARKET_CLOSE_TIME = "16:00"


def init_db(tiker_symbol):
    """Initializes the MongoDB connection and returns the collection."""
    try:
        client = pymongo.MongoClient(MONGODB_URI)
        db_name = tiker_symbol+DB_NAME_EXT
        db = client[db_name]
        collection = db[COLLECTION_NAME]
        print(f"✅ Connected to MongoDB at {MONGODB_URI}")
        return collection
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise


def do_fetch_and_save(collection, ticker_symbol):
    """Fetches options data for specified tickers and saves them to MongoDB."""
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    print(f"\n🕒 Starting data pull at {timestamp.isoformat()}...")

    try:
       print(f"Fetching data for {ticker_symbol}...")
       ticker = yf.Ticker(ticker_symbol)

       # Get all available expiration dates
       expirations = ticker.options

       if not expirations:
           print(f"⚠️ No options data available for {ticker_symbol}.")
           return

       for exp_date in expirations:
           # Fetch the option chain for the specific expiration date
           opt_chain = ticker.option_chain(exp_date)

           # Convert pandas DataFrames to dictionaries
           calls_dict = opt_chain.calls.to_dict(orient="records")
           puts_dict = opt_chain.puts.to_dict(orient="records")

           # Structure the document payload
           document = {
               "ticker": ticker_symbol,
               "expiration_date": exp_date,
               "fetched_at": timestamp,
               "calls": calls_dict,
               "puts": puts_dict,
           }

           # Insert into MongoDB
           collection.insert_one(document)

       print(f"✅ Successfully saved options for {ticker_symbol}.")

    except Exception as e:
       print(f"❌ Error processing {ticker_symbol}: {e}")


def fetch_and_save(tiker_symbol):
    collection = init_db(tiker_symbol)

    print(
        f"🚀 Script started. Tracking: {tiker_symbol}. Pulling every {INTERVAL_SECONDS / 60} minutes."
    )

    while True:
        start_time = time.time()

        do_fetch_and_save(collection, tiker_symbol)

        # Calculate exact sleep time to keep intervals accurate
        elapsed_time = time.time() - start_time
        sleep_time = max(0, INTERVAL_SECONDS - elapsed_time)

        print(f"Sleeping for {round(sleep_time, 2)} seconds...")
        time.sleep(sleep_time)


def main():
    tikers = sys.argv[1:]
    
    if not tikers:
        print("Please provid at least one tiker")
        return

    collections = {key: None for key in tikers}
    for tiker_symbol in tikers:
        collections[tiker_symbol] = init_db(tiker_symbol)

    print(
        f"🚀 Script started. Tracking: {tiker_symbol}. Pulling every {INTERVAL_SECONDS / 60} minutes."
    )

    while True:
        now = datetime.datetime.now().time()
        #check for marcket open time
        open_time = datetime.datetime.strptime(MARKET_OPEN_TIME, "%H:%M").time()
        close_time = datetime.datetime.strptime(MARKET_CLOSE_TIME, "%H:%M").time()
        if now > open_time and now < close_time:
            start_time = time.time()

            for tiker_symbol in tikers:
                do_fetch_and_save(collections[tiker_symbol], tiker_symbol)

            # Calculate exact sleep time to keep intervals accurate
            elapsed_time = time.time() - start_time
            sleep_time = max(0, INTERVAL_SECONDS - elapsed_time)

            print(f"Sleeping for {round(sleep_time, 2)} seconds...")
            time.sleep(sleep_time)
        else:
            now = datetime.datetime.now()
            target = now.replace(hour=9, minute=30, second=0)
            #sleep more for friday
            if datetime.datetime.today().weekday() == 4:
                target += datetime.timedelta(days=3)
            else:
                target += datetime.timedelta(days=1)

            delta_seconds = (target - now).total_seconds()
            print(f"Sleeping for {delta_seconds} seconds until {target}")
            time.sleep(delta_seconds)

if __name__ == "__main__":
    main()


