
# app.py
import streamlit as st
import oracledb
import hashlib
import datetime
import pandas as pd
from PIL import Image
import os
import time
import base64
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_USER = os.getenv("DB_USER", "new_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "1521")
DB_SERVICE = os.getenv("DB_SERVICE", "XEPDB1")

# Initialize DB and create tables
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
                                password_hash VARCHAR2(255) NOT NULL,
                                user_type VARCHAR2(50) NOT NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''')
                    
                    
                except oracledb.DatabaseError as e:
                    error, = e.args
                    if error.code != 955:  # ORA-00955: name is already used by an existing object
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
                            CONSTRAINT fk_donors_user_id FOREIGN KEY (user_id) REFERENCES users(user_id)
                        )
                        ''')
                except oracledb.DatabaseError as e:
                    error, = e.args
                    if error.code != 955:
                        raise
                
                # Create donor_contacts table
                try:
                    cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'DONOR_CONTACTS'")
                    (table_exists,) = cursor.fetchone()

                    if not table_exists:
                        cursor.execute('''
                        CREATE TABLE donor_contacts (
                            contact_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                            donor_id NUMBER NOT NULL,
                            email VARCHAR2(100),
                            phone VARCHAR2(50),
                            CONSTRAINT fk_donor_contacts_donor_id FOREIGN KEY (donor_id) REFERENCES donors(donor_id)
                        )
                        ''')
                except oracledb.DatabaseError as e:
                    error, = e.args
                    if error.code != 955:
                        raise
                
                # Create donor_addresses table
                try:
                    cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'DONOR_ADDRESSES'")
                    (table_exists,) = cursor.fetchone()

                    if not table_exists:
                        cursor.execute('''
                        CREATE TABLE donor_addresses (
                            address_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                            donor_id NUMBER NOT NULL,
                            street VARCHAR2(200),
                            city VARCHAR2(100),
                            CONSTRAINT fk_donor_addresses_donor_id FOREIGN KEY (donor_id) REFERENCES donors(donor_id)
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
                            CONSTRAINT fk_ngos_user_id FOREIGN KEY (user_id) REFERENCES users(user_id)
                        )
                        ''')
                except oracledb.DatabaseError as e:
                    error, = e.args
                    if error.code != 955:
                        raise
                
                # Create ngo_contacts table
                try:
                    cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'NGO_CONTACTS'")
                    (table_exists,) = cursor.fetchone()

                    if not table_exists:
                        cursor.execute('''
                        CREATE TABLE ngo_contacts (
                            contact_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                            ngo_id NUMBER NOT NULL,
                            email VARCHAR2(100),
                            phone VARCHAR2(50),
                            CONSTRAINT fk_ngo_contacts_ngo_id FOREIGN KEY (ngo_id) REFERENCES ngos(ngo_id)
                        )
                        ''')
                except oracledb.DatabaseError as e:
                    error, = e.args
                    if error.code != 955:
                        raise
                
                # Create ngo_addresses table
                try:
                    cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'NGO_ADDRESSES'")
                    (table_exists,) = cursor.fetchone()

                    if not table_exists:
                        cursor.execute('''
                        CREATE TABLE ngo_addresses (
                            address_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                            ngo_id NUMBER NOT NULL,
                            street VARCHAR2(200),
                            city VARCHAR2(100),
                            CONSTRAINT fk_ngo_addresses_ngo_id FOREIGN KEY (ngo_id) REFERENCES ngos(ngo_id)
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
                            CONSTRAINT fk_requests_ngo_id FOREIGN KEY (ngo_id) REFERENCES ngos(ngo_id)
                        )
                        ''')
                except oracledb.DatabaseError as e:
                    error, = e.args
                    if error.code != 955:
                        raise
                
                # Create request_donations mapping table
                try:
                    cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'REQUEST_DONATIONS'")
                    (table_exists,) = cursor.fetchone()

                    if not table_exists:
                        cursor.execute('''
                        CREATE TABLE request_donations (
                            id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                            request_id NUMBER NOT NULL,
                            donation_id NUMBER NOT NULL,
                            CONSTRAINT fk_req_don_request_id FOREIGN KEY (request_id) REFERENCES requests(request_id),
                            CONSTRAINT fk_req_don_donation_id FOREIGN KEY (donation_id) REFERENCES food_donations(donation_id)
                        )
                        ''')
                except oracledb.DatabaseError as e:
                    error, = e.args
                    if error.code != 955:
                        raise
                
                # Create trigger to update donation status when assigned to an NGO
                try:
                    cursor.execute('''
                    CREATE OR REPLACE TRIGGER update_donation_status
                    AFTER UPDATE OF ngo_id ON food_donations
                    FOR EACH ROW
                    BEGIN
                        IF :NEW.ngo_id IS NOT NULL THEN
                            UPDATE food_donations SET status = 'Assigned' WHERE donation_id = :NEW.donation_id;
                        END IF;
                    END;
                    ''')
                except oracledb.DatabaseError:
                    pass  # Trigger might already exist
                
                # Create trigger to update request status when donations are assigned
                try:
                    cursor.execute('''
                    CREATE OR REPLACE TRIGGER update_request_status
                    AFTER INSERT ON request_donations
                    FOR EACH ROW
                    DECLARE
                        donation_count NUMBER;
                    BEGIN
                        SELECT COUNT(*) INTO donation_count FROM request_donations 
                        WHERE request_id = :NEW.request_id;
                        
                        IF donation_count > 0 THEN
                            UPDATE requests SET status = 'Fulfilled' WHERE request_id = :NEW.request_id;
                        END IF;
                    END;
                    ''')
                except oracledb.DatabaseError:
                    pass  # Trigger might already exist
                
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
                    "INSERT INTO users (username, password_hash, user_type) VALUES (:1, :2, :3) RETURNING user_id INTO :4",
                    [username, hash_password(password), user_type, user_id_var]
                )
                user_id = user_id_var.getvalue()[0]  # Get value from the bind variable
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
                    "SELECT user_id, user_type FROM users WHERE username = :1 AND password_hash = :2",
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
                    "INSERT INTO donors (user_id, name) VALUES (:1, :2) RETURNING donor_id INTO :3",
                    [user_id, name, donor_id_var]
                )
                
                donor_id = donor_id_var.getvalue()[0]  # Get the returned donor_id
                
                # Insert into donor_contacts table
                cursor.execute(
                    "INSERT INTO donor_contacts (donor_id, email, phone) VALUES (:1, :2, :3)",
                    [donor_id, email, phone]
                )
                
                # Insert into donor_addresses table
                cursor.execute(
                    "INSERT INTO donor_addresses (donor_id, street, city) VALUES (:1, :2, :3)",
                    [donor_id, street, city]
                )
                
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
                # Using JOIN to get complete donor information
                cursor.execute('''
                SELECT d.name, dc.email, dc.phone, da.street, da.city
                FROM donors d
                JOIN donor_contacts dc ON d.donor_id = dc.donor_id
                JOIN donor_addresses da ON d.donor_id = da.donor_id
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
                    "INSERT INTO ngos (user_id, name) VALUES (:1, :2) RETURNING ngo_id INTO :3",
                    [user_id, name, ngo_id_var]
                )
                ngo_id = ngo_id_var.getvalue()[0]  # Get actual value

                # Insert into ngo_contacts table
                cursor.execute(
                    "INSERT INTO ngo_contacts (ngo_id, email, phone) VALUES (:1, :2, :3)",
                    [ngo_id, email, phone]
                )

                # Insert into ngo_addresses table
                cursor.execute(
                    "INSERT INTO ngo_addresses (ngo_id, street, city) VALUES (:1, :2, :3)",
                    [ngo_id, street, city]
                )

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
                # Using JOIN to get complete NGO information
                cursor.execute('''
                SELECT n.name, nc.email, nc.phone, na.street, na.city
                FROM ngos n
                JOIN ngo_contacts nc ON n.ngo_id = nc.ngo_id
                JOIN ngo_addresses na ON n.ngo_id = na.ngo_id
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


def get_ngo_requests(ngo_id):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                SELECT request_id, food_type, quantity, 
                       TO_CHAR(request_date, 'YYYY-MM-DD') as request_date, 
                       status
                FROM requests
                WHERE ngo_id = :1
                ORDER BY request_date DESC
                ''', [ngo_id])
                
                columns = ['request_id', 'food_type', 'quantity', 'request_date', 'status']
                
                result = []
                for row in cursor:
                    result.append(dict(zip(columns, row)))
                
                return result
    except oracledb.DatabaseError as e:
        print(f"Error in get_ngo_requests: {e}")
        return []

def get_available_donations(ngo_id=None):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                query = '''
                SELECT fd.donation_id, d.name as donor_name, fd.food_type, 
                       TO_CHAR(fd.donation_date, 'YYYY-MM-DD') as donation_date, 
                       TO_CHAR(fd.expiry_date, 'YYYY-MM-DD') as expiry_date, 
                       fd.quantity
                FROM food_donations fd
                JOIN donors d ON fd.donor_id = d.donor_id
                WHERE fd.status = 'Available'
                AND fd.expiry_date >= TO_DATE(:1, 'YYYY-MM-DD')
                '''
                
                params = [datetime.date.today().isoformat()]
                
                # If ngo_id is specified, exclude donations already assigned to this NGO
                if ngo_id:
                    query += " AND (fd.ngo_id IS NULL OR fd.ngo_id = :2)"
                    params.append(ngo_id)
                
                query += " ORDER BY fd.expiry_date ASC"
                
                cursor.execute(query, params)
                
                columns = ['donation_id', 'donor_name', 'food_type', 'donation_date', 
                           'expiry_date', 'quantity']
                
                result = []
                for row in cursor:
                    result.append(dict(zip(columns, row)))
                
                return result
    except oracledb.DatabaseError as e:
        print(f"Error in get_available_donations: {e}")
        return []

def claim_donation(donation_id, ngo_id):
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(''' 
                UPDATE food_donations 
                SET ngo_id = :ngo_id, status = 'Assigned' 
                WHERE donation_id = :donation_id AND (status = 'Available' OR ngo_id = :ngo_id)
                ''', {
                    "ngo_id": ngo_id,
                    "donation_id": donation_id
                })
                
                success = cursor.rowcount > 0
                conn.commit()
                return success
    except oracledb.DatabaseError as e:
        print(f"Error in claim_donation: {e}")
        return False

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
                
                result = []
                for row in cursor:
                    result.append(dict(zip(columns, row)))
                
                return result
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
    tab1, tab2, tab3 = st.tabs(["Donate Food", "My Donations", "Analytics"])
    
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
        ngo_options = [("", "Select an NGO (Optional)")] + ngos
        selected_ngo = st.selectbox("Donate to specific NGO", ngo_options, format_func=lambda x: x[1] if x else "Select an NGO (Optional)")
        
        if st.button("Submit Donation"):
            if food_type and quantity > 0 and donation_date and expiry_date:
                if expiry_date < donation_date:
                    st.error("Expiry date cannot be before donation date.")
                else:
                    ngo_id = selected_ngo[0] if selected_ngo and selected_ngo[0] != "" else None
                    
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
    tab1, tab2, tab3, tab4 = st.tabs(["Available Donations", "My Requests", "Make Request", "Analytics"])
    
    with tab1:
        st.header("Available Food Donations")
        
        st.markdown("""
        <div class="highlight">
        Browse available food donations and claim them for your organization.
        </div>
        """, unsafe_allow_html=True)
        
        available_donations = get_available_donations(st.session_state.entity_id)
        
        if not available_donations:
            st.info("No available donations at the moment. Please check back later.")
        else:
            for i, donation in enumerate(available_donations):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="card">
                        <h3>{donation['food_type']}</h3>
                        <p><strong>Donor:</strong> {donation['donor_name']}</p>
                        <p><strong>Quantity:</strong> {donation['quantity']} kg</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="card">
                        <p><strong>Donated:</strong> {donation['donation_date']}</p>
                        <p><strong>Expires:</strong> {donation['expiry_date']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    if st.button("Claim", key=f"claim_{donation['donation_id']}"):
                        if claim_donation(donation['donation_id'], st.session_state.entity_id):
                            st.success("Donation claimed successfully!")
                            time.sleep(1)  # Short delay for UI feedback
                            st.rerun()
                        else:
                            st.error("Failed to claim donation. It may have been claimed by another NGO.")
    
    with tab2:
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
    
    with tab3:
        st.header("Make Food Request")
        
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
    
    with tab4:
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
        
        # Highlight current NGO's statistics
        if ngo_distribution:
            current_ngo_stats = next((item for item in ngo_distribution if item['ngo_name'] == ngo_info['name']), None)
            
            if current_ngo_stats:
                st.markdown(f"""
                <div class="dashboard-stats">
                    <div class="stat-card">
                        <h3>Your Donations Received</h3>
                        <p style="font-size: 24px; font-weight: bold;">{current_ngo_stats['donations_received']}</p>
                    </div>
                    <div class="stat-card">
                        <h3>Total Food Received</h3>
                        <p style="font-size: 24px; font-weight: bold;">{current_ngo_stats['total_quantity']:.2f} kg</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Your organization hasn't received any donations yet.")

if __name__ == "__main__":
    main()