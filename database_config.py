import psycopg2
from psycopg2 import sql
import hashlib
from typing import Optional, Dict, Any

class DatabaseConfig:
    """Database configuration and connection management"""
    
    def __init__(self, host='aws-0-ap-southeast-1.pooler.supabase.com', port=5432, database='postgres', 
                 user='postgres.ozcfmovkaoipiilhunit', password='postgres123!'):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
    
    def connect(self):
        """Establish database connection with better parameters for cloud databases"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                connect_timeout=30, 
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
            self.connection.set_session(autocommit=True) 
            print("Database connection established successfully")
            return True
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def get_connection(self):
        """Get current database connection with auto-reconnect"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if not self.connection or self.connection.closed:
                    print(f"Attempt {attempt + 1}: Database connection lost or not established. Reconnecting...")
                    if not self.connect():
                        if attempt < max_attempts - 1:
                            print(f"Connection failed, retrying in 2 seconds...")
                            import time
                            time.sleep(2)
                            continue
                        else:
                            print("Failed to establish database connection after all attempts")
                            return None
                
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                print("Database connection verified")
                return self.connection
                
            except (psycopg2.Error, psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                print(f"Attempt {attempt + 1}: Connection test failed: {e}")
                if self.connection:
                    try:
                        self.connection.close()
                    except:
                        pass
                    self.connection = None
                
                if attempt < max_attempts - 1:
                    print("Retrying connection...")
                    import time
                    time.sleep(2)
                else:
                    print("Failed to establish stable database connection")
                    return None
        
        return self.connection

class UserManager:
    """Handle user authentication and management"""
    
    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
        self.init_user_table()
    
    def init_user_table(self):
        """Create users table if it doesn't exist"""
        try:
            conn = self.db_config.get_connection()
            cursor = conn.cursor()
            
            create_table_query = """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('manager', 'sales_manager', 'restocker')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            );
            """
            
            cursor.execute(create_table_query)
            conn.commit()
            cursor.close()
            
            self.migrate_existing_users()
            
        except psycopg2.Error as e:
            print(f"Error creating users table: {e}")
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def migrate_existing_users(self):
        """Migrate users from text file to database"""
        try:
            conn = self.db_config.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            if user_count > 0:
                cursor.close()
                return 
            
            try:
                with open("user_credentials.txt", 'r') as file:
                    for line in file:
                        line = line.strip()
                        if line:
                            username, password, role = line.split(",")
                            self.create_user(username, password, role)
            except FileNotFoundError:
                self.create_user("manager", "123", "manager")
                self.create_user("Smanager", "123", "sales_manager")
                self.create_user("restocker", "123", "restocker")
            
            cursor.close()
            
        except psycopg2.Error as e:
            print(f"Error migrating users: {e}")
    
    def create_user(self, username: str, password: str, role: str) -> bool:
        """Create a new user"""
        try:
            conn = self.db_config.get_connection()
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            insert_query = """
            INSERT INTO users (username, password_hash, role) 
            VALUES (%s, %s, %s)
            ON CONFLICT (username) DO NOTHING
            """
            
            cursor.execute(insert_query, (username, password_hash, role))
            conn.commit()
            cursor.close()
            return True
            
        except psycopg2.Error as e:
            print(f"Error creating user: {e}")
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user info"""
        try:
            conn = self.db_config.get_connection()
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            query = """
            SELECT id, username, role, is_active 
            FROM users 
            WHERE username = %s AND password_hash = %s AND is_active = TRUE
            """
            
            cursor.execute(query, (username, password_hash))
            result = cursor.fetchone()
            
            if result:
                update_query = """
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE id = %s
                """
                cursor.execute(update_query, (result[0],))
                conn.commit()
                
                user_info = {
                    'id': result[0],
                    'username': result[1],
                    'role': result[2],
                    'is_active': result[3]
                }
                cursor.close()
                return user_info
            
            cursor.close()
            return None
            
        except psycopg2.Error as e:
            print(f"Error authenticating user: {e}")
            return None
    
    def get_user_login_history(self, username: str) -> list:
        """Get user login history"""
        try:
            conn = self.db_config.get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT last_login, created_at 
            FROM users 
            WHERE username = %s
            """
            
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            cursor.close()
            
            return result if result else []
            
        except psycopg2.Error as e:
            print(f"Error getting user history: {e}")
            return []

db_config = DatabaseConfig()
user_manager = UserManager(db_config)
