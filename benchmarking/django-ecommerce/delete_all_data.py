import sqlite3

# Replace with the path to your SQLite database file
db_file = '/home/annie/django-ecommerce/django-ecommerce/db.sqlite3'

def delete_all_data():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Get a list of all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        # Delete all rows from each table
        cursor.execute(f"DELETE FROM {table_name};")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    delete_all_data()

