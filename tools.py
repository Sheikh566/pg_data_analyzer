import re, os
import psycopg2
from psycopg2.extras import RealDictCursor, RealDictRow

from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )


def validate_select_query(query: str) -> bool:
    """
    Validate that the generated query is a SELECT statement only.

    Args:
        query: SQL query to validate

    Returns:
        True if valid SELECT query, False otherwise
    """
    # Remove comments and whitespace
    cleaned_query = re.sub(r'--.*?\n', '', query, flags=re.MULTILINE)
    cleaned_query = re.sub(r'/\*.*?\*/', '', cleaned_query, flags=re.DOTALL)
    cleaned_query = cleaned_query.strip()
    
    # Check if it starts with SELECT (case insensitive)
    if not re.match(r'^\s*SELECT\b', cleaned_query, re.IGNORECASE):
        return False
    
    # Check for forbidden statements
    forbidden_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE']
    for keyword in forbidden_keywords:
        if re.search(rf'\b{keyword}\b', cleaned_query, re.IGNORECASE):
            return False

    return True

def execute_query(query: str) -> dict[str, list[RealDictRow]]:
    """
    Execute a SQL SELECT query against the database.
    
    Args:
        query: SQL SELECT query to execute
        
    Returns:
        List of dictionaries containing query results
    """
    
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                return { 'result': results }
    except Exception as e:
        raise RuntimeError(f"Query execution failed: {str(e)}")

def get_database_schema() -> dict:
    """
    Get basic database schema information for context.
    
    Returns:
        Dictionary containing schema information with table names and columns
    """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get table names and basic column info
                cursor.execute(f"""
                    SELECT
                        table_name,
                        column_name,
                        data_type,
                        is_nullable
                    FROM information_schema.columns 
                    WHERE table_schema = '{os.getenv("DB_SCHEMA", "public")}'
                    ORDER BY table_name, ordinal_position
                """)
                
                schema_info = cursor.fetchall()

                # Format schema information
                tables: dict[str, list[dict[str, str]]] = {}
                for row in schema_info:
                    table_name = row['table_name']
                    if table_name not in tables:
                        tables[table_name] = []
                    tables[table_name].append({
                        'column': row['column_name'],
                        'type': row['data_type'],
                        'nullable': row['is_nullable']
                    })
                
                schema_text = "Database Schema:\n"
                for table_name, columns in tables.items():
                    schema_text += f"\nTable: {table_name}\n"
                    for col in columns:
                        nullable = "NULL" if col['nullable'] == 'YES' else "NOT NULL"
                        schema_text += f"  - {col['column']} ({col['type']}, {nullable})\n"
                
            return { 'schema': schema_text }
    except Exception as e:
        return { 'error': f"Encountered an error: {str(e)}" }

if __name__ == "__main__":
    # list all table names
    print(execute_query("""SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"""))