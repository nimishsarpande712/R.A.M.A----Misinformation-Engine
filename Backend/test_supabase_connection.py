#!/usr/bin/env python3
"""
Test script for Supabase PostgreSQL connectivity.
Run this script to verify your database connection is working.
"""

from app.supabase_db import SupabasePostgresConnection, test_supabase_connection

def main():
    """Main function to test Supabase PostgreSQL connection."""
    print("=" * 50)
    print("Supabase PostgreSQL Connection Test")
    print("=" * 50)
    
    # Method 1: Simple connection test
    print("\n1. Testing simple connection...")
    success = test_supabase_connection()
    
    if success:
        print("✅ Simple connection test passed!")
    else:
        print("❌ Simple connection test failed!")
        print("\nPlease check your .env file and ensure:")
        print("- user: Your Supabase postgres username")
        print("- password: Your Supabase database password") 
        print("- host: Your Supabase host (usually ending with supabase.co)")
        print("- port: 5432")
        print("- dbname: postgres")
        return
    
    print("\n2. Testing with connection class...")
    # Method 2: Test with connection class
    try:
        with SupabasePostgresConnection() as db:
            # Test basic query
            result = db.execute_query("SELECT version();")
            if result:
                print("✅ PostgreSQL Version:", result[0][0])
            
            # Test current timestamp
            result = db.execute_query("SELECT NOW();")
            if result:
                print("✅ Current Timestamp:", result[0][0])
            
            # Test database list (you might not have permissions for this)
            try:
                result = db.execute_query("SELECT datname FROM pg_database WHERE datistemplate = false;")
                if result:
                    print("✅ Available databases:")
                    for db_name in result:
                        print(f"  - {db_name[0]}")
            except Exception as e:
                print(f"ℹ️  Database list query failed (this is normal): {e}")
            
        print("\n✅ All connection tests passed!")
        print("Your Supabase PostgreSQL connection is working correctly!")
        
    except Exception as e:
        print(f"❌ Connection class test failed: {e}")

if __name__ == "__main__":
    main()