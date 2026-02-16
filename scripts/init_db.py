import os
import psycopg2
from api.config import get_settings

def init_db():
    settings = get_settings()
    
    # Path to the migration file
    migration_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'migrations', '001_initial.sql')
    
    if not os.path.exists(migration_path):
        print(f"Migration file not found at {migration_path}")
        return

    try:
        # Connect to the database
        conn = psycopg2.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            dbname=settings.POSTGRES_DB
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Read and execute the SQL file
        with open(migration_path, 'r') as f:
            sql = f.read()
            print("Executing migration 001_initial.sql...")
            cur.execute(sql)
            print("Migration executed successfully.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    init_db()
