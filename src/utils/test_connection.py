#!/usr/bin/env python3
"""
Test script to verify MongoDB connection and query a specified collection
Usage: python3 test_connection.py <database> <collection>
"""
import os
import sys
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.mongodb_client import MongoDBClient

def test_connection(database_name, collection_name):
    """Test MongoDB connection and query specified collection"""
    
    # Load environment variables
    load_dotenv()
    
    # Get connection details from environment
    host = os.getenv('MONGO_HOST', 'localhost')
    port = int(os.getenv('MONGO_PORT', 27017))
    username = os.getenv('MONGO_USERNAME')
    password = os.getenv('MONGO_PASSWORD')
    retry_writes = os.getenv('MONGO_RETRY_WRITES', 'true')
    write_concern = os.getenv('MONGO_WRITE_CONCERN', 'majority')
    app_name = os.getenv('MONGO_APP_NAME', 'Cluster0')
    
    print(f"Connecting to MongoDB...")
    print(f"Host: {host}")
    print(f"Username: {username}")
    print("-" * 50)
    
    try:
        # Create client and connect
        client = MongoDBClient(
            host=host,
            port=port,
            database=database_name,
            username=username,
            password=password,
            retry_writes=retry_writes,
            write_concern=write_concern,
            app_name=app_name
        )
        
        # Test connection
        client.connect()
        print("✅ Successfully connected to MongoDB!")
        
        # Query specified collection
        if client.database is not None:
            # First check if the collection exists
            collection_names = client.database.list_collection_names()
            if collection_name not in collection_names:
                print(f"❌ Collection '{collection_name}' not found in database '{database_name}'")
                print(f"📋 Available collections: {', '.join(collection_names) if collection_names else 'None'}")
            else:
                collection = client.database[collection_name]
                
                # Count documents
                count = collection.count_documents({})
                print(f"📊 Total documents in {collection_name}: {count}")
                
                if count > 0:
                    # Get first few documents
                    print("\n📋 Sample records:")
                    documents = list(collection.find({}).limit(5))
                    
                    for i, doc in enumerate(documents, 1):
                        print(f"\nRecord {i}:")
                        for key, value in doc.items():
                            if key != '_id':  # Skip MongoDB's internal ID for cleaner output
                                print(f"  {key}: {value}")
                        print("-" * 30)
                    
                    print(f"\n✅ Successfully retrieved {len(documents)} sample records")
                else:
                    print(f"⚠️  Collection '{collection_name}' exists but is empty")
        else:
            print("❌ Could not access database")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    finally:
        if 'client' in locals():
            client.close()
            print("\n🔌 Connection closed")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 test_connection.py <database> <collection>")
        print("Example: python3 test_connection.py classicmodels orderdetails")
        sys.exit(1)
    
    database_name = sys.argv[1]
    collection_name = sys.argv[2]
    
    print(f"Testing connection to database: '{database_name}', collection: '{collection_name}'")
    test_connection(database_name, collection_name)
