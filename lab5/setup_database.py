import pymysql
import time
from db_config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# Function to connect to the database with retries
def connect_to_db():
    retries = 5
    for i in range(retries):
        try:
            print("Attempting to connect to the database...")
            conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                connect_timeout=10
            )
            print("✅ Database connection successful!")
            return conn
        except pymysql.err.OperationalError as e:
            print(f"Connection failed: {e}. Retrying in 15 seconds...")
            time.sleep(15)
    raise Exception("Could not connect to the database after several retries.")

# Main logic
try:
    connection = connect_to_db()
    cursor = connection.cursor()
    
    print("Creating the 'feedback' table... [cite: 4]")
    
    # SQL statement to create the table [cite: 19]
    create_table_query = """
    CREATE TABLE IF NOT EXISTS feedback (
        id INT AUTO_INCREMENT PRIMARY KEY,
        author VARCHAR(100) NOT NULL,
        comment TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    cursor.execute(create_table_query)
    connection.commit()
    
    print("✅ 'feedback' table created successfully.")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if 'connection' in locals() and connection.open:
        cursor.close()
        connection.close()
        print("Database connection closed.")