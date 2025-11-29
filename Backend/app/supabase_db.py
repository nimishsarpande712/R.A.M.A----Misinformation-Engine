import psycopg2
from dotenv import load_dotenv
import os
from typing import Optional, List, Dict

class SupabasePostgresConnection:
    def __init__(self):
        """Initialize the Supabase PostgreSQL connection."""
        # Load environment variables from .env
        load_dotenv()
        
        # Fetch variables
        self.user = os.getenv("user")
        self.password = os.getenv("password")
        self.host = os.getenv("host")
        self.port = os.getenv("port")
        self.dbname = os.getenv("dbname")
        self.connection: Optional[psycopg2.extensions.connection] = None
        self.cursor: Optional[psycopg2.extensions.cursor] = None
    
    def connect(self) -> bool:
        """
        Establish connection to Supabase PostgreSQL database.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.connection = psycopg2.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                dbname=self.dbname
            )
            print("Supabase PostgreSQL connection successful!")
            return True
            
        except Exception as e:
            print(f"Failed to connect to Supabase PostgreSQL: {e}")
            return False
    
    def get_cursor(self) -> Optional[psycopg2.extensions.cursor]:
        """
        Get a cursor for executing SQL queries.
        
        Returns:
            psycopg2.extensions.cursor: Database cursor or None if connection failed
        """
        if self.connection:
            self.cursor = self.connection.cursor()
            return self.cursor
        else:
            print("No active connection. Please connect first.")
            return None
    
    def execute_query(self, query: str, params: tuple = None) -> list:
        """
        Execute a SQL query and return results.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Query parameters
            
        Returns:
            list: Query results
        """
        try:
            if not self.connection:
                if not self.connect():
                    return []
            
            cursor = self.get_cursor()
            if cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # For SELECT queries, fetch results
                if query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    return results
                else:
                    # For INSERT, UPDATE, DELETE queries, commit changes
                    self.connection.commit()
                    return []
            
        except Exception as e:
            print(f"Error executing query: {e}")
            if self.connection:
                self.connection.rollback()
            return []
    
    def close(self) -> None:
        """Close the database connection."""
        try:
            if self.cursor:
                self.cursor.close()
                print("Cursor closed.")
            
            if self.connection:
                self.connection.close()
                print("Supabase PostgreSQL connection closed.")
                
        except Exception as e:
            print(f"Error closing connection: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# ========================================
# USER HISTORY & QUERY TRACKING
# ========================================

def create_user_history_table(db_connection: SupabasePostgresConnection) -> bool:
    """
    Create user_history table in Supabase for tracking all user queries and results.
    
    Schema:
    - id: Primary key
    - user_id: User identifier (can be session ID or hashed IP)
    - query_text: The claim/query text
    - verdict: Returned verdict
    - confidence: Confidence score
    - sources_count: Number of sources used
    - timestamp: Query timestamp
    - category: Query category
    - language: Query language
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS user_history (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(255),
        query_text TEXT NOT NULL,
        verdict VARCHAR(50),
        confidence FLOAT,
        sources_count INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        category VARCHAR(100),
        language VARCHAR(10),
        raw_response JSONB
    );
    
    CREATE INDEX IF NOT EXISTS idx_user_history_user_id ON user_history(user_id);
    CREATE INDEX IF NOT EXISTS idx_user_history_timestamp ON user_history(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_user_history_verdict ON user_history(verdict);
    """
    
    result = db_connection.execute_query(create_table_query)
    return True


def create_news_data_table(db_connection: SupabasePostgresConnection) -> bool:
    """
    Create news_data table in Supabase for storing all ingested news with metadata.
    
    Schema:
    - id: Primary key
    - title: News title
    - url: News URL (unique)
    - source: News source
    - body: Full article text
    - published_at: Publication timestamp
    - ingested_at: Ingestion timestamp
    - language: Article language
    - category: News category
    - verified: Whether fact-checked
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS news_data (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        url TEXT UNIQUE NOT NULL,
        source VARCHAR(255),
        body TEXT,
        published_at TIMESTAMP,
        ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        language VARCHAR(10) DEFAULT 'en',
        category VARCHAR(100),
        verified BOOLEAN DEFAULT FALSE,
        metadata JSONB
    );
    
    CREATE INDEX IF NOT EXISTS idx_news_data_source ON news_data(source);
    CREATE INDEX IF NOT EXISTS idx_news_data_published ON news_data(published_at DESC);
    CREATE INDEX IF NOT EXISTS idx_news_data_url ON news_data(url);
    CREATE INDEX IF NOT EXISTS idx_news_data_verified ON news_data(verified);
    """
    
    result = db_connection.execute_query(create_table_query)
    return True


def insert_user_query_history(
    db_connection: SupabasePostgresConnection,
    user_id: str,
    query_text: str,
    verdict: str,
    confidence: float,
    sources_count: int,
    category: str = None,
    language: str = "en",
    raw_response: dict = None
) -> bool:
    """
    Insert a user query into history table.
    """
    import json
    
    query = """
    INSERT INTO user_history 
    (user_id, query_text, verdict, confidence, sources_count, category, language, raw_response)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    params = (
        user_id,
        query_text,
        verdict,
        confidence,
        sources_count,
        category,
        language,
        json.dumps(raw_response) if raw_response else None
    )
    
    try:
        db_connection.execute_query(query, params)
        return True
    except Exception as e:
        print(f"Error inserting user history: {e}")
        return False


def get_user_history(
    db_connection: SupabasePostgresConnection,
    user_id: str,
    limit: int = 50
) -> List[Dict]:
    """
    Get user's query history.
    """
    query = """
    SELECT id, query_text, verdict, confidence, sources_count, 
           timestamp, category, language
    FROM user_history
    WHERE user_id = %s
    ORDER BY timestamp DESC
    LIMIT %s
    """
    
    results = db_connection.execute_query(query, (user_id, limit))
    
    history = []
    if results:
        for row in results:
            history.append({
                "id": row[0],
                "query_text": row[1],
                "verdict": row[2],
                "confidence": row[3],
                "sources_count": row[4],
                "timestamp": str(row[5]),
                "category": row[6],
                "language": row[7]
            })
    
    return history


def insert_news_data(
    db_connection: SupabasePostgresConnection,
    title: str,
    url: str,
    source: str,
    body: str,
    published_at: str = None,
    language: str = "en",
    category: str = None,
    metadata: dict = None
) -> bool:
    """
    Insert news data into Supabase.
    """
    import json
    
    query = """
    INSERT INTO news_data 
    (title, url, source, body, published_at, language, category, metadata)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (url) DO UPDATE SET
        title = EXCLUDED.title,
        body = EXCLUDED.body,
        published_at = EXCLUDED.published_at,
        metadata = EXCLUDED.metadata
    """
    
    params = (
        title,
        url,
        source,
        body,
        published_at,
        language,
        category,
        json.dumps(metadata) if metadata else None
    )
    
    try:
        db_connection.execute_query(query, params)
        return True
    except Exception as e:
        print(f"Error inserting news data: {e}")
        return False


def test_supabase_connection():
    """Test function to verify Supabase PostgreSQL connectivity."""
    # Load environment variables from .env
    load_dotenv()
    
    # Fetch variables
    USER = os.getenv("user")
    PASSWORD = os.getenv("password")
    HOST = os.getenv("host")
    PORT = os.getenv("port")
    DBNAME = os.getenv("dbname")
    
    # Connect to the database
    try:
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        print("Connection successful!")
        
        # Create a cursor to execute SQL queries
        cursor = connection.cursor()
        
        # Example query
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        print("Current Time:", result)

        # Close the cursor and connection
        cursor.close()
        connection.close()
        print("Connection closed.")
        
        return True

    except Exception as e:
        print(f"Failed to connect: {e}")
        return False


if __name__ == "__main__":
    # Test the connection
    print("Testing Supabase PostgreSQL connection...")
    test_supabase_connection()
    
    print("\nTesting with connection class...")
    # Test with the connection class
    with SupabasePostgresConnection() as db:
        result = db.execute_query("SELECT NOW();")
        if result:
            print("Current Time (via class):", result[0])