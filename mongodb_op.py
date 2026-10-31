import pprint
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# 1. Update your connection string if you use MongoDB Atlas or a remote server
# Local connection string: "mongodb://localhost:27017/"
MONGO_URI = "mongodb://localhost:27017/"

try:
    # 2. Connect to the MongoDB server
    client = MongoClient(MONGO_URI)
    
    # Force a connection check
    client.admin.command('ping')
    print("Successfully connected to MongoDB.\n" + "="*50 + "\n")
    
    # 3. Retrieve and iterate through all available database names
    db_names = client.list_database_names()
    
    for db_name in db_names:
        # Skip internal system databases if you only want user data
        if db_name in ['admin', 'local', 'config']:
            continue
            
        print(f"DATABASE: {db_name}")
        print("-" * 40)
        
        db = client[db_name]
        
        # 4. Retrieve and iterate through all collections in the database
        collection_names = db.list_collection_names()
        
        if not collection_names:
            print("  (No collections found)\n")
            continue
            
        for col_name in collection_names:
            print(f"  COLLECTION: {col_name}")
            collection = db[col_name]
            
            # 5. Fetch all documents within the collection
            # .find() with no arguments acts as a 'SELECT *' query
            cursor = collection.find()
            
            # Count the documents to see if it's empty
            doc_count = collection.count_documents({})
            if doc_count == 0:
                print("    [Empty Collection]")
            else:
                # 6. Print out each individual document
                for document in cursor:
                    # pprint makes nested JSON structures look clean and readable
                    print("    ", end="")
                    pprint.pprint(document, indent=4)
            print() # Blank line between collections
        print("="*50 + "\n")

except ConnectionFailure:
    print("Could not connect to the MongoDB server. Please check your URI or connection.")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Always close the connection when finished
    client.close()

