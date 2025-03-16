import sqlite3

# Path to your database
db_path = 'c:/Users/SAMSUNG/Desktop/MINI/real_backend/db.sqlite'

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in database:", tables)

    # Check the schema of the users table
    cursor.execute("PRAGMA table_info(users);")
    schema = cursor.fetchall()
    print("Users table schema:", schema)

    # Fetch and display all users with all columns
    cursor.execute("SELECT * FROM users;")
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            # Convert Row object to dictionary dynamically including all columns
            user = dict(row)
            print("User:", user)
    else:
        print("No users found in database")

    # Close the connection
    conn.close()
except Exception as e:
    print(f"Error accessing database: {e}")