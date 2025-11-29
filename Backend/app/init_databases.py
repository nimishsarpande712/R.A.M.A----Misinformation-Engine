"""
Database Initialization Script for R.A.M.A.

This script initializes all necessary database tables and indexes
for both Supabase (PostgreSQL) and MongoDB.

Run this before starting the application for the first time.
"""

import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

# Import after load_dotenv
from app.supabase_db import (
    SupabasePostgresConnection,
    create_user_history_table,
    create_news_data_table
)


def init_supabase():
    """Initialize Supabase PostgreSQL tables."""
    logger.info("=" * 60)
    logger.info("Initializing Supabase PostgreSQL Database")
    logger.info("=" * 60)
    
    try:
        with SupabasePostgresConnection() as db:
            # Create user_history table
            logger.info("Creating user_history table...")
            create_user_history_table(db)
            logger.info("✓ user_history table created")
            
            # Create news_data table
            logger.info("Creating news_data table...")
            create_news_data_table(db)
            logger.info("✓ news_data table created")
            
        logger.info("✓ Supabase initialization complete")
        return True
        
    except Exception as e:
        logger.error(f"✗ Supabase initialization failed: {e}")
        return False


def init_mongodb():
    """Initialize MongoDB collections and indexes."""
    logger.info("=" * 60)
    logger.info("Initializing MongoDB Database")
    logger.info("=" * 60)
    
    try:
        # Import MongoDB client here to avoid connection on module load
        from app.mongodb import mongo_client
        
        # Test connection
        if not mongo_client.is_connected():
            logger.error("✗ MongoDB not connected - check MONGODB_URI in .env")
            logger.warning("  MongoDB is optional - system will work with Supabase only")
            return False
        
        logger.info("✓ MongoDB connected")
        
        # Collections will be auto-created on first insert
        # Indexes are created in mongodb.py via _create_indexes()
        
        # List existing collections
        collections = mongo_client.db.list_collection_names()
        logger.info(f"Existing collections: {', '.join(collections) if collections else 'None'}")
        
        logger.info("✓ MongoDB initialization complete")
        return True
        
    except Exception as e:
        logger.error(f"✗ MongoDB initialization failed: {e}")
        logger.warning("  MongoDB is optional - system will work with Supabase only")
        return False


def init_all_databases():
    """Initialize all databases."""
    logger.info("")
    logger.info("#" * 60)
    logger.info("# R.A.M.A. DATABASE INITIALIZATION")
    logger.info("#" * 60)
    logger.info("")
    
    supabase_success = init_supabase()
    logger.info("")
    
    mongodb_success = init_mongodb()
    logger.info("")
    
    logger.info("=" * 60)
    logger.info("INITIALIZATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Supabase: {'✓ SUCCESS' if supabase_success else '✗ FAILED'}")
    logger.info(f"MongoDB:  {'✓ SUCCESS' if mongodb_success else '⚠ SKIPPED (optional)'}")
    logger.info("=" * 60)
    
    if supabase_success:
        logger.info("✓ Core database (Supabase) initialized successfully!")
        logger.info("You can now start the R.A.M.A. backend.")
        if not mongodb_success:
            logger.warning("⚠ MongoDB not initialized - using Supabase only mode")
        return True
    else:
        logger.error("✗ Critical: Supabase initialization failed")
        logger.error("Please check your .env file and Supabase credentials")
        return False


if __name__ == "__main__":
    success = init_all_databases()
    exit(0 if success else 1)
