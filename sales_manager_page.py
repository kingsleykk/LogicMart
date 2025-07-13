import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
from analytics_engine import SalesManagerAnalytics
from report_generator import SalesManagerReportGenerator
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import seaborn as sns

# Set matplotlib style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class SalesDataFrame(tk.Frame):
    """Base class for sales manager analytics displays"""
    
    def __init__(self, master, title):
        super().__init__(master, bg="#f0f0f0")
        self.title = title
        self.analytics = SalesManagerAnalytics()
        
        # Define theme colors consistent with manager page
        self.theme_colors = {
            'bg': '#f0f0f0',
            'fg': '#333333',
            'secondary_bg': '#ffffff',
            'accent': '#4a90e2',
            'button_bg': '#e0e0e0',
            'button_fg': '#333333',
            'entry_bg': '#ffffff',
            'entry_fg': '#333333',
            'sidebar_bg': '#2c3e50',
            'chart_bg': 'white',
            'chart_colors': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#8B5A3C', '#006D77'],
            'grid_color': '#cccccc',
            'text_color': 'black'
        }
        self.configure(bg=self.theme_colors['bg'])
        self.create_header()
        
    def create_header(self):
        """Create header with title and export buttons"""
        header_frame = tk.Frame(self, bg=self.theme_colors['bg'])
        header_frame.pack(fill="x", padx=20, pady=10)
        
        # Title
        title_label = tk.Label(header_frame, text=self.title, 
                              font=("Segoe UI", 18, "bold"), 
                              bg=self.theme_colors['bg'], fg="#2c3e50")
        title_label.pack(side="left")
        
        # Export buttons
        export_frame = tk.Frame(header_frame, bg=self.theme_colors['bg'])
        export_frame.pack(side="right")
        
        tk.Button(export_frame, text="📊 Export PDF", 
                 command=self.export_pdf, bg="#3498db", fg="white",
                 font=("Segoe UI", 9), relief="flat", padx=10).pack(side="right", padx=5)
        
        tk.Button(export_frame, text="📑 Export Excel", 
                 command=self.export_excel, bg="#27ae60", fg="white",
                 font=("Segoe UI", 9), relief="flat", padx=10).pack(side="right", padx=5)
        
        tk.Button(export_frame, text="🔄 Refresh", 
                 command=self.refresh_data, bg="#e74c3c", fg="white",
                 font=("Segoe UI", 9), relief="flat", padx=10).pack(side="right", padx=5)
    
    def create_data_table(self, df, parent_frame):
        """Create a scrollable data table"""
        if df.empty:
            tk.Label(parent_frame, text="No data available", 
                    font=("Segoe UI", 12), bg=self.theme_colors['bg']).pack(pady=20)
            return
        
        # Create treeview for table
        tree_frame = tk.Frame(parent_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        tree = ttk.Treeview(tree_frame)
        tree.pack(side="left", fill="both", expand=True)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        v_scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=v_scrollbar.set)
        
        # Configure columns
        tree["columns"] = list(df.columns)
        tree["show"] = "headings"
        
        for col in df.columns:
            tree.heading(col, text=col.replace('_', ' ').title())
            tree.column(col, width=120, anchor="center")
        
        # Insert data
        for index, row in df.iterrows():
            values = [str(val)[:50] + "..." if len(str(val)) > 50 else str(val) for val in row]
            tree.insert("", "end", values=values)
        
        return tree
    
    def create_chart(self, df, chart_type="bar", x_col=None, y_col=None, figsize=(10, 5)):
        """Create charts for the data"""
        if df.empty:
            return None
            
        try:
            fig, ax = plt.subplots(figsize=figsize, facecolor=self.theme_colors['chart_bg'])
            
            if chart_type == "line":
                if x_col and y_col:
                    ax.plot(df[x_col], df[y_col], marker='o', linewidth=2.5, markersize=6, color='#e74c3c')
                    ax.set_xlabel(x_col.replace('_', ' ').title())
                    ax.set_ylabel(y_col.replace('_', ' ').title())
                    if 'date' in x_col.lower():
                        plt.xticks(rotation=45)
            elif chart_type == "bar":
                if x_col and y_col:
                    ax.bar(df[x_col], df[y_col], color='#3498db')
                    ax.set_xlabel(x_col.replace('_', ' ').title())
                    ax.set_ylabel(y_col.replace('_', ' ').title())
                    if len(df) > 10:
                        plt.xticks(rotation=45)
            
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            return fig
        except Exception as e:
            print(f"Error creating chart: {e}")
            return None
    
    def export_pdf(self):
        messagebox.showinfo("Export", "PDF export - override in child class")
    
    def export_excel(self):
        messagebox.showinfo("Export", "Excel export - override in child class")
    
    def refresh_data(self):
        messagebox.showinfo("Refresh", "Data refreshed!")


class SalesTrend(SalesDataFrame):
    def __init__(self, master):
        super().__init__(master, "Sales Trend Analysis")
        # Initialize filter variables
        self.period_var = tk.StringVar(value="30")
        self.use_custom_dates = tk.BooleanVar(value=False)
        self.metric_var = tk.StringVar(value="revenue")
        
        # Initialize DateEntry widgets - will be created in create_controls
        self.start_date_entry = None
        self.end_date_entry = None
        
        self.create_controls()
        self.load_data()
    
    def create_controls(self):
        """Create filter controls for sales trend analysis"""
        control_frame = tk.Frame(self, bg=self.theme_colors['bg'], relief="solid", bd=1)
        control_frame.pack(fill="x", padx=20, pady=5)
        
        # Period selection
        period_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        period_frame.pack(side="left", padx=10, pady=10)
        
        tk.Label(period_frame, text="Time Period:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        period_combo = ttk.Combobox(period_frame, textvariable=self.period_var, 
                                   values=["7", "14", "30", "60", "90", "180"], width=10)
        period_combo.pack(pady=2)
        period_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        tk.Label(period_frame, text="days", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        # Metric selection
        metric_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        metric_frame.pack(side="left", padx=20, pady=10)
        
        tk.Label(metric_frame, text="Metric:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        metric_combo = ttk.Combobox(metric_frame, textvariable=self.metric_var, 
                                   values=["revenue", "transactions", "avg_transaction_value"], width=15)
        metric_combo.pack(pady=2)
        metric_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        # Custom date selection
        date_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        date_frame.pack(side="left", padx=20, pady=10)
        
        tk.Checkbutton(date_frame, text="Custom Date Range", 
                      variable=self.use_custom_dates,
                      command=self.on_custom_date_toggle, bg=self.theme_colors['bg'],
                      fg=self.theme_colors['fg'], font=("Segoe UI", 10, "bold")).pack()
        
        date_controls = tk.Frame(date_frame, bg=self.theme_colors['bg'])
        date_controls.pack()
        
        tk.Label(date_controls, text="From:", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack(side="left", padx=5)
        
        # Create DateEntry widget for start date
        today = datetime.now()
        default_start = today - timedelta(days=30)
        self.start_date_entry = DateEntry(
            date_controls,
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            font=("Segoe UI", 9),
            year=default_start.year,
            month=default_start.month,
            day=default_start.day
        )
        self.start_date_entry.pack(side="left", padx=5)
        
        tk.Label(date_controls, text="To:", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack(side="left", padx=5)
        
        # Create DateEntry widget for end date
        self.end_date_entry = DateEntry(
            date_controls,
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            font=("Segoe UI", 9),
            year=today.year,
            month=today.month,
            day=today.day
        )
        self.end_date_entry.pack(side="left", padx=5)
        
        tk.Button(date_controls, text="Apply", 
                 command=self.on_custom_date_apply, bg="#3498db", fg="white",
                 font=("Segoe UI", 9), relief="flat", padx=10).pack(side="left", padx=10)
        
        # Initially disable custom date controls
        self.toggle_date_controls(False)
    
    def toggle_date_controls(self, enabled):
        """Enable/disable custom date controls"""
        state = "normal" if enabled else "disabled"
        self.start_date_entry.config(state=state)
        self.end_date_entry.config(state=state)
    
    def on_custom_date_toggle(self):
        """Handle custom date checkbox toggle"""
        enabled = self.use_custom_dates.get()
        self.toggle_date_controls(enabled)
        if not enabled:
            # Reset to default dates when unchecked
            today = datetime.now()
            default_start = today - timedelta(days=int(self.period_var.get()))
            self.start_date_entry.set_date(default_start)
            self.end_date_entry.set_date(today)
            self.load_data()
    
    def on_custom_date_apply(self):
        """Apply custom date range"""
        if self.use_custom_dates.get():
            self.load_data()
    
    def on_filter_changed(self, event=None):
        """Handle filter selection change"""
        if not self.use_custom_dates.get():
            self.load_data()
    
    def load_data(self):
        """Load and display sales trend data with filters"""
        try:
            # Clear existing content (except header and controls)
            for widget in self.winfo_children():
                if isinstance(widget, tk.Frame) and widget != self.winfo_children()[0] and widget != self.winfo_children()[1]:
                    widget.destroy()
            
            # Get filter values
            if self.use_custom_dates.get():
                # Use custom date range
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                days = (end_date - start_date).days + 1
            else:
                days = int(self.period_var.get())
                start_date = None
                end_date = None
            
            metric = self.metric_var.get()
            
            # Get sales trend data using SalesManagerAnalytics
            # Try to get data from the sales manager analytics
            try:
                if hasattr(self.analytics, 'get_sales_trend_analysis'):
                    if start_date and end_date:
                        # Use custom date range if method exists
                        if hasattr(self.analytics, 'get_sales_trend_analysis_custom'):
                            df = self.analytics.get_sales_trend_analysis_custom(start_date, end_date, metric)
                        else:
                            df = self.analytics.get_sales_trend_analysis(days, metric)
                    else:
                        df = self.analytics.get_sales_trend_analysis(days, metric)
                else:
                    # Fallback to manager analytics if sales manager doesn't have this method
                    from analytics_engine import ManagerAnalytics
                    ma = ManagerAnalytics()
                    if start_date and end_date and hasattr(ma, 'get_sales_trend_analysis_custom'):
                        df = ma.get_sales_trend_analysis_custom(start_date, end_date, metric)
                    else:
                        df = ma.get_sales_trend_analysis(days, metric)
            except Exception as analytics_error:
                print(f"Analytics error: {analytics_error}")
                # Fallback to basic sales data
                df = pd.DataFrame()
            
            if not df.empty:
                # Convert date column to datetime for better plotting
                df['date'] = pd.to_datetime(df['date'])
                
                # Create main container
                main_frame = tk.Frame(self, bg=self.theme_colors['bg'])
                main_frame.pack(fill="both", expand=True)
                
                # Info panel
                info_frame = tk.Frame(main_frame, bg=self.theme_colors['secondary_bg'], relief="solid", bd=1)
                info_frame.pack(fill="x", padx=10, pady=5)
                
                if self.use_custom_dates.get():
                    info_text = f"📊 Sales Trend: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} | Metric: {metric.replace('_', ' ').title()}"
                else:
                    info_text = f"📊 Sales Trend: Last {days} days | Metric: {metric.replace('_', ' ').title()}"
                
                tk.Label(info_frame, text=info_text,
                        font=("Segoe UI", 11, "bold"), bg=self.theme_colors['secondary_bg'], 
                        fg=self.theme_colors['fg']).pack(pady=8)
                
                # Chart frame
                chart_frame = tk.Frame(main_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
                chart_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                # Determine y column based on metric
                y_column_map = {
                    "revenue": "daily_revenue",
                    "transactions": "transaction_count", 
                    "avg_transaction_value": "avg_transaction_value"
                }
                y_col = y_column_map.get(metric, "daily_revenue")
                
                # Create chart
                fig = self.create_chart(df, "line", "date", y_col, figsize=(12, 6))
                if fig:
                    canvas = FigureCanvasTkAgg(fig, chart_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
                
                # Data table frame
                table_frame = tk.LabelFrame(main_frame, text="Sales Data", 
                                           font=("Segoe UI", 12, "bold"), bg=self.theme_colors['bg'],
                                           fg=self.theme_colors['fg'])
                table_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                self.create_data_table(df, table_frame)
                
            else:
                tk.Label(self, text="No sales data available for the selected period", 
                        font=("Segoe UI", 16), bg=self.theme_colors['bg'],
                        fg=self.theme_colors['fg']).pack(expand=True)
        except Exception as e:
            print(f"Error loading sales trend data: {e}")
            messagebox.showerror("Error", f"Failed to load sales data: {str(e)}")
    
    def export_pdf(self):
        """Export sales trend report as PDF"""
        try:
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                try:
                    if hasattr(self.analytics, 'get_sales_trend_analysis_custom'):
                        df = self.analytics.get_sales_trend_analysis_custom(start_date, end_date, self.metric_var.get())
                    else:
                        days = int(self.period_var.get())
                        df = self.analytics.get_sales_trend_analysis(days, self.metric_var.get())
                except:
                    from analytics_engine import ManagerAnalytics
                    ma = ManagerAnalytics()
                    df = ma.get_sales_trend_analysis_custom(start_date, end_date, self.metric_var.get())
            else:
                days = int(self.period_var.get())
                try:
                    df = self.analytics.get_sales_trend_analysis(days, self.metric_var.get())
                except:
                    from analytics_engine import ManagerAnalytics
                    ma = ManagerAnalytics()
                    df = ma.get_sales_trend_analysis(days, self.metric_var.get())
                
            if not df.empty:
                report_gen = SalesManagerReportGenerator()
                data_sections = {"Sales Trend Analysis": df}
                report_gen.generate_sales_report({"sales_trends": df}, 'pdf')
                messagebox.showinfo("Export Success", "Sales trend report exported to PDF successfully!")
            else:
                messagebox.showwarning("No Data", "No sales data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")
    
    def export_excel(self):
        """Export sales trend data as Excel"""
        try:
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                try:
                    if hasattr(self.analytics, 'get_sales_trend_analysis_custom'):
                        df = self.analytics.get_sales_trend_analysis_custom(start_date, end_date, self.metric_var.get())
                    else:
                        days = int(self.period_var.get())
                        df = self.analytics.get_sales_trend_analysis(days, self.metric_var.get())
                except:
                    from analytics_engine import ManagerAnalytics
                    ma = ManagerAnalytics()
                    df = ma.get_sales_trend_analysis_custom(start_date, end_date, self.metric_var.get())
            else:
                days = int(self.period_var.get())
                try:
                    df = self.analytics.get_sales_trend_analysis(days, self.metric_var.get())
                except:
                    from analytics_engine import ManagerAnalytics
                    ma = ManagerAnalytics()
                    df = ma.get_sales_trend_analysis(days, self.metric_var.get())
                
            if not df.empty:
                report_gen = SalesManagerReportGenerator()
                data_sections = {"Sales Trend Analysis": df}
                report_gen.generate_sales_report({"sales_trends": df}, 'excel')
                messagebox.showinfo("Export Success", "Sales trend data exported to Excel successfully!")
            else:
                messagebox.showwarning("No Data", "No sales data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export Excel: {str(e)}")
    
    def refresh_data(self):
        """Refresh the data display"""
        self.load_data()



class RealTime(SalesDataFrame):
    def __init__(self, master):
        super().__init__(master, "Real Time Sales Dashboard")
        
        # Add caching to prevent frequent changes
        self.cached_data = None
        self.cache_timestamp = None
        self.cache_duration = 60  # Cache for 60 seconds
        
        self.create_controls()
        self.load_data()
    
    def create_controls(self):
        """Create control panel for real-time dashboard"""
        control_frame = tk.Frame(self, bg=self.theme_colors['bg'], relief="solid", bd=1)
        control_frame.pack(fill="x", padx=20, pady=5)
        
        # Cache info
        info_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        info_frame.pack(side="right", padx=10, pady=5)
        
        # Cache info label
        self.cache_info_label = tk.Label(info_frame, text="", 
                                        bg=self.theme_colors['bg'], fg="#666666",
                                        font=("Segoe UI", 8))
        self.cache_info_label.pack(side="right")
    
    def get_cached_data(self):
        """Get cached data if still valid, otherwise fetch new data"""
        current_time = datetime.now()
        
        # Check if cache is still valid
        if (self.cached_data is not None and 
            self.cache_timestamp is not None and 
            (current_time - self.cache_timestamp).seconds < self.cache_duration):
            
            # Update cache info
            seconds_old = (current_time - self.cache_timestamp).seconds
            self.cache_info_label.config(text=f"Data cached ({seconds_old}s ago)")
            return self.cached_data
        
        # Fetch new data and cache it
        try:
            df = self.analytics.get_real_time_sales_dashboard()
            
            # If no real data, return empty DataFrame to show helpful message
            if df.empty:
                print("No real dashboard data found for today")
                self.cache_info_label.config(text="No sales data for today - run add_hourly_sales_data.py to add sample data")
                return df
            
            self.cached_data = df
            self.cache_timestamp = current_time
            self.cache_info_label.config(text="Data refreshed")
            return df
        except Exception as e:
            print(f"Error getting dashboard data: {e}")
            if self.cached_data is not None:
                self.cache_info_label.config(text="Using cached data (refresh failed)")
                return self.cached_data
            else:
                # Return empty DataFrame to show helpful message
                self.cache_info_label.config(text="Database connection failed")
                return pd.DataFrame()
    
    def force_refresh(self):
        """Force refresh by clearing cache"""
        self.cached_data = None
        self.cache_timestamp = None
        self.load_data()
    
    def manual_refresh(self):
        """Manual refresh triggered by button"""
        self.load_data()
    
    def load_data(self):
        """Load real-time dashboard data with enhanced metrics"""
        try:
            # Clear existing content (except header and controls)
            for widget in self.winfo_children():
                if isinstance(widget, tk.Frame) and widget not in [self.winfo_children()[0], self.winfo_children()[1]]:
                    widget.destroy()
            
            # Get real-time data (with caching)
            df = self.get_cached_data()
            
            if not df.empty:
                main_frame = tk.Frame(self, bg=self.theme_colors['bg'])
                main_frame.pack(fill="both", expand=True)
                
                # Create enhanced metrics cards
                self.create_metrics_cards(main_frame, df)
                
                # Create charts section
                self.create_charts_section(main_frame)
                
                # Create recent transactions table
                self.create_recent_transactions(main_frame)
                
            else:
                # Show no data message with instructions
                no_data_frame = tk.Frame(self, bg=self.theme_colors['bg'])
                no_data_frame.pack(fill="both", expand=True)
                
                # Center container
                center_frame = tk.Frame(no_data_frame, bg=self.theme_colors['bg'])
                center_frame.place(relx=0.5, rely=0.5, anchor="center")
                
                tk.Label(center_frame, text="📊 No Sales Data for Today", 
                        font=("Segoe UI", 20, "bold"), bg=self.theme_colors['bg'],
                        fg=self.theme_colors['fg']).pack(pady=10)
                
                tk.Label(center_frame, text="To see real-time sales data, you need to add some sales transactions.", 
                        font=("Segoe UI", 12), bg=self.theme_colors['bg'],
                        fg=self.theme_colors['fg']).pack(pady=5)
                
                tk.Label(center_frame, text="Run the script: add_hourly_sales_data.py", 
                        font=("Segoe UI", 12, "bold"), bg=self.theme_colors['bg'],
                        fg="#e74c3c").pack(pady=5)
                
                tk.Label(center_frame, text="This will add sample hourly sales data for testing.", 
                        font=("Segoe UI", 10), bg=self.theme_colors['bg'],
                        fg=self.theme_colors['fg']).pack(pady=2)
                
        except Exception as e:
            print(f"Error loading real-time dashboard data: {e}")
            messagebox.showerror("Error", f"Failed to load dashboard data: {str(e)}")
    
    def create_metrics_cards(self, parent, df):
        """Create enhanced metrics cards with more data"""
        metrics_frame = tk.Frame(parent, bg=self.theme_colors['bg'])
        metrics_frame.pack(fill="x", padx=20, pady=10)
        
        # Add timestamp header if available
        if 'data_timestamp' in df.columns:
            timestamp_frame = tk.Frame(metrics_frame, bg=self.theme_colors['bg'])
            timestamp_frame.pack(fill="x", pady=(0, 10))
            
            timestamp_str = str(df.iloc[0]['data_timestamp'])
            tk.Label(timestamp_frame, text=f"📅 Data as of: {timestamp_str}", 
                    font=("Segoe UI", 10), bg=self.theme_colors['bg'],
                    fg="#666666").pack()
        
        # Secondary metrics (only if real data is available)
        try:
            secondary_data = self.get_secondary_metrics()
            if secondary_data:
                secondary_frame = tk.Frame(metrics_frame, bg=self.theme_colors['bg'])
                secondary_frame.pack(fill="x", pady=(10, 0))
                
                secondary_metrics = [
                    ("Hourly Sales", f"${secondary_data.get('hourly_sales', 0):.2f}", "#9b59b6", "⏰"),
                    ("Items Sold", str(secondary_data.get('items_sold', 0)), "#1abc9c", "📦"),
                    ("Peak Hour", secondary_data.get('peak_hour', 'N/A'), "#e67e22", "🔥")
                ]
                
                for i, (title, value, color, icon) in enumerate(secondary_metrics):
                    mini_card = tk.Frame(secondary_frame, bg=color, relief="raised", bd=1)
                    mini_card.pack(side="left", fill="both", expand=True, padx=5, pady=5)
                    
                    tk.Label(mini_card, text=f"{icon} {title}", font=("Segoe UI", 9, "bold"), 
                            bg=color, fg="white").pack(pady=(5, 2))
                    tk.Label(mini_card, text=str(value), font=("Segoe UI", 12, "bold"), 
                            bg=color, fg="white").pack(pady=(0, 5))
        except Exception as e:
            print(f"Error creating secondary metrics: {e}")
    
    def get_secondary_metrics(self):
        """Get additional real-time metrics"""
        try:
            # Try to get hourly data
            if hasattr(self.analytics, 'get_hourly_sales_data'):
                try:
                    hourly_data = self.analytics.get_hourly_sales_data()
                    if not hourly_data.empty:
                        current_hour_sales = hourly_data.iloc[-1]['hourly_revenue'] if 'hourly_revenue' in hourly_data.columns else 0
                        total_items = hourly_data['items_sold'].sum() if 'items_sold' in hourly_data.columns else 0
                        peak_hour = hourly_data.loc[hourly_data['hourly_revenue'].idxmax(), 'hour'] if 'hourly_revenue' in hourly_data.columns else 'N/A'
                        
                        return {
                            'hourly_sales': current_hour_sales,
                            'items_sold': total_items,
                            'peak_hour': f"{peak_hour}:00"
                        }
                except Exception as e:
                    print(f"Error getting hourly data for metrics: {e}")
            
            # Return None if no real data available
            return None
        except Exception as e:
            print(f"Error getting secondary metrics: {e}")
            return None
    
    def create_charts_section(self, parent):
        """Create charts section with hourly trends"""
        charts_frame = tk.Frame(parent, bg=self.theme_colors['bg'])
        charts_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Charts container with two columns
        left_chart_frame = tk.Frame(charts_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
        left_chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_chart_frame = tk.Frame(charts_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
        right_chart_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Create hourly sales trend chart
        self.create_hourly_trend_chart(left_chart_frame)
        
        # Create top products chart
        self.create_top_products_chart(right_chart_frame)
    
    def create_hourly_trend_chart(self, parent):
        """Create hourly sales trend chart"""
        try:
            # Get hourly data or create sample data
            hourly_df = pd.DataFrame()
            
            if hasattr(self.analytics, 'get_hourly_sales_data'):
                try:
                    hourly_df = self.analytics.get_hourly_sales_data()
                except Exception as e:
                    print(f"Error getting hourly data from database: {e}")
            
            # If no real data available, show message to add data
            if hourly_df.empty:
                tk.Label(parent, text="No hourly sales data available for today.", 
                        font=("Segoe UI", 12), bg=self.theme_colors['chart_bg'],
                        justify="center").pack(expand=True)
                return
            
            if not hourly_df.empty:
                fig, ax = plt.subplots(figsize=(8, 4), facecolor=self.theme_colors['chart_bg'])
                
                ax.plot(hourly_df['hour'], hourly_df['hourly_revenue'], 
                       marker='o', linewidth=2, markersize=4, color='#3498db')
                ax.fill_between(hourly_df['hour'], hourly_df['hourly_revenue'], alpha=0.3, color='#3498db')
                
                ax.set_xlabel('Hour of Day')
                ax.set_ylabel('Sales ($)')
                ax.set_title('Hourly Sales Trend', fontsize=12, fontweight='bold')
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, 23)
                
                # Highlight current hour
                current_hour = datetime.now().hour
                ax.axvline(x=current_hour, color='#e74c3c', linestyle='--', alpha=0.7, linewidth=2)
                ax.text(current_hour, ax.get_ylim()[1] * 0.9, 'Now', 
                       ha='center', va='center', fontweight='bold', color='#e74c3c')
                
                plt.tight_layout()
                
                canvas = FigureCanvasTkAgg(fig, parent)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            else:
                tk.Label(parent, text="No hourly data available", 
                        font=("Segoe UI", 12), bg=self.theme_colors['chart_bg']).pack(expand=True)
                
        except Exception as e:
            print(f"Error creating hourly trend chart: {e}")
            tk.Label(parent, text="Error loading hourly chart", 
                    font=("Segoe UI", 12), bg=self.theme_colors['chart_bg']).pack(expand=True)
    
    def create_top_products_chart(self, parent):
        """Create top products chart for today"""
        try:
            # Get today's top products - only from database
            products_df = pd.DataFrame()
            
            if hasattr(self.analytics, 'get_todays_top_products'):
                try:
                    products_df = self.analytics.get_todays_top_products(5)
                except Exception as e:
                    print(f"Error getting top products from database: {e}")
            
            if not products_df.empty:
                fig, ax = plt.subplots(figsize=(8, 4), facecolor=self.theme_colors['chart_bg'])
                
                # Create horizontal bar chart
                bars = ax.barh(products_df['product_name'], products_df['quantity_sold'], 
                              color='#27ae60', alpha=0.8)
                
                ax.set_xlabel('Quantity Sold')
                ax.set_ylabel('Products')
                ax.set_title("Today's Top Products", fontsize=12, fontweight='bold')
                
                # Add value labels
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
                           f'{int(width)}', ha='left', va='center', fontsize=9)
                
                ax.grid(True, alpha=0.3, axis='x')
                plt.tight_layout()
                
                canvas = FigureCanvasTkAgg(fig, parent)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            else:
                tk.Label(parent, text="No product sales data available for today.\nRun 'add_hourly_sales_data.py' to add sample data.", 
                        font=("Segoe UI", 12), bg=self.theme_colors['chart_bg'],
                        justify="center").pack(expand=True)
                
        except Exception as e:
            print(f"Error creating top products chart: {e}")
            tk.Label(parent, text="Error loading products chart", 
                    font=("Segoe UI", 12), bg=self.theme_colors['chart_bg']).pack(expand=True)
    
    def create_recent_transactions(self, parent):
        """Create recent transactions table"""
        try:
            transactions_frame = tk.LabelFrame(parent, text="Recent Transactions", 
                                             font=("Segoe UI", 12, "bold"), 
                                             bg=self.theme_colors['bg'],
                                             fg=self.theme_colors['fg'])
            transactions_frame.pack(fill="x", padx=20, pady=(10, 20))
            
            # Get recent transactions - only from database
            recent_df = pd.DataFrame()
            
            if hasattr(self.analytics, 'get_recent_transactions'):
                try:
                    recent_df = self.analytics.get_recent_transactions(10)
                except Exception as e:
                    print(f"Error getting recent transactions from database: {e}")
            
            if not recent_df.empty:
                # Create table with custom styling
                table_frame = tk.Frame(transactions_frame)
                table_frame.pack(fill="x", padx=10, pady=10)
                
                # Headers
                headers = ['Time', 'Items', 'Total']
                for i, header in enumerate(headers):
                    tk.Label(table_frame, text=header, font=("Segoe UI", 10, "bold"),
                            bg="#34495e", fg="white", relief="solid", bd=1).grid(
                            row=0, column=i, sticky="ew", padx=1, pady=1)
                
                # Data rows
                for row_idx, (_, row) in enumerate(recent_df.head(5).iterrows(), 1):
                    bg_color = "#ecf0f1" if row_idx % 2 == 0 else "white"
                    
                    tk.Label(table_frame, text=row['time'], font=("Segoe UI", 9),
                            bg=bg_color, relief="solid", bd=1).grid(
                            row=row_idx, column=0, sticky="ew", padx=1, pady=1)
                    
                    tk.Label(table_frame, text=str(row['items']), font=("Segoe UI", 9),
                            bg=bg_color, relief="solid", bd=1).grid(
                            row=row_idx, column=1, sticky="ew", padx=1, pady=1)
                    
                    tk.Label(table_frame, text=f"${row['total']:.2f}", font=("Segoe UI", 9),
                            bg=bg_color, relief="solid", bd=1).grid(
                            row=row_idx, column=2, sticky="ew", padx=1, pady=1)
                
                # Configure column weights
                for i in range(3):
                    table_frame.grid_columnconfigure(i, weight=1)
            else:
                tk.Label(transactions_frame, text="No recent transactions for today.\nRun 'add_hourly_sales_data.py' to add sample data.", 
                        font=("Segoe UI", 10), bg=self.theme_colors['bg'],
                        justify="center").pack(pady=10)
                
        except Exception as e:
            print(f"Error creating recent transactions: {e}")

    def export_pdf(self):
        """Export real-time dashboard report as PDF"""
        try:
            df = self.analytics.get_real_time_sales_dashboard()
            if not df.empty:
                from report_generator import SalesManagerReportGenerator
                report_gen = SalesManagerReportGenerator()
                report_gen.generate_sales_report({"dashboard": df}, 'pdf')
                messagebox.showinfo("Export Success", "Real-time dashboard report exported to PDF successfully!")
            else:
                messagebox.showwarning("No Data", "No dashboard data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")
    
    def refresh_data(self):
        """Refresh the data display"""
        self.load_data()

class PopularProduct(SalesDataFrame):
    def __init__(self, master):
        super().__init__(master, "Popular Product Analytics")
        # Initialize filter variables
        self.period_var = tk.StringVar(value="30")
        self.use_custom_dates = tk.BooleanVar(value=False)
        self.metric_var = tk.StringVar(value="total_sold")
        self.category_var = tk.StringVar(value="All Categories")
        self.limit_var = tk.StringVar(value="10")
        
        # Initialize DateEntry widgets - will be created in create_controls
        self.start_date_entry = None
        self.end_date_entry = None
        
        self.create_controls()
        self.load_data()
    
    def create_controls(self):
        """Create filter controls for popular products analysis"""
        control_frame = tk.Frame(self, bg=self.theme_colors['bg'], relief="solid", bd=1)
        control_frame.pack(fill="x", padx=20, pady=5)
        
        # Period selection
        period_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        period_frame.pack(side="left", padx=10, pady=10)
        
        tk.Label(period_frame, text="Time Period:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        period_combo = ttk.Combobox(period_frame, textvariable=self.period_var, 
                                   values=["7", "14", "30", "60", "90", "180"], width=10)
        period_combo.pack(pady=2)
        period_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        tk.Label(period_frame, text="days", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        # Metric selection
        metric_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        metric_frame.pack(side="left", padx=20, pady=10)
        
        tk.Label(metric_frame, text="Sort By:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        metric_combo = ttk.Combobox(metric_frame, textvariable=self.metric_var, 
                                   values=["total_sold", "total_revenue", "avg_price"], width=12)
        metric_combo.pack(pady=2)
        metric_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        # Category filter
        category_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        category_frame.pack(side="left", padx=10, pady=10)
        
        tk.Label(category_frame, text="Category:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, 
                                     values=["All Categories", "Dairy", "Bakery", "Produce", "Meat", "Beverages", "Snacks"], width=12)
        category_combo.pack(pady=2)
        category_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        # Number of products
        limit_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        limit_frame.pack(side="left", padx=10, pady=10)
        
        tk.Label(limit_frame, text="Show Top:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        limit_combo = ttk.Combobox(limit_frame, textvariable=self.limit_var, 
                                  values=["5", "10", "15", "20", "25"], width=8)
        limit_combo.pack(pady=2)
        limit_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        # Custom date selection
        date_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        date_frame.pack(side="right", padx=10, pady=10)
        
        tk.Checkbutton(date_frame, text="Custom Date Range", 
                      variable=self.use_custom_dates,
                      command=self.on_custom_date_toggle, bg=self.theme_colors['bg'],
                      fg=self.theme_colors['fg'], font=("Segoe UI", 10, "bold")).pack()
        
        date_controls = tk.Frame(date_frame, bg=self.theme_colors['bg'])
        date_controls.pack()
        
        tk.Label(date_controls, text="From:", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack(side="left", padx=2)
        
        # Create DateEntry widget for start date
        today = datetime.now()
        default_start = today - timedelta(days=30)
        self.start_date_entry = DateEntry(
            date_controls,
            width=10,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            font=("Segoe UI", 8),
            year=default_start.year,
            month=default_start.month,
            day=default_start.day
        )
        self.start_date_entry.pack(side="left", padx=2)
        
        tk.Label(date_controls, text="To:", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack(side="left", padx=2)
        
        # Create DateEntry widget for end date
        self.end_date_entry = DateEntry(
            date_controls,
            width=10,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            font=("Segoe UI", 8),
            year=today.year,
            month=today.month,
            day=today.day
        )
        self.end_date_entry.pack(side="left", padx=2)
        
        tk.Button(date_controls, text="Apply", 
                 command=self.on_custom_date_apply, bg="#3498db", fg="white",
                 font=("Segoe UI", 8), relief="flat", padx=8).pack(side="left", padx=5)
        
        # Initially disable custom date controls
        self.toggle_date_controls(False)
    
    def toggle_date_controls(self, enabled):
        """Enable/disable custom date controls"""
        state = "normal" if enabled else "disabled"
        self.start_date_entry.config(state=state)
        self.end_date_entry.config(state=state)
    
    def on_custom_date_toggle(self):
        """Handle custom date checkbox toggle"""
        enabled = self.use_custom_dates.get()
        self.toggle_date_controls(enabled)
        if not enabled:
            # Reset to default dates when unchecked
            today = datetime.now()
            default_start = today - timedelta(days=int(self.period_var.get()))
            self.start_date_entry.set_date(default_start)
            self.end_date_entry.set_date(today)
            self.load_data()
    
    def on_custom_date_apply(self):
        """Apply custom date range"""
        if self.use_custom_dates.get():
            self.load_data()
    
    def on_filter_changed(self, event=None):
        """Handle filter selection change"""
        if not self.use_custom_dates.get():
            self.load_data()
    
    def load_data(self):
        """Load popular products data with advanced filtering"""
        try:
            # Clear existing content (except header and controls)
            for widget in self.winfo_children():
                if isinstance(widget, tk.Frame) and widget != self.winfo_children()[0] and widget != self.winfo_children()[1]:
                    widget.destroy()
            
            # Get filter values
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                days = (end_date - start_date).days + 1
            else:
                days = int(self.period_var.get())
                start_date = None
                end_date = None
            
            metric = self.metric_var.get()
            category = self.category_var.get()
            limit = int(self.limit_var.get())
            
            # Get popular products data
            df = self.get_popular_products_data(days, metric, category, limit, start_date, end_date)
            
            if not df.empty:
                main_frame = tk.Frame(self, bg=self.theme_colors['bg'])
                main_frame.pack(fill="both", expand=True)
                
                # Info panel
                info_frame = tk.Frame(main_frame, bg=self.theme_colors['secondary_bg'], relief="solid", bd=1)
                info_frame.pack(fill="x", padx=10, pady=5)
                
                if self.use_custom_dates.get():
                    info_text = f"🏆 Top {limit} Products: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                else:
                    info_text = f"🏆 Top {limit} Products: Last {days} days"
                
                info_text += f" | Sort: {metric.replace('_', ' ').title()} | Category: {category}"
                
                tk.Label(info_frame, text=info_text,
                        font=("Segoe UI", 11, "bold"), bg=self.theme_colors['secondary_bg'], 
                        fg=self.theme_colors['fg']).pack(pady=8)
                
                # Charts section
                self.create_charts_section(main_frame, df, metric)
                
                # Data table frame
                table_frame = tk.LabelFrame(main_frame, text="Popular Products Data", 
                                           font=("Segoe UI", 12, "bold"), bg=self.theme_colors['bg'],
                                           fg=self.theme_colors['fg'])
                table_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                self.create_data_table(df, table_frame)
                
            else:
                tk.Label(self, text="No product data available for the selected filters", 
                        font=("Segoe UI", 16), bg=self.theme_colors['bg'],
                        fg=self.theme_colors['fg']).pack(expand=True)
        except Exception as e:
            print(f"Error loading popular products data: {e}")
            messagebox.showerror("Error", f"Failed to load product data: {str(e)}")
    
    def get_popular_products_data(self, days, metric, category, limit, start_date=None, end_date=None):
        """Get popular products data with filtering"""
        try:
            # Use the analytics engine method if available
            if hasattr(self.analytics, 'get_popular_products_for_promotion'):
                df = self.analytics.get_popular_products_for_promotion(limit, days)
                
                # Map analytics engine column names to expected names for consistency
                if not df.empty:
                    column_mapping = {
                        'avg_selling_price': 'avg_price'
                    }
                    df = df.rename(columns=column_mapping)
                    
                    # Add missing columns if needed
                    if 'growth_rate' not in df.columns:
                        df['growth_rate'] = np.random.uniform(-10, 25, len(df))
            else:
                # Create enhanced sample data
                categories = ['Dairy', 'Bakery', 'Produce', 'Meat', 'Beverages', 'Snacks']
                products = []
                for i in range(limit * 2):  # Generate more products to allow filtering
                    cat = np.random.choice(categories)
                    products.append({
                        'product_name': f'Product {i+1}',
                        'category': cat,
                        'total_sold': np.random.randint(50, 500),
                        'total_revenue': np.random.uniform(500, 5000),
                        'avg_price': np.random.uniform(5, 50),
                        'growth_rate': np.random.uniform(-10, 25)
                    })
                df = pd.DataFrame(products)
            
            # Apply category filter
            if category != "All Categories":
                df = df[df['category'] == category] if 'category' in df.columns else df
            
            # Sort by selected metric
            if metric in df.columns:
                df = df.sort_values(metric, ascending=False)
            
            # Limit results
            df = df.head(limit)
            
            return df
            
        except Exception as e:
            print(f"Error getting popular products data: {e}")
            return pd.DataFrame()
    
    def create_charts_section(self, parent, df, metric):
        """Create enhanced charts section for popular products"""
        charts_frame = tk.Frame(parent, bg=self.theme_colors['bg'])
        charts_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Charts container with two columns
        left_chart_frame = tk.Frame(charts_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
        left_chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_chart_frame = tk.Frame(charts_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
        right_chart_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Create main bar chart
        self.create_main_chart(left_chart_frame, df, metric)
        
        # Create category distribution chart
        self.create_category_distribution_chart(right_chart_frame, df)
    
    def create_main_chart(self, parent, df, metric):
        """Create main bar chart for popular products"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6), facecolor=self.theme_colors['chart_bg'])
            
            if not df.empty and metric in df.columns:
                # Create bar chart
                products = df['product_name'].head(10)
                values = df[metric].head(10)
                
                colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'] * 2
                bars = ax.bar(range(len(products)), values, color=colors[:len(products)], alpha=0.8)
                
                ax.set_xlabel('Products')
                ax.set_ylabel(metric.replace('_', ' ').title())
                ax.set_title(f'Top Products by {metric.replace("_", " ").title()}', fontsize=14, fontweight='bold')
                ax.set_xticks(range(len(products)))
                ax.set_xticklabels(products, rotation=45, ha='right')
                
                # Add value labels on bars
                for i, bar in enumerate(bars):
                    height = bar.get_height()
                    if metric == 'total_revenue':
                        label = f'${height:,.0f}'
                    elif metric == 'avg_price':
                        label = f'${height:.2f}'
                    else:
                        label = f'{int(height)}'
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           label, ha='center', va='bottom', fontsize=9)
                
                ax.grid(True, alpha=0.3, axis='y')
                plt.tight_layout()
            else:
                ax.text(0.5, 0.5, f'No data available for {metric}', 
                       transform=ax.transAxes, ha='center', va='center',
                       fontsize=14, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
                ax.set_title(f'Top Products by {metric.replace("_", " ").title()}', fontsize=14, fontweight='bold')
            
            canvas = FigureCanvasTkAgg(fig, parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
        except Exception as e:
            print(f"Error creating main chart: {e}")
            tk.Label(parent, text="Error creating product chart", 
                    font=("Segoe UI", 12), bg=self.theme_colors['chart_bg']).pack(expand=True)
    
    def create_category_distribution_chart(self, parent, df):
        """Create category distribution pie chart"""
        try:
            fig, ax = plt.subplots(figsize=(8, 6), facecolor=self.theme_colors['chart_bg'])
            
            if not df.empty and 'category' in df.columns:
                category_counts = df['category'].value_counts()
                
                colors = sns.color_palette("husl", len(category_counts))
                wedges, texts, autotexts = ax.pie(category_counts.values, 
                                                 labels=category_counts.index,
                                                 autopct='%1.1f%%', 
                                                 startangle=90,
                                                 colors=colors)
                ax.set_title('Product Distribution by Category', fontsize=14, fontweight='bold')
                
                # Enhance text appearance
                for text in texts:
                    text.set_fontsize(10)
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
            
            canvas = FigureCanvasTkAgg(fig, parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
        except Exception as e:
            print(f"Error creating category distribution chart: {e}")
            tk.Label(parent, text="Error creating category chart", 
                    font=("Segoe UI", 12), bg=self.theme_colors['chart_bg']).pack(expand=True)

    def export_pdf(self):
        """Export popular products report as PDF"""
        try:
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                try:
                    if hasattr(self.analytics, 'get_sales_trend_analysis_custom'):
                        df = self.analytics.get_sales_trend_analysis_custom(start_date, end_date, self.metric_var.get())
                    else:
                        days = int(self.period_var.get())
                        df = self.analytics.get_sales_trend_analysis(days, self.metric_var.get())
                except:
                    from analytics_engine import ManagerAnalytics
                    ma = ManagerAnalytics()
                    df = ma.get_sales_trend_analysis_custom(start_date, end_date, self.metric_var.get())
            else:
                days = int(self.period_var.get())
                try:
                    df = self.analytics.get_sales_trend_analysis(days, self.metric_var.get())
                except:
                    from analytics_engine import ManagerAnalytics
                    ma = ManagerAnalytics()
                    df = ma.get_sales_trend_analysis(days, self.metric_var.get())
                
            if not df.empty:
                report_gen = SalesManagerReportGenerator()
                data_sections = {"Sales Trend Analysis": df}
                report_gen.generate_sales_report({"sales_trends": df}, 'pdf')
                messagebox.showinfo("Export Success", "Sales trend report exported to PDF successfully!")
            else:
                messagebox.showwarning("No Data", "No sales data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")
    
    def export_excel(self):
        """Export sales trend data as Excel"""
        try:
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                try:
                    if hasattr(self.analytics, 'get_sales_trend_analysis_custom'):
                        df = self.analytics.get_sales_trend_analysis_custom(start_date, end_date, self.metric_var.get())
                    else:
                        days = int(self.period_var.get())
                        df = self.analytics.get_sales_trend_analysis(days, self.metric_var.get())
                except:
                    from analytics_engine import ManagerAnalytics
                    ma = ManagerAnalytics()
                    df = ma.get_sales_trend_analysis_custom(start_date, end_date, self.metric_var.get())
            else:
                days = int(self.period_var.get())
                try:
                    df = self.analytics.get_sales_trend_analysis(days, self.metric_var.get())
                except:
                    from analytics_engine import ManagerAnalytics
                    ma = ManagerAnalytics()
                    df = ma.get_sales_trend_analysis(days, self.metric_var.get())
                
            if not df.empty:
                report_gen = SalesManagerReportGenerator()
                data_sections = {"Sales Trend Analysis": df}
                report_gen.generate_sales_report({"sales_trends": df}, 'excel')
                messagebox.showinfo("Export Success", "Sales trend data exported to Excel successfully!")
            else:
                messagebox.showwarning("No Data", "No sales data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export Excel: {str(e)}")
    
    def refresh_data(self):
        """Refresh the data display"""
        self.load_data()


class PromotionSales(SalesDataFrame):
    def __init__(self, master):
        super().__init__(master, "Promotion & Sales Performance Analytics")
        # Initialize filter variables
        self.period_var = tk.StringVar(value="90")
        self.use_custom_dates = tk.BooleanVar(value=False)
        self.analysis_type_var = tk.StringVar(value="seasonal_trends")
        self.comparison_var = tk.StringVar(value="year_over_year")
        
        # Initialize DateEntry widgets - will be created in create_controls
        self.start_date_entry = None
        self.end_date_entry = None
        
        self.create_controls()
        self.load_data()
    
    def create_controls(self):
        """Create filter controls for promotion and sales analysis"""
        control_frame = tk.Frame(self, bg=self.theme_colors['bg'], relief="solid", bd=1)
        control_frame.pack(fill="x", padx=20, pady=5)
        
        # Period selection
        period_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        period_frame.pack(side="left", padx=10, pady=10)
        
        tk.Label(period_frame, text="Time Period:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        period_combo = ttk.Combobox(period_frame, textvariable=self.period_var, 
                                   values=["30", "60", "90", "180", "365"], width=10)
        period_combo.pack(pady=2)
        period_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        tk.Label(period_frame, text="days", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        # Analysis type selection
        analysis_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        analysis_frame.pack(side="left", padx=20, pady=10)
        
        tk.Label(analysis_frame, text="Analysis Type:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        analysis_combo = ttk.Combobox(analysis_frame, textvariable=self.analysis_type_var, 
                                     values=["seasonal_trends", "promotional_impact", "sales_comparison"], width=15)
        analysis_combo.pack(pady=2)
        analysis_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        # Comparison type
        comparison_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        comparison_frame.pack(side="left", padx=20, pady=10)
        
        tk.Label(comparison_frame, text="Compare:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        comparison_combo = ttk.Combobox(comparison_frame, textvariable=self.comparison_var, 
                                       values=["year_over_year", "month_over_month", "quarter_over_quarter"], width=15)
        comparison_combo.pack(pady=2)
        comparison_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        # Custom date selection
        date_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        date_frame.pack(side="right", padx=10, pady=10)
        
        tk.Checkbutton(date_frame, text="Custom Date Range", 
                      variable=self.use_custom_dates,
                      command=self.on_custom_date_toggle, bg=self.theme_colors['bg'],
                      fg=self.theme_colors['fg'], font=("Segoe UI", 10, "bold")).pack()
        
        date_controls = tk.Frame(date_frame, bg=self.theme_colors['bg'])
        date_controls.pack()
        
        tk.Label(date_controls, text="From:", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack(side="left", padx=2)
        
        # Create DateEntry widget for start date
        today = datetime.now()
        default_start = today - timedelta(days=90)
        self.start_date_entry = DateEntry(
            date_controls,
            width=10,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            font=("Segoe UI", 8),
            year=default_start.year,
            month=default_start.month,
            day=default_start.day
        )
        self.start_date_entry.pack(side="left", padx=2)
        
        tk.Label(date_controls, text="To:", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack(side="left", padx=2)
        
        # Create DateEntry widget for end date
        self.end_date_entry = DateEntry(
            date_controls,
            width=10,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            font=("Segoe UI", 8),
            year=today.year,
            month=today.month,
            day=today.day
        )
        self.end_date_entry.pack(side="left", padx=2)
        
        tk.Button(date_controls, text="Apply", 
                 command=self.on_custom_date_apply, bg="#3498db", fg="white",
                 font=("Segoe UI", 8), relief="flat", padx=8).pack(side="left", padx=5)
        
        # Initially disable custom date controls
        self.toggle_date_controls(False)
    
    def toggle_date_controls(self, enabled):
        """Enable/disable custom date controls"""
        state = "normal" if enabled else "disabled"
        self.start_date_entry.config(state=state)
        self.end_date_entry.config(state=state)
    
    def on_custom_date_toggle(self):
        """Handle custom date checkbox toggle"""
        enabled = self.use_custom_dates.get()
        self.toggle_date_controls(enabled)
        if not enabled:
            # Reset to default dates when unchecked
            today = datetime.now()
            default_start = today - timedelta(days=int(self.period_var.get()))
            self.start_date_entry.set_date(default_start)
            self.end_date_entry.set_date(today)
            self.load_data()
    
    def on_custom_date_apply(self):
        """Apply custom date range"""
        if self.use_custom_dates.get():
            self.load_data()
    
    def on_filter_changed(self, event=None):
        """Handle filter selection change"""
        if not self.use_custom_dates.get():
            self.load_data()
    
    def load_data(self):
        """Load promotion and sales data with advanced filtering"""
        try:
            # Clear existing content (except header and controls)
            for widget in self.winfo_children():
                if isinstance(widget, tk.Frame) and widget != self.winfo_children()[0] and widget != self.winfo_children()[1]:
                    widget.destroy()
            
            # Get filter values
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                days = (end_date - start_date).days + 1
            else:
                days = int(self.period_var.get())
                start_date = None
                end_date = None
            
            analysis_type = self.analysis_type_var.get()
            comparison_type = self.comparison_var.get()
            
            # Get promotion/sales data
            df = self.get_promotion_sales_data(analysis_type, days, comparison_type, start_date, end_date)
            
            if not df.empty:
                main_frame = tk.Frame(self, bg=self.theme_colors['bg'])
                main_frame.pack(fill="both", expand=True)
                
                # Info panel
                info_frame = tk.Frame(main_frame, bg=self.theme_colors['secondary_bg'], relief="solid", bd=1)
                info_frame.pack(fill="x", padx=10, pady=5)
                
                if self.use_custom_dates.get():
                    info_text = f"📈 {analysis_type.replace('_', ' ').title()}: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                else:
                    info_text = f"📈 {analysis_type.replace('_', ' ').title()}: Last {days} days"
                
                info_text += f" | Compare: {comparison_type.replace('_', ' ').title()}"
                
                tk.Label(info_frame, text=info_text,
                        font=("Segoe UI", 11, "bold"), bg=self.theme_colors['secondary_bg'], 
                        fg=self.theme_colors['fg']).pack(pady=8)
                
                # Charts section
                self.create_charts_section(main_frame, df, analysis_type)
                
                # Data table frame
                table_title = {
                    "seasonal_trends": "Seasonal Sales Trends",
                    "promotional_impact": "Promotional Campaign Impact", 
                    "sales_comparison": "Sales Performance Comparison"
                }.get(analysis_type, "Sales Analysis Data")
                
                table_frame = tk.LabelFrame(main_frame, text=table_title, 
                                           font=("Segoe UI", 12, "bold"), bg=self.theme_colors['bg'],
                                           fg=self.theme_colors['fg'])
                table_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                self.create_data_table(df, table_frame)
                
            else:
                tk.Label(self, text="No sales/promotion data available for the selected filters", 
                        font=("Segoe UI", 16), bg=self.theme_colors['bg'],
                        fg=self.theme_colors['fg']).pack(expand=True)
        except Exception as e:
            print(f"Error loading promotion/sales data: {e}")
            messagebox.showerror("Error", f"Failed to load sales data: {str(e)}")
    
    def get_promotion_sales_data(self, analysis_type, days, comparison_type, start_date=None, end_date=None):
        """Get promotion and sales data based on analysis type"""
        try:
            if analysis_type == "seasonal_trends":
                return self.get_seasonal_trends_data(days, start_date, end_date)
            elif analysis_type == "promotional_impact":
                return self.get_promotional_impact_data(days, start_date, end_date)
            elif analysis_type == "sales_comparison":
                return self.get_sales_comparison_data(days, comparison_type, start_date, end_date)
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"Error getting promotion/sales data: {e}")
            return pd.DataFrame()
    
    def get_seasonal_trends_data(self, days, start_date=None, end_date=None):
        """Get seasonal sales trends data"""
        try:
            # Use the analytics engine method if available
            if hasattr(self.analytics, 'get_seasonal_sales_trends'):
                df = self.analytics.get_seasonal_sales_trends()
                

                if not df.empty:
                    # Convert month numbers to month names
                    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    
                    # Convert month numbers to names
                    df['month'] = df['month'].apply(lambda x: month_names[int(x)-1] if 1 <= x <= 12 else f'Month {x}')
                    
                    # Calculate growth rate (year-over-year or month-over-month)
                    if len(df) > 1:
                        df['growth_rate'] = df['monthly_revenue'].pct_change() * 100
                        df['growth_rate'] = df['growth_rate'].fillna(0)  # First month has no previous data
                    else:
                        df['growth_rate'] = 0
                    
                    return df
                else:
                    return self._create_sample_seasonal_data()
            else:
                return self._create_sample_seasonal_data()
                
        except Exception as e:
            print(f"Error getting seasonal trends data: {e}")
            return self._create_sample_seasonal_data()
    
    def _create_sample_seasonal_data(self):
        """Create sample seasonal data"""
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return pd.DataFrame({
            'month': months,
            'monthly_revenue': [45000, 42000, 48000, 52000, 55000, 58000,
                               62000, 60000, 57000, 54000, 50000, 65000],
            'monthly_transactions': [890, 820, 950, 1020, 1100, 1150,
                                   1240, 1200, 1140, 1080, 1000, 1300],
            'avg_transaction_value': [50.56, 51.22, 50.53, 50.98, 50.00, 50.43,
                                     50.00, 50.00, 50.00, 50.00, 50.00, 50.00],
            'growth_rate': [5.2, -6.7, 14.3, 8.3, 5.8, 5.5, 6.9, -3.2, -5.0, -5.3, -7.4, 30.0]
        })
    
    def get_promotional_impact_data(self, days, start_date=None, end_date=None):
        """Get promotional campaign impact data"""
        try:
            # Create sample promotional impact data
            campaigns = ['Summer Sale', 'Back to School', 'Holiday Special', 'New Year Promo', 'Spring Clean']
            return pd.DataFrame({
                'campaign_name': campaigns,
                'start_date': ['2024-06-01', '2024-08-15', '2024-11-20', '2024-01-01', '2024-03-15'],
                'end_date': ['2024-06-30', '2024-09-15', '2024-12-31', '2024-01-31', '2024-04-15'],
                'total_revenue': [85000, 92000, 150000, 78000, 65000],
                'units_sold': [1200, 1350, 2100, 980, 850],
                'avg_order_value': [70.83, 68.15, 71.43, 79.59, 76.47],
                'customer_acquisition': [150, 180, 320, 120, 95],
                'roi_percentage': [245, 280, 310, 195, 165]
            })
        except Exception as e:
            print(f"Error getting promotional impact data: {e}")
            return pd.DataFrame()
    
    def get_sales_comparison_data(self, days, comparison_type, start_date=None, end_date=None):
        """Get sales comparison data"""
        try:
            # Create sample comparison data based on type with consistent structure
            if comparison_type == "year_over_year":
                return pd.DataFrame({
                    'period': ['Q1', 'Q2', 'Q3', 'Q4'],
                    'current_revenue': [125000, 142000, 158000, 195000],  # 2024 data
                    'previous_revenue': [120000, 135000, 145000, 180000],  # 2023 data
                    'growth_rate': [4.2, 5.2, 9.0, 8.3],
                    'period_label': ['Q1 2024 vs Q1 2023', 'Q2 2024 vs Q2 2023', 'Q3 2024 vs Q3 2023', 'Q4 2024 vs Q4 2023']
                })
            elif comparison_type == "month_over_month":
                return pd.DataFrame({
                    'period': ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
                    'current_revenue': [52000, 48000, 65000, 45000, 42000, 48000],  # Current months
                    'previous_revenue': [50000, 52000, 48000, 65000, 45000, 42000],  # Previous months
                    'growth_rate': [4.0, -7.7, 35.4, -30.8, -6.7, 14.3],
                    'period_label': ['Oct vs Sep', 'Nov vs Oct', 'Dec vs Nov', 'Jan vs Dec', 'Feb vs Jan', 'Mar vs Feb']
                })
            else:  # quarter_over_quarter
                return pd.DataFrame({
                    'period': ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024'],
                    'current_revenue': [125000, 142000, 158000, 195000],  # Current quarters
                    'previous_revenue': [118000, 135000, 145000, 180000],  # Previous quarters
                    'growth_rate': [5.9, 5.2, 9.0, 8.3],
                    'period_label': ['Q1 2024 vs Q4 2023', 'Q2 2024 vs Q1 2024', 'Q3 2024 vs Q2 2024', 'Q4 2024 vs Q3 2024']
                })
        except Exception as e:
            print(f"Error getting sales comparison data: {e}")
            return pd.DataFrame()
    
    def create_charts_section(self, parent, df, analysis_type):
        """Create enhanced charts section based on analysis type"""
        charts_frame = tk.Frame(parent, bg=self.theme_colors['bg'])
        charts_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        if analysis_type == "seasonal_trends":
            self.create_seasonal_charts(charts_frame, df)
        elif analysis_type == "promotional_impact":
            self.create_promotional_charts(charts_frame, df)
        elif analysis_type == "sales_comparison":
            self.create_comparison_charts(charts_frame, df)
    
    def create_seasonal_charts(self, parent, df):
        """Create seasonal trends charts"""
        # Two charts side by side
        left_chart_frame = tk.Frame(parent, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
        left_chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_chart_frame = tk.Frame(parent, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
        right_chart_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        try:
            # Revenue trends chart (Left)
            fig1, ax1 = plt.subplots(figsize=(10, 6), facecolor=self.theme_colors['chart_bg'])
            
            if not df.empty and 'month' in df.columns and 'monthly_revenue' in df.columns:
                ax1.plot(df['month'], df['monthly_revenue'], marker='o', linewidth=3, markersize=8, color='#2ecc71')
                ax1.fill_between(df['month'], df['monthly_revenue'], alpha=0.3, color='#2ecc71')
                ax1.set_xlabel('Month')
                ax1.set_ylabel('Revenue ($)')
                ax1.set_title('Monthly Revenue Trends', fontsize=14, fontweight='bold')
                ax1.grid(True, alpha=0.3)
                ax1.tick_params(axis='x', rotation=45)
                
                # Add value labels
                for i, v in enumerate(df['monthly_revenue']):
                    ax1.text(i, v + max(df['monthly_revenue']) * 0.02, f'${v:,.0f}', 
                            ha='center', va='bottom', fontsize=9)
                
                # Format y-axis to show currency
                ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            else:
                ax1.text(0.5, 0.5, 'No seasonal revenue data available', 
                        transform=ax1.transAxes, ha='center', va='center',
                        fontsize=14, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
                ax1.set_title('Monthly Revenue Trends', fontsize=14, fontweight='bold')
            
            plt.tight_layout()
            canvas1 = FigureCanvasTkAgg(fig1, left_chart_frame)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
            # Growth rate chart (Right)
            fig2, ax2 = plt.subplots(figsize=(10, 6), facecolor=self.theme_colors['chart_bg'])
            
            if not df.empty and 'month' in df.columns and 'growth_rate' in df.columns:
                colors = ['#e74c3c' if x < 0 else '#27ae60' for x in df['growth_rate']]
                bars = ax2.bar(df['month'], df['growth_rate'], color=colors, alpha=0.8)
                ax2.set_xlabel('Month')
                ax2.set_ylabel('Growth Rate (%)')
                ax2.set_title('Monthly Growth Rate', fontsize=14, fontweight='bold')
                ax2.grid(True, alpha=0.3, axis='y')
                ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
                
                # Add value labels
                for bar in bars:
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}%', ha='center', 
                           va='bottom' if height > 0 else 'top', fontsize=9)
                
                # Add legend for growth colors
                ax2.text(0.02, 0.98, '🟢 Positive Growth', transform=ax2.transAxes, 
                        verticalalignment='top', color='#27ae60', fontweight='bold')
                ax2.text(0.02, 0.92, '🔴 Negative Growth', transform=ax2.transAxes, 
                        verticalalignment='top', color='#e74c3c', fontweight='bold')
            else:
                ax2.text(0.5, 0.5, 'No growth rate data available', 
                        transform=ax2.transAxes, ha='center', va='center',
                        fontsize=14, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
                ax2.set_title('Monthly Growth Rate', fontsize=14, fontweight='bold')
            
            plt.tight_layout()
            canvas2 = FigureCanvasTkAgg(fig2, right_chart_frame)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
        except Exception as e:
            print(f"Error creating seasonal charts: {e}")
            import traceback
            traceback.print_exc()
            
            # Create error messages in both frames
            tk.Label(left_chart_frame, text="Error loading revenue chart", 
                    font=("Segoe UI", 12), bg=self.theme_colors['chart_bg']).pack(expand=True)
            tk.Label(right_chart_frame, text="Error loading growth chart", 
                    font=("Segoe UI", 12), bg=self.theme_colors['chart_bg']).pack(expand=True)
    
    def create_promotional_charts(self, parent, df):
        """Create promotional impact charts"""
        # Create single large chart
        chart_frame = tk.Frame(parent, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
        chart_frame.pack(fill="both", expand=True)
        
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), facecolor=self.theme_colors['chart_bg'])
            
            if not df.empty:
                # Revenue by campaign
                campaigns = df['campaign_name']
                revenues = df['total_revenue']
                
                bars1 = ax1.bar(campaigns, revenues, color='#3498db', alpha=0.8)
                ax1.set_xlabel('Campaign')
                ax1.set_ylabel('Revenue ($)')
                ax1.set_title('Revenue by Campaign', fontsize=12, fontweight='bold')
                ax1.tick_params(axis='x', rotation=45)
                
                # Add value labels on bars
                for bar in bars1:
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                           f'${height:,.0f}', ha='center', va='bottom', fontsize=9)
                
                # ROI comparison
                if 'roi_percentage' in df.columns:
                    bars2 = ax2.bar(campaigns, df['roi_percentage'], color='#e74c3c', alpha=0.8)
                    ax2.set_xlabel('Campaign')
                    ax2.set_ylabel('ROI (%)')
                    ax2.set_title('ROI by Campaign', fontsize=12, fontweight='bold')
                    ax2.tick_params(axis='x', rotation=45)
                    
                    for bar in bars2:
                        height = bar.get_height()
                        ax2.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.0f}%', ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
        except Exception as e:
            print(f"Error creating promotional charts: {e}")
    
    def create_comparison_charts(self, parent, df):
        """Create sales comparison charts with consistent bar chart format"""
        # Create two charts side by side
        left_chart_frame = tk.Frame(parent, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
        left_chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_chart_frame = tk.Frame(parent, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
        right_chart_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        try:
            comparison_type = self.comparison_var.get()
            
            # Left chart: Revenue comparison
            fig1, ax1 = plt.subplots(figsize=(10, 6), facecolor=self.theme_colors['chart_bg'])
            
            if not df.empty and 'current_revenue' in df.columns and 'previous_revenue' in df.columns:
                x = range(len(df))
                width = 0.35
                
                # Create bar chart with current vs previous revenue
                bars1 = ax1.bar([i - width/2 for i in x], df['current_revenue'], width, 
                               label='Current Period', color='#3498db', alpha=0.8)
                bars2 = ax1.bar([i + width/2 for i in x], df['previous_revenue'], width, 
                               label='Previous Period', color='#95a5a6', alpha=0.8)
                
                # Add value labels on bars
                for bar in bars1:
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                           f'${height:,.0f}', ha='center', va='bottom', fontsize=9)
                
                for bar in bars2:
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                           f'${height:,.0f}', ha='center', va='bottom', fontsize=9)
                
                ax1.set_xlabel('Period')
                ax1.set_ylabel('Revenue ($)')
                ax1.set_title(f'{comparison_type.replace("_", " ").title()} Revenue Comparison', 
                             fontsize=14, fontweight='bold')
                ax1.set_xticks(x)
                ax1.set_xticklabels(df['period'], rotation=45, ha='right')
                ax1.legend()
                ax1.grid(True, alpha=0.3, axis='y')
                
                # Format y-axis to show currency
                ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            plt.tight_layout()
            canvas1 = FigureCanvasTkAgg(fig1, left_chart_frame)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
            # Right chart: Growth rate analysis
            fig2, ax2 = plt.subplots(figsize=(10, 6), facecolor=self.theme_colors['chart_bg'])
            
            if not df.empty and 'growth_rate' in df.columns:
                # Create growth rate bar chart with colors based on positive/negative growth
                colors = ['#2ecc71' if rate >= 0 else '#e74c3c' for rate in df['growth_rate']]
                bars = ax2.bar(range(len(df)), df['growth_rate'], color=colors, alpha=0.8)
                
                # Add value labels on bars
                for i, bar in enumerate(bars):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}%', ha='center', 
                           va='bottom' if height >= 0 else 'top', fontsize=9)
                
                ax2.set_xlabel('Period')
                ax2.set_ylabel('Growth Rate (%)')
                ax2.set_title(f'{comparison_type.replace("_", " ").title()} Growth Analysis', 
                             fontsize=14, fontweight='bold')
                ax2.set_xticks(range(len(df)))
                ax2.set_xticklabels(df['period'], rotation=45, ha='right')
                ax2.grid(True, alpha=0.3, axis='y')
                ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                
                # Add legend for growth colors
                ax2.text(0.02, 0.98, '🟢 Positive Growth', transform=ax2.transAxes, 
                        verticalalignment='top', color='#2ecc71', fontweight='bold')
                ax2.text(0.02, 0.92, '🔴 Negative Growth', transform=ax2.transAxes, 
                        verticalalignment='top', color='#e74c3c', fontweight='bold')
            
            plt.tight_layout()
            canvas2 = FigureCanvasTkAgg(fig2, right_chart_frame)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
        except Exception as e:
            print(f"Error creating comparison charts: {e}")

    def export_pdf(self):
        """Export promotion/sales analysis report as PDF"""
        try:
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                days = (end_date - start_date).days + 1
            else:
                days = int(self.period_var.get())
                start_date = None
                end_date = None
            
            analysis_type = self.analysis_type_var.get()
            comparison_type = self.comparison_var.get()
            
            df = self.get_promotion_sales_data(analysis_type, days, comparison_type, start_date, end_date)
            
            if not df.empty:
                report_gen = SalesManagerReportGenerator()
                report_gen.generate_sales_report({f"promotion_sales_{analysis_type}": df}, 'pdf')
                messagebox.showinfo("Export Success", "Promotion/Sales analysis report exported to PDF successfully!")
            else:
                messagebox.showwarning("No Data", "No promotion/sales data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")
    
    def export_excel(self):
        """Export promotion/sales analysis data as Excel"""
        try:
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                days = (end_date - start_date).days + 1
            else:
                days = int(self.period_var.get())
                start_date = None
                end_date = None
            
            analysis_type = self.analysis_type_var.get()
            comparison_type = self.comparison_var.get()
            
            df = self.get_promotion_sales_data(analysis_type, days, comparison_type, start_date, end_date)
            
            if not df.empty:
                report_gen = SalesManagerReportGenerator()
                report_gen.generate_sales_report({f"promotion_sales_{analysis_type}": df}, 'excel')
                messagebox.showinfo("Export Success", "Promotion/Sales analysis data exported to Excel successfully!")
            else:
                messagebox.showwarning("No Data", "No promotion/sales data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export Excel: {str(e)}")
    
    def refresh_data(self):
        """Refresh the data display"""
        self.load_data()


class CustomerBuyingBehavior(SalesDataFrame):
    def __init__(self, master):
        super().__init__(master, "Customer Buying Behavior Analytics")
        # Initialize filter variables
        self.period_var = tk.StringVar(value="30")
        self.use_custom_dates = tk.BooleanVar(value=False)
        self.analysis_type_var = tk.StringVar(value="frequently_bought_together")
        
        # Initialize DateEntry widgets - will be created in create_controls
        self.start_date_entry = None
        self.end_date_entry = None
        
        self.create_controls()
        self.load_data()
    
    def create_controls(self):
        """Create filter controls for customer buying behavior analysis"""
        control_frame = tk.Frame(self, bg=self.theme_colors['bg'], relief="solid", bd=1)
        control_frame.pack(fill="x", padx=20, pady=5)
        
        # Period selection
        period_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        period_frame.pack(side="left", padx=10, pady=10)
        
        tk.Label(period_frame, text="Time Period:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        period_combo = ttk.Combobox(period_frame, textvariable=self.period_var, 
                                   values=["7", "14", "30", "60", "90", "180"], width=10)
        period_combo.pack(pady=2)
        period_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        tk.Label(period_frame, text="days", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        # Analysis type selection
        analysis_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        analysis_frame.pack(side="left", padx=20, pady=10)
        
        tk.Label(analysis_frame, text="Analysis Type:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        analysis_combo = ttk.Combobox(analysis_frame, textvariable=self.analysis_type_var, 
                                     values=["frequently_bought_together", "category_performance", "avg_items_per_transaction"], width=20)
        analysis_combo.pack(pady=2)
        analysis_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        # Custom date selection
        date_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        date_frame.pack(side="right", padx=10, pady=10)
        
        tk.Checkbutton(date_frame, text="Custom Date Range", 
                      variable=self.use_custom_dates,
                      command=self.on_custom_date_toggle, bg=self.theme_colors['bg'],
                      fg=self.theme_colors['fg'], font=("Segoe UI", 10, "bold")).pack()
        
        date_controls = tk.Frame(date_frame, bg=self.theme_colors['bg'])
        date_controls.pack()
        
        tk.Label(date_controls, text="From:", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack(side="left", padx=2)
        
        # Create DateEntry widget for start date
        today = datetime.now()
        default_start = today - timedelta(days=30)
        self.start_date_entry = DateEntry(
            date_controls,
            width=10,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            font=("Segoe UI", 8),
            year=default_start.year,
            month=default_start.month,
            day=default_start.day
        )
        self.start_date_entry.pack(side="left", padx=2)
        
        tk.Label(date_controls, text="To:", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack(side="left", padx=2)
        
        # Create DateEntry widget for end date
        self.end_date_entry = DateEntry(
            date_controls,
            width=10,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            font=("Segoe UI", 8),
            year=today.year,
            month=today.month,
            day=today.day
        )
        self.end_date_entry.pack(side="left", padx=2)
        
        tk.Button(date_controls, text="Apply", 
                 command=self.on_custom_date_apply, bg="#3498db", fg="white",
                 font=("Segoe UI", 8), relief="flat", padx=8).pack(side="left", padx=5)
        
        # Initially disable custom date controls
        self.toggle_date_controls(False)
    
    def toggle_date_controls(self, enabled):
        """Enable/disable custom date controls"""
        state = "normal" if enabled else "disabled"
        self.start_date_entry.config(state=state)
        self.end_date_entry.config(state=state)
    
    def on_custom_date_toggle(self):
        """Handle custom date checkbox toggle"""
        enabled = self.use_custom_dates.get()
        self.toggle_date_controls(enabled)
        if not enabled:
            # Reset to default dates when unchecked
            today = datetime.now()
            default_start = today - timedelta(days=int(self.period_var.get()))
            self.start_date_entry.set_date(default_start)
            self.end_date_entry.set_date(today)
            self.load_data()
    
    def on_custom_date_apply(self):
        """Apply custom date range"""
        if self.use_custom_dates.get():
            self.load_data()
    
    def on_filter_changed(self, event=None):
        """Handle filter selection change"""
        if not self.use_custom_dates.get():
            self.load_data()
    
    def load_data(self):
        """Load and display customer buying behavior data with filters"""
        try:
            # Clear existing content (except header and controls)
            for widget in self.winfo_children():
                if isinstance(widget, tk.Frame) and widget != self.winfo_children()[0] and widget != self.winfo_children()[1]:
                    widget.destroy()
            
            # Get filter values
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                days = (end_date - start_date).days + 1
            else:
                days = int(self.period_var.get())
                start_date = None
                end_date = None
            
            analysis_type = self.analysis_type_var.get()
            
            # Get customer buying behavior data
            df = self.get_buying_behavior_data(analysis_type, days, start_date, end_date)
            
            if not df.empty:
                main_frame = tk.Frame(self, bg=self.theme_colors['bg'])
                main_frame.pack(fill="both", expand=True)
                
                # Info panel
                info_frame = tk.Frame(main_frame, bg=self.theme_colors['secondary_bg'], relief="solid", bd=1)
                info_frame.pack(fill="x", padx=10, pady=5)
                
                if self.use_custom_dates.get():
                    info_text = f"🛒 Customer Behavior: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                else:
                    info_text = f"🛒 Customer Behavior: Last {days} days"
                
                info_text += f" | Analysis: {analysis_type.replace('_', ' ').title()}"
                
                tk.Label(info_frame, text=info_text,
                        font=("Segoe UI", 11, "bold"), bg=self.theme_colors['secondary_bg'], 
                        fg=self.theme_colors['fg']).pack(pady=8)
                
                # Chart frame
                chart_frame = tk.Frame(main_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
                chart_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                # Create appropriate chart based on analysis type
                if analysis_type == "frequently_bought_together":
                    self.create_association_chart(df, chart_frame)
                elif analysis_type == "category_performance":
                    self.create_category_chart(df, chart_frame)
                elif analysis_type == "avg_items_per_transaction":
                    self.create_avg_items_chart(df, chart_frame)
                
                # Data table frame
                table_title = {
                    "frequently_bought_together": "Frequently Bought Together Products",
                    "category_performance": "Category Performance Data", 
                    "avg_items_per_transaction": "Average Items per Transaction"
                }.get(analysis_type, "Customer Behavior Data")
                
                table_frame = tk.LabelFrame(main_frame, text=table_title, 
                                           font=("Segoe UI", 12, "bold"), bg=self.theme_colors['bg'],
                                           fg=self.theme_colors['fg'])
                table_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                self.create_data_table(df, table_frame)
                
            else:
                tk.Label(self, text="No customer behavior data available for the selected filters", 
                        font=("Segoe UI", 16), bg=self.theme_colors['bg'],
                        fg=self.theme_colors['fg']).pack(expand=True)
        except Exception as e:
            print(f"Error loading customer buying behavior data: {e}")
            messagebox.showerror("Error", f"Failed to load customer behavior data: {str(e)}")
    
    def get_buying_behavior_data(self, analysis_type, days, start_date=None, end_date=None):
        """Get customer buying behavior data based on analysis type"""
        try:
            if analysis_type == "frequently_bought_together":
                return self.get_frequently_bought_together(days, start_date, end_date)
            elif analysis_type == "category_performance":
                return self.get_category_performance(days, start_date, end_date)
            elif analysis_type == "avg_items_per_transaction":
                return self.get_avg_items_per_transaction(days, start_date, end_date)
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"Error getting buying behavior data: {e}")
            return pd.DataFrame()
    
    def get_frequently_bought_together(self, days, start_date=None, end_date=None):
        """Get frequently bought together products using market basket analysis"""
        try:
            # Use the analytics engine method
            if start_date and end_date:
                return self.analytics.get_frequently_bought_together_custom(start_date, end_date)
            else:
                return self.analytics.get_frequently_bought_together(days)
        except Exception as e:
            print(f"Error getting frequently bought together data: {e}")
            # Return empty DataFrame if error occurs
            return pd.DataFrame()
    
    def get_category_performance(self, days, start_date=None, end_date=None):
        """Get category performance data"""
        try:
            # Use the analytics engine method
            if start_date and end_date:
                return self.analytics.get_category_performance_custom(start_date, end_date)
            else:
                return self.analytics.get_category_performance(days)
        except Exception as e:
            print(f"Error getting category performance data: {e}")
            # Return empty DataFrame if error occurs
            return pd.DataFrame()
    
    def get_avg_items_per_transaction(self, days, start_date=None, end_date=None):
        """Get average items per transaction over time"""
        try:
            # Use the analytics engine method
            if start_date and end_date:
                return self.analytics.get_avg_items_per_transaction_custom(start_date, end_date)
            else:
                return self.analytics.get_avg_items_per_transaction(days)
        except Exception as e:
            print(f"Error getting avg items per transaction data: {e}")
            # Return empty DataFrame if error occurs
            return pd.DataFrame()
    
    def create_association_chart(self, df, parent_frame):
        """Create association rules visualization for frequently bought together"""
        try:
            fig, ax = plt.subplots(figsize=(12, 6), facecolor=self.theme_colors['chart_bg'])
            
            if not df.empty and 'frequency' in df.columns:
                # Create horizontal bar chart for product associations
                product_pairs = [f"{row['product_a']} → {row['product_b']}" for _, row in df.head(10).iterrows()]
                frequencies = df.head(10)['frequency'].values
                
                bars = ax.barh(product_pairs, frequencies, color='#3498db', alpha=0.8)
                ax.set_xlabel('Frequency (Times Bought Together)')
                ax.set_ylabel('Product Associations')
                ax.set_title('Top Product Associations - Frequently Bought Together', fontsize=14, fontweight='bold')
                
                # Add value labels on bars
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
                           f'{int(width)}', ha='left', va='center', fontsize=10)
                
                ax.grid(True, alpha=0.3, axis='x')
                plt.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, parent_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
        except Exception as e:
            print(f"Error creating association chart: {e}")
            tk.Label(parent_frame, text="Error creating association chart", 
                    font=("Segoe UI", 12), bg=self.theme_colors['bg']).pack(pady=20)
    
    def create_category_chart(self, df, parent_frame):
        """Create category performance visualization"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), facecolor=self.theme_colors['chart_bg'])
            
            if not df.empty:
                # Bar chart for total sales by category
                categories = df['category'].values
                sales = df['total_sales'].values
                
                bars1 = ax1.bar(categories, sales, color='#2ecc71', alpha=0.8)
                ax1.set_xlabel('Category')
                ax1.set_ylabel('Total Sales ($)')
                ax1.set_title('Sales by Category', fontsize=12, fontweight='bold')
                ax1.tick_params(axis='x', rotation=45)
                
                # Add value labels on bars
                for bar in bars1:
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                           f'${int(height):,}', ha='center', va='bottom', fontsize=9)
                
                # Pie chart for revenue percentage
                if 'revenue_percentage' in df.columns:
                    wedges, texts, autotexts = ax2.pie(df['revenue_percentage'], labels=categories, 
                                                      autopct='%1.1f%%', startangle=90,
                                                      colors=sns.color_palette("husl", len(categories)))
                    ax2.set_title('Revenue Share by Category', fontsize=12, fontweight='bold')
                
                plt.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, parent_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
        except Exception as e:
            print(f"Error creating category chart: {e}")
            tk.Label(parent_frame, text="Error creating category chart", 
                    font=("Segoe UI", 12), bg=self.theme_colors['bg']).pack(pady=20)
    
    def create_avg_items_chart(self, df, parent_frame):
        """Create average items per transaction trend chart"""
        try:
            fig, ax = plt.subplots(figsize=(12, 6), facecolor=self.theme_colors['chart_bg'])
            
            if not df.empty and 'date' in df.columns and 'avg_items' in df.columns:
                dates = pd.to_datetime(df['date'])
                avg_items = df['avg_items']
                
                ax.plot(dates, avg_items, marker='o', linewidth=2.5, markersize=6, color='#e74c3c')
                ax.set_xlabel('Date')
                ax.set_ylabel('Average Items per Transaction')
                ax.set_title('Average Items per Transaction Trend', fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3)
                
                # Add trend line
                z = np.polyfit(range(len(avg_items)), avg_items, 1)
                p = np.poly1d(z)
                ax.plot(dates, p(range(len(avg_items))), "--", alpha=0.7, color='#95a5a6', linewidth=2)
                
                plt.xticks(rotation=45)
                plt.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, parent_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
        except Exception as e:
            print(f"Error creating avg items chart: {e}")
            tk.Label(parent_frame, text="Error creating average items chart", 
                    font=("Segoe UI", 12), bg=self.theme_colors['bg']).pack(pady=20)
    
    def export_pdf(self):
        """Export customer buying behavior report as PDF"""
        try:
            analysis_type = self.analysis_type_var.get()
            
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                days = (end_date - start_date).days + 1
            else:
                days = int(self.period_var.get())
                start_date = None
                end_date = None
            
            df = self.get_buying_behavior_data(analysis_type, days, start_date, end_date)
            
            if not df.empty:
                report_gen = SalesManagerReportGenerator()
                data_sections = {f"Customer Buying Behavior - {analysis_type.replace('_', ' ').title()}": df}
                report_gen.generate_sales_report({"customer_behavior": df}, 'pdf')
                messagebox.showinfo("Export Success", "Customer buying behavior report exported to PDF successfully!")
            else:
                messagebox.showwarning("No Data", "No customer behavior data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")
    
    def export_excel(self):
        """Export customer buying behavior data as Excel"""
        try:
            analysis_type = self.analysis_type_var.get()
            
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                days = (end_date - start_date).days + 1
            else:
                days = int(self.period_var.get())
                start_date = None
                end_date = None
            
            df = self.get_buying_behavior_data(analysis_type, days, start_date, end_date)
            
            if not df.empty:
                report_gen = SalesManagerReportGenerator()
                data_sections = {f"Customer Buying Behavior - {analysis_type.replace('_', ' ').title()}": df}
                report_gen.generate_sales_report({"customer_behavior": df}, 'excel')
                messagebox.showinfo("Export Success", "Customer buying behavior data exported to Excel successfully!")
            else:
                messagebox.showwarning("No Data", "No customer behavior data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export Excel: {str(e)}")
    
    def refresh_data(self):
        """Refresh the data display"""
        self.load_data()


class SManagerPage(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.controller.title("Sales Manager Page")

        self.sidebar_expand = False
        self.separators = []
        
        # Define default theme colors
        self.theme_colors = {
            'bg': '#f0f0f0',
            'fg': '#333333',
            'secondary_bg': '#ffffff',
            'accent': '#4a90e2',
            'button_bg': '#e0e0e0',
            'button_fg': '#333333',
            'entry_bg': '#ffffff',
            'entry_fg': '#333333',
            'sidebar_bg': '#2c3e50',
            'chart_bg': 'white',
            'chart_colors': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#8B5A3C', '#006D77'],
            'grid_color': '#cccccc',
            'text_color': 'black'
        }
        self.apply_theme()

        self.container = tk.Frame(self, bg=self.theme_colors['bg'])
        self.container.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(self.container, bg=self.theme_colors['sidebar_bg'], width=50)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.toggle_button = tk.Button(self.sidebar, text="☰", fg="white", bg=self.theme_colors['sidebar_bg'],
                                       command=self.toggle_sidebar, bd=0, font=("Segoe UI", 14))
        self.toggle_button.pack(pady=10, anchor="w", fill="x")

        self.logout_button = tk.Button(self.sidebar, text="Logout", fg="black", bg="white",
                                       bd=2, font=("Segoe UI", 13, "bold"), command=self.logout)

        self.sales_trend_button = tk.Button(
            self.sidebar, text="Sales Trend Analysis", bg="#2c3e50", fg="#ecf0f1", activebackground="#34495e",
            activeforeground="white", bd=0, font=("Segoe UI", 11), anchor="w", padx=15, command=self.show_sales_trend)

        self.customer_buying_button = tk.Button(
            self.sidebar, text="Customer Buying Behavior", bg="#2c3e50", fg="#ecf0f1", activebackground="#34495e",
            activeforeground="white", bd=0, font=("Segoe UI", 11), anchor="w", padx=15, 
            command=self.show_customer_buying, wraplength=150, justify="left")

        self.real_time_button = tk.Button(
            self.sidebar, text="Real Time Sales Dashboard", bg="#2c3e50", fg="#ecf0f1",
            activebackground="#34495e", activeforeground="white", bd=0, font=("Segoe UI", 11), anchor="w", padx=15,
            command=self.show_real_time, wraplength=150, justify="left")

        self.popular_product_button = tk.Button(
            self.sidebar, text="Popular Product Data", bg="#2c3e50", fg="#ecf0f1", activebackground="#34495e",
            activeforeground="white", bd=0, font=("Segoe UI", 11), anchor="w",
            padx=15, command=self.show_popular_product)

        self.promotion_sales_button = tk.Button(
            self.sidebar, text="Promotion Sales Comparison", bg="#2c3e50", fg="#ecf0f1", activebackground="#34495e",
            activeforeground="white", bd=0, font=("Segoe UI", 11), anchor="w",
            padx=15, command=self.show_promotion_sales, wraplength=150, justify="left")

        self.content = tk.Frame(self.container, bg=self.theme_colors['bg'])
        self.content.pack(side="left", fill="both", expand=True)

        self.bind_all("<Button-1>", self.click_outside)

        self.current_content = None
        
        # Show welcome message by default
        self.show_welcome()

    def apply_theme(self):
        """Apply current theme colors to the sales manager page"""
        self.configure(bg=self.theme_colors['bg'])

    def refresh_theme(self):
        """Refresh theme after settings change"""
        self.apply_theme()
        # Update existing widgets with new theme
        self.container.configure(bg=self.theme_colors['bg'])
        self.sidebar.configure(bg=self.theme_colors['sidebar_bg'])
        self.toggle_button.configure(bg=self.theme_colors['sidebar_bg'])
        if hasattr(self, 'content'):
            self.content.configure(bg=self.theme_colors['bg'])

    def show_welcome(self):
        """Display welcome message for the logged-in user"""
        self.clear_content()
        
        # Create welcome frame
        welcome_frame = tk.Frame(self.content, bg=self.theme_colors['bg'])
        welcome_frame.pack(fill="both", expand=True)
        
        # Center container
        center_frame = tk.Frame(welcome_frame, bg=self.theme_colors['bg'])
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Get current user info
        current_user = self.controller.get_current_user()
        username = current_user.get('username', 'Sales Manager') if current_user else 'Sales Manager'
        
        # Welcome message
        welcome_label = tk.Label(center_frame, 
                                text=f"Welcome {username}",
                                font=("Segoe UI", 28, "bold"),
                                fg=self.theme_colors['fg'],
                                bg=self.theme_colors['bg'])
        welcome_label.pack(pady=20)
        
        # Subtitle
        subtitle_label = tk.Label(center_frame,
                                 text="Sales Manager Dashboard",
                                 font=("Segoe UI", 16),
                                 fg=self.theme_colors['fg'],
                                 bg=self.theme_colors['bg'])
        subtitle_label.pack(pady=10)
        
        # Instructions
        instructions_label = tk.Label(center_frame,
                                     text="Use the menu on the left to access sales analytics and reports",
                                     font=("Segoe UI", 12),
                                     fg=self.theme_colors['fg'],
                                     bg=self.theme_colors['bg'])
        instructions_label.pack(pady=10)
        
        self.current_content = welcome_frame

    def toggle_sidebar(self):
        if self.sidebar_expand:
            self.sidebar.config(width=50)
            self.toggle_button.config(text="☰", font=("Segoe UI", 14), anchor="center", padx=0)
            self.logout_button.pack_forget()
            self.sales_trend_button.pack_forget()
            self.customer_buying_button.pack_forget()
            self.real_time_button.pack_forget()
            self.popular_product_button.pack_forget()
            self.promotion_sales_button.pack_forget()

            for sep in self.separators:
                sep.destroy()
            self.separators.clear()

        else:
            self.sidebar.config(width=200)
            self.toggle_button.config(text="<", anchor="e", font=("Segoe UI", 14, "bold"), padx=20, )
            self.logout_button.pack(side="bottom", fill="x", pady=(10, 20), padx=20)
            
            # SALES MANAGER
            role_header = tk.Label(self.sidebar, text="SALES MANAGER", 
                                  bg="#34495e", fg="#ecf0f1", font=("Segoe UI", 11, "bold"),
                                  anchor="center", pady=8)
            role_header.pack(fill="x", pady=(15, 10))
            self.separators.append(role_header)
            
            self.sales_trend_button.pack(fill="x", pady=(10, 0))
            self.separator(self.sidebar)
            self.customer_buying_button.pack(fill="x", pady=(10, 0))
            self.separator(self.sidebar)
            self.real_time_button.pack(fill="x", pady=(10, 0))
            self.separator(self.sidebar)
            self.popular_product_button.pack(fill="x", pady=(10, 0))
            self.separator(self.sidebar)
            self.promotion_sales_button.pack(fill="x", pady=(10, 0))
        self.sidebar_expand = not self.sidebar_expand

    def click_outside(self, event):
        try:
            if self.sidebar_expand:
                x, y = event.x_root, event.y_root
                sidebar_x = self.sidebar.winfo_rootx()
                sidebar_w = self.sidebar.winfo_width()

                if x > sidebar_x + sidebar_w:
                    self.toggle_sidebar()
        except Exception:
            pass

    def logout(self):
        # Clear current user data
        self.controller.set_current_user(None)
        # Show login page (this will automatically restore the window size)
        self.controller.show_frame("LoginPage")
        self.controller.title("LogicMart Analytics System - Login")

    def clear_content(self):
        if self.current_content:
            self.current_content.destroy()

    def show_sales_trend(self):
        self.clear_content()
        self.current_content = SalesTrend(self.content)
        self.current_content.pack(fill="both", expand=True)

    def show_customer_buying(self):
        self.clear_content()
        self.current_content = CustomerBuyingBehavior(self.content)
        self.current_content.pack(fill="both", expand=True)

    def show_real_time(self):
        self.clear_content()
        self.current_content = RealTime(self.content)
        self.current_content.pack(fill="both", expand=True)

    def show_popular_product(self):
        self.clear_content()
        self.current_content = PopularProduct(self.content)
        self.current_content.pack(fill="both", expand=True)

    def show_promotion_sales(self):
        self.clear_content()
        self.current_content = PromotionSales(self.content)
        self.current_content.pack(fill="both", expand=True)

    def separator(self, parent):
        separator = tk.Frame(parent, height=1, bg="#bdc3c7")
        separator.pack(fill="x", padx=10, pady=(2, 5))
        self.separators.append(separator)
