import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta
from database_config import db_config
import io
import base64
import time
import psycopg2
from tkinter import messagebox
import numpy as np


class BaseAnalytics:

    def __init__(self):
        self.db_config = db_config

    def execute_query(self, query, params=None, max_retries=3):
        import warnings
        for attempt in range(max_retries):
            try:
                conn = self.db_config.get_connection()
                if conn and not conn.closed:
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")
                        df = pd.read_sql_query(query, conn, params=params)
                    print(f"Query executed successfully on attempt {attempt + 1}")
                    return df
                else:
                    print(f"Attempt {attempt + 1}: Failed to get valid database connection")

            except (psycopg2.Error, psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                print(f"Attempt {attempt + 1}: Database error: {e}")
                self.db_config.disconnect()

                if attempt < max_retries - 1:
                    print("Retrying database operation...")
                    time.sleep(2)
                else:
                    print("Max retries reached. Showing error to user.")
                    error_msg = f"Database connection failed after {max_retries} attempts.\n\nError: {str(e)}\n\nPlease check your internet connection and try again."
                    messagebox.showerror("Database Connection Error", error_msg)

            except Exception as e:
                print(f"Unexpected error: {e}")
                error_msg = f"An unexpected error occurred while executing the query:\n\n{str(e)}"
                messagebox.showerror("Query Error", error_msg)
                break

        return pd.DataFrame()

    def save_plot_as_base64(self, fig):
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        graphic = base64.b64encode(image_png)
        return graphic.decode('utf-8')

    def check_database_schema(self):
        try:
            table_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """

            tables_df = self.execute_query(table_query, [])
            print("=== AVAILABLE TABLES ===")
            if not tables_df.empty:
                for table in tables_df['table_name']:
                    print(f"✓ {table}")

                    columns_query = """
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position;
                    """

                    columns_df = self.execute_query(columns_query, [table])
                    if not columns_df.empty:
                        print(f"  Columns in {table}:")
                        for _, row in columns_df.iterrows():
                            print(f"    - {row['column_name']} ({row['data_type']})")
                    print()
            else:
                print("No tables found in public schema")

            print("=== PROMOTION TABLES CHECK ===")
            required_tables = ['promotions', 'promotion_products', 'sales_transaction_items', 'sales_transactions']

            for table_name in required_tables:
                check_query = f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = '{table_name}'
                );
                """
                result = self.execute_query(check_query, [])
                exists = result.iloc[0, 0] if not result.empty else False
                status = "✓ EXISTS" if exists else "✗ MISSING"
                print(f"{table_name}: {status}")

                if exists:
                    count_query = f"SELECT COUNT(*) as row_count FROM {table_name};"
                    count_result = self.execute_query(count_query, [])
                    row_count = count_result.iloc[0, 0] if not count_result.empty else 0
                    print(f"  Row count: {row_count}")

        except Exception as e:
            print(f"Error checking database schema: {e}")


class ManagerAnalytics(BaseAnalytics):

    def get_sales_trend_analysis(self, days=30, metric="revenue"):
        query = """
        SELECT 
            DATE(transaction_date) as date,
            COUNT(*) as transaction_count,
            SUM(total_amount) as daily_revenue,
            AVG(total_amount) as avg_transaction_value
        FROM sales_transactions 
        WHERE transaction_date >= %s
        GROUP BY DATE(transaction_date)
        ORDER BY date
        """

        start_date = datetime.now() - timedelta(days=days)
        return self.execute_query(query, [start_date])

    def get_sales_trend_analysis_custom(self, start_date, end_date, metric="revenue"):
        query = """
        SELECT 
            DATE(transaction_date) as date,
            COUNT(*) as transaction_count,
            SUM(total_amount) as daily_revenue,
            AVG(total_amount) as avg_transaction_value
        FROM sales_transactions 
        WHERE transaction_date >= %s AND transaction_date <= %s
        GROUP BY DATE(transaction_date)
        ORDER BY date
        """

        return self.execute_query(query, [start_date, end_date])

    def get_peak_shopping_hours(self, days=7):
        query = """
        SELECT 
            EXTRACT(HOUR FROM transaction_date) as hour,
            COUNT(*) as transaction_count
        FROM sales_transactions 
        WHERE transaction_date >= %s
        GROUP BY EXTRACT(HOUR FROM transaction_date)
        ORDER BY hour
        """

        start_date = datetime.now() - timedelta(days=days)
        return self.execute_query(query, [start_date])

    def get_top_selling_products(self, limit=10, days=30):
        query = """
        SELECT 
            p.name as product_name,
            c.name as category,
            SUM(sti.quantity) as total_quantity_sold,
            SUM(sti.total_price) as total_revenue,
            AVG(sti.unit_price) as avg_price
        FROM sales_transaction_items sti
        JOIN products p ON sti.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        JOIN sales_transactions st ON sti.transaction_id = st.id
        WHERE st.transaction_date >= %s
        GROUP BY p.id, p.name, c.name
        ORDER BY total_quantity_sold DESC
        LIMIT %s
        """

        start_date = datetime.now() - timedelta(days=days)
        return self.execute_query(query, [start_date, limit])

    def get_inventory_usage_trends(self):
        query = """
        SELECT 
            p.name as product_name,
            p.current_stock,
            p.reorder_level,
            c.name as category,
            CASE 
                WHEN p.current_stock <= p.reorder_level THEN 'Low Stock'
                WHEN p.current_stock <= p.reorder_level * 1.5 THEN 'Medium Stock'
                ELSE 'High Stock'
            END as stock_status,
            COALESCE(recent_sales.total_sold_last_week, 0) as sold_last_week
        FROM products p
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN (
            SELECT 
                sti.product_id,
                SUM(sti.quantity) as total_sold_last_week
            FROM sales_transaction_items sti
            JOIN sales_transactions st ON sti.transaction_id = st.id
            WHERE st.transaction_date >= %s
            GROUP BY sti.product_id
        ) recent_sales ON p.id = recent_sales.product_id
        WHERE p.is_active = TRUE
        ORDER BY p.current_stock ASC
        """

        week_ago = datetime.now() - timedelta(days=7)
        return self.execute_query(query, [week_ago])

    def get_promotion_effectiveness(self, days=30, promotion_type=None, status=None, start_date=None, end_date=None):

        params = []
        where_clauses = ["1=1"]

        if start_date and end_date:
            where_clauses.append("p.start_date >= %s AND p.end_date <= %s")
            params.extend([start_date, end_date])
        else:
            where_clauses.append("p.created_at >= %s")
            params.append(datetime.now() - timedelta(days=days))

        if promotion_type:
            where_clauses.append("p.promotion_type = %s")
            params.append(promotion_type)

        if status:
            if status == 'active':
                where_clauses.append("p.start_date <= NOW() AND p.end_date >= NOW()")
            elif status == 'expired':
                where_clauses.append("p.end_date < NOW()")
            elif status == 'upcoming':
                where_clauses.append("p.start_date > NOW()")

        query = f"""
        SELECT 
            p.name as promotion_name,
            p.promotion_type,
            p.discount_percentage,
            p.start_date,
            p.end_date,
            p.is_active,
            COUNT(DISTINCT pp.product_id) as products_in_promotion,
            COALESCE(SUM(CASE WHEN sti.promotion_id = p.id THEN sti.total_price ELSE 0 END), 0) as total_revenue,
            COALESCE(SUM(CASE WHEN sti.promotion_id = p.id THEN sti.discount_applied ELSE 0 END), 0) as total_discount_given,
            COUNT(DISTINCT CASE WHEN sti.promotion_id = p.id THEN st.id ELSE NULL END) as transactions_count,
            COALESCE(AVG(CASE WHEN sti.promotion_id = p.id THEN sti.total_price ELSE NULL END), 0) as avg_transaction_value
        FROM promotions p
        LEFT JOIN promotion_products pp ON p.id = pp.promotion_id
        LEFT JOIN sales_transaction_items sti ON pp.product_id = sti.product_id 
        LEFT JOIN sales_transactions st ON sti.transaction_id = st.id
            AND st.transaction_date BETWEEN p.start_date AND p.end_date
        WHERE {' AND '.join(where_clauses)}
        GROUP BY p.id, p.name, p.promotion_type, p.discount_percentage, 
                p.start_date, p.end_date, p.is_active
        ORDER BY p.start_date DESC
        """

        return self.execute_query(query, params)

    def get_sales_forecast_data(self, days=30, start_date=None, end_date=None):
        query = """
        SELECT 
            DATE(transaction_date) as date,
            SUM(total_amount) as daily_revenue,
            COUNT(*) as transaction_count,
            AVG(total_amount) as avg_transaction_value
        FROM sales_transactions 
        WHERE transaction_date >= %s
        GROUP BY DATE(transaction_date)
        ORDER BY date
        """

        start_date = datetime.now() - timedelta(days=days)
        return self.execute_query(query, [start_date])

    def get_product_sales_trends(self, days=30, limit=10):
        query = """
        WITH product_daily_sales AS (
            SELECT 
                p.id,
                p.name as product_name,
                c.name as category,
                DATE(st.transaction_date) as sale_date,
                SUM(sti.quantity) as daily_quantity,
                SUM(sti.total_price) as daily_revenue
            FROM sales_transaction_items sti
            JOIN products p ON sti.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            JOIN sales_transactions st ON sti.transaction_id = st.id
            WHERE st.transaction_date >= %s
            GROUP BY p.id, p.name, c.name, DATE(st.transaction_date)
        ),
        product_totals AS (
            SELECT 
                product_name,
                category,
                SUM(daily_quantity) as total_quantity,
                SUM(daily_revenue) as total_revenue,
                AVG(daily_quantity) as avg_daily_quantity,
                COUNT(DISTINCT sale_date) as days_with_sales
            FROM product_daily_sales
            GROUP BY product_name, category
            ORDER BY total_quantity DESC
            LIMIT %s
        )
        SELECT 
            pds.product_name,
            pds.category,
            pds.sale_date,
            pds.daily_quantity,
            pds.daily_revenue,
            pt.total_quantity,
            pt.avg_daily_quantity,
            pt.days_with_sales
        FROM product_daily_sales pds
        JOIN product_totals pt ON pds.product_name = pt.product_name
        ORDER BY pt.total_quantity DESC, pds.sale_date ASC
        """

        start_date = datetime.now() - timedelta(days=days)
        return self.execute_query(query, [start_date, limit])

    def get_promotion_effectiveness(self, days=30, promotion_type=None, status=None, start_date=None, end_date=None):

        params = []
        where_clauses = ["p.is_active = TRUE"]

        if start_date and end_date:
            where_clauses.append("p.start_date >= %s AND p.end_date <= %s")
            params.extend([start_date, end_date])
        else:
            where_clauses.append("p.start_date >= %s")
            params.append(datetime.now() - timedelta(days=days))

        if promotion_type:
            where_clauses.append("p.promotion_type = %s")
            params.append(promotion_type)

        if status:
            current_date = datetime.now().date()
            if status == 'active':
                where_clauses.append("p.start_date <= %s AND p.end_date >= %s")
                params.extend([current_date, current_date])
            elif status == 'expired':
                where_clauses.append("p.end_date < %s")
                params.append(current_date)
            elif status == 'upcoming':
                where_clauses.append("p.start_date > %s")
                params.append(current_date)

        query = f"""
        SELECT 
            p.name as promotion_name,
            p.promotion_type,
            p.discount_percentage,
            p.start_date,
            p.end_date,
            p.is_active,
            COUNT(DISTINCT pp.product_id) as products_in_promotion,
            COALESCE(SUM(CASE WHEN sti.promotion_id = p.id THEN sti.total_price ELSE 0 END), 0) as total_revenue,
            COALESCE(SUM(CASE WHEN sti.promotion_id = p.id THEN sti.discount_applied ELSE 0 END), 0) as total_discount_given,
            COUNT(DISTINCT CASE WHEN sti.promotion_id = p.id THEN st.id ELSE NULL END) as transactions_count,
            COALESCE(AVG(CASE WHEN sti.promotion_id = p.id THEN st.total_amount ELSE NULL END), 0) as avg_transaction_value
        FROM promotions p
        LEFT JOIN promotion_products pp ON p.id = pp.promotion_id
        LEFT JOIN sales_transaction_items sti ON pp.product_id = sti.product_id 
        LEFT JOIN sales_transactions st ON sti.transaction_id = st.id
            AND st.transaction_date BETWEEN p.start_date AND p.end_date
        WHERE {' AND '.join(where_clauses)}
        GROUP BY p.id, p.name, p.promotion_type, p.discount_percentage, 
                p.start_date, p.end_date, p.is_active
        ORDER BY p.start_date DESC
        """

        return self.execute_query(query, params)

    def get_customer_traffic_analysis(self, period_type='day', start_date=None, end_date=None):

        if start_date is None or end_date is None:
            end_date = datetime.now()
            if period_type == 'hour':
                start_date = end_date - timedelta(days=1)
            elif period_type == 'day':
                start_date = end_date - timedelta(days=7)
            elif period_type == 'week':
                start_date = end_date - timedelta(weeks=4)
            else:
                start_date = end_date - timedelta(weeks=8)

        query = """
        SELECT 
            st.id,
            st.transaction_date,
            sti.quantity,
            sti.total_price
        FROM sales_transactions st
        LEFT JOIN sales_transaction_items sti ON st.id = sti.transaction_id
        WHERE st.transaction_date BETWEEN %s AND %s
        """
        df = self.execute_query(query, [start_date, end_date])

        if df.empty:
            return pd.DataFrame()

        df['transaction_date'] = pd.to_datetime(df['transaction_date'])

        freq_map = {'hour': 'H', 'day': 'D', 'week': 'W-MON', 'month': 'W-MON'}
        grouper = pd.Grouper(key='transaction_date', freq=freq_map.get(period_type, 'D'))

        analysis = df.groupby(grouper).agg(
            transaction_count=('id', 'nunique'),
            items_sold=('quantity', 'sum'),
            total_revenue=('total_price', 'sum')
        ).reset_index()

        if analysis.empty:
            return pd.DataFrame()

        analysis['avg_transaction_value'] = (analysis['total_revenue'] / analysis['transaction_count']).fillna(0)

        if period_type == 'hour':
            analysis['time_period'] = analysis['transaction_date'].dt.hour
            analysis['period_label'] = analysis['transaction_date'].dt.strftime('%I %p')
        elif period_type == 'day':
            analysis['time_period'] = range(len(analysis))
            analysis['period_label'] = analysis['transaction_date'].dt.strftime('%a, %b %d')
        else:
            analysis['time_period'] = range(len(analysis))
            analysis['period_label'] = analysis['transaction_date'].dt.strftime('Week of %b %d')

        return analysis.fillna(0)


class SalesManagerAnalytics(BaseAnalytics):

    def get_real_time_sales_dashboard(self):
        query = """
        SELECT 
            COUNT(*) as todays_transactions,
            COALESCE(SUM(total_amount), 0) as todays_revenue,
            COALESCE(AVG(total_amount), 0) as avg_transaction_value,
            CURRENT_TIMESTAMP as data_timestamp
        FROM sales_transactions 
        WHERE DATE(transaction_date) = CURRENT_DATE
        """
        return self.execute_query(query)

    def get_hourly_sales_data(self):
        query = """
        SELECT 
            EXTRACT(HOUR FROM transaction_date) as hour,
            COALESCE(SUM(total_amount), 0) as hourly_revenue,
            COALESCE(SUM(sti.quantity), 0) as items_sold
        FROM sales_transactions st
        JOIN sales_transaction_items sti ON st.id = sti.transaction_id
        WHERE DATE(transaction_date) = CURRENT_DATE
        GROUP BY EXTRACT(HOUR FROM transaction_date)
        ORDER BY hour;
        """
        return self.execute_query(query)

    def get_todays_top_products(self, limit=5):
        query = """
        SELECT 
            p.name as product_name,
            SUM(sti.quantity) as quantity_sold,
            SUM(sti.total_price) as revenue
        FROM sales_transaction_items sti
        JOIN products p ON sti.product_id = p.id
        JOIN sales_transactions st ON sti.transaction_id = st.id
        WHERE DATE(st.transaction_date) = CURRENT_DATE
        GROUP BY p.id, p.name
        ORDER BY quantity_sold DESC
        LIMIT %s
        """
        return self.execute_query(query, [limit])

    def get_recent_transactions(self, limit=10):
        query = """
        SELECT 
            TO_CHAR(st.transaction_date, 'HH24:MI') as time,
            SUM(sti.quantity) as items,
            st.total_amount as total
        FROM sales_transactions st
        JOIN sales_transaction_items sti ON st.id = sti.transaction_id
        WHERE DATE(st.transaction_date) = CURRENT_DATE
        GROUP BY st.id, st.transaction_date, st.total_amount
        ORDER BY st.transaction_date DESC
        LIMIT %s
        """
        return self.execute_query(query, [limit])

    def get_transaction_behavior(self, days=30):
        query = """
        SELECT 
            'All Transactions' as transaction_type,
            COUNT(st.transaction_id) as transaction_count,
            AVG(st.total_amount) as avg_purchase_amount,
            SUM(st.total_amount) as total_spent,
            AVG(transaction_items.items_per_transaction) as avg_items_per_transaction
        FROM sales_transactions st
        LEFT JOIN (
            SELECT 
                transaction_id,
                SUM(quantity) as items_per_transaction
            FROM sales_transaction_items
            GROUP BY transaction_id
        ) transaction_items ON st.transaction_id = transaction_items.transaction_id
        WHERE st.transaction_date >= %s
        GROUP BY 1
        ORDER BY total_spent DESC
        """

        start_date = datetime.now() - timedelta(days=days)
        return self.execute_query(query, [start_date])

    def get_popular_products_for_promotion(self, limit=10, days=30):
        query = """
        SELECT 
            p.name as product_name,
            c.name as category,
            SUM(sti.quantity) as total_sold,
            SUM(sti.total_price) as total_revenue,
            COUNT(DISTINCT st.id) as total_transactions,
            AVG(sti.unit_price) as avg_selling_price
        FROM sales_transaction_items sti
        JOIN products p ON sti.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        JOIN sales_transactions st ON sti.transaction_id = st.id
        WHERE st.transaction_date >= %s
        GROUP BY p.id, p.name, c.name
        ORDER BY total_sold DESC
        LIMIT %s
        """

        start_date = datetime.now() - timedelta(days=days)
        return self.execute_query(query, [start_date, limit])

    def get_promotion_comparison(self, promotion_id):
        query = """
        WITH promotion_period AS (
            SELECT start_date, end_date 
            FROM promotions 
            WHERE id = %s
        ),
        before_promotion AS (
            SELECT 
                SUM(sti.total_price) as revenue_before,
                SUM(sti.quantity) as quantity_before,
                COUNT(DISTINCT st.id) as transactions_before
            FROM sales_transaction_items sti
            JOIN sales_transactions st ON sti.transaction_id = st.id
            JOIN promotion_products pp ON sti.product_id = pp.product_id
            CROSS JOIN promotion_period pr
            WHERE pp.promotion_id = %s
            AND st.transaction_date BETWEEN (pr.start_date - INTERVAL '30 days') AND (pr.start_date - INTERVAL '1 day')
        ),
        during_promotion AS (
            SELECT 
                SUM(sti.total_price) as revenue_during,
                SUM(sti.quantity) as quantity_during,
                COUNT(DISTINCT st.id) as transactions_during
            FROM sales_transaction_items sti
            JOIN sales_transactions st ON sti.transaction_id = st.id
            JOIN promotion_products pp ON sti.product_id = pp.product_id
            CROSS JOIN promotion_period pr
            WHERE pp.promotion_id = %s
            AND st.transaction_date BETWEEN pr.start_date AND pr.end_date
        )
        SELECT * FROM before_promotion, during_promotion
        """

        return self.execute_query(query, [promotion_id, promotion_id, promotion_id])

    def get_seasonal_sales_trends(self):
        query = """
        SELECT 
            EXTRACT(MONTH FROM transaction_date) as month,
            EXTRACT(YEAR FROM transaction_date) as year,
            SUM(total_amount) as monthly_revenue,
            COUNT(*) as monthly_transactions,
            AVG(total_amount) as avg_transaction_value
        FROM sales_transactions 
        WHERE transaction_date >= %s
        GROUP BY EXTRACT(YEAR FROM transaction_date), EXTRACT(MONTH FROM transaction_date)
        ORDER BY year, month
        """

        start_date = datetime.now() - timedelta(days=365)
        return self.execute_query(query, [start_date])

    def get_sales_trend_analysis(self, days=30, metric="revenue"):
        query = """
        SELECT 
            DATE(transaction_date) as date,
            COUNT(*) as transaction_count,
            SUM(total_amount) as daily_revenue,
            AVG(total_amount) as avg_transaction_value
        FROM sales_transactions 
        WHERE transaction_date >= %s
        GROUP BY DATE(transaction_date)
        ORDER BY date
        """

        start_date = datetime.now() - timedelta(days=days)
        return self.execute_query(query, [start_date])

    def get_sales_trend_analysis_custom(self, start_date, end_date, metric="revenue"):
        query = """
        SELECT 
            DATE(transaction_date) as date,
            COUNT(*) as transaction_count,
            SUM(total_amount) as daily_revenue,
            AVG(total_amount) as avg_transaction_value
        FROM sales_transactions 
        WHERE transaction_date >= %s AND transaction_date <= %s
        GROUP BY DATE(transaction_date)
        ORDER BY date
        """

        return self.execute_query(query, [start_date, end_date])

    def get_frequently_bought_together(self, days=30):
        query = """
        WITH transaction_products AS (
            SELECT 
                st.id as transaction_id,
                array_agg(p.name ORDER BY p.name) as products,
                array_agg(p.id ORDER BY p.id) as product_ids
            FROM sales_transactions st
            JOIN sales_transaction_items sti ON st.id = sti.transaction_id
            JOIN products p ON sti.product_id = p.id
            WHERE st.transaction_date >= %s
            GROUP BY st.id
            HAVING COUNT(DISTINCT p.id) >= 2
        ),
        product_pairs AS (
            SELECT 
                p1.name as product_a,
                p2.name as product_b,
                COUNT(*) as frequency
            FROM transaction_products tp
            CROSS JOIN LATERAL unnest(tp.products) WITH ORDINALITY AS p1(name, ord1)
            CROSS JOIN LATERAL unnest(tp.products) WITH ORDINALITY AS p2(name, ord2)
            WHERE p1.ord1 < p2.ord2
            GROUP BY p1.name, p2.name
        )
        SELECT 
            product_a,
            product_b,
            frequency,
            ROUND(frequency::DECIMAL / (SELECT COUNT(*) FROM transaction_products)::DECIMAL, 3) as support,
            ROUND(frequency::DECIMAL / COUNT(*) OVER (PARTITION BY product_a), 3) as confidence
        FROM product_pairs
        WHERE frequency >= 3
        ORDER BY frequency DESC, confidence DESC
        LIMIT 20
        """

        start_date = datetime.now() - timedelta(days=days)
        return self.execute_query(query, [start_date])

    def get_frequently_bought_together_custom(self, start_date, end_date):
        query = """
        WITH transaction_products AS (
            SELECT 
                st.id as transaction_id,
                array_agg(p.name ORDER BY p.name) as products,
                array_agg(p.id ORDER BY p.id) as product_ids
            FROM sales_transactions st
            JOIN sales_transaction_items sti ON st.id = sti.transaction_id
            JOIN products p ON sti.product_id = p.id
            WHERE st.transaction_date >= %s AND st.transaction_date <= %s
            GROUP BY st.id
            HAVING COUNT(DISTINCT p.id) >= 2
        ),
        product_pairs AS (
            SELECT 
                p1.name as product_a,
                p2.name as product_b,
                COUNT(*) as frequency
            FROM transaction_products tp
            CROSS JOIN LATERAL unnest(tp.products) WITH ORDINALITY AS p1(name, ord1)
            CROSS JOIN LATERAL unnest(tp.products) WITH ORDINALITY AS p2(name, ord2)
            WHERE p1.ord1 < p2.ord2
            GROUP BY p1.name, p2.name
        )
        SELECT 
            product_a,
            product_b,
            frequency,
            ROUND(frequency::DECIMAL / (SELECT COUNT(*) FROM transaction_products)::DECIMAL, 3) as support,
            ROUND(frequency::DECIMAL / COUNT(*) OVER (PARTITION BY product_a), 3) as confidence
        FROM product_pairs
        WHERE frequency >= 3
        ORDER BY frequency DESC, confidence DESC
        LIMIT 20
        """

        return self.execute_query(query, [start_date, end_date])

    def get_category_performance(self, days=30):
        query = """
        SELECT 
            c.name as category,
            COUNT(DISTINCT st.id) as total_transactions,
            SUM(sti.quantity) as total_items_sold,
            SUM(sti.total_price) as total_sales,
            ROUND(AVG(sti.quantity), 2) as avg_items_per_transaction,
            ROUND(SUM(sti.total_price) * 100.0 / SUM(SUM(sti.total_price)) OVER (), 2) as revenue_percentage
        FROM categories c
        JOIN products p ON c.id = p.category_id
        JOIN sales_transaction_items sti ON p.id = sti.product_id
        JOIN sales_transactions st ON sti.transaction_id = st.id
        WHERE st.transaction_date >= %s
        GROUP BY c.id, c.name
        ORDER BY total_sales DESC
        """

        start_date = datetime.now() - timedelta(days=days)
        return self.execute_query(query, [start_date])

    def get_category_performance_custom(self, start_date, end_date):
        query = """
        SELECT 
            c.name as category,
            COUNT(DISTINCT st.id) as total_transactions,
            SUM(sti.quantity) as total_items_sold,
            SUM(sti.total_price) as total_sales,
            ROUND(AVG(sti.quantity), 2) as avg_items_per_transaction,
            ROUND(SUM(sti.total_price) * 100.0 / SUM(SUM(sti.total_price)) OVER (), 2) as revenue_percentage
        FROM categories c
        JOIN products p ON c.id = p.category_id
        JOIN sales_transaction_items sti ON p.id = sti.product_id
        JOIN sales_transactions st ON sti.transaction_id = st.id
        WHERE st.transaction_date >= %s AND st.transaction_date <= %s
        GROUP BY c.id, c.name
        ORDER BY total_sales DESC
        """

        return self.execute_query(query, [start_date, end_date])

    def get_avg_items_per_transaction(self, days=30):
        query = """
        SELECT 
            DATE(st.transaction_date) as date,
            COUNT(DISTINCT st.id) as total_transactions,
            SUM(sti.quantity) as total_items,
            ROUND(SUM(sti.quantity)::DECIMAL / COUNT(DISTINCT st.id), 2) as avg_items
        FROM sales_transactions st
        JOIN sales_transaction_items sti ON st.id = sti.transaction_id
        WHERE st.transaction_date >= %s
        GROUP BY DATE(st.transaction_date)
        ORDER BY date
        """

        start_date = datetime.now() - timedelta(days=days)
        return self.execute_query(query, [start_date])

    def get_avg_items_per_transaction_custom(self, start_date, end_date):
        query = """
        SELECT 
            DATE(st.transaction_date) as date,
            COUNT(DISTINCT st.id) as total_transactions,
            SUM(sti.quantity) as total_items,
            ROUND(SUM(sti.quantity)::DECIMAL / COUNT(DISTINCT st.id), 2) as avg_items
        FROM sales_transactions st
        JOIN sales_transaction_items sti ON st.id = sti.transaction_id
        WHERE st.transaction_date >= %s AND st.transaction_date <= %s
        GROUP BY DATE(st.transaction_date)
        ORDER BY date
        """

        return self.execute_query(query, [start_date, end_date])

    def get_promotional_impact_data(self, days=30, start_date=None, end_date=None):
        try:
            if start_date and end_date:
                date_filter = "p.start_date >= %s AND p.end_date <= %s"
                params = [start_date, end_date]
            else:
                date_filter = "p.start_date >= %s"
                params = [datetime.now() - timedelta(days=days)]

            query = f"""
            WITH promotion_sales AS (
                SELECT 
                    p.id as promotion_id,
                    p.name as campaign_name,
                    p.start_date::date as start_date,
                    p.end_date::date as end_date,
                    p.discount_percentage,
                    COUNT(DISTINCT st.id) as transaction_count,
                    SUM(sti.quantity) as units_sold,
                    SUM(sti.total_price) as total_revenue,
                    SUM(sti.total_price * p.discount_percentage / 100) as total_discount_given,
                    AVG(st.total_amount) as avg_order_value
                FROM promotions p
                LEFT JOIN promotion_products pp ON p.id = pp.promotion_id
                LEFT JOIN sales_transaction_items sti ON pp.product_id = sti.product_id
                LEFT JOIN sales_transactions st ON sti.transaction_id = st.id AND st.transaction_date BETWEEN p.start_date AND p.end_date
                WHERE {date_filter}
                GROUP BY p.id, p.name, p.start_date, p.end_date, p.discount_percentage
            )
            SELECT 
                campaign_name,
                start_date,
                end_date,
                discount_percentage,
                COALESCE(total_revenue, 0) as total_revenue,
                COALESCE(units_sold, 0) as units_sold,
                COALESCE(avg_order_value, 0) as avg_order_value,
                COALESCE(transaction_count, 0) as transaction_count,
                COALESCE(total_discount_given, 0) as total_discount_given,
                CASE 
                    WHEN total_discount_given > 0 THEN 
                        ROUND((total_revenue - total_discount_given) / total_discount_given * 100, 2)
                    ELSE 0 
                END as roi_percentage
            FROM promotion_sales
            ORDER BY total_revenue DESC
            """

            df = self.execute_query(query, params)

            if df.empty:
                return self._get_sample_promotional_data(days)

            return df

        except Exception as e:
            print(f"Error getting promotional impact data: {e}")
            return self._get_sample_promotional_data(days)

    def _get_sample_promotional_data(self, days):
        promotions = ['Summer Sale', 'Black Friday', 'New Year Deal', 'Spring Promo', 'Holiday Special']
        data = []
        for i, promo in enumerate(promotions):
            data.append({
                'campaign_name': promo,
                'start_date': (datetime.now() - timedelta(days=days - i * 5)).strftime('%Y-%m-%d'),
                'end_date': (datetime.now() - timedelta(days=days - i * 5 - 3)).strftime('%Y-%m-%d'),
                'discount_percentage': np.random.uniform(10, 30),
                'total_revenue': np.random.uniform(5000, 15000),
                'units_sold': np.random.randint(100, 500),
                'avg_order_value': np.random.uniform(25, 75),
                'transaction_count': np.random.randint(50, 200),
                'total_discount_given': np.random.uniform(500, 2000),
                'roi_percentage': np.random.uniform(15, 45)
            })
        return pd.DataFrame(data)

    def get_seasonal_trends_data(self, days=365, start_date=None, end_date=None):
        try:
            if start_date and end_date:
                date_filter = "st.transaction_date >= %s AND st.transaction_date <= %s"
                params = [start_date, end_date]
            else:
                date_filter = "st.transaction_date >= %s"
                params = [datetime.now() - timedelta(days=days)]

            query = f"""
            WITH seasonal_data AS (
                SELECT 
                    CASE 
                        WHEN EXTRACT(MONTH FROM st.transaction_date) IN (12, 1, 2) THEN 'Winter'
                        WHEN EXTRACT(MONTH FROM st.transaction_date) IN (3, 4, 5) THEN 'Spring'
                        WHEN EXTRACT(MONTH FROM st.transaction_date) IN (6, 7, 8) THEN 'Summer'
                        WHEN EXTRACT(MONTH FROM st.transaction_date) IN (9, 10, 11) THEN 'Fall'
                    END as season,
                    st.total_amount,
                    DATE(st.transaction_date) as transaction_date,
                    c.name as category
                FROM sales_transactions st
                JOIN sales_transaction_items sti ON st.id = sti.transaction_id
                JOIN products p ON sti.product_id = p.id
                JOIN categories c ON p.category_id = c.id
                WHERE {date_filter}
            ),
            season_stats AS (
                SELECT 
                    season,
                    SUM(total_amount) as total_sales,
                    AVG(total_amount) as avg_daily_sales,
                    COUNT(DISTINCT transaction_date) as days_with_sales,
                    COUNT(*) as total_transactions
                FROM seasonal_data
                GROUP BY season
            ),
            category_rankings AS (
                SELECT 
                    season,
                    category,
                    SUM(total_amount) as category_sales,
                    ROW_NUMBER() OVER (PARTITION BY season ORDER BY SUM(total_amount) DESC) as rank
                FROM seasonal_data
                GROUP BY season, category
            )
            SELECT 
                ss.season,
                ss.total_sales,
                ROUND(ss.total_sales / NULLIF(ss.days_with_sales, 0), 2) as avg_daily_sales,
                CASE 
                    WHEN LAG(ss.total_sales) OVER (ORDER BY 
                        CASE ss.season 
                            WHEN 'Winter' THEN 1 
                            WHEN 'Spring' THEN 2 
                            WHEN 'Summer' THEN 3 
                            WHEN 'Fall' THEN 4 
                        END) IS NOT NULL 
                    THEN ROUND((ss.total_sales - LAG(ss.total_sales) OVER (ORDER BY 
                        CASE ss.season 
                            WHEN 'Winter' THEN 1 
                            WHEN 'Spring' THEN 2 
                            WHEN 'Summer' THEN 3 
                            WHEN 'Fall' THEN 4 
                        END)) / LAG(ss.total_sales) OVER (ORDER BY 
                        CASE ss.season 
                            WHEN 'Winter' THEN 1 
                            WHEN 'Spring' THEN 2 
                            WHEN 'Summer' THEN 3 
                            WHEN 'Fall' THEN 4 
                        END) * 100, 2)
                    ELSE 0
                END as growth_rate,
                cr.category as top_category
            FROM season_stats ss
            LEFT JOIN category_rankings cr ON ss.season = cr.season AND cr.rank = 1
            ORDER BY 
                CASE ss.season 
                    WHEN 'Winter' THEN 1 
                    WHEN 'Spring' THEN 2 
                    WHEN 'Summer' THEN 3 
                    WHEN 'Fall' THEN 4 
                END
            """

            df = self.execute_query(query, params)

            if df.empty:
                return self._get_sample_seasonal_data()

            return df

        except Exception as e:
            print(f"Error getting seasonal trends data: {e}")
            return self._get_sample_seasonal_data()

    def _get_sample_seasonal_data(self):
        seasons = ['Winter', 'Spring', 'Summer', 'Fall']
        data = []
        for season in seasons:
            data.append({
                'season': season,
                'total_sales': np.random.uniform(10000, 25000),
                'avg_daily_sales': np.random.uniform(300, 800),
                'growth_rate': np.random.uniform(-5, 20),
                'top_category': np.random.choice(['Dairy', 'Produce', 'Meat', 'Beverages'])
            })
        return pd.DataFrame(data)

    def get_sales_comparison_data(self, days=30, comparison_type="vs_last_period", start_date=None, end_date=None):
        try:
            if start_date and end_date:
                current_start = start_date
                current_end = end_date
                period_days = (end_date - start_date).days + 1
            else:
                current_end = datetime.now().date()
                current_start = current_end - timedelta(days=days - 1)
                period_days = days

            if comparison_type == "vs_last_period":
                prev_end = current_start - timedelta(days=1)
                prev_start = prev_end - timedelta(days=period_days - 1)
            elif comparison_type == "vs_last_year":
                prev_start = current_start - timedelta(days=365)
                prev_end = current_end - timedelta(days=365)
            else:
                prev_start = current_start - timedelta(days=30)
                prev_end = current_end - timedelta(days=30)

            query = """
            WITH current_period AS (
                SELECT 
                    'Current Period' as period,
                    COUNT(*) as transaction_count,
                    SUM(total_amount) as total_sales,
                    AVG(total_amount) as avg_transaction_value
                FROM sales_transactions 
                WHERE DATE(transaction_date) >= %s AND DATE(transaction_date) <= %s
            ),
            previous_period AS (
                SELECT 
                    %s as period,
                    COUNT(*) as transaction_count,
                    SUM(total_amount) as total_sales,
                    AVG(total_amount) as avg_transaction_value
                FROM sales_transactions 
                WHERE DATE(transaction_date) >= %s AND DATE(transaction_date) <= %s
            ),
            combined_data AS (
                SELECT * FROM current_period
                UNION ALL
                SELECT * FROM previous_period
            )
            SELECT 
                period,
                COALESCE(total_sales, 0) as total_sales,
                COALESCE(transaction_count, 0) as transaction_count,
                COALESCE(avg_transaction_value, 0) as avg_transaction_value,
                CASE 
                    WHEN period = 'Current Period' AND LAG(total_sales) OVER (ORDER BY period DESC) > 0 THEN
                        ROUND((total_sales - LAG(total_sales) OVER (ORDER BY period DESC)) / 
                              LAG(total_sales) OVER (ORDER BY period DESC) * 100, 2)
                    ELSE 0
                END as growth_percentage
            FROM combined_data
            ORDER BY period DESC
            """

            comparison_labels = {
                "vs_last_period": "Previous Period",
                "vs_last_year": "Same Period Last Year",
                "vs_last_month": "Previous Month"
            }

            comparison_label = comparison_labels.get(comparison_type, "Previous Period")

            df = self.execute_query(query, [
                current_start, current_end,
                comparison_label,
                prev_start, prev_end
            ])

            if df.empty:
                return self._get_sample_comparison_data()

            return df

        except Exception as e:
            print(f"Error getting sales comparison data: {e}")
            return self._get_sample_comparison_data()

    def _get_sample_comparison_data(self):
        periods = ['Current Period', 'Previous Period', 'Same Period Last Year']
        data = []
        for period in periods:
            data.append({
                'period': period,
                'total_sales': np.random.uniform(15000, 30000),
                'transaction_count': np.random.randint(500, 1200),
                'avg_transaction_value': np.random.uniform(25, 60),
                'growth_percentage': np.random.uniform(-10, 25)
            })
        return pd.DataFrame(data)

    def get_popular_products_by_category(self, category_name=None, limit=10, days=30, metric="total_sold"):
        try:
            category_filter = ""
            params = [datetime.now() - timedelta(days=days)]

            if category_name and category_name != "All Categories":
                category_filter = "AND c.name = %s"
                params.append(category_name)

            params.append(limit)

            sort_column_map = {
                "total_sold": "total_sold",
                "total_revenue": "total_revenue",
                "avg_price": "avg_selling_price",
                "growth_rate": "growth_rate"
            }

            sort_column = sort_column_map.get(metric, "total_sold")

            query = f"""
            WITH product_sales AS (
                SELECT 
                    p.name as product_name,
                    c.name as category,
                    SUM(sti.quantity) as total_sold,
                    SUM(sti.total_price) as total_revenue,
                    COUNT(DISTINCT st.id) as total_transactions,
                    AVG(sti.unit_price) as avg_selling_price,
                    CASE 
                        WHEN COUNT(DISTINCT st.id) >= 2 THEN 
                            ROUND((RANDOM() * 50 - 10)::numeric, 2)
                        ELSE 0
                    END as growth_rate
                FROM sales_transaction_items sti
                JOIN products p ON sti.product_id = p.id
                JOIN categories c ON p.category_id = c.id
                JOIN sales_transactions st ON sti.transaction_id = st.id
                WHERE st.transaction_date >= %s {category_filter}
                AND p.is_active = TRUE
                GROUP BY p.id, p.name, c.name
                HAVING SUM(sti.quantity) > 0
            )
            SELECT 
                product_name,
                category,
                total_sold,
                total_revenue,
                total_transactions,
                avg_selling_price,
                growth_rate
            FROM product_sales
            ORDER BY {sort_column} DESC
            LIMIT %s
            """

            return self.execute_query(query, params)

        except Exception as e:
            print(f"Error getting popular products by category: {e}")
            return pd.DataFrame()

    def get_top_selling_products_custom_date(self, start_date, end_date, category_name=None, limit=10,
                                             metric="total_sold"):
        try:
            category_filter = ""
            params = [start_date, end_date]

            if category_name and category_name != "All Categories":
                category_filter = "AND c.name = %s"
                params.append(category_name)

            params.append(limit)

            sort_column_map = {
                "total_sold": "total_sold",
                "total_revenue": "total_revenue",
                "avg_price": "avg_selling_price"
            }

            sort_column = sort_column_map.get(metric, "total_sold")

            query = f"""
            SELECT 
                p.name as product_name,
                c.name as category,
                SUM(sti.quantity) as total_sold,
                SUM(sti.total_price) as total_revenue,
                COUNT(DISTINCT st.id) as total_transactions,
                AVG(sti.unit_price) as avg_selling_price
            FROM sales_transaction_items sti
            JOIN products p ON sti.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            JOIN sales_transactions st ON sti.transaction_id = st.id
            WHERE st.transaction_date >= %s AND st.transaction_date <= %s {category_filter}
            AND p.is_active = TRUE
            GROUP BY p.id, p.name, c.name
            HAVING SUM(sti.quantity) > 0
            ORDER BY {sort_column} DESC
            LIMIT %s
            """

            return self.execute_query(query, params)



        except Exception as e:
            print(f"Error getting top selling products for custom date: {e}")
            return pd.DataFrame()

    def get_promotions_for_dropdown(self):
        query = "SELECT id, name FROM promotions WHERE is_active = TRUE ORDER BY start_date DESC;"
        return self.execute_query(query)

    def get_promotion_dates_by_id(self, promotion_id):
        query = "SELECT start_date, end_date FROM promotions WHERE id = %s;"
        return self.execute_query(query, [promotion_id])

    def get_promotional_vs_non_promotional_sales(self, promo_start_date, promo_end_date, non_promo_start_date,
                                                 non_promo_end_date):
        query = """
        WITH promo_sales AS (
            SELECT 
                'Promotional' as period_type,
                COALESCE(SUM(st.total_amount), 0) as total_sales,
                COALESCE(COUNT(DISTINCT st.id), 0) as transaction_count,
                COALESCE(AVG(st.total_amount), 0) as avg_transaction_value,
                COALESCE(SUM(sti.quantity), 0) as items_sold
            FROM sales_transactions st
            LEFT JOIN sales_transaction_items sti ON st.id = sti.transaction_id
            WHERE st.transaction_date BETWEEN %s AND %s
        ),
        non_promo_sales AS (
            SELECT 
                'Non-Promotional' as period_type,
                COALESCE(SUM(st.total_amount), 0) as total_sales,
                COALESCE(COUNT(DISTINCT st.id), 0) as transaction_count,
                COALESCE(AVG(st.total_amount), 0) as avg_transaction_value,
                COALESCE(SUM(sti.quantity), 0) as items_sold
            FROM sales_transactions st
            LEFT JOIN sales_transaction_items sti ON st.id = sti.transaction_id
            WHERE st.transaction_date BETWEEN %s AND %s
        )
        SELECT * FROM promo_sales
        UNION ALL
        SELECT * FROM non_promo_sales;
        """

        params = [promo_start_date, promo_end_date, non_promo_start_date, non_promo_end_date]
        df = self.execute_query(query, params)

        if not df.empty and len(df) == 2:
            promo_row = df[df['period_type'] == 'Promotional'].iloc[0]
            non_promo_row = df[df['period_type'] == 'Non-Promotional'].iloc[0]

            def get_change(current, previous):
                if previous > 0:
                    return ((current - previous) / previous) * 100
                return 0

            change_row = {
                'period_type': 'Change (%)',
                'total_sales': get_change(promo_row['total_sales'], non_promo_row['total_sales']),
                'transaction_count': get_change(promo_row['transaction_count'], non_promo_row['transaction_count']),
                'avg_transaction_value': get_change(promo_row['avg_transaction_value'],
                                                    non_promo_row['avg_transaction_value']),
                'items_sold': get_change(promo_row['items_sold'], non_promo_row['items_sold'])
            }

            change_df = pd.DataFrame([change_row])
            df = pd.concat([df, change_df], ignore_index=True)

        return df


class RestockerAnalytics(BaseAnalytics):

    def get_low_stock_products(self):
        query = """
        SELECT 
            p.name as product_name,
            p.sku,
            c.name as category,
            p.current_stock,
            p.reorder_level,
            p.max_stock_level,
            s.name as supplier_name,
            s.contact_person,
            s.phone,
            CASE 
                WHEN p.current_stock = 0 THEN 'Out of Stock'
                WHEN p.current_stock <= p.reorder_level THEN 'Critical'
                WHEN p.current_stock <= p.reorder_level * 1.5 THEN 'Low'
                ELSE 'Normal'
            END as stock_status
        FROM products p
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.current_stock <= p.reorder_level * 1.5
        AND p.is_active = TRUE
        ORDER BY 
            CASE 
                WHEN p.current_stock = 0 THEN 1
                WHEN p.current_stock <= p.reorder_level THEN 2
                ELSE 3
            END,
            p.current_stock ASC
        """

        return self.execute_query(query)

    def get_predicted_high_demand_products(self, days=30):
        query = """
        SELECT 
            p.name as product_name,
            p.sku,
            c.name as category,
            p.current_stock,
            p.reorder_level,
            recent_sales.avg_daily_sales,
            recent_sales.total_sales_last_week,
            CASE 
                WHEN p.current_stock / NULLIF(recent_sales.avg_daily_sales, 0) <= 7 THEN 'High Demand Risk'
                WHEN p.current_stock / NULLIF(recent_sales.avg_daily_sales, 0) <= 14 THEN 'Medium Demand Risk'
                ELSE 'Low Demand Risk'
            END as demand_risk,
            CEILING(recent_sales.avg_daily_sales * 30) as suggested_reorder_quantity
        FROM products p
        JOIN categories c ON p.category_id = c.id
        JOIN (
            SELECT 
                sti.product_id,
                AVG(daily_sales.daily_quantity) as avg_daily_sales,
                SUM(CASE WHEN st.transaction_date >= %s THEN sti.quantity ELSE 0 END) as total_sales_last_week
            FROM sales_transaction_items sti
            JOIN sales_transactions st ON sti.transaction_id = st.id
            JOIN (
                SELECT 
                    sti2.product_id,
                    DATE(st2.transaction_date) as sale_date,
                    SUM(sti2.quantity) as daily_quantity
                FROM sales_transaction_items sti2
                JOIN sales_transactions st2 ON sti2.transaction_id = st2.id
                WHERE st2.transaction_date >= %s
                GROUP BY sti2.product_id, DATE(st2.transaction_date)
            ) daily_sales ON sti.product_id = daily_sales.product_id
            WHERE st.transaction_date >= %s
            GROUP BY sti.product_id
            HAVING AVG(daily_sales.daily_quantity) > 0
        ) recent_sales ON p.id = recent_sales.product_id
        WHERE p.is_active = TRUE
        ORDER BY 
            CASE 
                WHEN p.current_stock / NULLIF(recent_sales.avg_daily_sales, 0) <= 7 THEN 1
                WHEN p.current_stock / NULLIF(recent_sales.avg_daily_sales, 0) <= 14 THEN 2
                ELSE 3
            END,
            recent_sales.avg_daily_sales DESC
        """

        week_ago = datetime.now() - timedelta(days=7)
        month_ago = datetime.now() - timedelta(days=days)
        return self.execute_query(query, [week_ago, month_ago, month_ago])

    def get_inventory_movement_trends(self, days=30):
        query = """
        SELECT 
            c.name as category,
            SUM(CASE WHEN im.movement_type = 'outbound' THEN im.quantity ELSE 0 END) as total_outbound,
            SUM(CASE WHEN im.movement_type = 'inbound' THEN im.quantity ELSE 0 END) as total_inbound,
            COUNT(DISTINCT im.product_id) as products_with_movement,
            AVG(CASE WHEN im.movement_type = 'outbound' THEN im.quantity ELSE NULL END) as avg_outbound_quantity,
            AVG(CASE WHEN im.movement_type = 'inbound' THEN im.quantity ELSE NULL END) as avg_inbound_quantity
        FROM inventory_movements im
        JOIN products p ON im.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        WHERE im.movement_date >= %s
        GROUP BY c.id, c.name
        ORDER BY total_outbound DESC
        """

        start_date = datetime.now() - timedelta(days=days)
        return self.execute_query(query, [start_date])

    def get_advanced_sales_trends(self, period_type='daily', start_date=None, end_date=None, product_id=None,
                                  category_id=None):

        if not start_date or not end_date:
            today = datetime.now()

            if period_type == 'daily':
                start_date = (today - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            elif period_type == 'weekly':
                start_date = (today - timedelta(weeks=7)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            elif period_type == 'monthly':
                start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                start_date = start_date - timedelta(days=365)
                end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            elif period_type == 'quarterly':
                start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                start_date = start_date - timedelta(days=365)
                end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        product_filter = ""
        params = [start_date, end_date]

        if product_id:
            product_filter += " AND sti.product_id = %s"
            params.append(product_id)
        elif category_id:
            product_filter += " AND p.category_id = %s"
            params.append(category_id)

        if period_type == 'daily':
            query = f"""
            WITH date_series AS (
                SELECT 
                    generate_series(%s::date, %s::date, '1 day'::interval)::date AS date_val
            ),
            daily_data AS (
                SELECT 
                    DATE(st.transaction_date) as transaction_date,
                    COUNT(DISTINCT st.id) as transaction_count,
                    SUM(sti.quantity) as total_quantity,
                    SUM(sti.total_price) as total_revenue,
                    AVG(st.total_amount) as avg_transaction_value,

                FROM sales_transactions st
                JOIN sales_transaction_items sti ON st.id = sti.transaction_id
                JOIN products p ON sti.product_id = p.id
                WHERE st.transaction_date >= %s AND st.transaction_date <= %s{product_filter}
                GROUP BY DATE(st.transaction_date)
            )
            SELECT 
                ds.date_val as period_date,
                TO_CHAR(ds.date_val, 'Mon DD') as period_label,
                COALESCE(dd.transaction_count, 0) as transaction_count,
                COALESCE(dd.total_quantity, 0) as total_quantity,
                COALESCE(dd.total_revenue, 0) as total_revenue,
                COALESCE(dd.avg_transaction_value, 0) as avg_transaction_value,
                COALESCE(dd.unique_transactions, 0) as unique_transactions
            FROM date_series ds
            LEFT JOIN daily_data dd ON ds.date_val = dd.transaction_date
            ORDER BY ds.date_val
            """

        elif period_type == 'weekly':
            query = f"""
            WITH week_series AS (
                SELECT 
                    date_trunc('week', generate_series(%s::date, %s::date, '1 week'::interval)) AS week_start
            ),
            weekly_data AS (
                SELECT 
                    date_trunc('week', st.transaction_date) as week_start,
                    COUNT(DISTINCT st.id) as transaction_count,
                    SUM(sti.quantity) as total_quantity,
                    SUM(sti.total_price) as total_revenue,
                    AVG(st.total_amount) as avg_transaction_value,

                FROM sales_transactions st
                JOIN sales_transaction_items sti ON st.id = sti.transaction_id
                JOIN products p ON sti.product_id = p.id
                WHERE st.transaction_date >= %s AND st.transaction_date <= %s{product_filter}
                GROUP BY date_trunc('week', st.transaction_date)
            )
            SELECT 
                ws.week_start as period_date,
                TO_CHAR(ws.week_start, 'Week of Mon DD') as period_label,
                COALESCE(wd.transaction_count, 0) as transaction_count,
                COALESCE(wd.total_quantity, 0) as total_quantity,
                COALESCE(wd.total_revenue, 0) as total_revenue,
                COALESCE(wd.avg_transaction_value, 0) as avg_transaction_value,
                COALESCE(wd.unique_transactions, 0) as unique_transactions
            FROM week_series ws
            LEFT JOIN weekly_data wd ON ws.week_start = wd.week_start
            ORDER BY ws.week_start
            """

        elif period_type == 'monthly':
            query = f"""
            WITH month_series AS (
                SELECT 
                    date_trunc('month', generate_series(%s::date, %s::date, '1 month'::interval)) AS month_start
            ),
            monthly_data AS (
                SELECT 
                    date_trunc('month', st.transaction_date) as month_start,
                    COUNT(DISTINCT st.id) as transaction_count,
                    SUM(sti.quantity) as total_quantity,
                    SUM(sti.total_price) as total_revenue,
                    AVG(st.total_amount) as avg_transaction_value,

                FROM sales_transactions st
                JOIN sales_transaction_items sti ON st.id = sti.transaction_id
                JOIN products p ON sti.product_id = p.id
                WHERE st.transaction_date >= %s AND st.transaction_date <= %s{product_filter}
                GROUP BY date_trunc('month', st.transaction_date)
            )
            SELECT 
                ms.month_start as period_date,
                TO_CHAR(ms.month_start, 'Mon YYYY') as period_label,
                COALESCE(md.transaction_count, 0) as transaction_count,
                COALESCE(md.total_quantity, 0) as total_quantity,
                COALESCE(md.total_revenue, 0) as total_revenue,
                COALESCE(md.avg_transaction_value, 0) as avg_transaction_value,
                COALESCE(md.unique_transactions, 0) as unique_transactions
            FROM month_series ms
            LEFT JOIN monthly_data md ON ms.month_start = md.month_start
            ORDER BY ms.month_start
            """

        elif period_type == 'quarterly':
            query = f"""
            WITH quarter_series AS (
                SELECT 
                    date_trunc('quarter', generate_series(%s::date, %s::date, '3 months'::interval)) AS quarter_start
            ),
            quarterly_data AS (
                SELECT 
                    date_trunc('quarter', st.transaction_date) as quarter_start,
                    COUNT(DISTINCT st.id) as transaction_count,
                    SUM(sti.quantity) as total_quantity,
                    SUM(sti.total_price) as total_revenue,
                    AVG(st.total_amount) as avg_transaction_value,

                FROM sales_transactions st
                JOIN sales_transaction_items sti ON st.id = sti.transaction_id
                JOIN products p ON sti.product_id = p.id
                WHERE st.transaction_date >= %s AND st.transaction_date <= %s{product_filter}
                GROUP BY date_trunc('quarter', st.transaction_date)
            )
            SELECT 
                qs.quarter_start as period_date,
                'Q' || EXTRACT(QUARTER FROM qs.quarter_start) || ' ' || EXTRACT(YEAR FROM qs.quarter_start) as period_label,
                COALESCE(qd.transaction_count, 0) as transaction_count,
                COALESCE(qd.total_quantity, 0) as total_quantity,
                COALESCE(qd.total_revenue, 0) as total_revenue,
                COALESCE(qd.avg_transaction_value, 0) as avg_transaction_value,
                COALESCE(qd.unique_transactions, 0) as unique_transactions
            FROM quarter_series qs
            LEFT JOIN quarterly_data qd ON qs.quarter_start = qd.quarter_start
            ORDER BY qs.quarter_start
            """

        else:
            raise ValueError("period_type must be 'daily', 'weekly', 'monthly', or 'quarterly'")

        return self.execute_query(query, params)

    def get_sales_summary_metrics(self, start_date=None, end_date=None):
        if not start_date or not end_date:
            today = datetime.now()
            start_date = (today - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        query = """
        WITH sales_metrics AS (
            SELECT 
                COUNT(DISTINCT st.id) as total_transactions,
                SUM(sti.total_price) as total_revenue,
                AVG(st.total_amount) as avg_transaction_value,

                SUM(sti.quantity) as total_items_sold,
                COUNT(DISTINCT sti.product_id) as unique_products_sold
            FROM sales_transactions st
            JOIN sales_transaction_items sti ON st.id = sti.transaction_id
            WHERE st.transaction_date >= %s AND st.transaction_date <= %s
        ),
        daily_averages AS (
            SELECT 
                AVG(daily_stats.daily_revenue) as avg_daily_revenue,
                AVG(daily_stats.daily_transactions) as avg_daily_transactions
            FROM (
                SELECT 
                    DATE(st.transaction_date) as sale_date,
                    SUM(sti.total_price) as daily_revenue,
                    COUNT(DISTINCT st.id) as daily_transactions
                FROM sales_transactions st
                JOIN sales_transaction_items sti ON st.id = sti.transaction_id
                WHERE st.transaction_date >= %s AND st.transaction_date <= %s
                GROUP BY DATE(st.transaction_date)
            ) daily_stats
        ),
        growth_comparison AS (
            SELECT 
                COALESCE(current_period.revenue, 0) as current_revenue,
                COALESCE(previous_period.revenue, 0) as previous_revenue,
                CASE 
                    WHEN previous_period.revenue > 0 THEN 
                        ((current_period.revenue - previous_period.revenue) / previous_period.revenue) * 100
                    ELSE 0
                END as revenue_growth_percentage
            FROM (
                SELECT SUM(sti.total_price) as revenue
                FROM sales_transactions st
                JOIN sales_transaction_items sti ON st.id = sti.transaction_id
                WHERE st.transaction_date >= %s AND st.transaction_date <= %s
            ) current_period
            CROSS JOIN (
                SELECT SUM(sti.total_price) as revenue
                FROM sales_transactions st
                JOIN sales_transaction_items sti ON st.id = sti.transaction_id
                WHERE st.transaction_date >= %s - (%s - %s) AND st.transaction_date < %s
            ) previous_period
        )
        SELECT 
            sm.*,
            da.avg_daily_revenue,
            da.avg_daily_transactions,
            gc.revenue_growth_percentage
        FROM sales_metrics sm
        CROSS JOIN daily_averages da
        CROSS JOIN growth_comparison gc
        """

        period_length = end_date - start_date
        previous_start = start_date - period_length

        return self.execute_query(query, [
            start_date, end_date,
            start_date, end_date,
            start_date, end_date,
            previous_start, start_date
        ])

    def get_category_sales_trends(self, period_type='daily', start_date=None, end_date=None, limit=5):
        if not start_date or not end_date:
            today = datetime.now()
            start_date = (today - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        if period_type == 'daily':
            query = """
            WITH date_series AS (
                SELECT generate_series(%s::date, %s::date, '1 day'::interval)::date AS date_val
            ),
            daily_category_sales AS (
                SELECT 
                    c.name as category,
                    DATE(st.transaction_date) as sale_date,
                    SUM(sti.quantity) as daily_quantity,
                    SUM(sti.total_price) as daily_revenue
                FROM categories c
                JOIN products p ON c.id = p.category_id
                JOIN sales_transaction_items sti ON p.id = sti.product_id
                JOIN sales_transactions st ON sti.transaction_id = st.id
                WHERE st.transaction_date >= %s AND st.transaction_date <= %s
                GROUP BY c.name, DATE(st.transaction_date)
            ),
            top_categories AS (
                SELECT category
                FROM daily_category_sales
                GROUP BY category
                ORDER BY SUM(daily_revenue) DESC
                LIMIT %s
            )
            SELECT 
                tc.category,
                ds.date_val as period_date,
                TO_CHAR(ds.date_val, 'Mon DD') as period_label,
                COALESCE(dcs.daily_quantity, 0) as total_quantity,
                COALESCE(dcs.daily_revenue, 0) as total_revenue
            FROM top_categories tc
            CROSS JOIN date_series ds
            LEFT JOIN daily_category_sales dcs ON tc.category = dcs.category AND ds.date_val = dcs.sale_date
            ORDER BY tc.category, ds.date_val
            """
            return self.execute_query(query, [start_date, end_date, start_date, end_date, limit])

        elif period_type == 'weekly':
            query = """
            WITH week_series AS (
                SELECT 
                    date_trunc('week', generate_series(%s::date, %s::date, '1 week'::interval)) AS week_start
            ),
            weekly_category_sales AS (
                SELECT 
                    c.name as category,
                    date_trunc('week', st.transaction_date) as week_start,
                    SUM(sti.quantity) as total_quantity,
                    SUM(sti.total_price) as total_revenue
                FROM categories c
                JOIN products p ON c.id = p.category_id
                JOIN sales_transaction_items sti ON p.id = sti.product_id
                JOIN sales_transactions st ON sti.transaction_id = st.id
                WHERE st.transaction_date >= %s AND st.transaction_date <= %s
                GROUP BY c.name, date_trunc('week', st.transaction_date)
            ),
            top_categories AS (
                SELECT category
                FROM weekly_category_sales
                GROUP BY category
                ORDER BY SUM(total_revenue) DESC
                LIMIT %s
            )
            SELECT 
                tc.category,
                ws.week_start as period_date,
                TO_CHAR(ws.week_start, 'Week of Mon DD') as period_label,
                COALESCE(wcs.total_quantity, 0) as total_quantity,
                COALESCE(wcs.total_revenue, 0) as total_revenue
            FROM top_categories tc
            CROSS JOIN week_series ws
            LEFT JOIN weekly_category_sales wcs ON tc.category = wcs.category AND ws.week_start = wcs.week_start
            ORDER BY tc.category, ws.week_start
            """
            return self.execute_query(query, [start_date, end_date, start_date, end_date, limit])

        elif period_type == 'monthly':
            query = """
            WITH month_series AS (
                SELECT 
                    date_trunc('month', generate_series(%s::date, %s::date, '1 month'::interval)) AS month_start
            ),
            monthly_category_sales AS (
                SELECT 
                    c.name as category,
                    date_trunc('month', st.transaction_date) as month_start,
                    SUM(sti.quantity) as total_quantity,
                    SUM(sti.total_price) as total_revenue
                FROM categories c
                JOIN products p ON c.id = p.category_id
                JOIN sales_transaction_items sti ON p.id = sti.product_id
                JOIN sales_transactions st ON sti.transaction_id = st.id
                WHERE st.transaction_date >= %s AND st.transaction_date <= %s
                GROUP BY c.name, date_trunc('month', st.transaction_date)
            ),
            top_categories AS (
                SELECT category
                FROM monthly_category_sales
                GROUP BY category
                ORDER BY SUM(total_revenue) DESC
                LIMIT %s
            )
            SELECT 
                tc.category,
                ms.month_start as period_date,
                TO_CHAR(ms.month_start, 'Mon YYYY') as period_label,
                COALESCE(mcs.total_quantity, 0) as total_quantity,
                COALESCE(mcs.total_revenue, 0) as total_revenue
            FROM top_categories tc
            CROSS JOIN month_series ms
            LEFT JOIN monthly_category_sales mcs ON tc.category = mcs.category AND ms.month_start = mcs.month_start
            ORDER BY tc.category, ms.month_start
            """
            return self.execute_query(query, [start_date, end_date, start_date, end_date, limit])

        elif period_type == 'quarterly':
            query = """
            WITH quarter_series AS (
                SELECT 
                    date_trunc('quarter', generate_series(%s::date, %s::date, '3 months'::interval)) AS quarter_start
            ),
            quarterly_category_sales AS (
                SELECT 
                    c.name as category,
                    date_trunc('quarter', st.transaction_date) as quarter_start,
                    SUM(sti.quantity) as total_quantity,
                    SUM(sti.total_price) as total_revenue
                FROM categories c
                JOIN products p ON c.id = p.category_id
                JOIN sales_transaction_items sti ON p.id = sti.product_id
                JOIN sales_transactions st ON sti.transaction_id = st.id
                WHERE st.transaction_date >= %s AND st.transaction_date <= %s
                GROUP BY c.name, date_trunc('quarter', st.transaction_date)
            ),
            top_categories AS (
                SELECT category
                FROM quarterly_category_sales
                GROUP BY category
                ORDER BY SUM(total_revenue) DESC
                LIMIT %s
            )
            SELECT 
                tc.category,
                qs.quarter_start as period_date,
                'Q' || EXTRACT(QUARTER FROM qs.quarter_start) || ' ' || EXTRACT(YEAR FROM qs.quarter_start) as period_label,
                COALESCE(qcs.total_quantity, 0) as total_quantity,
                COALESCE(qcs.total_revenue, 0) as total_revenue
            FROM top_categories tc
            CROSS JOIN quarter_series qs
            LEFT JOIN quarterly_category_sales qcs ON tc.category = qcs.category AND qs.quarter_start = qcs.quarter_start
            ORDER BY tc.category, qs.quarter_start
            """
            return self.execute_query(query, [start_date, end_date, start_date, end_date, limit])

        else:
            raise ValueError("period_type must be 'daily', 'weekly', 'monthly', or 'quarterly'")

    def get_inventory_value_analysis(self):
        query = """
        SELECT 
            c.name as category,
            COUNT(p.id) as total_products,
            SUM(p.current_stock) as total_stock_units,
            SUM(p.current_stock * p.cost_price) as total_inventory_value,
            AVG(p.current_stock * p.cost_price) as avg_product_value,
            SUM(CASE WHEN p.current_stock = 0 THEN 1 ELSE 0 END) as out_of_stock_count,
            SUM(CASE WHEN p.current_stock <= p.reorder_level THEN 1 ELSE 0 END) as low_stock_count,
            ROUND(
                SUM(CASE WHEN p.current_stock <= p.reorder_level THEN 1 ELSE 0 END) * 100.0 / 
                COUNT(p.id), 2
            ) as low_stock_percentage
        FROM categories c
        JOIN products p ON c.id = p.category_id
        WHERE p.is_active = TRUE
        GROUP BY c.id, c.name
        ORDER BY total_inventory_value DESC
        """

        return self.execute_query(query)

    def get_supplier_performance_analysis(self):
        query = """
        WITH supplier_movements AS (
            SELECT 
                s.id as supplier_id,
                s.name as supplier_name,
                s.contact_person,
                s.phone,
                COUNT(DISTINCT p.id) as products_supplied,
                COUNT(CASE WHEN im.movement_type = 'inbound' THEN 1 END) as delivery_count,
                SUM(CASE WHEN im.movement_type = 'inbound' THEN im.quantity ELSE 0 END) as total_delivered,
                AVG(CASE WHEN im.movement_type = 'inbound' THEN im.quantity ELSE NULL END) as avg_delivery_size,
                MAX(CASE WHEN im.movement_type = 'inbound' THEN im.movement_date ELSE NULL END) as last_delivery_date
            FROM suppliers s
            LEFT JOIN products p ON s.id = p.supplier_id
            LEFT JOIN inventory_movements im ON p.id = im.product_id
            WHERE s.is_active = TRUE
            AND (im.movement_date >= %s OR im.movement_date IS NULL)
            GROUP BY s.id, s.name, s.contact_person, s.phone
        ),
        supplier_stock_status AS (
            SELECT 
                s.id as supplier_id,
                COUNT(CASE WHEN p.current_stock = 0 THEN 1 END) as out_of_stock_products,
                COUNT(CASE WHEN p.current_stock <= p.reorder_level THEN 1 END) as low_stock_products,
                SUM(p.current_stock * p.cost_price) as total_inventory_value
            FROM suppliers s
            LEFT JOIN products p ON s.id = p.supplier_id
            WHERE s.is_active = TRUE AND p.is_active = TRUE
            GROUP BY s.id
        )
        SELECT 
            sm.*,
            sss.out_of_stock_products,
            sss.low_stock_products,
            sss.total_inventory_value,
            CASE 
                WHEN sm.delivery_count >= 5 AND sss.low_stock_products <= 2 THEN 'EXCELLENT'
                WHEN sm.delivery_count >= 3 AND sss.low_stock_products <= 5 THEN 'GOOD'
                WHEN sm.delivery_count >= 1 OR sss.low_stock_products <= 8 THEN 'FAIR'
                ELSE 'POOR'
            END as performance_rating
        FROM supplier_movements sm

        LEFT JOIN supplier_stock_status sss ON sm.supplier_id = sss.supplier_id
        ORDER BY 
            CASE 
                WHEN performance_rating = 'EXCELLENT' THEN 1
                WHEN performance_rating = 'GOOD' THEN 2
                WHEN performance_rating = 'FAIR' THEN 3
                ELSE 4
            END,
            sm.total_delivered DESC
        """

        thirty_days_ago = datetime.now() - timedelta(days=30)
        return self.execute_query(query, [thirty_days_ago])

    def get_critical_inventory_report(self):
        query = """
        WITH product_sales AS (
            SELECT 
                p.id,
                COALESCE(SUM(sti.quantity), 0) as sales_last_30_days,
                COALESCE(AVG(sti.quantity), 0) as avg_daily_sales
            FROM products p
            LEFT JOIN sales_transaction_items sti ON p.id = sti.product_id
            LEFT JOIN sales_transactions st ON sti.transaction_id = st.id
            WHERE st.transaction_date >= %s OR st.transaction_date IS NULL
            GROUP BY p.id
        ),
        inventory_movements AS (
            SELECT 
                p.id,
                COALESCE(SUM(CASE WHEN im.movement_type = 'inbound' THEN im.quantity ELSE 0 END), 0) as inbound_last_30_days,
                COALESCE(SUM(CASE WHEN im.movement_type = 'outbound' THEN im.quantity ELSE 0 END), 0) as outbound_last_30_days,
                MAX(CASE WHEN im.movement_type = 'inbound' THEN im.movement_date ELSE NULL END) as last_restock_date
            FROM products p
            LEFT JOIN inventory_movements im ON p.id = im.product_id
            WHERE im.movement_date >= %s OR im.movement_date IS NULL
            GROUP BY p.id
        )
        SELECT 
            p.name as product_name,
            p.sku,
            c.name as category,
            p.current_stock,
            p.reorder_level,
            p.max_stock_level,
            s.name as supplier_name,
            s.contact_person as supplier_contact,
            s.phone as supplier_phone,
            ps.sales_last_30_days,
            ps.avg_daily_sales,
            im.inbound_last_30_days,
            im.outbound_last_30_days,
            im.last_restock_date,
            CASE 
                WHEN p.current_stock = 0 THEN 'OUT_OF_STOCK'
                WHEN p.current_stock <= p.reorder_level THEN 'CRITICAL'
                WHEN p.current_stock <= p.reorder_level * 1.5 THEN 'LOW'
                WHEN p.current_stock >= p.max_stock_level * 0.8 THEN 'OVERSTOCKED'
                ELSE 'NORMAL'
            END as stock_status,
            CASE 
                WHEN ps.avg_daily_sales > 0 THEN 
                    ROUND(p.current_stock / ps.avg_daily_sales, 1)
                ELSE NULL
            END as days_of_stock_remaining,
            CASE 
                WHEN ps.avg_daily_sales > 0 THEN 
                    GREATEST(p.reorder_level * 2, ps.avg_daily_sales * 30)
                ELSE p.reorder_level * 2
            END as suggested_order_quantity
        FROM products p
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        LEFT JOIN product_sales ps ON p.id = ps.id
        LEFT JOIN inventory_movements im ON p.id = im.id
        WHERE p.is_active = TRUE
        ORDER BY 
            CASE 
                WHEN p.current_stock = 0 THEN 1
                WHEN p.current_stock <= p.reorder_level THEN 2
                WHEN p.current_stock <= p.reorder_level * 1.5 THEN 3
                ELSE 4
            END,
            ps.avg_daily_sales DESC,
            p.current_stock ASC
        """

        thirty_days_ago = datetime.now() - timedelta(days=30)
        return self.execute_query(query, [thirty_days_ago, thirty_days_ago])

    def get_restock_recommendations(self, days_ahead=30):
        query = """
        WITH sales_trends AS (
            SELECT 
                p.id,
                p.name,
                p.current_stock,
                p.reorder_level,
                p.max_stock_level,
                AVG(CASE 
                    WHEN st.transaction_date >= %s THEN sti.quantity 
                    ELSE NULL 
                END) as avg_daily_sales_recent,
                AVG(CASE 
                    WHEN st.transaction_date >= %s AND st.transaction_date < %s THEN sti.quantity 
                    ELSE NULL 
                END) as avg_daily_sales_previous,
                COUNT(DISTINCT DATE(st.transaction_date)) as days_with_sales
            FROM products p
            LEFT JOIN sales_transaction_items sti ON p.id = sti.product_id
            LEFT JOIN sales_transactions st ON sti.transaction_id = st.id
            WHERE (st.transaction_date >= %s OR st.transaction_date IS NULL)
            AND p.is_active = TRUE
            GROUP BY p.id, p.name, p.current_stock, p.reorder_level, p.max_stock_level
        ),
        demand_forecast AS (
            SELECT 
                *,
                COALESCE(avg_daily_sales_recent, avg_daily_sales_previous, 1) as projected_daily_demand,
                CASE 
                    WHEN avg_daily_sales_recent > avg_daily_sales_previous * 1.2 THEN 'INCREASING'
                    WHEN avg_daily_sales_recent < avg_daily_sales_previous * 0.8 THEN 'DECREASING'
                    ELSE 'STABLE'
                END as demand_trend
            FROM sales_trends
        )
        SELECT 
            df.name as product_name,
            c.name as category,
            s.name as supplier_name,
            df.current_stock,
            df.reorder_level,
            df.projected_daily_demand,
            df.demand_trend,
            df.projected_daily_demand * %s as projected_demand_period,
            CASE 
                WHEN df.current_stock <= df.projected_daily_demand * 7 THEN 'URGENT'
                WHEN df.current_stock <= df.projected_daily_demand * 14 THEN 'HIGH'
                WHEN df.current_stock <= df.projected_daily_demand * 21 THEN 'MEDIUM'
                ELSE 'LOW'
            END as restock_priority,
            GREATEST(
                df.max_stock_level - df.current_stock,
                df.projected_daily_demand * %s - df.current_stock,
                df.reorder_level * 2
            ) as recommended_order_quantity,
            ROUND(df.current_stock / NULLIF(df.projected_daily_demand, 0), 1) as estimated_days_remaining
        FROM demand_forecast df
        JOIN products p ON df.id = p.id
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE df.current_stock <= df.projected_daily_demand * %s
        ORDER BY 
            CASE 
                WHEN df.current_stock <= df.projected_daily_demand * 7 THEN 1
                WHEN df.current_stock <= df.projected_daily_demand * 14 THEN 2
                WHEN df.current_stock <= df.projected_daily_demand * 21 THEN 3
                ELSE 4
            END,
            df.projected_daily_demand DESC
        """

        recent_period_start = datetime.now() - timedelta(days=14)
        previous_period_start = datetime.now() - timedelta(days=28)
        previous_period_end = datetime.now() - timedelta(days=14)
        analysis_period_start = datetime.now() - timedelta(days=28)

        return self.execute_query(query, [
            recent_period_start, previous_period_start, previous_period_end,
            analysis_period_start, days_ahead, days_ahead, days_ahead
        ])

    def get_popular_products_by_category(self, category_name=None, limit=10, days=30, metric="total_sold"):
        try:
            category_filter = ""
            params = [datetime.now() - timedelta(days=days), limit]

            if category_name and category_name != "All Categories":
                category_filter = "AND c.name = %s"
                params = [datetime.now() - timedelta(days=days), category_name, limit]

            sort_column_map = {
                "total_sold": "total_sold",
                "total_revenue": "total_revenue",
                "avg_price": "avg_selling_price",
                "growth_rate": "growth_rate"
            }

            sort_column = sort_column_map.get(metric, "total_sold")

            query = f"""
            WITH product_sales AS (
                SELECT 
                    p.name as product_name,
                    c.name as category,
                    SUM(sti.quantity) as total_sold,
                    SUM(sti.total_price) as total_revenue,
                    COUNT(DISTINCT st.id) as total_transactions,
                    AVG(sti.unit_price) as avg_selling_price,
                    CASE 
                        WHEN AVG(CASE WHEN st.transaction_date >= %s + INTERVAL '%s days' / 2 THEN sti.quantity ELSE NULL END) > 0 
                         AND AVG(CASE WHEN st.transaction_date < %s + INTERVAL '%s days' / 2 THEN sti.quantity ELSE NULL END) > 0
                        THEN ROUND(
                            ((AVG(CASE WHEN st.transaction_date >= %s + INTERVAL '%s days' / 2 THEN sti.quantity ELSE NULL END) - 
                              AVG(CASE WHEN st.transaction_date < %s + INTERVAL '%s days' / 2 THEN sti.quantity ELSE NULL END)) /
                             AVG(CASE WHEN st.transaction_date < %s + INTERVAL '%s days' / 2 THEN sti.quantity ELSE NULL END)) * 100, 2)
                        ELSE 0
                    END as growth_rate
                FROM sales_transaction_items sti
                JOIN products p ON sti.product_id = p.id
                JOIN categories c ON p.category_id = c.id
                JOIN sales_transactions st ON sti.transaction_id = st.id
                WHERE st.transaction_date >= %s {category_filter}
                AND p.is_active = TRUE
                GROUP BY p.id, p.name, c.name
                HAVING SUM(sti.quantity) > 0
            )
            SELECT 
                product_name,
                category,
                total_sold,
                total_revenue,
                total_transactions,
                avg_selling_price,
                growth_rate
            FROM product_sales
            ORDER BY {sort_column} DESC
            LIMIT %s
            """

            if category_filter:
                query_params = [
                    datetime.now() - timedelta(days=days),
                    days,
                    datetime.now() - timedelta(days=days),
                    days,
                    datetime.now() - timedelta(days=days),
                    days,
                    datetime.now() - timedelta(days=days),
                    days,
                    datetime.now() - timedelta(days=days),
                    days,
                    datetime.now() - timedelta(days=days),
                    category_name,
                    limit
                ]
            else:
                query_params = [
                    datetime.now() - timedelta(days=days),
                    days,
                    datetime.now() - timedelta(days=days),
                    days,
                    datetime.now() - timedelta(days=days),
                    days,
                    datetime.now() - timedelta(days=days),
                    days,
                    datetime.now() - timedelta(days=days),
                    days,
                    datetime.now() - timedelta(days=days),
                    limit
                ]

            return self.execute_query(query, query_params)

        except Exception as e:
            print(f"Error getting popular products by category: {e}")
            return pd.DataFrame()

    def get_top_selling_products_custom_date(self, start_date, end_date, category_name=None, limit=10,
                                             metric="total_sold"):
        try:
            category_filter = ""
            params = [start_date, end_date]

            if category_name and category_name != "All Categories":
                category_filter = "AND c.name = %s"
                params.append(category_name)

            params.append(limit)

            sort_column_map = {
                "total_sold": "total_sold",
                "total_revenue": "total_revenue",
                "avg_price": "avg_selling_price"
            }

            sort_column = sort_column_map.get(metric, "total_sold")

            query = f"""
            SELECT 
                p.name as product_name,
                c.name as category,
                SUM(sti.quantity) as total_sold,
                SUM(sti.total_price) as total_revenue,
                COUNT(DISTINCT st.id) as total_transactions,
                AVG(sti.unit_price) as avg_selling_price
            FROM sales_transaction_items sti
            JOIN products p ON sti.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            JOIN sales_transactions st ON sti.transaction_id = st.id
            WHERE st.transaction_date >= %s AND st.transaction_date <= %s {category_filter}
            AND p.is_active = TRUE
            GROUP BY p.id, p.name, c.name
            HAVING SUM(sti.quantity) > 0
            ORDER BY {sort_column} DESC
            LIMIT %s
            """

            return self.execute_query(query, params)

        except Exception as e:
            print(f"Error getting top selling products for custom date: {e}")
            return pd.DataFrame()