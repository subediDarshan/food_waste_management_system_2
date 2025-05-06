import oracledb
import os

# Database configuration
DB_USER = os.getenv("DB_USER", "new_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "1521")
DB_SERVICE = os.getenv("DB_SERVICE", "XEPDB1")

def reset_database():
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}") as conn:
            with conn.cursor() as cursor:
                # First drop trigger
                try:
                    cursor.execute("DROP TRIGGER check_donation_date")
                    print("Dropped trigger: check_donation_date")
                except oracledb.DatabaseError:
                    print("Trigger check_donation_date does not exist")

                # Drop tables in correct order (child tables first)
                tables = [
                    "request_donations",      # Links between requests and donations
                    "food_donations",         # Contains donations
                    "requests",              # Contains requests
                    "donors",                # Donor main table with contact & address
                    "ngos",                  # NGO main table with contact & address
                    "users"                  # Users table (parent table)
                ]

                for table in tables:
                    try:
                        cursor.execute(f"DROP TABLE {table} CASCADE CONSTRAINTS")
                        print(f"Dropped table: {table}")
                    except oracledb.DatabaseError:
                        print(f"Table {table} does not exist")

                conn.commit()
                print("\nDatabase reset completed successfully!")

    except oracledb.DatabaseError as e:
        print(f"Error resetting database: {e}")
        return False

if __name__ == "__main__":
    print("Starting database reset...")
    reset_database()