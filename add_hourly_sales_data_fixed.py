#!/usr/bin/env python3
"""
Fixed Hourly Sales Data Generator
Adds sample hourly sales data for today to test the real-time dashboard
"""

import random
from datetime import datetime, timedelta
from database_config import DatabaseConfig

def add_hourly_sales_data():
    """Add sample hourly sales data for today"""
    try:
        print("=== Fixed Hourly Sales Data Generator ===")
        print("Adding sample hourly sales data for today...")
        
        db = DatabaseConfig()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get today's date
        today = datetime.now().date()
        
        # Check if data already exists for today
        cursor.execute("""
            SELECT COUNT(*) FROM sales_transactions 
            WHERE DATE(transaction_date) = %s
        """, (today,))
        
        existing_count = cursor.fetchone()[0]
        if existing_count > 0:
            print(f"Found {existing_count} existing transactions for today.")
            response = input("Do you want to add more data? (y/n): ")
            if response.lower() != 'y':
                print("Cancelled.")
                return
        
        # Get the next transaction ID
        cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM sales_transactions")
        next_transaction_id = cursor.fetchone()[0]
        
        # Get available products
        cursor.execute("SELECT id, name, selling_price FROM products WHERE is_active = TRUE LIMIT 20")
        products = cursor.fetchall()
        
        if not products:
            print("❌ No products found in database!")
            return
        
        print(f"Found {len(products)} products to use")
        
        # Business hours: 8 AM to 10 PM
        business_hours = {
            8: 1,   # 8 AM - slow start
            9: 8,   # 9 AM - morning rush
            10: 7,  # 10 AM
            11: 7,  # 11 AM
            12: 10, # 12 PM - lunch rush
            13: 12, # 1 PM - lunch continues
            14: 4,  # 2 PM - quiet
            15: 6,  # 3 PM
            16: 8,  # 4 PM - afternoon pickup
            17: 13, # 5 PM - evening rush
            18: 9,  # 6 PM
            19: 15, # 7 PM - peak evening
            20: 4,  # 8 PM - winding down
            21: 4,  # 9 PM
            22: 2   # 10 PM - closing
        }
        
        total_transactions = 0
        total_revenue = 0
        
        for hour, num_transactions in business_hours.items():
            print(f"Adding {num_transactions} transactions for hour {hour}:00")
            
            for i in range(num_transactions):
                try:
                    # Generate transaction time within the hour
                    minute = random.randint(0, 59)
                    second = random.randint(0, 59)
                    transaction_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute, second=second))
                    
                    # Generate transaction details
                    transaction_id_str = f"TXN{today.strftime('%Y%m%d')}{hour:02d}{i:03d}"
                    
                    # Random number of items (1-5)
                    num_items = random.randint(1, 5)
                    transaction_total = 0
                    transaction_items = []
                    
                    for item_num in range(num_items):
                        product = random.choice(products)
                        quantity = random.randint(1, 3)
                        unit_price = float(product[2])  # selling_price
                        total_price = quantity * unit_price
                        transaction_total += total_price
                        
                        transaction_items.append({
                            'product_id': product[0],
                            'quantity': quantity,
                            'unit_price': unit_price,
                            'total_price': total_price
                        })
                    
                    # Add some tax (5%)
                    tax_amount = round(transaction_total * 0.05, 2)
                    total_with_tax = transaction_total + tax_amount
                    
                    # Random payment method
                    payment_methods = ['cash', 'card', 'mobile']
                    payment_method = random.choice(payment_methods)
                    
                    # Insert transaction
                    cursor.execute("""
                        INSERT INTO sales_transactions 
                        (id, transaction_id, cashier_id, total_amount, tax_amount, discount_amount, payment_method, transaction_date, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        next_transaction_id,
                        transaction_id_str,
                        1,  # Default cashier_id
                        total_with_tax,
                        tax_amount,
                        0.0,  # No discount
                        payment_method,
                        transaction_time,
                        'completed'
                    ))
                    
                    # Insert transaction items
                    for item in transaction_items:
                        cursor.execute("""
                            INSERT INTO sales_transaction_items 
                            (transaction_id, product_id, quantity, unit_price, total_price, discount_applied)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            next_transaction_id,
                            item['product_id'],
                            item['quantity'],
                            item['unit_price'],
                            item['total_price'],
                            0.0
                        ))
                    
                    total_transactions += 1
                    total_revenue += total_with_tax
                    next_transaction_id += 1
                    
                    print(f"  ✅ Added transaction {transaction_id_str} - ${total_with_tax:.2f}")
                    
                except Exception as e:
                    print(f"  ❌ Error adding transaction: {e}")
                    continue
        
        # Commit all changes
        conn.commit()
        cursor.close()
        
        print(f"\n🎉 Successfully added {total_transactions} transactions!")
        print(f"💰 Total revenue: ${total_revenue:.2f}")
        print(f"📅 Date: {today}")
        print("\n✨ You can now refresh your real-time dashboard to see the data!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_hourly_sales_data()
