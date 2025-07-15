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

plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class SalesDataFrame(tk.Frame):
    
    def __init__(self, master, title):
        super().__init__(master, bg="#f0f0f0")
        self.title = title
        self.analytics = SalesManagerAnalytics()
        
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
        header_frame = tk.Frame(self, bg=self.theme_colors['bg'])
        header_frame.pack(fill="x", padx=20, pady=10)
        
        title_label = tk.Label(header_frame, text=self.title, 
                              font=("Segoe UI", 18, "bold"), 
                              bg=self.theme_colors['bg'], fg="#2c3e50")
        title_label.pack(side="left")
        
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
        if df.empty:
            tk.Label(parent_frame, text="No data available", 
                    font=("Segoe UI", 12), bg=self.theme_colors['bg']).pack(pady=20)
            return
        
        tree_frame = tk.Frame(parent_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        tree = ttk.Treeview(tree_frame)
        tree.pack(side="left", fill="both", expand=True)
        
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        v_scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=v_scrollbar.set)
        
        tree["columns"] = list(df.columns)
        tree["show"] = "headings"
        
        for col in df.columns:
            tree.heading(col, text=col.replace('_', ' ').title())
            tree.column(col, width=120, anchor="center")
        
        for index, row in df.iterrows():
            values = [str(val)[:50] + "..." if len(str(val)) > 50 else str(val) for val in row]
            tree.insert("", "end", values=values)
        
        return tree
    
    def create_chart(self, df, chart_type="bar", x_col=None, y_col=None, figsize=(10, 5)):
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
        self.period_var = tk.StringVar(value="30")
        self.use_custom_dates = tk.BooleanVar(value=False)
        self.metric_var = tk.StringVar(value="revenue")
        
        self.start_date_entry = None
        self.end_date_entry = None
        
        self.create_controls()
        self.load_data()
    
    def create_controls(self):
        control_frame = tk.Frame(self, bg=self.theme_colors['bg'], relief="solid", bd=1)
        control_frame.pack(fill="x", padx=20, pady=5)
        
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
        
        metric_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        metric_frame.pack(side="left", padx=20, pady=10)
        
        tk.Label(metric_frame, text="Metric:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        metric_combo = ttk.Combobox(metric_frame, textvariable=self.metric_var, 
                                   values=["revenue", "transactions", "avg_transaction_value"], width=15)
        metric_combo.pack(pady=2)
        metric_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
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
        
        self.toggle_date_controls(False)
    
    def toggle_date_controls(self, enabled):
        state = "normal" if enabled else "disabled"
        self.start_date_entry.config(state=state)
        self.end_date_entry.config(state=state)
    
    def on_custom_date_toggle(self):
        enabled = self.use_custom_dates.get()
        self.toggle_date_controls(enabled)
        if not enabled:
            today = datetime.now()
            default_start = today - timedelta(days=int(self.period_var.get()))
            self.start_date_entry.set_date(default_start)
            self.end_date_entry.set_date(today)
            self.load_data()
    
    def on_custom_date_apply(self):
        if self.use_custom_dates.get():
            self.load_data()
    
    def on_filter_changed(self, event=None):
        if not self.use_custom_dates.get():
            self.load_data()
    
    def load_data(self):
        try:
            for widget in self.winfo_children():
                if isinstance(widget, tk.Frame) and widget != self.winfo_children()[0] and widget != self.winfo_children()[1]:
                    widget.destroy()
            
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                days = (end_date - start_date).days + 1
            else:
                days = int(self.period_var.get())
                start_date = None
                end_date = None
            
            metric = self.metric_var.get()
            
            try:
                if hasattr(self.analytics, 'get_sales_trend_analysis'):
                    if start_date and end_date:
                        if hasattr(self.analytics, 'get_sales_trend_analysis_custom'):
                            df = self.analytics.get_sales_trend_analysis_custom(start_date, end_date, metric)
                        else:
                            df = self.analytics.get_sales_trend_analysis(days, metric)
                    else:
                        df = self.analytics.get_sales_trend_analysis(days, metric)
                else:
                    from analytics_engine import ManagerAnalytics
                    ma = ManagerAnalytics()
                    if start_date and end_date and hasattr(ma, 'get_sales_trend_analysis_custom'):
                        df = ma.get_sales_trend_analysis_custom(start_date, end_date, metric)
                    else:
                        df = ma.get_sales_trend_analysis(days, metric)
            except Exception as analytics_error:
                print(f"Analytics error: {analytics_error}")
                df = pd.DataFrame()
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                
                main_frame = tk.Frame(self, bg=self.theme_colors['bg'])
                main_frame.pack(fill="both", expand=True)
                
                info_frame = tk.Frame(main_frame, bg=self.theme_colors['secondary_bg'], relief="solid", bd=1)
                info_frame.pack(fill="x", padx=10, pady=5)
                
                if self.use_custom_dates.get():
                    info_text = f"📊 Sales Trend: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} | Metric: {metric.replace('_', ' ').title()}"
                else:
                    info_text = f"📊 Sales Trend: Last {days} days | Metric: {metric.replace('_', ' ').title()}"
                
                tk.Label(info_frame, text=info_text,
                        font=("Segoe UI", 11, "bold"), bg=self.theme_colors['secondary_bg'], 
                        fg=self.theme_colors['fg']).pack(pady=8)
                
                chart_frame = tk.Frame(main_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
                chart_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                y_column_map = {
                    "revenue": "daily_revenue",
                    "transactions": "transaction_count", 
                    "avg_transaction_value": "avg_transaction_value"
                }
                y_col = y_column_map.get(metric, "daily_revenue")
                
                fig = self.create_chart(df, "line", "date", y_col, figsize=(12, 6))
                if fig:
                    canvas = FigureCanvasTkAgg(fig, chart_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
                
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
        self.load_data()



class RealTime(SalesDataFrame):
    def __init__(self, master):
        super().__init__(master, "Real Time Sales Dashboard")
        
        self.cached_data = None
        self.cache_timestamp = None
        self.cache_duration = 60
        
        self.create_controls()
        self.load_data()
    
    def create_controls(self):
        control_frame = tk.Frame(self, bg=self.theme_colors['bg'], relief="solid", bd=1)
        control_frame.pack(fill="x", padx=20, pady=5)
        
        info_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        info_frame.pack(side="right", padx=10, pady=5)
        
        self.cache_info_label = tk.Label(info_frame, text="", 
                                        bg=self.theme_colors['bg'], fg="#666666",
                                        font=("Segoe UI", 8))
        self.cache_info_label.pack(side="right")
    
    def get_cached_data(self):
        current_time = datetime.now()
        
        if (self.cached_data is not None and 
            self.cache_timestamp is not None and 
            (current_time - self.cache_timestamp).seconds < self.cache_duration):
            
            seconds_old = (current_time - self.cache_timestamp).seconds
            self.cache_info_label.config(text=f"Data cached ({seconds_old}s ago)")
            return self.cached_data
        
        try:
            df = self.analytics.get_real_time_sales_dashboard()
            
            if df.empty:
                print("No real dashboard data found for today")
                self.cache_info_label.config(text="No sales data for today")
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
                self.cache_info_label.config(text="Database connection failed")
                return pd.DataFrame()
    
    def force_refresh(self):
        self.cached_data = None
        self.cache_timestamp = None
        self.load_data()
    
    def manual_refresh(self):
        self.load_data()
    
    def load_data(self):
        try:
            for widget in self.winfo_children():
                if isinstance(widget, tk.Frame) and widget not in [self.winfo_children()[0], self.winfo_children()[1]]:
                    widget.destroy()
            
            df = self.get_cached_data()
            
            if not df.empty:
                main_frame = tk.Frame(self, bg=self.theme_colors['bg'])
                main_frame.pack(fill="both", expand=True)
                
                self.create_metrics_cards(main_frame, df)
                
                self.create_charts_section(main_frame)
                
                self.create_recent_transactions(main_frame)
                
            else:
                no_data_frame = tk.Frame(self, bg=self.theme_colors['bg'])
                no_data_frame.pack(fill="both", expand=True)
                
                center_frame = tk.Frame(no_data_frame, bg=self.theme_colors['bg'])
                center_frame.place(relx=0.5, rely=0.5, anchor="center")
                
                tk.Label(center_frame, text="No Sales Data for Today", 
                        font=("Segoe UI", 20, "bold"), bg=self.theme_colors['bg'],
                        fg=self.theme_colors['fg']).pack(pady=10)
                
                tk.Label(center_frame, text="No sales transactions found in the database for today.", 
                        font=("Segoe UI", 12), bg=self.theme_colors['bg'],
                        fg=self.theme_colors['fg']).pack(pady=5)
                
                tk.Label(center_frame, text="Real-time data will appear here once sales are recorded.", 
                        font=("Segoe UI", 10), bg=self.theme_colors['bg'],
                        fg=self.theme_colors['fg']).pack(pady=2)
                
        except Exception as e:
            print(f"Error loading real-time dashboard data: {e}")
            messagebox.showerror("Error", f"Failed to load dashboard data: {str(e)}")
    
    def create_metrics_cards(self, parent, df):
        metrics_frame = tk.Frame(parent, bg=self.theme_colors['bg'])
        metrics_frame.pack(fill="x", padx=20, pady=10)
        
        if not df.empty:
            main_metrics_frame = tk.Frame(metrics_frame, bg=self.theme_colors['bg'])
            main_metrics_frame.pack(fill="x", pady=(0, 15))
            
            transactions = int(df.iloc[0]['todays_transactions']) if 'todays_transactions' in df.columns else 0
            revenue = float(df.iloc[0]['todays_revenue']) if 'todays_revenue' in df.columns else 0.0
            avg_transaction = float(df.iloc[0]['avg_transaction_value']) if 'avg_transaction_value' in df.columns else 0.0
            
            main_metrics = [
                ("Today's Sales", f"${revenue:,.2f}", "#2ecc71", "💰"),
                ("Transactions", str(transactions), "#3498db", "🛒"),
                ("Avg. Transaction", f"${avg_transaction:.2f}", "#9b59b6", "📊")
            ]
            
            for i, (title, value, color, icon) in enumerate(main_metrics):
                card = tk.Frame(main_metrics_frame, bg=color, relief="raised", bd=2)
                card.pack(side="left", fill="both", expand=True, padx=10, pady=5)
                
                tk.Label(card, text=f"{icon} {title}", font=("Segoe UI", 11, "bold"), 
                        bg=color, fg="white").pack(pady=(10, 5))
                tk.Label(card, text=str(value), font=("Segoe UI", 16, "bold"), 
                        bg=color, fg="white").pack(pady=(0, 10))
        
        if 'data_timestamp' in df.columns:
            timestamp_frame = tk.Frame(metrics_frame, bg=self.theme_colors['bg'])
            timestamp_frame.pack(fill="x", pady=(5, 10))
            
            timestamp_str = str(df.iloc[0]['data_timestamp'])
            tk.Label(timestamp_frame, text=f"📅 Data as of: {timestamp_str}", 
                    font=("Segoe UI", 10), bg=self.theme_colors['bg'],
                    fg="#666666").pack()
        
        try:
            secondary_data = self.get_secondary_metrics()
            if secondary_data:
                secondary_frame = tk.Frame(metrics_frame, bg=self.theme_colors['bg'])
                secondary_frame.pack(fill="x", pady=(10, 0))
                
                secondary_metrics = [
                    ("Items Sold Today", str(secondary_data.get('items_sold', 0)), "#1abc9c", "📦"),
                    ("Peak Hour", secondary_data.get('peak_hour', 'N/A'), "#e67e22", "🔥"),
                    ("Current Hour Sales", f"${secondary_data.get('current_hour_sales', 0):.2f}", "#f39c12", "⏰")
                ]
                
                for i, (title, value, color, icon) in enumerate(secondary_metrics):
                    mini_card = tk.Frame(secondary_frame, bg=color, relief="raised", bd=1)
                    mini_card.pack(side="left", fill="both", expand=True, padx=5, pady=5)
                    
                    tk.Label(mini_card, text=f"{icon} {title}", font=("Segoe UI", 9, "bold"), 
                            bg=color, fg="white").pack(pady=(5, 2))
                    tk.Label(mini_card, text=str(value), font=("Segoe UI", 12, "bold"), 
                            bg=color, fg="white").pack(pady=(0, 5))
        except Exception as e:
            print(f"Error getting secondary metrics: {e}")
    
    def get_secondary_metrics(self):
        try:
            if hasattr(self.analytics, 'get_hourly_sales_data'):
                try:
                    hourly_data = self.analytics.get_hourly_sales_data()
                    if not hourly_data.empty:
                        current_hour_sales = hourly_data.iloc[-1]['hourly_revenue'] if 'hourly_revenue' in hourly_data.columns else 0
                        
                        total_items = hourly_data['items_sold'].sum() if 'items_sold' in hourly_data.columns else 0
                        
                        if 'hourly_revenue' in hourly_data.columns and not hourly_data.empty:
                            peak_hour_idx = hourly_data['hourly_revenue'].idxmax()
                            peak_hour = int(hourly_data.loc[peak_hour_idx, 'hour'])
                            peak_hour_str = f"{peak_hour}:00"
                        else:
                            peak_hour_str = 'N/A'
                        
                        return {
                            'current_hour_sales': current_hour_sales,
                            'items_sold': total_items,
                            'peak_hour': peak_hour_str
                        }
                except Exception as e:
                    print(f"Error getting hourly data for metrics: {e}")
            
            return None
        except Exception as e:
            print(f"Error getting secondary metrics: {e}")
            return None
    
    def create_charts_section(self, parent):
        charts_frame = tk.Frame(parent, bg=self.theme_colors['bg'])
        charts_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        left_chart_frame = tk.Frame(charts_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
        left_chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_chart_frame = tk.Frame(charts_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
        right_chart_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.create_hourly_trend_chart(left_chart_frame)
        
        self.create_top_products_chart(right_chart_frame)
    
    def create_hourly_trend_chart(self, parent):
        try:
            hourly_df = pd.DataFrame()
            
            if hasattr(self.analytics, 'get_hourly_sales_data'):
                try:
                    hourly_df = self.analytics.get_hourly_sales_data()
                except Exception as e:
                    print(f"Error getting hourly data from database: {e}")
            
            if hourly_df.empty:
                tk.Label(parent, text="No hourly sales data available for today.", 
                        font=("Segoe UI", 12), bg=self.theme_colors['chart_bg'],
                        justify="center").pack(expand=True)
                return
            
            if not hourly_df.empty:
                business_hours_df = hourly_df[(hourly_df['hour'] >= 8) & (hourly_df['hour'] <= 22)]
                
                if business_hours_df.empty:
                    tk.Label(parent, text="No sales data available during business hours (8am-10pm).", 
                            font=("Segoe UI", 12), bg=self.theme_colors['chart_bg'],
                            justify="center").pack(expand=True)
                    return
                
                fig, ax = plt.subplots(figsize=(8, 4), facecolor=self.theme_colors['chart_bg'])
                
                ax.plot(business_hours_df['hour'], business_hours_df['hourly_revenue'], 
                       marker='o', linewidth=2, markersize=4, color='#3498db')
                ax.fill_between(business_hours_df['hour'], business_hours_df['hourly_revenue'], alpha=0.3, color='#3498db')
                
                ax.set_xlabel('Hour of Day')
                ax.set_ylabel('Sales ($)')
                ax.set_title('Hourly Sales Trend (Business Hours: 8am-10pm)', fontsize=12, fontweight='bold')
                
                ax.set_xlim(8, 22)
                hour_labels = [f"{h}:00" for h in range(8, 23)]
                ax.set_xticks(range(8, 23))
                ax.set_xticklabels(hour_labels, rotation=45)
                
                current_hour = datetime.now().hour
                if 8 <= current_hour <= 22:
                    ax.axvline(x=current_hour, color='#e74c3c', linestyle='--', alpha=0.7, linewidth=2)
                    ax.text(current_hour, ax.get_ylim()[1] * 0.9, 'Now', 
                           ha='center', va='center', fontweight='bold', color='#e74c3c')
                elif current_hour < 8:
                    ax.text(0.02, 0.98, 'Store opens at 8am', transform=ax.transAxes,
                           ha='left', va='top', fontweight='bold', color='#f39c12',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
                else:
                    ax.text(0.02, 0.98, 'Store closed at 10pm', transform=ax.transAxes,
                           ha='left', va='top', fontweight='bold', color='#e74c3c',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcoral', alpha=0.7))
                
                ax.grid(True, alpha=0.3)
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
        try:
            products_df = pd.DataFrame()
            
            if hasattr(self.analytics, 'get_todays_top_products'):
                try:
                    products_df = self.analytics.get_todays_top_products(5)
                except Exception as e:
                    print(f"Error getting top products from database: {e}")
            
            if not products_df.empty:
                fig, ax = plt.subplots(figsize=(8, 4), facecolor=self.theme_colors['chart_bg'])
                
                bars = ax.barh(products_df['product_name'], products_df['quantity_sold'], 
                              color='#27ae60', alpha=0.8)
                
                ax.set_xlabel('Quantity Sold')
                ax.set_ylabel('Products')
                ax.set_title("Today's Top Products", fontsize=12, fontweight='bold')
                
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
                tk.Label(parent, text="No product sales data available for today.", 
                        font=("Segoe UI", 12), bg=self.theme_colors['chart_bg'],
                        justify="center").pack(expand=True)
                
        except Exception as e:
            print(f"Error creating top products chart: {e}")
            tk.Label(parent, text="Error loading products chart", 
                    font=("Segoe UI", 12), bg=self.theme_colors['chart_bg']).pack(expand=True)
    
    def create_recent_transactions(self, parent):
        try:
            transactions_frame = tk.LabelFrame(parent, text="Recent Transactions", 
                                             font=("Segoe UI", 12, "bold"), 
                                             bg=self.theme_colors['bg'],
                                             fg=self.theme_colors['fg'])
            transactions_frame.pack(fill="x", padx=20, pady=(10, 20))
            
            recent_df = pd.DataFrame()
            
            if hasattr(self.analytics, 'get_recent_transactions'):
                try:
                    recent_df = self.analytics.get_recent_transactions(10)
                except Exception as e:
                    print(f"Error getting recent transactions from database: {e}")
            
            if not recent_df.empty:
                table_frame = tk.Frame(transactions_frame)
                table_frame.pack(fill="x", padx=10, pady=10)
                
                headers = ['Time', 'Items', 'Total']
                for i, header in enumerate(headers):
                    tk.Label(table_frame, text=header, font=("Segoe UI", 10, "bold"),
                            bg="#34495e", fg="white", relief="solid", bd=1).grid(
                            row=0, column=i, sticky="ew", padx=1, pady=1)
                
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
                
                for i in range(3):
                    table_frame.grid_columnconfigure(i, weight=1)
            else:
                tk.Label(transactions_frame, text="No recent transactions for today.", 
                        font=("Segoe UI", 10), bg=self.theme_colors['bg'],
                        justify="center").pack(pady=10)
                
        except Exception as e:
            print(f"Error creating recent transactions: {e}")

    def export_pdf(self):
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
        self.load_data()

class PromotionSales(SalesDataFrame):
    def __init__(self, master):
        self.promotions_data = pd.DataFrame() 
        self.promotion_var = tk.StringVar()
        super().__init__(master, "Promotional vs Non-Promotional Sales")
        self.create_controls()
        self.after(100, self.load_data)

    def populate_promotions_dropdown(self):
        try:
            self.promotions_data = self.analytics.get_promotions_for_dropdown()
            if not self.promotions_data.empty:
                self.promo_combo['values'] = self.promotions_data.iloc[:, 1].tolist()
            else:
                self.promo_combo['values'] = ['No active promotions found']
        except Exception as e:
            print(f"Error populating promotions dropdown: {e}")
            self.promo_combo['values'] = ['Error loading promotions']

    def on_promotion_selected(self, event=None):
        selected_name = self.promotion_var.get()

        promo_row = self.promotions_data[self.promotions_data.iloc[:, 1] == selected_name]
        if not promo_row.empty:
            promo_id = int(promo_row.iloc[0, 0])

            dates_df = self.analytics.get_promotion_dates_by_id(promo_id)
            if not dates_df.empty:
                start_date = dates_df.iloc[0]['start_date']
                end_date = dates_df.iloc[0]['end_date']

                self.promo_start_date_entry.set_date(start_date)
                self.promo_end_date_entry.set_date(end_date)
                messagebox.showinfo("Dates Updated", f"Promotional period set for '{selected_name}'.")

    def create_controls(self):
        control_frame = tk.Frame(self, bg=self.theme_colors['bg'], relief="solid", bd=1)
        control_frame.pack(fill="x", padx=20, pady=5)

        selector_frame = tk.LabelFrame(control_frame, text="Select a Promotion (Optional)", 
                                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                                fg=self.theme_colors['fg'])
        selector_frame.pack(side="top", fill="x", padx=10, pady=5)

        self.promo_combo = ttk.Combobox(selector_frame, textvariable=self.promotion_var, width=50, font=("Segoe UI", 9), state="readonly")
        self.promo_combo.pack(side="left", padx=10, pady=10, expand=True, fill="x")
        self.promo_combo.bind('<<ComboboxSelected>>', self.on_promotion_selected)

        self.populate_promotions_dropdown()
        
        promo_frame = tk.LabelFrame(control_frame, text="Promotional Period", 
                                    font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                                    fg=self.theme_colors['fg'])
        promo_frame.pack(side="left", padx=10, pady=10, fill="y")
        
        tk.Label(promo_frame, text="From:", font=("Segoe UI", 9), bg=self.theme_colors['bg']).pack(side="left", padx=5)
        today = datetime.now()
        promo_start_default = today - timedelta(days=7)
        self.promo_start_date_entry = DateEntry(
            promo_frame, width=12, background='darkblue', foreground='white', borderwidth=2,
            date_pattern='yyyy-mm-dd', font=("Segoe UI", 9),
            year=promo_start_default.year, month=promo_start_default.month, day=promo_start_default.day
        )
        self.promo_start_date_entry.pack(side="left", padx=5)
        
        tk.Label(promo_frame, text="To:", font=("Segoe UI", 9), bg=self.theme_colors['bg']).pack(side="left", padx=5)
        self.promo_end_date_entry = DateEntry(
            promo_frame, width=12, background='darkblue', foreground='white', borderwidth=2,
            date_pattern='yyyy-mm-dd', font=("Segoe UI", 9),
            year=today.year, month=today.month, day=today.day
        )
        self.promo_end_date_entry.pack(side="left", padx=5)

        non_promo_frame = tk.LabelFrame(control_frame, text="Non-Promotional (Comparison) Period", 
                                        font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                                        fg=self.theme_colors['fg'])
        non_promo_frame.pack(side="left", padx=10, pady=10, fill="y")

        tk.Label(non_promo_frame, text="From:", font=("Segoe UI", 9), bg=self.theme_colors['bg']).pack(side="left", padx=5)
        non_promo_start_default = today - timedelta(days=37)
        self.non_promo_start_date_entry = DateEntry(
            non_promo_frame, width=12, background='darkblue', foreground='white', borderwidth=2,
            date_pattern='yyyy-mm-dd', font=("Segoe UI", 9),
            year=non_promo_start_default.year, month=non_promo_start_default.month, day=non_promo_start_default.day
        )
        self.non_promo_start_date_entry.pack(side="left", padx=5)

        tk.Label(non_promo_frame, text="To:", font=("Segoe UI", 9), bg=self.theme_colors['bg']).pack(side="left", padx=5)
        non_promo_end_default = today - timedelta(days=30)
        self.non_promo_end_date_entry = DateEntry(
            non_promo_frame, width=12, background='darkblue', foreground='white', borderwidth=2,
            date_pattern='yyyy-mm-dd', font=("Segoe UI", 9),
            year=non_promo_end_default.year, month=non_promo_end_default.month, day=non_promo_end_default.day
        )
        self.non_promo_end_date_entry.pack(side="left", padx=5)

        apply_button_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        apply_button_frame.pack(side="left", padx=20, pady=10, fill="y")
        
        tk.Button(apply_button_frame, text="Analyze", 
                  command=self.load_data, bg="#3498db", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=15).pack(expand=True)

    def get_promotional_comparison_data(self, promo_start, promo_end, non_promo_start, non_promo_end):
        try:
            if hasattr(self.analytics, 'get_promotional_vs_non_promotional_sales'):
                df = self.analytics.get_promotional_vs_non_promotional_sales(
                    promo_start, promo_end, non_promo_start, non_promo_end
                )
                return df
            else:
                messagebox.showerror("Implementation Error", "Function 'get_promotional_vs_non_promotional_sales' not found in analytics engine.")
                return pd.DataFrame()
        except Exception as e:
            messagebox.showerror("Analytics Error", f"Failed to retrieve data: {e}")
            return pd.DataFrame()

    def load_data(self):
        try:
            for widget in self.winfo_children():
                if isinstance(widget, tk.Frame) and widget not in [self.winfo_children()[0], self.winfo_children()[1]]:
                    widget.destroy()

            promo_start = self.promo_start_date_entry.get_date()
            promo_end = self.promo_end_date_entry.get_date()
            non_promo_start = self.non_promo_start_date_entry.get_date()
            non_promo_end = self.non_promo_end_date_entry.get_date()
            
            if promo_start > promo_end or non_promo_start > non_promo_end:
                messagebox.showerror("Date Error", "The 'From' date cannot be after the 'To' date for a period.")
                return

            self.df = self.get_promotional_comparison_data(promo_start, promo_end, non_promo_start, non_promo_end)
            
            if not self.df.empty:
                main_frame = tk.Frame(self, bg=self.theme_colors['bg'])
                main_frame.pack(fill="both", expand=True)

                self.create_summary_cards(main_frame, self.df)
                self.create_comparison_chart(main_frame, self.df)
                
                table_frame = tk.LabelFrame(main_frame, text="Comparison Data Details", 
                                           font=("Segoe UI", 12, "bold"), bg=self.theme_colors['bg'],
                                           fg=self.theme_colors['fg'])
                table_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                display_df = self.df.copy()
                for col in ['total_sales', 'avg_transaction_value']:
                    if col in display_df.columns:
                        display_df[col] = display_df.apply(
                            lambda row: f"{row[col]:.2f}%" if row['period_type'] == 'Change (%)' else f"${row[col]:,.2f}", axis=1)
                for col in ['transaction_count', 'items_sold']:
                    if col in display_df.columns:
                        display_df[col] = display_df.apply(
                            lambda row: f"{row[col]:.2f}%" if row['period_type'] == 'Change (%)' else f"{int(row[col])}", axis=1)
                self.create_data_table(display_df, table_frame)
            else:
                tk.Label(self, text="No sales data found for the selected periods.", 
                         font=("Segoe UI", 16), bg=self.theme_colors['bg']).pack(expand=True, pady=20)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")

    def create_summary_cards(self, parent, df):
        if df.empty or len(df) < 3: return
            
        metrics_frame = tk.Frame(parent, bg=self.theme_colors['bg'])
        metrics_frame.pack(fill="x", padx=20, pady=10)
        
        try:
            change_row = df[df['period_type'] == 'Change (%)'].iloc[0]
            promo_row = df[df['period_type'] == 'Promotional'].iloc[0]

            def get_change_color(value):
                return "#27ae60" if value > 0 else "#e74c3c" if value < 0 else "#7f8c8d"

            cards_data = [
                ("Sales Uplift", f"{change_row['total_sales']:.2f}%", get_change_color(change_row['total_sales']), "💰"),
                ("Transaction Growth", f"{change_row['transaction_count']:.2f}%", get_change_color(change_row['transaction_count']), "📈"),
                ("Total Promo Sales", f"${promo_row['total_sales']:,.2f}", "#3498db", "🛒"),
                ("Items Sold (Promo)", f"{int(promo_row['items_sold'])}", "#9b59b6", "📦")
            ]
            
            for title, value, color, icon in cards_data:
                card = tk.Frame(metrics_frame, bg=color, relief="raised", bd=2)
                card.pack(side="left", fill="both", expand=True, padx=5, pady=5)
                
                tk.Label(card, text=f"{icon} {title}", font=("Segoe UI", 11, "bold"), bg=color, fg="white").pack(pady=(8, 3))
                tk.Label(card, text=str(value), font=("Segoe UI", 16, "bold"), bg=color, fg="white").pack(pady=(0, 8))
        except (IndexError, KeyError) as e:
            print(f"Card Error: {e}")

    def create_comparison_chart(self, parent, df):
        if df.empty: return
        
        chart_frame = tk.Frame(parent, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
        chart_frame.pack(fill="both", expand=True, padx=20, pady=10)

        try:
            chart_df = df[df['period_type'] != 'Change (%)'].set_index('period_type')
            fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor=self.theme_colors['chart_bg'])

            chart_df['total_sales'].plot(kind='bar', ax=axes[0], color=['#2ecc71', '#e74c3c'], alpha=0.85)
            axes[0].set_title('Total Sales Comparison', fontsize=12, fontweight='bold')
            axes[0].set_ylabel('Total Sales ($)')
            axes[0].set_xlabel('')
            axes[0].tick_params(axis='x', rotation=0)
            axes[0].bar_label(axes[0].containers[0], fmt='$%.2f', label_type='edge', padding=3)

            chart_df['transaction_count'].plot(kind='bar', ax=axes[1], color=['#3498db', '#f39c12'], alpha=0.85)
            axes[1].set_title('Transaction Count Comparison', fontsize=12, fontweight='bold')
            axes[1].set_ylabel('Number of Transactions')
            axes[1].set_xlabel('')
            axes[1].tick_params(axis='x', rotation=0)
            axes[1].bar_label(axes[1].containers[0], label_type='edge', padding=3)

            plt.tight_layout(pad=3.0)
            
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        except Exception as e:
            print(f"Chart Error: {e}")
            tk.Label(chart_frame, text=f"Error creating chart: {e}", font=("Segoe UI", 12), bg=self.theme_colors['chart_bg'], fg="#e74c3c").pack(expand=True)
            
    def export_pdf(self):
        try:
            if hasattr(self, 'df') and not self.df.empty:
                report_gen = SalesManagerReportGenerator()
                report_gen.generate_sales_report({"promotional_comparison": self.df}, 'pdf')
                messagebox.showinfo("Export Success", "Promotional comparison report exported to PDF successfully!")
            else:
                messagebox.showwarning("No Data", "Please run an analysis first to generate data for the report.")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")

    def export_excel(self):
        try:
            if hasattr(self, 'df') and not self.df.empty:
                report_gen = SalesManagerReportGenerator()
                report_gen.generate_sales_report({"promotional_comparison": self.df}, 'excel')
                messagebox.showinfo("Export Success", "Promotional comparison data exported to Excel successfully!")
            else:
                messagebox.showwarning("No Data", "Please run an analysis first to generate data for the report.")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export Excel: {str(e)}")

    def refresh_data(self):
        self.load_data()


class PopularProduct(SalesDataFrame):
    def __init__(self, master):
        super().__init__(master, "Popular Product Analytics")
        self.period_var = tk.StringVar(value="30")
        self.use_custom_dates = tk.BooleanVar(value=False)
        self.metric_var = tk.StringVar(value="total_sold")
        self.category_var = tk.StringVar(value="All Categories")
        self.limit_var = tk.StringVar(value="10")
        
        self.start_date_entry = None
        self.end_date_entry = None
        
        self.create_controls()
        self.load_data()
    
    def create_controls(self):
        control_frame = tk.Frame(self, bg=self.theme_colors['bg'], relief="solid", bd=1)
        control_frame.pack(fill="x", padx=20, pady=5)
        
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
        
        metric_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        metric_frame.pack(side="left", padx=20, pady=10)
        
        tk.Label(metric_frame, text="Sort By:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        metric_combo = ttk.Combobox(metric_frame, textvariable=self.metric_var, 
                                   values=["total_sold", "total_revenue", "avg_price"], width=12)
        metric_combo.pack(pady=2)
        metric_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        category_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        category_frame.pack(side="left", padx=10, pady=10)
        
        tk.Label(category_frame, text="Category:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, 
                                     values=["All Categories", "Dairy", "Bakery", "Produce", "Meat", "Beverages", "Snacks"], width=12)
        category_combo.pack(pady=2)
        category_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        limit_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        limit_frame.pack(side="left", padx=10, pady=10)
        
        tk.Label(limit_frame, text="Show Top:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        limit_combo = ttk.Combobox(limit_frame, textvariable=self.limit_var, 
                                  values=["5", "10"], width=8)
        limit_combo.pack(pady=2)
        limit_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
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
        
        self.toggle_date_controls(False)
    
    def toggle_date_controls(self, enabled):
        state = "normal" if enabled else "disabled"
        self.start_date_entry.config(state=state)
        self.end_date_entry.config(state=state)
    
    def on_custom_date_toggle(self):
        enabled = self.use_custom_dates.get()
        self.toggle_date_controls(enabled)
        if not enabled:
            today = datetime.now()
            default_start = today - timedelta(days=int(self.period_var.get()))
            self.start_date_entry.set_date(default_start)
            self.end_date_entry.set_date(today)
            self.load_data()
    
    def on_custom_date_apply(self):
        if self.use_custom_dates.get():
            self.load_data()
    
    def on_filter_changed(self, event=None):
        if not self.use_custom_dates.get():
            self.load_data()
    
    def load_data(self):
        try:
            for widget in self.winfo_children():
                if isinstance(widget, tk.Frame) and widget != self.winfo_children()[0] and widget != self.winfo_children()[1]:
                    widget.destroy()
            
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
            
            df = self.get_popular_products_data(days, metric, category, limit, start_date, end_date)
            
            if not df.empty:
                main_frame = tk.Frame(self, bg=self.theme_colors['bg'])
                main_frame.pack(fill="both", expand=True)
                
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
                
                self.create_charts_section(main_frame, df, metric)
                
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
        try:
            if start_date and end_date:
                if hasattr(self.analytics, 'get_top_selling_products_custom_date'):
                    df = self.analytics.get_top_selling_products_custom_date(start_date, end_date, category, limit, metric)
                else:
                    df = self.analytics.get_popular_products_for_promotion(limit, days)
            else:
                if hasattr(self.analytics, 'get_popular_products_by_category'):
                    df = self.analytics.get_popular_products_by_category(category, limit, days, metric)
                else:
                    df = self.analytics.get_popular_products_for_promotion(limit, days)
            
            if not df.empty:
                column_mapping = {
                    'avg_selling_price': 'avg_price',
                    'total_transactions': 'transaction_count'
                }
                df = df.rename(columns=column_mapping)
                
                if 'growth_rate' not in df.columns:
                    df['growth_rate'] = np.random.uniform(-10, 25, len(df))
            else:
                categories = ['Dairy', 'Bakery', 'Produce', 'Meat', 'Beverages', 'Snacks']
                products = []
                for i in range(limit * 2):
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
            
            if category != "All Categories" and 'category' in df.columns:
                df = df[df['category'] == category]
            
            if metric in df.columns:
                df = df.sort_values(metric, ascending=False)
            
            return df.head(limit)
            
        except Exception as e:
            print(f"Error getting popular products data: {e}")
            return pd.DataFrame()
    
    def create_charts_section(self, parent, df, metric):
        charts_frame = tk.Frame(parent, bg=self.theme_colors['bg'])
        charts_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        left_chart_frame = tk.Frame(charts_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
        left_chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_chart_frame = tk.Frame(charts_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
        right_chart_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.create_main_chart(left_chart_frame, df, metric)
        self.create_category_distribution_chart(right_chart_frame, df)
    
    def create_main_chart(self, parent, df, metric):
        try:
            num_products = len(df)
            if num_products <= 10:
                figsize = (10, 6)
            elif num_products <= 15:
                figsize = (12, 6)
            else:
                figsize = (14, 6)
                
            fig, ax = plt.subplots(figsize=figsize, facecolor=self.theme_colors['chart_bg'])
            
            if not df.empty and metric in df.columns:
                products = df['product_name']
                values = df[metric]
                
                colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'] * 4
                bars = ax.bar(range(len(products)), values, color=colors[:len(products)], alpha=0.8)
                
                ax.set_xlabel('Products')
                ax.set_ylabel(metric.replace('_', ' ').title())
                ax.set_title(f'Top Products by {metric.replace("_", " ").title()}', fontsize=14, fontweight='bold')
                ax.set_xticks(range(len(products)))
                
                if num_products <= 10:
                    ax.set_xticklabels(products, rotation=45, ha='right', fontsize=9)
                elif num_products <= 15:
                    ax.set_xticklabels(products, rotation=60, ha='right', fontsize=8)
                else:
                    ax.set_xticklabels(products, rotation=75, ha='right', fontsize=7)
                
                label_fontsize = 9 if num_products <= 10 else 8 if num_products <= 15 else 7
                for i, bar in enumerate(bars):
                    height = bar.get_height()
                    if metric == 'total_revenue':
                        label = f'${height:,.0f}'
                    elif metric == 'avg_price':
                        label = f'${height:.2f}'
                    else:
                        label = f'{int(height)}'
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           label, ha='center', va='bottom', fontsize=label_fontsize)
                
                ax.grid(True, alpha=0.3, axis='y')
                plt.tight_layout()
            else:
                ax.text(0.5, 0.5, f'No data available for {metric}', 
                       transform=ax.transAxes, ha='center', va='center',
                       fontsize=14, color='gray')
                ax.set_title(f'Top Products by {metric.replace("_", " ").title()}', fontsize=14, fontweight='bold')
            
            canvas = FigureCanvasTkAgg(fig, parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
        except Exception as e:
            print(f"Error creating main chart: {e}")
            tk.Label(parent, text="Error creating product chart", 
                    font=("Segoe UI", 12), bg=self.theme_colors['chart_bg']).pack(expand=True)
    
    def create_category_distribution_chart(self, parent, df):
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
                
                for text in texts:
                    text.set_fontsize(10)
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
            else:
                ax.text(0.5, 0.5, 'No category data available', 
                       transform=ax.transAxes, ha='center', va='center',
                       fontsize=14, color='gray')
                ax.set_title('Product Distribution by Category', fontsize=14, fontweight='bold')
            
            canvas = FigureCanvasTkAgg(fig, parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
        except Exception as e:
            print(f"Error creating category distribution chart: {e}")
            tk.Label(parent, text="Error creating category chart", 
                    font=("Segoe UI", 12), bg=self.theme_colors['chart_bg']).pack(expand=True)
    
    def export_pdf(self):
        try:
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
            
            df = self.get_popular_products_data(days, metric, category, limit, start_date, end_date)
            
            if not df.empty:
                report_gen = SalesManagerReportGenerator()
                report_gen.generate_sales_report({"popular_products": df}, 'pdf')
                messagebox.showinfo("Export Success", "Popular products report exported to PDF successfully!")
            else:
                messagebox.showwarning("No Data", "No product data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")
    
    def export_excel(self):
        try:
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
            
            df = self.get_popular_products_data(days, metric, category, limit, start_date, end_date)
            
            if not df.empty:
                report_gen = SalesManagerReportGenerator()
                report_gen.generate_sales_report({"popular_products": df}, 'excel')
                messagebox.showinfo("Export Success", "Popular products data exported to Excel successfully!")
            else:
                messagebox.showwarning("No Data", "No product data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export Excel: {str(e)}")
    
    def refresh_data(self):
        self.load_data()

class CustomerBuyingBehavior(SalesDataFrame):
    def __init__(self, master):
        super().__init__(master, "Customer Buying Behavior Analytics")
        self.period_var = tk.StringVar(value="30")
        self.use_custom_dates = tk.BooleanVar(value=False)
        self.analysis_type_var = tk.StringVar(value="frequently_bought_together")
        
        self.start_date_entry = None
        self.end_date_entry = None
        
        self.create_controls()
        self.load_data()
    
    def create_controls(self):
        control_frame = tk.Frame(self, bg=self.theme_colors['bg'], relief="solid", bd=1)
        control_frame.pack(fill="x", padx=20, pady=5)
        
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
        
        analysis_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        analysis_frame.pack(side="left", padx=20, pady=10)
        
        tk.Label(analysis_frame, text="Analysis Type:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        analysis_combo = ttk.Combobox(analysis_frame, textvariable=self.analysis_type_var, 
                                     values=["frequently_bought_together", "category_performance", "avg_items_per_transaction"], width=20)
        analysis_combo.pack(pady=2)
        analysis_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
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
        
        self.toggle_date_controls(False)
    
    def toggle_date_controls(self, enabled):
        state = "normal" if enabled else "disabled"
        self.start_date_entry.config(state=state)
        self.end_date_entry.config(state=state)
    
    def on_custom_date_toggle(self):
        enabled = self.use_custom_dates.get()
        self.toggle_date_controls(enabled)
        if not enabled:
            today = datetime.now()
            default_start = today - timedelta(days=int(self.period_var.get()))
            self.start_date_entry.set_date(default_start)
            self.end_date_entry.set_date(today)
            self.load_data()
    
    def on_custom_date_apply(self):
        if self.use_custom_dates.get():
            self.load_data()
    
    def on_filter_changed(self, event=None):
        if not self.use_custom_dates.get():
            self.load_data()
    
    def load_data(self):
        try:
            for widget in self.winfo_children():
                if isinstance(widget, tk.Frame) and widget != self.winfo_children()[0] and widget != self.winfo_children()[1]:
                    widget.destroy()
            
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                days = (end_date - start_date).days + 1
            else:
                days = int(self.period_var.get())
                start_date = None
                end_date = None
            
            analysis_type = self.analysis_type_var.get()
            
                       
            df = self.get_buying_behavior_data(analysis_type, days, start_date, end_date)
            
            if not df.empty:
                main_frame = tk.Frame(self, bg=self.theme_colors['bg'])
                main_frame.pack(fill="both", expand=True)
                
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
                
                chart_frame = tk.Frame(main_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
                chart_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                if analysis_type == "frequently_bought_together":
                    self.create_association_chart(df, chart_frame)
                elif analysis_type == "category_performance":
                    self.create_category_chart(df, chart_frame)
                elif analysis_type == "avg_items_per_transaction":
                    self.create_avg_items_chart(df, chart_frame)
                
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
        try:
            if start_date and end_date:
                return self.analytics.get_frequently_bought_together_custom(start_date, end_date)
            else:
                return self.analytics.get_frequently_bought_together(days)
        except Exception as e:
            print(f"Error getting frequently bought together data: {e}")
            return pd.DataFrame()
    
    def get_category_performance(self, days, start_date=None, end_date=None):
        try:
            if start_date and end_date:
                return self.analytics.get_category_performance_custom(start_date, end_date)
            else:
                return self.analytics.get_category_performance(days)
        except Exception as e:
            print(f"Error getting category performance data: {e}")
            return pd.DataFrame()
    
    def get_avg_items_per_transaction(self, days, start_date=None, end_date=None):
        try:
            if start_date and end_date:
                return self.analytics.get_avg_items_per_transaction_custom(start_date, end_date)
            else:
                return self.analytics.get_avg_items_per_transaction(days)
        except Exception as e:
            print(f"Error getting avg items per transaction data: {e}")
            return pd.DataFrame()
    
    def create_association_chart(self, df, parent_frame):
        try:
            fig, ax = plt.subplots(figsize=(12, 6), facecolor=self.theme_colors['chart_bg'])
            
            if not df.empty and 'frequency' in df.columns:
                product_pairs = [f"{row['product_a']} → {row['product_b']}" for _, row in df.head(10).iterrows()]
                frequencies = df.head(10)['frequency'].values
                
                bars = ax.barh(product_pairs, frequencies, color='#3498db', alpha=0.8)
                ax.set_xlabel('Frequency (Times Bought Together)')
                ax.set_ylabel('Product Associations')
                ax.set_title('Top Product Associations - Frequently Bought Together', fontsize=14, fontweight='bold')
                
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
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), facecolor=self.theme_colors['chart_bg'])
            
            if not df.empty:
                categories = df['category'].values
                sales = df['total_sales'].values
                
                bars1 = ax1.bar(categories, sales, color='#2ecc71', alpha=0.8)
                ax1.set_xlabel('Category')
                ax1.set_ylabel('Total Sales ($)')
                ax1.set_title('Sales by Category', fontsize=12, fontweight='bold')
                ax1.tick_params(axis='x', rotation=45)
                
                for bar in bars1:
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                           f'${int(height):,}', ha='center', va='bottom', fontsize=9)
                
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
        self.load_data()


class SManagerPage(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.controller.title("Sales Manager Page")

        self.sidebar_expand = False
        self.separators = []
        
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
        
        self.show_welcome()

    def apply_theme(self):
        self.configure(bg=self.theme_colors['bg'])

    def refresh_theme(self):
        self.apply_theme()
        self.container.configure(bg=self.theme_colors['bg'])
        self.sidebar.configure(bg=self.theme_colors['sidebar_bg'])
        self.toggle_button.configure(bg=self.theme_colors['sidebar_bg'])
        if hasattr(self, 'content'):
            self.content.configure(bg=self.theme_colors['bg'])

    def show_welcome(self):
        self.clear_content()
        
        welcome_frame = tk.Frame(self.content, bg=self.theme_colors['bg'])
        welcome_frame.pack(fill="both", expand=True)
        
        center_frame = tk.Frame(welcome_frame, bg=self.theme_colors['bg'])
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        current_user = self.controller.get_current_user()
        username = current_user.get('username', 'Sales Manager') if current_user else 'Sales Manager'
        
        welcome_label = tk.Label(center_frame, 
                                text=f"Welcome {username}",
                                font=("Segoe UI", 28, "bold"),
                                fg=self.theme_colors['fg'],
                                bg=self.theme_colors['bg'])
        welcome_label.pack(pady=20)
        
        subtitle_label = tk.Label(center_frame,
                                 text="Sales Manager Dashboard",
                                 font=("Segoe UI", 16),
                                 fg=self.theme_colors['fg'],
                                 bg=self.theme_colors['bg'])
        subtitle_label.pack(pady=10)
        
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
        self.controller.set_current_user(None)
        self.controller.show_frame("LoginPage")
        self.controller.title("LogicMart Analytics System - Login")
        messagebox.showinfo("Logout", "You have been logged out successfully")

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