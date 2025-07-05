import psycopg2
from database_config import db_config

def create_database_schema():
    """Create all necessary tables for the supermarket analysis system"""
    
    tables = {
        'categories': """
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """,
        
        'suppliers': """
            CREATE TABLE IF NOT EXISTS suppliers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                contact_person VARCHAR(100),
                email VARCHAR(100),
                phone VARCHAR(20),
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """,
        
        'products': """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                sku VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(200) NOT NULL,
                category_id INTEGER REFERENCES categories(id),
                supplier_id INTEGER REFERENCES suppliers(id),
                cost_price DECIMAL(10,2),
                selling_price DECIMAL(10,2),
                current_stock INTEGER DEFAULT 0,
                reorder_level INTEGER DEFAULT 10,
                max_stock_level INTEGER DEFAULT 1000,
                unit VARCHAR(20) DEFAULT 'piece',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """,
        
        'customers': """
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                customer_code VARCHAR(50) UNIQUE,
                name VARCHAR(100),
                email VARCHAR(100),
                phone VARCHAR(20),
                address TEXT,
                date_of_birth DATE,
                membership_type VARCHAR(20) DEFAULT 'regular',
                total_purchases DECIMAL(12,2) DEFAULT 0,
                points INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """,
        
        'promotions': """
            CREATE TABLE IF NOT EXISTS promotions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                promotion_type VARCHAR(20) CHECK (promotion_type IN ('discount', 'bogo', 'bundle', 'loyalty')),
                discount_percentage DECIMAL(5,2),
                discount_amount DECIMAL(10,2),
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """,
        
        'promotion_products': """
            CREATE TABLE IF NOT EXISTS promotion_products (
                id SERIAL PRIMARY KEY,
                promotion_id INTEGER REFERENCES promotions(id),
                product_id INTEGER REFERENCES products(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(promotion_id, product_id)
            );
        """,
        
        'sales_transactions': """
            CREATE TABLE IF NOT EXISTS sales_transactions (
                id SERIAL PRIMARY KEY,
                transaction_id VARCHAR(50) UNIQUE NOT NULL,
                customer_id INTEGER REFERENCES customers(id),
                cashier_id INTEGER REFERENCES users(id),
                total_amount DECIMAL(12,2) NOT NULL,
                tax_amount DECIMAL(12,2) DEFAULT 0,
                discount_amount DECIMAL(12,2) DEFAULT 0,
                payment_method VARCHAR(20) DEFAULT 'cash',
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'completed'
            );
        """,
        
        'sales_transaction_items': """
            CREATE TABLE IF NOT EXISTS sales_transaction_items (
                id SERIAL PRIMARY KEY,
                transaction_id INTEGER REFERENCES sales_transactions(id),
                product_id INTEGER REFERENCES products(id),
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(12,2) NOT NULL,
                discount_applied DECIMAL(10,2) DEFAULT 0,
                promotion_id INTEGER REFERENCES promotions(id)
            );
        """,
        
        'inventory_movements': """
            CREATE TABLE IF NOT EXISTS inventory_movements (
                id SERIAL PRIMARY KEY,
                product_id INTEGER REFERENCES products(id),
                movement_type VARCHAR(20) CHECK (movement_type IN ('inbound', 'outbound', 'adjustment', 'transfer')),
                quantity INTEGER NOT NULL,
                reference_id INTEGER, -- could be transaction_id, purchase_order_id, etc.
                reference_type VARCHAR(20), -- 'sale', 'purchase', 'adjustment', 'transfer'
                notes TEXT,
                movement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER REFERENCES users(id)
            );
        """,
        
        'purchase_orders': """
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id SERIAL PRIMARY KEY,
                order_number VARCHAR(50) UNIQUE NOT NULL,
                supplier_id INTEGER REFERENCES suppliers(id),
                order_date DATE NOT NULL,
                expected_delivery DATE,
                actual_delivery DATE,
                total_amount DECIMAL(12,2),
                status VARCHAR(20) DEFAULT 'pending',
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """,
        
        'purchase_order_items': """
            CREATE TABLE IF NOT EXISTS purchase_order_items (
                id SERIAL PRIMARY KEY,
                purchase_order_id INTEGER REFERENCES purchase_orders(id),
                product_id INTEGER REFERENCES products(id),
                quantity_ordered INTEGER NOT NULL,
                quantity_received INTEGER DEFAULT 0,
                unit_cost DECIMAL(10,2) NOT NULL,
                total_cost DECIMAL(12,2) NOT NULL
            );
        """,
        
        'daily_sales_summary': """
            CREATE TABLE IF NOT EXISTS daily_sales_summary (
                id SERIAL PRIMARY KEY,
                summary_date DATE UNIQUE NOT NULL,
                total_transactions INTEGER DEFAULT 0,
                total_revenue DECIMAL(12,2) DEFAULT 0,
                total_customers INTEGER DEFAULT 0,
                average_transaction_value DECIMAL(10,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
    }
    
    try:
        conn = db_config.get_connection()
        cursor = conn.cursor()
        
        print("Creating database schema...")
        
        for table_name, create_sql in tables.items():
            print(f"Creating table: {table_name}")
            cursor.execute(create_sql)
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);",
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);",
            "CREATE INDEX IF NOT EXISTS idx_sales_date ON sales_transactions(transaction_date);",
            "CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales_transactions(customer_id);",
            "CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory_movements(product_id);",
            "CREATE INDEX IF NOT EXISTS idx_inventory_date ON inventory_movements(movement_date);",
        ]
        
        print("Creating indexes...")
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        cursor.close()
        print("Database schema created successfully!")
        
        # Insert sample data
        insert_sample_data()
        
    except psycopg2.Error as e:
        print(f"Error creating database schema: {e}")

def insert_sample_data():
    """Insert sample data for testing"""
    try:
        conn = db_config.get_connection()
        cursor = conn.cursor()
        
        print("Inserting sample data...")
        
        # Categories
        categories = [
            ('Fruits & Vegetables', 'Fresh produce'),
            ('Dairy & Eggs', 'Milk, cheese, eggs and dairy products'),
            ('Meat & Seafood', 'Fresh and frozen meat and seafood'),
            ('Bakery', 'Bread, cakes, and baked goods'),
            ('Beverages', 'Soft drinks, juices, water'),
            ('Snacks', 'Chips, crackers, nuts'),
            ('Household', 'Cleaning supplies, toiletries'),
            ('Frozen Foods', 'Frozen vegetables, meals, ice cream')
        ]
        
        for name, desc in categories:
            cursor.execute(
                "INSERT INTO categories (name, description) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
                (name, desc)
            )
        
        # Suppliers
        suppliers = [
            ('Fresh Farm Co.', 'John Smith', 'john@freshfarm.com', '555-0101', '123 Farm Road'),
            ('Dairy Best Ltd.', 'Mary Johnson', 'mary@dairybest.com', '555-0102', '456 Milk Street'),
            ('Ocean Fresh Seafood', 'Bob Wilson', 'bob@oceanfresh.com', '555-0103', '789 Harbor Ave'),
            ('Golden Bakery', 'Sarah Brown', 'sarah@goldenbakery.com', '555-0104', '321 Baker Street'),
            ('Beverage Distributors Inc.', 'Mike Davis', 'mike@bevdist.com', '555-0105', '654 Drink Boulevard')
        ]
        
        for name, contact, email, phone, address in suppliers:
            cursor.execute(
                "INSERT INTO suppliers (name, contact_person, email, phone, address) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (name, contact, email, phone, address)
            )
        
        conn.commit()
        cursor.close()
        print("Sample data inserted successfully!")
        
    except psycopg2.Error as e:
        print(f"Error inserting sample data: {e}")

if __name__ == "__main__":
    create_database_schema()
