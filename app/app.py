import streamlit as st
import oracledb
import hashlib
import datetime
import pandas as pd
import os
import time



DB_USER = os.getenv("DB_USER", "new_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "1521")
DB_SERVICE = os.getenv("DB_SERVICE", "XEPDB1")


def init_db():
    try:
        with oracledb.connect(user="new_user", password="password", dsn="localhost:1521/XEPDB1") as conn:
            with conn.cursor() as cursor:
                # Create users table
                try:
                    cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'USERS'")
                    (table_exists,) = cursor.fetchone()

                    if not table_exists:
                        cursor.execute('''
                            CREATE TABLE users (
                                user_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                                username VARCHAR2(100) UNIQUE NOT NULL,
                                password VARCHAR2(255) NOT NULL,
                                user_type VARCHAR2(50) NOT NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''')
                    
                    
                except oracledb.DatabaseError as e:
                    error, = e.args
                    if error.code != 955:  
                        raise
                
                # Create donors table
                try:
                    cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'DONORS'")
                    (table_exists,) = cursor.fetchone()

                    if not table_exists:
                        cursor.execute('''
                        CREATE TABLE donors (
                            donor_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                            user_id NUMBER NOT NULL,
                            name VARCHAR2(100) NOT NULL,
                            email VARCHAR2(100),
                            phone VARCHAR2(50),
                            street VARCHAR2(200),
                            city VARCHAR2(100),
                            CONSTRAINT fk_donors_user_id FOREIGN KEY (user_id) REFERENCES users(user_id)
                        )
                        ''')
                except oracledb.DatabaseError as e:
                    error, = e.args
                    if error.code != 955:
                        raise
                
                
                
                # Create ngos table
                try:
                    cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'NGOS'")
                    (table_exists,) = cursor.fetchone()

                    if not table_exists:
                        cursor.execute('''
                        CREATE TABLE ngos (
                            ngo_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                            user_id NUMBER NOT NULL,
                            name VARCHAR2(100) NOT NULL,
                            email VARCHAR2(100),
                            phone VARCHAR2(50),
                            street VARCHAR2(200),
                            city VARCHAR2(100),
                            CONSTRAINT fk_ngos_user_id FOREIGN KEY (user_id) REFERENCES users(user_id)
                        )
                        ''')
                except oracledb.DatabaseError as e:
                    error, = e.args
                    if error.code != 955:
                        raise
                
                
                
                # Create food_donations table
                try:
                    cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'FOOD_DONATIONS'")
                    (table_exists,) = cursor.fetchone()

                    if not table_exists:
                        cursor.execute('''
                        CREATE TABLE food_donations (
                            donation_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                            donor_id NUMBER NOT NULL,
                            ngo_id NUMBER,
                            food_type VARCHAR2(100) NOT NULL,
                            donation_date DATE NOT NULL,
                            expiry_date DATE NOT NULL,
                            quantity NUMBER NOT NULL,
                            status VARCHAR2(50) DEFAULT 'Available',
                            CONSTRAINT fk_food_donations_donor_id FOREIGN KEY (donor_id) REFERENCES donors(donor_id),
                            CONSTRAINT fk_food_donations_ngo_id FOREIGN KEY (ngo_id) REFERENCES ngos(ngo_id)
                        )
                        ''')
                except oracledb.DatabaseError as e:
                    error, = e.args
                    if error.code != 955:
                        raise

                # Add trigger to check donation date
                try:
                    cursor.execute("""
                    CREATE OR REPLACE TRIGGER check_donation_date
                    BEFORE INSERT ON food_donations
                    FOR EACH ROW
                    DECLARE
                        v_days NUMBER;
                    BEGIN
                        v_days := :NEW.expiry_date - :NEW.donation_date;
                        IF v_days < 0 THEN
                            RAISE_APPLICATION_ERROR(-20001, 'Expiry date cannot be before donation date');
                        END IF;
                    END;
                    """)
                    
                except oracledb.DatabaseError as e:
                    error, = e.args
                    if error.code != 955:
                        raise
                
                # Create requests table
                try:
                    cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'REQUESTS'")
                    (table_exists,) = cursor.fetchone()

                    if not table_exists:
                        cursor.execute('''
                        CREATE TABLE requests (
                            request_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                            ngo_id NUMBER NOT NULL,
                            food_type VARCHAR2(100) NOT NULL,
                            quantity NUMBER NOT NULL,
                            request_date DATE NOT NULL,
                            status VARCHAR2(50) DEFAULT 'Pending',
                            donation_id NUMBER,
                            CONSTRAINT fk_requests_ngo_id FOREIGN KEY (ngo_id) REFERENCES ngos(ngo_id),
                            CONSTRAINT fk_requests_donation_id FOREIGN KEY (donation_id) REFERENCES food_donations(donation_id)
                        )
                        ''')
                except oracledb.DatabaseError as e:
                    error, = e.args
                    if error.code != 955:
                        raise
                
                
                
                
                conn.commit()
                
    except oracledb.DatabaseError as e:
        print(f"Database error: {e}")
        raise

# Authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, user_type):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                user_id_var = cursor.var(oracledb.NUMBER)  # Create bind variable
                cursor.execute(
                    "INSERT INTO users (username, password, user_type) VALUES (:1, :2, :3) RETURNING user_id INTO :4",
                    [username, hash_password(password), user_type, user_id_var]
                )
                user_id = user_id_var.getvalue()[0]  
                conn.commit()
                return user_id
    except oracledb.IntegrityError:
        return None

def authenticate(username, password):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT user_id, user_type FROM users WHERE username = :1 AND password = :2",
                    [username, hash_password(password)]
                )
                result = cursor.fetchone()
                
                if result:
                    return {"user_id": result[0], "user_type": result[1]}
                return None
    except oracledb.DatabaseError:
        return None

# Donor functions
def register_donor(user_id, name, email, phone, street, city):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                # Create the bind variable for donor_id
                donor_id_var = cursor.var(oracledb.NUMBER)
                
                # Insert into donors table
                cursor.execute(
                    "INSERT INTO donors (user_id, name, email, phone, street, city) VALUES (:1, :2, :3, :4, :5, :6) RETURNING donor_id INTO :7",
                    [user_id, name, email, phone, street, city, donor_id_var]
                )
                
                donor_id = donor_id_var.getvalue()[0]  # Get the returned donor_id
                
                conn.commit()
                return donor_id
    except oracledb.DatabaseError as e:
        print(f"Error in register_donor: {e}")
        return None


def get_donor_id_by_user_id(user_id):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT donor_id FROM donors WHERE user_id = :1", [user_id])
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                return None
    except oracledb.DatabaseError:
        return None

def get_donor_info(donor_id):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                SELECT d.name, d.email, d.phone, d.street, d.city
                FROM donors d
                WHERE d.donor_id = :1
                ''', [donor_id])
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        "name": result[0],
                        "email": result[1],
                        "phone": result[2],
                        "street": result[3],
                        "city": result[4]
                    }
                return None
    except oracledb.DatabaseError as e:
        print(f"Error in get_donor_info: {e}")
        return None

def create_donation(donor_id, food_type, donation_date, expiry_date, quantity, ngo_id=None):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                status = 'Assigned' if ngo_id else 'Available'
                
                # Create a bind variable to capture the donation_id
                donation_id_var = cursor.var(oracledb.NUMBER)
                
                cursor.execute('''
                    INSERT INTO food_donations 
                    (donor_id, food_type, donation_date, expiry_date, quantity, ngo_id, status) 
                    VALUES (:1, :2, TO_DATE(:3, 'YYYY-MM-DD'), TO_DATE(:4, 'YYYY-MM-DD'), :5, :6, :7)
                    RETURNING donation_id INTO :8
                ''', [donor_id, food_type, donation_date, expiry_date, quantity, ngo_id, status, donation_id_var])
                
                donation_id = donation_id_var.getvalue()[0]
                conn.commit()
                return donation_id
    except oracledb.DatabaseError as e:
        print(f"Error in create_donation: {e}")
        return None


def get_donor_donations(donor_id):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                SELECT fd.donation_id, fd.food_type, 
                       TO_CHAR(fd.donation_date, 'YYYY-MM-DD') as donation_date, 
                       TO_CHAR(fd.expiry_date, 'YYYY-MM-DD') as expiry_date, 
                       fd.quantity, fd.status, NVL(n.name, 'None') as ngo_name
                FROM food_donations fd
                LEFT JOIN ngos n ON fd.ngo_id = n.ngo_id
                WHERE fd.donor_id = :1
                ORDER BY fd.donation_date DESC
                ''', [donor_id])
                
                columns = ['donation_id', 'food_type', 'donation_date', 'expiry_date', 
                           'quantity', 'status', 'ngo_name']
                
                result = []
                for row in cursor:
                    result.append(dict(zip(columns, row)))
                
                return result
    except oracledb.DatabaseError as e:
        print(f"Error in get_donor_donations: {e}")
        return []

# NGO functions
def register_ngo(user_id, name, email, phone, street, city):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                # Create bind variable for ngo_id
                ngo_id_var = cursor.var(oracledb.NUMBER)

                # Insert into ngos table
                cursor.execute(
                    "INSERT INTO ngos (user_id, name, email, phone, street, city) VALUES (:1, :2, :3, :4, :5, :6) RETURNING ngo_id INTO :7",
                    [user_id, name, email, phone, street, city, ngo_id_var]
                )
                ngo_id = ngo_id_var.getvalue()[0]  # Get actual value

                conn.commit()
                return ngo_id
    except oracledb.DatabaseError as e:
        print(f"Error in register_ngo: {e}")
        return None


def get_ngo_id_by_user_id(user_id):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT ngo_id FROM ngos WHERE user_id = :1", [user_id])
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                return None
    except oracledb.DatabaseError:
        return None

def get_ngo_info(ngo_id):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                
                cursor.execute('''
                SELECT n.name, n.email, n.phone, n.street, n.city
                FROM ngos n
                WHERE n.ngo_id = :1
                ''', [ngo_id])
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        "name": result[0],
                        "email": result[1],
                        "phone": result[2],
                        "street": result[3],
                        "city": result[4]
                    }
                return None
    except oracledb.DatabaseError as e:
        print(f"Error in get_ngo_info: {e}")
        return None

def create_request(ngo_id, food_type, quantity):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                request_date = datetime.date.today().isoformat()
                
                # Create bind variable for request_id
                request_id_var = cursor.var(oracledb.NUMBER)
                
                cursor.execute('''
                    INSERT INTO requests (ngo_id, food_type, quantity, request_date, status) 
                    VALUES (:1, :2, :3, TO_DATE(:4, 'YYYY-MM-DD'), 'Pending')
                    RETURNING request_id INTO :5
                ''', [ngo_id, food_type, quantity, request_date, request_id_var])
                
                request_id = request_id_var.getvalue()[0]  # Retrieve actual ID
                conn.commit()
                return request_id
    except oracledb.DatabaseError as e:
        print(f"Error in create_request: {e}")
        return None

def get_all_pending_requests():
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                SELECT r.request_id, r.food_type, r.quantity, 
                       TO_CHAR(r.request_date, 'YYYY-MM-DD') as request_date, 
                       r.status, n.ngo_id, n.name as ngo_name
                FROM requests r
                JOIN ngos n ON r.ngo_id = n.ngo_id
                WHERE r.status = 'Pending'
                ORDER BY r.request_date
                ''')
                
                columns = ['request_id', 'food_type', 'quantity', 'request_date', 
                           'status', 'ngo_id', 'ngo_name']
                
                result = []
                for row in cursor:
                    result.append(dict(zip(columns, row)))
                
                return result
    except oracledb.DatabaseError as e:
        print(f"Error in get_all_pending_requests: {e}")
        return []

def create_donation(donor_id, food_type, donation_date, expiry_date, quantity, ngo_id):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                # Create a bind variable to capture the donation_id
                donation_id_var = cursor.var(oracledb.NUMBER)
                
                cursor.execute('''
                    INSERT INTO food_donations 
                    (donor_id, food_type, donation_date, expiry_date, quantity, ngo_id, status) 
                    VALUES (:1, :2, TO_DATE(:3, 'YYYY-MM-DD'), TO_DATE(:4, 'YYYY-MM-DD'), :5, :6, 'Assigned')
                    RETURNING donation_id INTO :7
                ''', [donor_id, food_type, donation_date, expiry_date, quantity, ngo_id, donation_id_var])
                
                donation_id = donation_id_var.getvalue()[0]
                conn.commit()
                return donation_id
    except oracledb.DatabaseError as e:
        print(f"Error in create_donation: {e}")
        return None

def create_donation_for_request(donor_id, food_type, donation_date, expiry_date, quantity, ngo_id, request_id):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                # Create a bind variable to capture the donation_id
                donation_id_var = cursor.var(oracledb.NUMBER)
                
                # Insert the donation
                cursor.execute('''
                    INSERT INTO food_donations 
                    (donor_id, food_type, donation_date, expiry_date, quantity, ngo_id, status) 
                    VALUES (:1, :2, TO_DATE(:3, 'YYYY-MM-DD'), TO_DATE(:4, 'YYYY-MM-DD'), :5, :6, 'Assigned')
                    RETURNING donation_id INTO :7
                ''', [donor_id, food_type, donation_date, expiry_date, quantity, ngo_id, donation_id_var])
                
                donation_id = donation_id_var.getvalue()[0]
                
                # Update request with donation_id and status
                cursor.execute('''
                    UPDATE requests 
                    SET status = 'Fulfilled',
                        donation_id = :1
                    WHERE request_id = :2
                ''', [donation_id, request_id])
                
                conn.commit()
                return donation_id
    except oracledb.DatabaseError as e:
        print(f"Error in create_donation_for_request: {e}")
        return None





def get_ngo_requests(ngo_id):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                # Create and call PL/SQL procedure
                plsql = """
                CREATE OR REPLACE PROCEDURE get_ngo_request_count(
                    p_ngo_id IN NUMBER,
                    p_count OUT NUMBER
                ) IS
                BEGIN
                    SELECT COUNT(*) INTO p_count 
                    FROM requests 
                    WHERE ngo_id = p_ngo_id;
                END;
                """
                
                # Create procedure
                cursor.execute(plsql)
                
                # Create output variable
                count_var = cursor.var(oracledb.NUMBER)
                
                # Execute procedure
                cursor.callproc("get_ngo_request_count", [ngo_id, count_var])
                
                # If no requests, return empty list
                if count_var.getvalue() == 0:
                    return []
                    
                # If has requests, get them with regular SQL
                cursor.execute('''
                    SELECT request_id, food_type, quantity, 
                           TO_CHAR(request_date, 'YYYY-MM-DD') as request_date, 
                           status
                    FROM requests
                    WHERE ngo_id = :1
                    ORDER BY request_date DESC
                ''', [ngo_id])
                
                columns = ['request_id', 'food_type', 'quantity', 'request_date', 'status']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
    except oracledb.DatabaseError as e:
        print(f"Error in get_ngo_requests: {e}")
        return []

def get_all_ngos():
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT ngo_id, name FROM ngos ORDER BY name")
                return cursor.fetchall()
    except oracledb.DatabaseError as e:
        print(f"Error in get_all_ngos: {e}")
        return []

# Analytics functions
def get_donation_statistics():
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                # Using GROUP BY for analytics
                cursor.execute('''
                SELECT 
                    food_type, 
                    COUNT(donation_id) as total_donations,
                    SUM(quantity) as total_quantity,
                    AVG(quantity) as avg_quantity,
                    TO_CHAR(MIN(donation_date), 'YYYY-MM-DD') as first_donation,
                    TO_CHAR(MAX(donation_date), 'YYYY-MM-DD') as last_donation
                FROM food_donations
                GROUP BY food_type
                ORDER BY total_quantity DESC
                ''')
                
                columns = ['food_type', 'total_donations', 'total_quantity', 
                           'avg_quantity', 'first_donation', 'last_donation']
                
                result = []
                for row in cursor:
                    result.append(dict(zip(columns, row)))
                
                return result
    except oracledb.DatabaseError as e:
        print(f"Error in get_donation_statistics: {e}")
        return []

def get_donation_trends():
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                # Using Oracle's date functions for analytics
                cursor.execute('''
                SELECT 
                    TO_CHAR(donation_date, 'YYYY-MM') as month,
                    COUNT(donation_id) as donation_count,
                    SUM(quantity) as total_quantity,
                    (SELECT COUNT(DISTINCT donor_id) 
                     FROM food_donations fd2 
                     WHERE TO_CHAR(fd2.donation_date, 'YYYY-MM') = TO_CHAR(fd.donation_date, 'YYYY-MM')
                    ) as active_donors
                FROM food_donations fd
                WHERE donation_date >= ADD_MONTHS(TRUNC(SYSDATE), -12)
                GROUP BY TO_CHAR(donation_date, 'YYYY-MM')
                ORDER BY month
                ''')
                
                columns = ['month', 'donation_count', 'total_quantity', 'active_donors']
                
                result = []
                for row in cursor:
                    result.append(dict(zip(columns, row)))
                
                return result
    except oracledb.DatabaseError as e:
        print(f"Error in get_donation_trends: {e}")
        return []

def get_ngo_donation_distribution():
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                # Using JOIN and GROUP BY together
                cursor.execute('''
                SELECT 
                    n.name as ngo_name,
                    COUNT(fd.donation_id) as donations_received,
                    SUM(fd.quantity) as total_quantity
                FROM ngos n
                JOIN food_donations fd ON n.ngo_id = fd.ngo_id
                GROUP BY n.ngo_id, n.name
                ORDER BY total_quantity DESC
                ''')
                
                columns = ['ngo_name', 'donations_received', 'total_quantity']
                
                result = []
                for row in cursor:
                    result.append(dict(zip(columns, row)))
                
                return result
    except oracledb.DatabaseError as e:
        print(f"Error in get_ngo_donation_distribution: {e}")
        return []

def get_top_donors():
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                # Create PL/SQL function
                plsql = """
                CREATE OR REPLACE FUNCTION get_donor_count
                RETURN NUMBER IS
                    v_count NUMBER;
                BEGIN
                    SELECT COUNT(DISTINCT donor_id) 
                    INTO v_count 
                    FROM food_donations;
                    RETURN v_count;
                END;
                """
                
                # Create function
                cursor.execute(plsql)
                
                # Create output variable and execute function correctly
                result = cursor.var(oracledb.NUMBER)
                cursor.execute("BEGIN :result := get_donor_count(); END;", {'result': result})
                donor_count = result.getvalue()
                
                # If no donors, return empty list
                if donor_count == 0:
                    return []
                    
                # If has donors, get them with regular SQL
                cursor.execute('''
                    SELECT 
                        d.name as donor_name,
                        COUNT(fd.donation_id) as donation_count,
                        SUM(fd.quantity) as total_donated
                    FROM donors d
                    JOIN food_donations fd ON d.donor_id = fd.donor_id
                    GROUP BY d.donor_id, d.name
                    ORDER BY total_donated DESC
                    FETCH FIRST 10 ROWS ONLY
                ''')
                
                columns = ['donor_name', 'donation_count', 'total_donated']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
    except oracledb.DatabaseError as e:
        print(f"Error in get_top_donors: {e}")
        return []

# Main Streamlit app
def main():
    
    # Initialize the database
    init_db()
    # Set page configuration and custom CSS
    st.set_page_config(
        page_title="Food Waste Management System",
        page_icon="🍽️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for a professional look
    st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton button {
        background-color: #1E88E5;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stTextInput > div > div > input {
        border-radius: 5px;
    }
    .st-eb {
        border-radius: 5px;
    }
    h1, h2, h3 {
        color: #1E3A8A;
    }
    .highlight {
        background-color: #f0f7ff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1E88E5;
        color: black;
    }
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        color: black;
    }
    .success-message {
        background-color: #D5F5E3;
        color: #196F3D;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .error-message {
        background-color: #FADBD8;
        color: #943126;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .info-message {
        background-color: #D6EAF8;
        color: #21618C;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .dashboard-stats {
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
    }
    .stat-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 10px 0;
        min-width: 200px;
        flex: 1;
        margin-right: 10px;
        color: black;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Session state initialization
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
    if 'entity_id' not in st.session_state:
        st.session_state.entity_id = None
    
    # Navigation based on authentication state
    if not st.session_state.authenticated:
        show_login_page()
    else:
        if st.session_state.user_type == 'Donor':
            show_donor_dashboard()
        elif st.session_state.user_type == 'NGO':
            show_ngo_dashboard()

def show_login_page():
    st.title("Food Waste Management System")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        <div class="card">
        <h2>Welcome to the Food Waste Management System</h2>
        <p>Our platform connects food donors with NGOs to reduce food waste and help those in need.</p>
        <ul>
            <li>Donors can contribute excess food</li>
            <li>NGOs can request and receive food donations</li>
            <li>Track donations and requests in real-time</li>
            <li>Make a positive impact on the environment and society</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-message">
        Please login or sign up to start using the platform.
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.subheader("Login")
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            
            login_col1, login_col2 = st.columns([1, 1])
            with login_col1:
                if st.button("Login", key="login_button"):
                    if login_username and login_password:
                        user = authenticate(login_username, login_password)
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.user_id = user["user_id"]
                            st.session_state.user_type = user["user_type"]
                            
                            if user["user_type"] == "Donor":
                                st.session_state.entity_id = get_donor_id_by_user_id(user["user_id"])
                            else:
                                st.session_state.entity_id = get_ngo_id_by_user_id(user["user_id"])
                            
                            st.success(f"Welcome back! You're logged in as a {user['user_type']}.")
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")
                    else:
                        st.warning("Please enter both username and password.")
        
        with tab2:
            st.subheader("Sign Up")
            signup_username = st.text_input("Username", key="signup_username")
            signup_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            user_type = st.selectbox("I am a", ["Donor", "NGO"])
            
            name = st.text_input("Name (Individual/Organization)")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            
            col1, col2 = st.columns(2)
            with col1:
                street = st.text_input("Street Address")
            with col2:
                city = st.text_input("City")
            
            if st.button("Sign Up"):
                if signup_password != confirm_password:
                    st.error("Passwords do not match.")
                elif not (signup_username and signup_password and name and email and phone and street and city):
                    st.warning("Please fill in all fields.")
                else:
                    user_id = register_user(signup_username, signup_password, user_type)
                    
                    if user_id:
                        if user_type == "Donor":
                            entity_id = register_donor(user_id, name, email, phone, street, city)
                            st.session_state.entity_id = entity_id
                        else:  # NGO
                            entity_id = register_ngo(user_id, name, email, phone, street, city)
                            st.session_state.entity_id = entity_id
                        
                        st.session_state.authenticated = True
                        st.session_state.user_id = user_id
                        st.session_state.user_type = user_type
                        
                        st.success("Account created successfully!")
                        st.rerun()
                    else:
                        st.error("Username already exists. Please choose a different username.")

def show_donor_dashboard():
    st.title("Donor Dashboard")
    
    # Get donor information
    donor_info = get_donor_info(st.session_state.entity_id)
    
    # Sidebar with donor info and logout button
    with st.sidebar:
        st.header(f"Welcome, {donor_info['name']}")
        st.write(f"📧 {donor_info['email']}")
        st.write(f"📱 {donor_info['phone']}")
        st.write(f"📍 {donor_info['street']}, {donor_info['city']}")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.user_type = None
            st.session_state.entity_id = None
            st.rerun()
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["Donate Food", "My Donations", "NGO Requests", "Analytics"])
    
    with tab1:
        st.header("Donate Food")
        
        st.markdown("""
        <div class="highlight">
        Help reduce food waste by donating your excess food to those in need.
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            food_type = st.text_input("Food Type (e.g., Fruits, Vegetables, Prepared Meals)")
            quantity = st.number_input("Quantity (kg)", min_value=0.1, step=0.1)
            
        with col2:
            donation_date = st.date_input("Donation Date", datetime.date.today())
            expiry_date = st.date_input("Expiry Date", datetime.date.today() + datetime.timedelta(days=3))
        
        # Get list of all NGOs
        ngos = get_all_ngos()
        ngo_options = ngos  # Remove the optional empty selection
        if not ngo_options:
            st.error("No NGOs are registered in the system. Donations cannot be made at this time.")
        else:
            selected_ngo = st.selectbox("Select NGO to donate to (Required)", ngo_options, format_func=lambda x: x[1])
        
        if st.button("Submit Donation"):
            if food_type and quantity > 0 and donation_date and expiry_date and selected_ngo:
                if expiry_date < donation_date:
                    st.error("Expiry date cannot be before donation date.")
                else:
                    ngo_id = selected_ngo[0]
                    
                    donation_id = create_donation(
                        st.session_state.entity_id,
                        food_type,
                        donation_date.isoformat(),
                        expiry_date.isoformat(),
                        quantity,
                        ngo_id
                    )
                    
                    if donation_id:
                        st.success("Donation submitted successfully! Thank you for your contribution.")
                    else:
                        st.error("Failed to submit donation. Please try again.")
            else:
                st.warning("Please fill in all required fields.")
    
    with tab2:
        st.header("My Donations")
        
        donations = get_donor_donations(st.session_state.entity_id)
        
        if not donations:
            st.info("You haven't made any donations yet.")
        else:
            df = pd.DataFrame(donations)
            
            # Format DataFrame
            df['donation_date'] = pd.to_datetime(df['donation_date']).dt.strftime('%b %d, %Y')
            df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.strftime('%b %d, %Y')
            df['quantity'] = df['quantity'].apply(lambda x: f"{x} kg")
            
            st.dataframe(
                df.rename(columns={
                    'donation_id': 'ID',
                    'food_type': 'Food Type',
                    'donation_date': 'Donation Date',
                    'expiry_date': 'Expiry Date',
                    'quantity': 'Quantity',
                    'status': 'Status',
                    'ngo_name': 'NGO'
                }),
                use_container_width=True
            )

    with tab3:
        st.header("NGO Food Requests")
        
        st.markdown("""
        <div class="highlight">
        Help fulfill specific food requests from NGOs. Your donations make a difference!
        </div>
        """, unsafe_allow_html=True)
        
        # Get all pending requests from NGOs
        all_requests = get_all_pending_requests()
        
        if not all_requests:
            st.info("There are no pending requests from NGOs at the moment.")
        else:
            for req in all_requests:
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="card">
                        <h3>{req['food_type']}</h3>
                        <p><strong>NGO:</strong> {req['ngo_name']}</p>
                        <p><strong>Quantity Needed:</strong> {req['quantity']} kg</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="card">
                        <p><strong>Request Date:</strong> {req['request_date']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    if st.button("Donate This", key=f"donate_req_{req['request_id']}"):
                        st.session_state.donating_to_request = req
                        st.rerun()
                        
        # Handle donation form for request
        if 'donating_to_request' in st.session_state and st.session_state.donating_to_request:
            req = st.session_state.donating_to_request
            st.markdown(f"""
            <div class="highlight">
            You are donating to fulfill a request from {req['ngo_name']} for {req['quantity']} kg of {req['food_type']}.
            </div>
            """, unsafe_allow_html=True)
            
            # Add unique keys to the date_input widgets
            donation_date = st.date_input(
                "Donation Date", 
                datetime.date.today(),
                key=f"request_donation_date_{req['request_id']}"
            )
            expiry_date = st.date_input(
                "Expiry Date", 
                datetime.date.today() + datetime.timedelta(days=3),
                key=f"request_expiry_date_{req['request_id']}"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm Donation"):
                    if donation_date and expiry_date:
                        if expiry_date < donation_date:
                            st.error("Expiry date cannot be before donation date.")
                        else:
                            # Create donation linked to this request
                            donation_id = create_donation_for_request(
                                st.session_state.entity_id,
                                req['food_type'],
                                donation_date.isoformat(),
                                expiry_date.isoformat(),
                                req['quantity'],
                                req['ngo_id'],
                                req['request_id']
                            )
                            
                            if donation_id:
                                st.success("Donation submitted successfully! Thank you for your contribution.")
                                del st.session_state.donating_to_request
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to submit donation. Please try again.")
            
            with col2:
                if st.button("Cancel"):
                    del st.session_state.donating_to_request
                    st.rerun()
    
    with tab4:
        st.header("Donation Analytics")
        
        # Get analytics data
        donation_stats = get_donation_statistics()
        top_donors = get_top_donors()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Food Type Distribution")
            if donation_stats:
                chart_data = pd.DataFrame(donation_stats)
                chart_data = chart_data[['food_type', 'total_quantity']]
                st.bar_chart(chart_data.set_index('food_type'))
            else:
                st.info("No donation data available for analytics.")
        
        with col2:
            st.subheader("Your Contribution")
            donor_donations = get_donor_donations(st.session_state.entity_id)
            
            # Calculate total quantity donated by the current donor
            total_donated = sum(float(d['quantity']) for d in donor_donations) if donor_donations else 0
            
            st.markdown(f"""
            <div class="stat-card">
                <h3>Total Donations</h3>
                <p style="font-size: 24px; font-weight: bold;">{len(donor_donations)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="stat-card">
                <h3>Total Quantity</h3>
                <p style="font-size: 24px; font-weight: bold;">{total_donated:.2f} kg</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.subheader("Top Donors")
        if top_donors:
            top_donors_df = pd.DataFrame(top_donors)
            top_donors_df['total_donated'] = top_donors_df['total_donated'].apply(lambda x: f"{x:.2f} kg")
            
            st.dataframe(
                top_donors_df.rename(columns={
                    'donor_name': 'Donor',
                    'donation_count': 'Donations',
                    'total_donated': 'Total Donated'
                }),
                use_container_width=True
            )
        else:
            st.info("No donor data available for ranking.")

def show_ngo_dashboard():
    st.title("NGO Dashboard")
    
    # Get NGO information
    ngo_info = get_ngo_info(st.session_state.entity_id)
    
    # Sidebar with NGO info and logout button
    with st.sidebar:
        st.header(f"Welcome, {ngo_info['name']}")
        st.write(f"📧 {ngo_info['email']}")
        st.write(f"📱 {ngo_info['phone']}")
        st.write(f"📍 {ngo_info['street']}, {ngo_info['city']}")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.user_type = None
            st.session_state.entity_id = None
            st.rerun()
    
    # Main content
    # Replace the tab definition line in show_ngo_dashboard():
    # Main content
    tab1, tab2, tab3 = st.tabs(["My Requests", "Make Request", "Analytics"])
    
    with tab1:
        st.header("My Requests")
        
        requests = get_ngo_requests(st.session_state.entity_id)
        
        if not requests:
            st.info("You haven't made any requests yet.")
        else:
            for request in requests:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="card">
                        <h3>{request['food_type']}</h3>
                        <p><strong>Quantity:</strong> {request['quantity']} kg</p>
                        <p><strong>Date:</strong> {request['request_date']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    status_color = {
                        "Pending": "#FFB74D",  # Orange
                        "Fulfilled": "#81C784",  # Green
                        "Cancelled": "#E57373"  # Red
                    }.get(request['status'], "#64B5F6")  # Default blue
                    
                    st.markdown(f"""
                    <div class="card">
                        <p style="background-color: {status_color}; padding: 10px; border-radius: 5px; text-align: center; color: white;">
                            <strong>{request['status']}</strong>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab2:
        st.header("Make Request")
        
        st.markdown("""
        <div class="highlight">
        Submit a request for the type of food your organization needs.
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            request_food_type = st.text_input("Food Type Needed")
        
        with col2:
            request_quantity = st.number_input("Quantity Needed (kg)", min_value=0.1, step=0.1)
        
        if st.button("Submit Request"):
            if request_food_type and request_quantity > 0:
                request_id = create_request(
                    st.session_state.entity_id,
                    request_food_type,
                    request_quantity
                )
                
                if request_id:
                    st.success("Request submitted successfully! We will try to match you with available donations.")
                else:
                    st.error("Failed to submit request. Please try again.")
            else:
                st.warning("Please fill in all required fields.")
    
    with tab3:
        st.header("Donation Analytics")
        
        # Get analytics data
        donation_trends = get_donation_trends()
        ngo_distribution = get_ngo_donation_distribution()
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Monthly Donation Trends")
            if donation_trends:
                trend_data = pd.DataFrame(donation_trends)
                st.line_chart(trend_data.set_index('month')['total_quantity'])
            else:
                st.info("No trend data available.")
        
        with col2:
            st.subheader("NGO Distribution")
            if ngo_distribution:
                ngo_data = pd.DataFrame(ngo_distribution)
                st.bar_chart(ngo_data.set_index('ngo_name')['total_quantity'])
            else:
                st.info("No NGO distribution data available.")

if __name__ == "__main__":
    main()