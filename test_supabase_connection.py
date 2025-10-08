#!/usr/bin/env python3
"""
Test script to verify Supabase connection and setup
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from supabase import create_client, Client
import json

def test_supabase_connection():
    """Test basic Supabase connection"""
    print("🔗 Testing Supabase Connection...")
    print(f"URL: {settings.SUPABASE_URL}")
    print(f"Service Key: {settings.SUPABASE_SERVICE_KEY[:20]}...")
    
    try:
        client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
        print("✅ Supabase client created successfully")
        return client
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        return None

def test_database_tables(client):
    """Test if tables exist"""
    print("\n📋 Testing Database Tables...")
    
    # Test quotes table
    try:
        response = client.table('quotes').select("*").limit(1).execute()
        print(f"✅ quotes table accessible - found {len(response.data)} records")
    except Exception as e:
        print(f"❌ quotes table error: {e}")
    
    # Test leads table
    try:
        response = client.table('leads').select("*").limit(1).execute()
        print(f"✅ leads table accessible - found {len(response.data)} records")
    except Exception as e:
        print(f"❌ leads table error: {e}")

def test_simple_insert(client):
    """Test simple insert operation"""
    print("\n💾 Testing Simple Insert...")
    
    test_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "contact_number": "1234567890",
        "branch_name": "Test Branch"
    }
    
    try:
        response = client.table('leads').insert(test_data).execute()
        if response.data:
            print(f"✅ Insert successful - ID: {response.data[0].get('id')}")
            # Clean up - delete the test record
            client.table('leads').delete().eq('id', response.data[0].get('id')).execute()
            print("🧹 Test record cleaned up")
        else:
            print(f"❌ Insert failed - no data returned")
    except Exception as e:
        print(f"❌ Insert failed: {e}")

def main():
    print("🚀 Supabase Connection Test")
    print("=" * 50)
    
    # Test connection
    client = test_supabase_connection()
    if not client:
        return
    
    # Test tables
    test_database_tables(client)
    
    # Test insert
    test_simple_insert(client)
    
    print("\n" + "=" * 50)
    print("✅ Supabase test complete")

if __name__ == "__main__":
    main()