import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
from analytics_engine import ManagerAnalytics
from report_generator import ManagerReportGenerator
import seaborn as sns
from tkcalendar import DateEntry
from datetime import datetime, timedelta

plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class DataDisplayFrame(tk.Frame):
    def __init__(self, master, title):
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
        
        super().__init__(master, bg=self.theme_colors['bg'])
        self.title = title
        self.analytics = ManagerAnalytics()
        self.create_header()
        
    def create_header(self):
        header_frame = tk.Frame(self, bg=self.theme_colors['bg'])
        header_frame.pack(fill="x", padx=20, pady=10)
        
        title_label = tk.Label(header_frame, text=self.title, 
                              font=("Segoe UI", 18, "bold"), 
                              bg=self.theme_colors['bg'], fg=self.theme_colors['fg'])
        title_label.pack(side="left")
        
        export_frame = tk.Frame(header_frame, bg=self.theme_colors['bg'])
        export_frame.pack(side="right")
        
        tk.Button(export_frame, text="📊 Export PDF", 
                 command=self.export_pdf, bg="#3498db", fg="white",
                 font=("Segoe UI", 9), relief="flat", padx=10).pack(side="right", padx=5)
        
        tk.Button(export_frame, text="📋 Export Excel", 
                 command=self.export_excel, bg="#27ae60", fg="white",
                 font=("Segoe UI", 9), relief="flat", padx=10).pack(side="right", padx=5)
        
        tk.Button(export_frame, text="🔄 Refresh", 
                 command=self.refresh_data, bg="#e74c3c", fg="white",
                 font=("Segoe UI", 9), relief="flat", padx=10).pack(side="right", padx=5)
    
    def create_data_table(self, df, parent_frame):
        if df.empty:
            tk.Label(parent_frame, text="No data available", 
                    font=("Segoe UI", 12), bg=self.theme_colors['bg'], 
                    fg=self.theme_colors['fg']).pack(pady=20)
            return
        
        table_container = tk.Frame(parent_frame, bg=self.theme_colors['bg'])
        table_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        tree_frame = tk.Frame(table_container, bg=self.theme_colors['bg'])
        tree_frame.pack(fill="both", expand=True)
        
        tree = ttk.Treeview(tree_frame)
        tree.pack(side="left", fill="both", expand=True)
        
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        v_scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(table_container, orient="horizontal", command=tree.xview)
        h_scrollbar.pack(side="bottom", fill="x")
        tree.configure(xscrollcommand=h_scrollbar.set)
        
        tree["columns"] = list(df.columns)
        tree["show"] = "headings"
        
        for col in df.columns:
            tree.heading(col, text=col.replace('_', ' ').title())
            tree.column(col, width=150, anchor="center")
        
        for index, row in df.iterrows():
            values = [str(val)[:100] + "..." if len(str(val)) > 100 else str(val) for val in row]
            tree.insert("", "end", values=values)
        
        return tree
    
    def create_chart(self, df, chart_type="bar", x_col=None, y_col=None, figsize=(10, 5)):
        if df.empty:
            return None
            
        fig, ax = plt.subplots(figsize=figsize, facecolor='white')
        
        try:
            if chart_type == "line" and x_col and y_col:
                ax.plot(df[x_col], df[y_col], marker='o', linewidth=2.5, markersize=6)
                ax.set_xlabel(x_col.replace('_', ' ').title())
                ax.set_ylabel(y_col.replace('_', ' ').title())
                
            elif chart_type == "bar" and x_col and y_col:
                bars = ax.bar(df[x_col], df[y_col], color='steelblue', alpha=0.8)
                ax.set_xlabel(x_col.replace('_', ' ').title())
                ax.set_ylabel(y_col.replace('_', ' ').title())
                
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}', ha='center', va='bottom', fontsize=9)
                           
            elif chart_type == "pie":
                labels = df.iloc[:, 0]
                values = df.iloc[:, 1]
                wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', 
                                                 startangle=90, colors=sns.color_palette("husl", len(labels)))
                
            ax.set_title(self.title, fontsize=14, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Chart Error: {str(e)}', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
        
        return fig
    
    def export_pdf(self):
        messagebox.showinfo("Export", "PDF export functionality - override in child class")
    
    def export_excel(self):
        messagebox.showinfo("Export", "Excel export functionality - override in child class")
    
    def refresh_data(self):
        self.load_data()


class SalesTrend(DataDisplayFrame):
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
                fg=self.theme_colors['fg']).grid(row=0, column=0, padx=5)
        
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
        self.start_date_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(date_controls, text="To:", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).grid(row=0, column=2, padx=5)
        
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
        self.end_date_entry.grid(row=0, column=3, padx=5)
        
        tk.Button(date_controls, text="Apply", 
                 command=self.on_custom_date_apply, bg="#3498db", fg="white",
                 font=("Segoe UI", 9), relief="flat", padx=10).grid(row=0, column=4, padx=10)
        
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
            
            if start_date and end_date:
                df = self.analytics.get_sales_trend_analysis_custom(start_date, end_date, metric)
            else:
                df = self.analytics.get_sales_trend_analysis(days, metric)
            
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
            messagebox.showerror("Error", f"Failed to load sales data: {str(e)}")
    
    def export_pdf(self):
        try:
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                df = self.analytics.get_sales_trend_analysis_custom(start_date, end_date, self.metric_var.get())
            else:
                days = int(self.period_var.get())
                df = self.analytics.get_sales_trend_analysis(days, self.metric_var.get())
                
            if not df.empty:
                report_gen = ManagerReportGenerator()
                charts = {}
                if not df.empty:
                    df_chart = df.copy()
                    df_chart['date'] = pd.to_datetime(df_chart['date'])
                    y_column_map = {
                        "revenue": "daily_revenue",
                        "transactions": "transaction_count", 
                        "avg_transaction_value": "avg_transaction_value"
                    }
                    y_col = y_column_map.get(self.metric_var.get(), "daily_revenue")
                    chart_buffer = report_gen.create_chart(df_chart, 'line', 'Sales Trend Analysis', 'date', y_col)
                    charts['Sales Trend Chart'] = chart_buffer
                
                data_sections = {"Sales Trend Analysis": df}
                report_gen.generate_pdf_report("Sales Trend Report", data_sections, charts)
            else:
                messagebox.showwarning("No Data", "No sales data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")
    
    def export_excel(self):
        try:
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                df = self.analytics.get_sales_trend_analysis_custom(start_date, end_date, self.metric_var.get())
            else:
                days = int(self.period_var.get())
                df = self.analytics.get_sales_trend_analysis(days, self.metric_var.get())
                
            if not df.empty:
                report_gen = ManagerReportGenerator()
                data_sections = {"Sales Trend Analysis": df}
                report_gen.generate_excel_report("Sales Trend Report", data_sections)
            else:
                messagebox.showwarning("No Data", "No sales data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export Excel: {str(e)}")
    
    def refresh_data(self):
        self.load_data()


class CustomerTraffic(DataDisplayFrame):
    def __init__(self, master):
        super().__init__(master, "Customer Traffic Reports")
        self.load_data()
    
    def load_data(self):
        df = self.analytics.get_peak_shopping_hours(7)
        
        if not df.empty:
            main_frame = tk.Frame(self, bg=self.theme_colors['bg'])
            main_frame.pack(fill="both", expand=True)
            
            chart_frame = tk.Frame(main_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
            chart_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            fig = self.create_chart(df, "bar", "hour", "transaction_count", figsize=(12, 6))
            if fig:
                canvas = FigureCanvasTkAgg(fig, chart_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
            table_frame = tk.LabelFrame(main_frame, text="Traffic Data by Hour", 
                                       font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
            table_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            self.create_data_table(df, table_frame)
        else:
            tk.Label(self, text="No traffic data available", 
                    font=("Segoe UI", 16), bg="#f0f0f0").pack(expand=True)
    
    def export_pdf(self):
        try:
            df = self.analytics.get_peak_shopping_hours(7)
            if not df.empty:
                report_gen = ManagerReportGenerator()
                charts = {}
                chart_buffer = report_gen.create_chart(df, 'bar', 'Customer Traffic by Hour', 'hour', 'transaction_count')
                charts['Traffic Chart'] = chart_buffer
                
                data_sections = {"Customer Traffic by Hour": df}
                report_gen.generate_pdf_report("Customer Traffic Report", data_sections, charts)
            else:
                messagebox.showwarning("No Data", "No traffic data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")
    
    def export_excel(self):
        try:
            df = self.analytics.get_peak_shopping_hours(7)
            if not df.empty:
                report_gen = ManagerReportGenerator()
                data_sections = {"Customer Traffic by Hour": df}
                report_gen.generate_excel_report("Customer Traffic Report", data_sections)
            else:
                messagebox.showwarning("No Data", "No traffic data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export Excel: {str(e)}")


class TopSelling(DataDisplayFrame):
    def __init__(self, master):
        super().__init__(master, "Top Selling Products")
        self.period_var = tk.StringVar(value="30")
        self.limit_var = tk.StringVar(value="10")
        self.category_var = tk.StringVar(value="All Categories")
        self.sort_by_var = tk.StringVar(value="quantity")
        self.use_custom_dates = tk.BooleanVar(value=False)
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
        
        limit_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        limit_frame.pack(side="left", padx=10, pady=10)
        
        tk.Label(limit_frame, text="Show Top:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        limit_combo = ttk.Combobox(limit_frame, textvariable=self.limit_var, 
                                  values=["5", "10", "15", "20", "25"], width=8)
        limit_combo.pack(pady=2)
        limit_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        tk.Label(limit_frame, text="products", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        sort_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        sort_frame.pack(side="left", padx=10, pady=10)
        
        tk.Label(sort_frame, text="Sort By:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_by_var, 
                                 values=["quantity", "revenue", "frequency"], width=12)
        sort_combo.pack(pady=2)
        sort_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        category_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        category_frame.pack(side="left", padx=10, pady=10)
        
        tk.Label(category_frame, text="Category:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, width=15)
        self.category_combo.pack(pady=2)
        self.category_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        date_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        date_frame.pack(side="right", padx=10, pady=10)
        
        tk.Checkbutton(date_frame, text="Custom Dates", 
                      variable=self.use_custom_dates,
                      command=self.on_custom_date_toggle, bg=self.theme_colors['bg'],
                      fg=self.theme_colors['fg'], font=("Segoe UI", 10, "bold")).pack()
        
        date_controls = tk.Frame(date_frame, bg=self.theme_colors['bg'])
        date_controls.pack()
        
        tk.Label(date_controls, text="From:", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).grid(row=0, column=0, padx=2)
        
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
        self.start_date_entry.grid(row=0, column=1, padx=2)
        
        tk.Label(date_controls, text="To:", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).grid(row=0, column=2, padx=2)
        
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
        self.end_date_entry.grid(row=0, column=3, padx=2)
        
        tk.Button(date_controls, text="Apply", 
                 command=self.on_custom_date_apply, bg="#3498db", fg="white",
                 font=("Segoe UI", 8), relief="flat", padx=8).grid(row=0, column=4, padx=5)
        
        self.toggle_date_controls(False)
        
        self.load_categories()
    
    def load_categories(self):
        try:
            categories = ["Electronics", "Clothing", "Food & Beverages", "Home & Garden", "Sports & Outdoors"]
            category_list = ["All Categories"] + categories
            self.category_combo['values'] = category_list
        except Exception as e:
            self.category_combo['values'] = ["All Categories"]
    
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
            
            limit = int(self.limit_var.get())
            category = self.category_var.get() if self.category_var.get() != "All Categories" else None
            sort_by = self.sort_by_var.get()
            
            if start_date and end_date:
                df = self.analytics.get_top_selling_products(limit, days)
            else:
                df = self.analytics.get_top_selling_products(limit, days)
            
            if not df.empty:
                main_frame = tk.Frame(self, bg=self.theme_colors['bg'])
                main_frame.pack(fill="both", expand=True)
                
                info_frame = tk.Frame(main_frame, bg=self.theme_colors['secondary_bg'], relief="solid", bd=1)
                info_frame.pack(fill="x", padx=10, pady=5)
                
                if self.use_custom_dates.get():
                    info_text = f"📊 Top {limit} Products: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                else:
                    info_text = f"📊 Top {limit} Products: Last {days} days"
                
                if category:
                    info_text += f" | Category: {category}"
                
                info_text += f" | Sorted by: {sort_by.replace('_', ' ').title()}"
                
                tk.Label(info_frame, text=info_text,
                        font=("Segoe UI", 11, "bold"), bg=self.theme_colors['secondary_bg'], 
                        fg=self.theme_colors['fg']).pack(pady=8)
                
                chart_frame = tk.Frame(main_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
                chart_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                top_5 = df.head(limit)
                
                y_column_map = {
                    "quantity": "total_quantity_sold",
                    "revenue": "total_revenue",
                    "frequency": "sales_frequency"
                }
                y_col = y_column_map.get(sort_by, "total_quantity_sold")
                
                fig = self.create_chart(top_5, "bar", "product_name", y_col, figsize=(12, 6))
                if fig:
                    canvas = FigureCanvasTkAgg(fig, chart_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
                
                table_frame = tk.LabelFrame(main_frame, text="Top Selling Products Data", 
                                           font=("Segoe UI", 12, "bold"), bg=self.theme_colors['bg'],
                                           fg=self.theme_colors['fg'])
                table_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                self.create_data_table(df, table_frame)
            else:
                tk.Label(self, text="No product sales data available for the selected filters", 
                        font=("Segoe UI", 16), bg=self.theme_colors['bg'],
                        fg=self.theme_colors['fg']).pack(expand=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load product data: {str(e)}")
    
    def export_pdf(self):
        try:
            if self.use_custom_dates.get():
                df = self.analytics.get_top_selling_products(
                    int(self.limit_var.get()), int(self.period_var.get())
                )
            else:
                df = self.analytics.get_top_selling_products(
                    int(self.limit_var.get()), int(self.period_var.get())
                )
                
            if not df.empty:
                report_gen = ManagerReportGenerator()
                charts = {}
                top_5 = df.head(5)
                y_column_map = {
                    "quantity": "total_quantity_sold",
                    "revenue": "total_revenue", 
                    "frequency": "sales_frequency"
                }
                y_col = y_column_map.get(self.sort_by_var.get(), "total_quantity_sold")
                chart_buffer = report_gen.create_chart(top_5, 'bar', 'Top 5 Products by Sales', 'product_name', y_col)
                charts['Top Products Chart'] = chart_buffer
                
                data_sections = {"Top Selling Products": df}
                report_gen.generate_pdf_report("Top Selling Products Report", data_sections, charts)
            else:
                messagebox.showwarning("No Data", "No product sales data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")
    
    def export_excel(self):
        try:
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                df = self.analytics.get_top_selling_products(
                    int(self.limit_var.get()), 30
                )
            else:
                df = self.analytics.get_top_selling_products(
                    int(self.limit_var.get()), int(self.period_var.get())
                )
                
            if not df.empty:
                report_gen = ManagerReportGenerator()
                data_sections = {"Top Selling Products": df}
                report_gen.generate_excel_report("Top Selling Products Report", data_sections)
            else:
                messagebox.showwarning("No Data", "No product sales data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export Excel: {str(e)}")
    
    def refresh_data(self):
        self.load_data()


class InventoryUsage(DataDisplayFrame):
    def __init__(self, master):
        super().__init__(master, "Inventory Usage and Restock Insights")
        self.load_data()
    
    def load_data(self):
        df = self.analytics.get_inventory_usage_trends()
        
        if not df.empty:
            main_frame = tk.Frame(self, bg="#f0f0f0")
            main_frame.pack(fill="both", expand=True)
            
            stats_frame = tk.LabelFrame(main_frame, text="Inventory Summary", 
                                       font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
            stats_frame.pack(fill="x", padx=10, pady=5)
            
            low_stock = len(df[df['stock_status'] == 'Low Stock'])
            medium_stock = len(df[df['stock_status'] == 'Medium Stock'])
            high_stock = len(df[df['stock_status'] == 'High Stock'])
            
            stats_text = f"Low Stock: {low_stock} | Medium Stock: {medium_stock} | High Stock: {high_stock}"
            tk.Label(stats_frame, text=stats_text, font=("Segoe UI", 11), 
                    bg="#f0f0f0", fg="#e74c3c" if low_stock > 0 else "#27ae60").pack(pady=5)
            
            table_frame = tk.LabelFrame(main_frame, text="Inventory Details", 
                                       font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
            table_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            self.create_data_table(df, table_frame)
        else:
            tk.Label(self, text="No inventory data available", 
                    font=("Segoe UI", 16), bg="#f0f0f0").pack(expand=True)
    
    def export_pdf(self):
        try:
            df = self.analytics.get_inventory_usage_trends()
            if not df.empty:
                report_gen = ManagerReportGenerator()
                data_sections = {"Inventory Usage and Restock Insights": df}
                report_gen.generate_pdf_report("Inventory Usage Report", data_sections)
            else:
                messagebox.showwarning("No Data", "No inventory data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")
    
    def export_excel(self):
        try:
            df = self.analytics.get_inventory_usage_trends()
            if not df.empty:
                report_gen = ManagerReportGenerator()
                data_sections = {"Inventory Usage and Restock Insights": df}
                report_gen.generate_excel_report("Inventory Usage Report", data_sections)
            else:
                messagebox.showwarning("No Data", "No inventory data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export Excel: {str(e)}")


class SalesForecast(DataDisplayFrame):
    def __init__(self, master):
        super().__init__(master, "Sales Forecast")
        self.period_var = tk.StringVar(value="30")
        self.forecast_type_var = tk.StringVar(value="moving_average")
        self.forecast_days_var = tk.StringVar(value="7")
        self.use_custom_dates = tk.BooleanVar(value=False)
        self.start_date_entry = None
        self.end_date_entry = None
        self.create_controls()
        self.load_data()
    
    def create_controls(self):
        control_frame = tk.Frame(self, bg=self.theme_colors['bg'], relief="solid", bd=1)
        control_frame.pack(fill="x", padx=20, pady=5)
        
        period_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        period_frame.pack(side="left", padx=10, pady=10)
        
        tk.Label(period_frame, text="Historical Data:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        period_combo = ttk.Combobox(period_frame, textvariable=self.period_var, 
                                   values=["14", "30", "60"], width=10)
        period_combo.pack(pady=2)
        period_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        tk.Label(period_frame, text="days", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        forecast_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        forecast_frame.pack(side="left", padx=10, pady=10)
        
        tk.Label(forecast_frame, text="Forecast Method:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        forecast_combo = ttk.Combobox(forecast_frame, textvariable=self.forecast_type_var, 
                                     values=["moving_average", "exponential"], width=15)
        forecast_combo.pack(pady=2)
        forecast_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        forecast_days_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        forecast_days_frame.pack(side="left", padx=10, pady=10)
        
        tk.Label(forecast_days_frame, text="Forecast Period:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        forecast_days_combo = ttk.Combobox(forecast_days_frame, textvariable=self.forecast_days_var, 
                                          values=["3", "7", "14", "30"], width=10)
        forecast_days_combo.pack(pady=2)
        forecast_days_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        tk.Label(forecast_days_frame, text="days ahead", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        date_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        date_frame.pack(side="right", padx=10, pady=10)
        
        tk.Checkbutton(date_frame, text="Custom Historical Period", 
                      variable=self.use_custom_dates,
                      command=self.on_custom_date_toggle, bg=self.theme_colors['bg'],
                      fg=self.theme_colors['fg'], font=("Segoe UI", 10, "bold")).pack()
        
        date_controls = tk.Frame(date_frame, bg=self.theme_colors['bg'])
        date_controls.pack()
        
        tk.Label(date_controls, text="From:", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).grid(row=0, column=0, padx=2)
        
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
        self.start_date_entry.grid(row=0, column=1, padx=2)
        
        tk.Label(date_controls, text="To:", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).grid(row=0, column=2, padx=2)
        
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
        self.end_date_entry.grid(row=0, column=3, padx=2)
        
        tk.Button(date_controls, text="Apply", 
                 command=self.on_custom_date_apply, bg="#3498db", fg="white",
                 font=("Segoe UI", 8), relief="flat", padx=8).grid(row=0, column=4, padx=5)
        
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
            
            forecast_type = self.forecast_type_var.get()
            forecast_days = int(self.forecast_days_var.get())
            
            if start_date and end_date:
                df = self.analytics.get_sales_forecast_data(days)
            else:
                df = self.analytics.get_sales_forecast_data(days)
            
            if not df.empty and len(df) >= 7:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                if forecast_type == "moving_average":
                    window = min(7, len(df))
                    df['forecast'] = df['daily_revenue'].rolling(window=window).mean()
                elif forecast_type == "linear_trend":
                    df['day_num'] = range(len(df))
                    slope = (df['daily_revenue'].iloc[-1] - df['daily_revenue'].iloc[0]) / len(df)
                    df['forecast'] = df['daily_revenue'].iloc[0] + slope * df['day_num']
                elif forecast_type == "exponential":
                    alpha = 0.3
                    df['forecast'] = df['daily_revenue'].ewm(alpha=alpha).mean()
                
                main_frame = tk.Frame(self, bg=self.theme_colors['bg'])
                main_frame.pack(fill="both", expand=True)
                
                info_frame = tk.Frame(main_frame, bg=self.theme_colors['secondary_bg'], relief="solid", bd=1)
                info_frame.pack(fill="x", padx=10, pady=5)
                
                if self.use_custom_dates.get():
                    info_text = f"📊 Sales Forecast: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                else:
                    info_text = f"📊 Sales Forecast: {days} days historical data"
                
                info_text += f" | Method: {forecast_type.replace('_', ' ').title()} | Forecast: {forecast_days} days"
                
                tk.Label(info_frame, text=info_text,
                        font=("Segoe UI", 11, "bold"), bg=self.theme_colors['secondary_bg'], 
                        fg=self.theme_colors['fg']).pack(pady=8)
                
                chart_frame = tk.Frame(main_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
                chart_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                fig, ax = plt.subplots(figsize=(12, 6), facecolor=self.theme_colors['chart_bg'])
                
                window_size = min(7, len(df) // 2)
                df['moving_avg'] = df['daily_revenue'].rolling(window=window_size, min_periods=1).mean()
                
                if forecast_type == "moving_average":
                    df['forecast'] = df['moving_avg']
                elif forecast_type == "linear_trend":
                    x = np.arange(len(df))
                    y = df['daily_revenue'].values
                    z = np.polyfit(x, y, 1)
                    p = np.poly1d(z)
                    df['forecast'] = p(x)
                elif forecast_type == "exponential":
                    alpha = 0.3
                    df['forecast'] = df['daily_revenue'].ewm(alpha=alpha, adjust=False).mean()
                else:
                    df['forecast'] = df['moving_avg']
                
                ax.plot(df['date'], df['daily_revenue'], label='Actual Revenue', marker='o', linewidth=2, alpha=0.8, color='#3498db')
                ax.plot(df['date'], df['forecast'], label=f'{forecast_type.replace("_", " ").title()} Forecast', 
                       linestyle='--', linewidth=2, alpha=0.8, color='#27ae60')
                
                last_date = df['date'].iloc[-1]
                future_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
                
                if forecast_type == "moving_average":
                    recent_values = df['daily_revenue'].tail(window_size).values
                    recent_trend = np.mean(np.diff(recent_values)) if len(recent_values) > 1 else 0
                    base_value = df['forecast'].iloc[-1]
                    future_values = [base_value + recent_trend * (i+1) for i in range(forecast_days)]
                    
                elif forecast_type == "linear_trend":
                    x = np.arange(len(df))
                    y = df['daily_revenue'].values
                    z = np.polyfit(x, y, 1)
                    p = np.poly1d(z)
                    future_x = np.arange(len(df), len(df) + forecast_days)
                    future_values = p(future_x)
                    
                elif forecast_type == "exponential":
                    last_values = df['daily_revenue'].tail(10).values
                    if len(last_values) > 1:
                        recent_growth = np.mean(np.diff(last_values)) / np.mean(last_values[:-1])
                        recent_growth = max(-0.1, min(0.1, recent_growth))
                    else:
                        recent_growth = 0.01
                    
                    last_forecast = df['forecast'].iloc[-1]
                    future_values = []
                    current_value = last_forecast
                    for i in range(forecast_days):
                        current_value = current_value * (1 + recent_growth) + np.random.normal(0, current_value * 0.05)
                        future_values.append(max(0, current_value))
                
                np.random.seed(42)
                variability = np.std(df['daily_revenue']) * 0.1
                future_values = [max(0, val + np.random.normal(0, variability)) for val in future_values]
                
                ax.plot(future_dates, future_values, label='Future Forecast', 
                       linestyle=':', linewidth=3, alpha=0.7, color='#e74c3c', marker='s', markersize=4)
                
                ax.set_xlabel('Date')
                ax.set_ylabel('Daily Revenue ($)')
                ax.set_title(f'Sales Forecast - {forecast_type.replace("_", " ").title()} Method')
                ax.legend()
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                canvas = FigureCanvasTkAgg(fig, chart_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
                
                stats_frame = tk.LabelFrame(main_frame, text="Forecast Statistics", 
                                           font=("Segoe UI", 12, "bold"), bg=self.theme_colors['bg'],
                                           fg=self.theme_colors['fg'])
                stats_frame.pack(fill="x", padx=10, pady=5)
                
                avg_revenue = df['daily_revenue'].mean()
                forecast_avg = df['forecast'].iloc[-7:].mean() if len(df) >= 7 else df['forecast'].mean()
                trend = "Increasing" if forecast_avg > avg_revenue else "Decreasing"
                
                mae = abs(df['daily_revenue'] - df['forecast']).mean()
                accuracy = max(0, 100 - (mae / avg_revenue * 100)) if avg_revenue > 0 else 0
                
                future_avg = sum(future_values) / len(future_values) if future_values else 0
                future_trend = "Increasing" if future_avg > forecast_avg else "Decreasing"
                
                stats_text = (f"Historical Avg: ${avg_revenue:.2f} | "
                            f"Recent Trend: {trend} | "
                            f"Model Accuracy: {accuracy:.1f}% | "
                            f"Future Prediction: ${future_avg:.2f} ({future_trend})")
                
                tk.Label(stats_frame, text=stats_text, font=("Segoe UI", 10), 
                        bg=self.theme_colors['bg'], fg=self.theme_colors['fg']).pack(pady=8)
                
            else:
                tk.Label(self, text="Insufficient data for forecasting (need at least 7 days)", 
                        font=("Segoe UI", 16), bg=self.theme_colors['bg'],
                        fg=self.theme_colors['fg']).pack(expand=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load forecast data: {str(e)}")
    
    def export_pdf(self):
        try:

            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                df = self.analytics.get_sales_forecast_data(start_date=start_date, end_date=end_date)
            else:
                days = int(self.period_var.get())
                df = self.analytics.get_sales_forecast_data(days=days)
                
            if not df.empty:
                report_gen = ManagerReportGenerator()
                data_sections = {"Sales Forecast Data": df}
                report_gen.generate_pdf_report("Sales Forecast Report", data_sections)
            else:
                messagebox.showwarning("No Data", "No forecast data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")
    
    def export_excel(self):
        try:
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                df = self.analytics.get_sales_forecast_data(30)
            else:
                df = self.analytics.get_sales_forecast_data(
                    int(self.period_var.get())
                )
                
            if not df.empty:
                report_gen = ManagerReportGenerator()
                data_sections = {"Sales Forecast Data": df}
                report_gen.generate_excel_report("Sales Forecast Report", data_sections)
            else:
                messagebox.showwarning("No Data", "No forecast data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export Excel: {str(e)}")
    
    def refresh_data(self):
        self.load_data()


class ManagerPage(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.controller.title("Manager Page")

        self.sidebar_expand = False
        self.separators = []
        
        self.theme_colors = {
            'bg': '#f0f0f0', 'fg': '#333333', 'secondary_bg': '#ffffff',
            'accent': '#4a90e2', 'button_bg': '#e0e0e0', 'button_fg': '#333333',
            'entry_bg': '#ffffff', 'entry_fg': '#333333', 'sidebar_bg': '#2c3e50',
            'chart_bg': 'white', 'chart_colors': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#8B5A3C', '#006D77'],
            'grid_color': '#cccccc', 'text_color': 'black'
        }
        self.configure(bg=self.theme_colors['bg'])

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

        self.product_trends_button = tk.Button(
            self.sidebar, text="Product Sales Trends", bg="#2c3e50", fg="#ecf0f1", activebackground="#34495e",
            activeforeground="white", bd=0, font=("Segoe UI", 11), anchor="w", padx=15,
            command=self.show_product_trends)

        self.customer_traffic_button = tk.Button(
            self.sidebar, text="Customer Traffic Reports", bg="#2c3e50", fg="#ecf0f1", activebackground="#34495e",
            activeforeground="white", bd=0, font=("Segoe UI", 11), anchor="w", padx=15,
            command=self.show_customer_traffic)

        self.top_selling_button = tk.Button(
            self.sidebar, text="Top Selling Products", bg="#2c3e50", fg="#ecf0f1", activebackground="#34495e",
            activeforeground="white", bd=0, font=("Segoe UI", 11), anchor="w", padx=15,
            command=self.show_top_selling)

        self.inventory_usage_button = tk.Button(
            self.sidebar, text="Inventory Usage and Restock Insights", bg="#2c3e50", fg="#ecf0f1",
            activebackground="#34495e", activeforeground="white", bd=0, font=("Segoe UI", 11), anchor="w", padx=15,
            command=self.show_inventory_usage, wraplength=150, justify="left")

        self.promotion_effectiveness_button = tk.Button(
            self.sidebar, text="Promotion Effectiveness", bg="#2c3e50", fg="#ecf0f1", activebackground="#34495e",
            activeforeground="white", bd=0, font=("Segoe UI", 11), anchor="w", padx=15,
            command=self.show_promotion_effectiveness)

        self.sales_forecast_button = tk.Button(
            self.sidebar, text="Sales Forecast", bg="#2c3e50", fg="#ecf0f1", activebackground="#34495e",
            activeforeground="white", bd=0, font=("Segoe UI", 11), anchor="w", padx=15,
            command=self.show_sales_forecast)

        self.content = tk.Frame(self.container, bg=self.theme_colors['bg'])
        self.content.pack(side="left", fill="both", expand=True)

        self.bind_all("<Button-1>", self.click_outside)

        self.current_content = None
        
        self.show_welcome()

    def show_welcome(self):
        self.clear_content()
        
        welcome_frame = tk.Frame(self.content, bg=self.theme_colors['bg'])
        welcome_frame.pack(fill="both", expand=True)
        
        center_frame = tk.Frame(welcome_frame, bg=self.theme_colors['bg'])
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        current_user = self.controller.get_current_user()
        username = current_user.get('username', 'Manager') if current_user else 'Manager'
        
        welcome_label = tk.Label(center_frame, 
                                text=f"Welcome {username}",
                                font=("Segoe UI", 28, "bold"),
                                fg=self.theme_colors['fg'],
                                bg=self.theme_colors['bg'])
        welcome_label.pack(pady=20)
        
        subtitle_label = tk.Label(center_frame,
                                 text="LogicMart Analytics Dashboard",
                                 font=("Segoe UI", 16),
                                 fg=self.theme_colors['fg'],
                                 bg=self.theme_colors['bg'])
        subtitle_label.pack(pady=10)
        
        instructions_label = tk.Label(center_frame,
                                     text="Use the menu on the left to access different analytics and reports",
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
            self.customer_traffic_button.pack_forget()
            self.product_trends_button.pack_forget()
            self.top_selling_button.pack_forget()
            self.inventory_usage_button.pack_forget()
            self.promotion_effectiveness_button.pack_forget()
            self.sales_forecast_button.pack_forget()

            for sep in self.separators:
                sep.destroy()
            self.separators.clear()

        else:
            self.sidebar.config(width=200)
            self.toggle_button.config(text="<", anchor="e", font=("Segoe UI", 14, "bold"), padx=20,)
            self.logout_button.pack(side="bottom", fill="x", pady=(10, 20), padx=20)
            
            role_header = tk.Label(self.sidebar, text="MANAGER", 
                                  bg="#34495e", fg="#ecf0f1", font=("Segoe UI", 11, "bold"),
                                  anchor="center", pady=8)
            role_header.pack(fill="x", pady=(15, 10))
            self.separators.append(role_header)
            
            self.sales_trend_button.pack(fill="x", pady=(10, 0))
            self.separator(self.sidebar)
            self.customer_traffic_button.pack(fill="x", pady=(10, 0))
            self.separator(self.sidebar)
            self.product_trends_button.pack(fill="x", pady=(10, 0))
            self.separator(self.sidebar)
            self.top_selling_button.pack(fill="x", pady=(10, 0))
            self.separator(self.sidebar)
            self.inventory_usage_button.pack(fill="x", pady=(10, 0))
            self.separator(self.sidebar)
            self.promotion_effectiveness_button.pack(fill="x", pady=(10, 0))
            self.separator(self.sidebar)
            self.sales_forecast_button.pack(fill="x", pady=(10, 0))
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

    def show_product_trends(self):
        self.clear_content()
        self.current_content = ProductSalesTrends(self.content)
        self.current_content.pack(fill="both", expand=True)

    def show_customer_traffic(self):
        self.clear_content()
        self.current_content = CustomerTrafficAnalysis(self.content)
        self.current_content.pack(fill="both", expand=True)

    def show_top_selling(self):
        self.clear_content()
        self.current_content = TopSelling(self.content)
        self.current_content.pack(fill="both", expand=True)

    def show_inventory_usage(self):
        self.clear_content()
        self.current_content = InventoryUsage(self.content)
        self.current_content.pack(fill="both", expand=True)

    def show_promotion_effectiveness(self):
        self.clear_content()
        self.current_content = PromotionEffectiveness(self.content)
        self.current_content.pack(fill="both", expand=True)

    def show_sales_forecast(self):
        self.clear_content()
        self.current_content = SalesForecast(self.content)
        self.current_content.pack(fill="both", expand=True)

    def separator(self, parent):
        separator = tk.Frame(parent, height=1, bg="#bdc3c7")
        separator.pack(fill="x", padx=10, pady=(2, 5))
        self.separators.append(separator)


class ProductSalesTrends(DataDisplayFrame):
    def __init__(self, master):
        super().__init__(master, "Product Sales Trends Analysis")
        self.period_var = tk.StringVar(value="30")
        self.create_controls()
        self.load_data()
    
    def create_controls(self):
        control_frame = tk.Frame(self, bg=self.theme_colors['bg'])
        control_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(control_frame, text="Analysis Period:", 
                font=("Segoe UI", 10, "bold"), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack(side="left")
        
        period_combo = ttk.Combobox(control_frame, textvariable=self.period_var, 
                                   values=["7", "14", "30", "60", "90"], width=10)
        period_combo.pack(side="left", padx=10)
        period_combo.bind('<<ComboboxSelected>>', self.on_period_changed)
        
        tk.Label(control_frame, text="days", 
                font=("Segoe UI", 10), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack(side="left")
    
    def on_period_changed(self, event=None):
        self.load_data()
    
    def load_data(self):
        try:
            days = int(self.period_var.get())
            df = self.analytics.get_product_sales_trends(days=days, limit=10)
            
            for widget in self.winfo_children():
                if isinstance(widget, tk.Frame) and widget != self.winfo_children()[0] and widget != self.winfo_children()[1]:
                    widget.destroy()
            
            if not df.empty:
                main_frame = tk.Frame(self, bg=self.theme_colors['bg'])
                main_frame.pack(fill="both", expand=True)
                
                products = df['product_name'].unique()[:5]
                
                chart_frame = tk.Frame(main_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
                chart_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                fig, axes = plt.subplots(2, 1, figsize=(14, 10), facecolor='white')
                
                for i, product in enumerate(products):
                    product_data = df[df['product_name'] == product].copy()
                    if not product_data.empty:
                        product_data = product_data.sort_values('sale_date')
                        axes[0].plot(product_data['sale_date'], product_data['daily_quantity'], 
                                   marker='o', label=product, linewidth=2, markersize=4)
                
                axes[0].set_title('Daily Quantity Sold - Top Products')
                axes[0].set_xlabel('Date')
                axes[0].set_ylabel('Quantity Sold')
                axes[0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                axes[0].grid(True, alpha=0.3)
                axes[0].tick_params(axis='x', rotation=45)
                
                for i, product in enumerate(products):
                    product_data = df[df['product_name'] == product].copy()
                    if not product_data.empty:
                        product_data = product_data.sort_values('sale_date')
                        axes[1].plot(product_data['sale_date'], product_data['daily_revenue'], 
                                   marker='s', label=product, linewidth=2, markersize=4)
                
                axes[1].set_title('Daily Revenue - Top Products')
                axes[1].set_xlabel('Date')
                axes[1].set_ylabel('Revenue ($)')
                axes[1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                axes[1].grid(True, alpha=0.3)
                axes[1].tick_params(axis='x', rotation=45)
                
                plt.tight_layout()
                
                canvas = FigureCanvasTkAgg(fig, chart_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
                
                summary_frame = tk.LabelFrame(main_frame, text="Product Performance Summary", 
                                            font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
                summary_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                summary_df = df.groupby(['product_name', 'category']).agg({
                    'total_quantity': 'first',
                    'avg_daily_quantity': 'first',
                    'days_with_sales': 'first'
                }).reset_index()
                
                self.create_data_table(summary_df, summary_frame)
            else:
                tk.Label(self, text="No sales data available for the selected period", 
                        font=("Segoe UI", 16), bg="#f0f0f0").pack(expand=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load sales trends data: {str(e)}")
    
    def export_pdf(self):
        try:
            days = int(self.period_var.get())
            df = self.analytics.get_product_sales_trends(days=days, limit=10)
            if not df.empty:
                report_gen = ManagerReportGenerator()
                report_gen.generate_comprehensive_report({"product_trends": df}, 'pdf')
                messagebox.showinfo("Export Success", "Product sales trends exported to PDF successfully!")
            else:
                messagebox.showwarning("No Data", "No data available to export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def export_excel(self):
        try:
            days = int(self.period_var.get())
            df = self.analytics.get_product_sales_trends(days=days, limit=10)
            if not df.empty:
                report_gen = ManagerReportGenerator()
                report_gen.generate_comprehensive_report({"product_trends": df}, 'excel')
                messagebox.showinfo("Export Success", "Product sales trends exported to Excel successfully!")
            else:
                messagebox.showwarning("No Data", "No data available to export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def refresh_data(self):
        self.load_data()


class CustomerTrafficAnalysis(DataDisplayFrame):
    def __init__(self, master):
        super().__init__(master, "Customer Traffic Analysis")
        self.period_var = tk.StringVar(value="7")
        self.use_custom_dates = tk.BooleanVar(value=False)
        self.data_history = {}
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
                                values=["7", "14", "30", "60", "90"], width=10, state="readonly")
        period_combo.pack(pady=2)
        period_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)

        tk.Label(period_frame, text="Days", 
                font=("Segoe UI", 9), bg=self.theme_colors['bg'], 
                fg=self.theme_colors['fg']).pack()
        
        date_frame = tk.Frame(control_frame, bg=self.theme_colors['bg'])
        date_frame.pack(side="left", padx=20, pady=10)
        
        tk.Checkbutton(date_frame, text="Custom Date Range", 
                      variable=self.use_custom_dates,
                      command=self.on_custom_date_toggle, bg=self.theme_colors['bg'],
                      fg=self.theme_colors['fg'], font=("Segoe UI", 10, "bold")).pack()
        
        date_controls = tk.Frame(date_frame, bg=self.theme_colors['bg'])
        date_controls.pack()
        
        tk.Label(date_controls, text="From:", 
                font=("Segoe UI", 9), bg="#f0f0f0").grid(row=0, column=0, padx=5)
        
        today = datetime.now()
        default_start = today - timedelta(days=7)
        self.start_date_entry = DateEntry(
            date_controls, width=12, background='darkblue', foreground='white',
            borderwidth=2, date_pattern='yyyy-mm-dd', font=("Segoe UI", 9),
            year=default_start.year, month=default_start.month, day=default_start.day
        )
        self.start_date_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(date_controls, text="To:", 
                font=("Segoe UI", 9), bg="#f0f0f0").grid(row=0, column=2, padx=5)
        
        self.end_date_entry = DateEntry(
            date_controls, width=12, background='darkblue', foreground='white',
            borderwidth=2, date_pattern='yyyy-mm-dd', font=("Segoe UI", 9),
            year=today.year, month=today.month, day=today.day
        )
        self.end_date_entry.grid(row=0, column=3, padx=5)
        
        tk.Button(date_controls, text="Apply", 
                 command=self.on_custom_date_apply, bg="#3498db", fg="white",
                 font=("Segoe UI", 9), relief="flat", padx=10).grid(row=0, column=4, padx=10)
        
        self.toggle_date_controls(False)
        
        history_frame = tk.Frame(control_frame, bg="#f0f0f0")
        history_frame.pack(side="right", padx=10, pady=10)
        
        tk.Button(history_frame, text="📊 Add to Chart", 
                 command=self.add_to_history, bg="#27ae60", fg="white",
                 font=("Segoe UI", 9), relief="flat", padx=10).pack(side="top")
        
        tk.Button(history_frame, text="🗑️ Clear Charts", 
                 command=self.clear_history, bg="#e74c3c", fg="white",
                 font=("Segoe UI", 9), relief="flat", padx=10).pack(side="top", pady=(5,0))
    
    def toggle_date_controls(self, enabled):
        state = "normal" if enabled else "disabled"
        self.start_date_entry.config(state=state)
        self.end_date_entry.config(state=state)
    
    def on_custom_date_toggle(self):
        enabled = self.use_custom_dates.get()
        self.toggle_date_controls(enabled)
        if not enabled:
            self.load_data()
    
    def on_custom_date_apply(self):
        if self.use_custom_dates.get():
            self.load_data()
    
    def on_filter_changed(self, event=None):
        if not self.use_custom_dates.get():
            self.load_data()
    
    def add_to_history(self):
        start_date, end_date = None, None
        if self.use_custom_dates.get():
            start_date = datetime.combine(self.start_date_entry.get_date(), datetime.min.time())
            end_date = datetime.combine(self.end_date_entry.get_date(), datetime.max.time())
            period_type = 'day'
        else:
            days = int(self.period_var.get())
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            if days <= 2:
                period_type = 'hour'
            elif days <= 90:
                period_type = 'day'
            else:
                period_type = 'week'
        if hasattr(self, 'current_df') and not self.current_df.empty:
            if self.use_custom_dates.get():
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                label = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            else:
                period_labels = {"hour": "Last 24 Hours", "day": "Last 7 Days", "week": "Last 4 Weeks", "month": "Last 8 Weeks"}
                label = f"{period_labels.get(period_type)} ({datetime.now().strftime('%H:%M')})"
            
            key = f"{label}_{len(self.data_history)}"
            self.data_history[key] = {'data': self.current_df.copy(), 'label': label, 'period_type': period_type}
            self.load_data()
            messagebox.showinfo("Added to Chart", f"Data layer added: {label}")
    
    def clear_history(self):
        self.data_history.clear()
        self.load_data()
        messagebox.showinfo("Charts Cleared", "All chart layers have been removed")
    
    def load_data(self):
        try:
            start_date, end_date = None, None
            if self.use_custom_dates.get():
                start_date = datetime.combine(self.start_date_entry.get_date(), datetime.min.time())
                end_date = datetime.combine(self.end_date_entry.get_date(), datetime.max.time())
                period_type = 'day' # Default to day view for custom ranges
            else:
                days = int(self.period_var.get())
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                period_type = 'day' if days <= 60 else 'week' # Use week view for longer periods

            df = self.analytics.get_customer_traffic_analysis(period_type, start_date, end_date)
            self.current_df = df

            for widget in self.winfo_children():
                if isinstance(widget, tk.Frame) and widget not in [self.winfo_children()[0], self.winfo_children()[1]]:
                    widget.destroy()

            if not df.empty:
                self.display_traffic_data(df, period_type, start_date, end_date)
            else:
                self.display_no_data_message(period_type, start_date, end_date)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load traffic data: {str(e)}")

    def display_traffic_data(self, df, period_type, start_date, end_date):
        main_frame = tk.Frame(self, bg=self.theme_colors['bg'])
        main_frame.pack(fill="both", expand=True)
        
        info_frame = tk.Frame(main_frame, bg=self.theme_colors['secondary_bg'], relief="solid", bd=1)
        info_frame.pack(fill="x", padx=10, pady=5)

        if self.use_custom_dates.get() and start_date and end_date:
            info_text = f"📊 Custom Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        else:
            days = int(self.period_var.get())
            info_text = f"📊 Traffic Analysis for Last {days} Days"

        if len(self.data_history) > 0:
            info_text += f" | {len(self.data_history)} comparison layers active"

        tk.Label(info_frame, text=info_text,
                font=("Segoe UI", 11, "bold"), bg=self.theme_colors['secondary_bg'], 
                fg=self.theme_colors['fg']).pack(pady=8)
        
        chart_frame = tk.Frame(main_frame, bg=self.theme_colors['chart_bg'], relief="solid", bd=1)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        fig, axes = plt.subplots(2, 2, figsize=(18, 12), facecolor=self.theme_colors['chart_bg'])
        fig.suptitle(f'Customer Traffic Analysis - {period_type.title()} View', fontsize=15, fontweight='bold', color=self.theme_colors['text_color'], y=0.97)
        plt.subplots_adjust(left=0.1, bottom=0.15, right=0.95, top=0.88, wspace=0.35, hspace=0.45)
        
        self.plot_traffic_data(axes, df, "Current Period", self.theme_colors['chart_colors'][0], alpha=1.0)
        
        for i, (key, hist_data) in enumerate(self.data_history.items()):
            if hist_data['period_type'] == period_type:
                self.plot_traffic_data(axes, hist_data['data'], hist_data['label'], self.theme_colors['chart_colors'][(i+1) % len(self.theme_colors['chart_colors'])], alpha=0.6)
        
        chart_titles = ['Transaction Volume', 'Items Sold', 'Revenue Performance', 'Avg Transaction Value']
        for i, ax in enumerate(axes.flat):
            ax.grid(True, alpha=0.3, color=self.theme_colors['grid_color'])
            ax.legend(loc='upper right', framealpha=0.9, facecolor=self.theme_colors['secondary_bg'], edgecolor=self.theme_colors['text_color'], fontsize=8, bbox_to_anchor=(0.98, 0.98))
            if not df.empty:
                periods = sorted(df['time_period'].unique())
                labels = [df[df['time_period'] == p]['period_label'].iloc[0] for p in periods]
                display_periods, display_labels = (periods[::len(periods)//5], [labels[periods.index(p)] for p in periods[::len(periods)//5]]) if len(periods) > 10 else (periods, labels)
                ax.set_xticks(display_periods)
                ax.set_xticklabels(display_labels, rotation=30, ha='right')
            ax.tick_params(axis='y', labelsize=8)
            if i in [2, 3]: ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            ax.set_title(chart_titles[i], fontsize=11, fontweight='bold', pad=12, color=self.theme_colors['text_color'])

        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        stats_frame = tk.LabelFrame(main_frame, text="Traffic Summary", font=("Segoe UI", 12, "bold"), bg=self.theme_colors['bg'], fg=self.theme_colors['fg'])
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        total_transactions, total_items, total_revenue, avg_transaction = df['transaction_count'].sum(), df['items_sold'].sum(), df['total_revenue'].sum(), df['avg_transaction_value'].mean()
        stats_text = f"Total Transactions: {total_transactions:,} | Items Sold: {int(total_items):,} | Total Revenue: ${total_revenue:,.2f} | Avg Transaction: ${avg_transaction:.2f}"
        tk.Label(stats_frame, text=stats_text, font=("Segoe UI", 10), bg=self.theme_colors['bg'], fg=self.theme_colors['fg']).pack(pady=8)

    def display_no_data_message(self, period_type, start_date, end_date):
        no_data_frame = tk.Frame(self, bg=self.theme_colors['bg'])
        no_data_frame.pack(fill="both", expand=True)
        center_frame = tk.Frame(no_data_frame, bg=self.theme_colors['bg'])
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(center_frame, text="📊 No Customer Traffic Data", font=("Segoe UI", 20, "bold"), bg=self.theme_colors['bg'], fg=self.theme_colors['fg']).pack(pady=10)
        tk.Label(center_frame, text=f"No sales transactions found for the selected {period_type} period.", font=("Segoe UI", 12), bg=self.theme_colors['bg'], fg=self.theme_colors['fg']).pack(pady=5)
        if self.use_custom_dates.get() and start_date and end_date:
            tk.Label(center_frame, text=f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", font=("Segoe UI", 10), bg=self.theme_colors['bg'], fg="#666666").pack(pady=2)
        tk.Label(center_frame, text="Try selecting a different time period or date range.", font=("Segoe UI", 10), bg=self.theme_colors['bg'], fg=self.theme_colors['fg']).pack(pady=2)

    def plot_traffic_data(self, axes, df, label, color, alpha=1.0, linewidth=2):
        if df.empty: return
        try:
            df_sorted = df.sort_values('time_period')
            axes[0, 0].plot(df_sorted['time_period'], df_sorted['transaction_count'], label=label, color=color, alpha=alpha, linewidth=linewidth, marker='o', markersize=4)
            axes[0, 0].set_ylabel('Transaction Count')
            axes[0, 1].plot(df_sorted['time_period'], df_sorted['items_sold'], label=label, color=color, alpha=alpha, linewidth=linewidth, marker='s', markersize=4)
            axes[0, 1].set_ylabel('Items Sold')
            axes[1, 0].plot(df_sorted['time_period'], df_sorted['total_revenue'], label=label, color=color, alpha=alpha, linewidth=linewidth, marker='^', markersize=4)
            axes[1, 0].set_ylabel('Revenue ($)')
            axes[1, 1].plot(df_sorted['time_period'], df_sorted['avg_transaction_value'], label=label, color=color, alpha=alpha, linewidth=linewidth, marker='d', markersize=4)
            axes[1, 1].set_ylabel('Avg Transaction ($)')
        except Exception as e:
            print(f"Error plotting traffic data: {e}")
    
    def export_pdf(self):
        try:
            start_date, end_date = None, None
            if self.use_custom_dates.get():
                start_date = datetime.combine(self.start_date_entry.get_date(), datetime.min.time())
                end_date = datetime.combine(self.end_date_entry.get_date(), datetime.max.time())
                period_type = 'day'
            else:
                days = int(self.period_var.get())
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)

                if days <= 2:
                    period_type = 'hour'
                elif days <= 90:
                    period_type = 'day'
                else:
                    period_type = 'week'
            start_date, end_date = None, None
            if self.use_custom_dates.get():
                start_date = datetime.combine(self.start_date_entry.get_date(), datetime.min.time())
                end_date = datetime.combine(self.end_date_entry.get_date(), datetime.max.time())
            
            df = self.analytics.get_customer_traffic_analysis(period_type, start_date, end_date)
            if not df.empty:
                report_gen = ManagerReportGenerator()
                report_gen.generate_comprehensive_report({"peak_hours": df}, 'pdf')
                messagebox.showinfo("Export Success", "Customer traffic analysis exported to PDF successfully!")
            else:
                messagebox.showwarning("No Data", "No data available to export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def export_excel(self):
        try:
            period_type = self.period_type_var.get()
            start_date, end_date = None, None
            if self.use_custom_dates.get():
                start_date = datetime.combine(self.start_date_entry.get_date(), datetime.min.time())
                end_date = datetime.combine(self.end_date_entry.get_date(), datetime.max.time())
            
            df = self.analytics.get_customer_traffic_analysis(period_type, start_date, end_date)
            if not df.empty:
                report_gen = ManagerReportGenerator()
                report_gen.generate_comprehensive_report({"peak_hours": df}, 'excel')
                messagebox.showinfo("Export Success", "Customer traffic analysis exported to Excel successfully!")
            else:
                messagebox.showwarning("No Data", "No data available to export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def refresh_data(self):
        self.load_data()


class PromotionEffectiveness(DataDisplayFrame):
    def __init__(self, master):
        super().__init__(master, "Promotion Effectiveness Analysis")
        self.period_var = tk.StringVar(value="30")
        self.promotion_type_var = tk.StringVar(value="all")
        self.status_var = tk.StringVar(value="all")
        self.start_date_var = tk.StringVar()
        self.end_date_var = tk.StringVar()
        self.setup_controls()
        self.load_data()
    
    def setup_controls(self):
        self.control_frame = tk.LabelFrame(self, text="Filter Controls", font=("Segoe UI", 12, "bold"), bg="#e8f4f8", fg="#2c3e50", relief="raised", bd=2)
        self.control_frame.pack(fill="x", padx=10, pady=5)
        
        row1_frame = tk.Frame(self.control_frame, bg="#e8f4f8")
        row1_frame.pack(fill="x", pady=5, padx=10)
        
        tk.Label(row1_frame, text="Time Period:", font=("Segoe UI", 10, "bold"), bg="#e8f4f8").pack(side="left", padx=(0, 5))
        
        period_combo = ttk.Combobox(row1_frame, textvariable=self.period_var, width=12, values=["7", "30", "90"], state="readonly")
        period_combo.pack(side="left", padx=(0, 15))
        period_combo.bind("<<ComboboxSelected>>", self.on_filter_change)
        tk.Label(row1_frame, text="Days", font=("Segoe UI", 9, "bold"), bg="#e8f4f8").pack(side="left", padx=(0, 5))
        
        tk.Label(row1_frame, text="Type:", font=("Segoe UI", 10, "bold"), bg="#e8f4f8").pack(side="left", padx=(0, 5))
        
        type_combo = ttk.Combobox(row1_frame, textvariable=self.promotion_type_var, width=12, values=["all", "discount", "bogo", "loyalty"], state="readonly")
        type_combo.pack(side="left", padx=(0, 15))
        type_combo.bind("<<ComboboxSelected>>", self.on_filter_change)
        
        tk.Label(row1_frame, text="Status:", font=("Segoe UI", 10, "bold"), bg="#e8f4f8").pack(side="left", padx=(0, 5))
        
        status_combo = ttk.Combobox(row1_frame, textvariable=self.status_var, width=12, values=["all", "active", "expired", "upcoming"], state="readonly")
        status_combo.pack(side="left", padx=(0, 15))
        status_combo.bind("<<ComboboxSelected>>", self.on_filter_change)
        
        refresh_btn = tk.Button(row1_frame, text="🔄 Refresh", command=self.load_data, bg="#3498db", fg="white", font=("Segoe UI", 9, "bold"), relief="raised", bd=2)
        refresh_btn.pack(side="right", padx=(10, 0))
        
        row2_frame = tk.Frame(self.control_frame, bg="#e8f4f8")
        row2_frame.pack(fill="x", pady=5, padx=10)
        
        self.date_frame = tk.Frame(row2_frame, bg="#e8f4f8")
        self.date_frame.pack(side="left", padx=(15, 0))
        
        tk.Label(self.date_frame, text="From:", font=("Segoe UI", 9, "bold"), bg="#e8f4f8").pack(side="left")
        
        self.start_date_picker = DateEntry(self.date_frame, width=10, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.start_date_picker.pack(side="left", padx=(5, 10))
        
        tk.Label(self.date_frame, text="To:", font=("Segoe UI", 9, "bold"), bg="#e8f4f8").pack(side="left")
        
        self.end_date_picker = DateEntry(self.date_frame, width=10, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.end_date_picker.pack(side="left", padx=5)
        
        self.date_frame.pack_forget()
    
    def on_filter_change(self, event=None):
        if self.period_var.get() == "custom":
            self.date_frame.pack(side="left", padx=(15, 0))
        else:
            self.date_frame.pack_forget()
        self.load_data()
    
    def load_data(self):
        try:
            for widget in self.winfo_children():
                if widget != self.control_frame:
                    widget.destroy()

            period_str = self.period_var.get()
            promotion_type = self.promotion_type_var.get() if self.promotion_type_var.get() != "all" else None
            status = self.status_var.get() if self.status_var.get() != "all" else None

            days = 30
            start_date = None
            end_date = None

            if period_str == "Custom":
                start_date = self.start_date_picker.get_date()
                end_date = self.end_date_picker.get_date()
            else:
                days = int(period_str)

            df = self.analytics.get_promotion_effectiveness(days=days, promotion_type=promotion_type, status=status, start_date=start_date, end_date=end_date)

            if not df.empty:
                self.display_promotion_data(df)
            else:
                tk.Label(self, text="No promotion data available for the selected filters.", font=("Segoe UI", 16), bg="#f0f0f0").pack(expand=True)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load promotion data: {str(e)}")

    def display_promotion_data(self, df):
        separator = tk.Frame(self, height=2, bg="#34495e")
        separator.pack(fill="x", padx=20, pady=5)

        main_frame = tk.Frame(self, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        metrics_frame = tk.Frame(main_frame, bg="#f0f0f0")
        metrics_frame.pack(fill="x", pady=(0, 10))

        total_promotions, active_promotions = len(df), df['is_active'].sum()
        total_revenue, total_transactions = df['total_revenue'].sum(), df['transactions_count'].sum()
        avg_discount = df[df['discount_percentage'] > 0]['discount_percentage'].mean() if not df[df['discount_percentage'] > 0].empty else 0
        
        metric_cards = [
            ("Total Promotions", total_promotions, "#34495e"),
            ("Active Promotions", active_promotions, "#27ae60"),
            ("Total Revenue", f"${total_revenue:,.2f}", "#e74c3c"),
            ("Avg Discount", f"{avg_discount:.1f}%", "#f39c12"),
            ("Total Transactions", int(total_transactions), "#8e44ad")
        ]

        for title, value, color in metric_cards:
            card = tk.Frame(metrics_frame, bg=color, relief="raised", bd=2)
            card.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            tk.Label(card, text=str(value), font=("Segoe UI", 16, "bold"), bg=color, fg="white").pack(pady=(10, 5))
            tk.Label(card, text=title, font=("Segoe UI", 10), bg=color, fg="white").pack(pady=(0, 10))

        chart_frame = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
        chart_frame.pack(fill="both", expand=True, pady=(0, 10))

        fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor='white')

        top_promos = df.nlargest(8, 'total_revenue')
        axes[0].bar(top_promos['promotion_name'], top_promos['total_revenue'], color='#3498db', alpha=0.8)
        axes[0].set_title('Revenue by Promotion', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('Revenue ($)')
        axes[0].tick_params(axis='x', rotation=45)

        promo_types = df['promotion_type'].value_counts()
        axes[1].pie(promo_types.values, labels=promo_types.index, autopct='%1.1f%%', startangle=90)
        axes[1].set_title('Promotion Types Distribution', fontsize=12, fontweight='bold')

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        table_frame = tk.LabelFrame(main_frame, text="Promotion Details", font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
        table_frame.pack(fill="both", expand=True)

        display_cols = ['promotion_name', 'promotion_type', 'start_date', 'end_date', 'total_revenue', 'transactions_count']
        self.create_data_table(df[display_cols], table_frame)
    
    def export_pdf(self):
        try:
            period = self.period_var.get()
            promotion_type = self.promotion_type_var.get() if self.promotion_type_var.get() != "all" else None
            status = self.status_var.get() if self.status_var.get() != "all" else None
            
            if period == "Custom":
                start_date = self.start_date_picker.get_date()
                end_date = self.end_date_picker.get_date()
                df = self.analytics.get_promotion_effectiveness(start_date=start_date, end_date=end_date, promotion_type=promotion_type, status=status)
            else:
                days = int(period)
                df = self.analytics.get_promotion_effectiveness(days=days, promotion_type=promotion_type, status=status)
            
            if not df.empty:
                report_gen = ManagerReportGenerator()
                data_sections = {"Promotion Effectiveness": df}
                report_gen.generate_pdf_report("Promotion Effectiveness Report", data_sections)
                messagebox.showinfo("Export Success", "Promotion effectiveness exported to PDF successfully!")
            else:
                messagebox.showwarning("No Data", "No data available to export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def export_excel(self):
        try:
            period = self.period_var.get()
            promotion_type = self.promotion_type_var.get() if self.promotion_type_var.get() != "all" else None
            status = self.status_var.get() if self.status_var.get() != "all" else None
            
            if period == "custom":
                start_date = self.start_date_picker.get_date()
                end_date = self.end_date_picker.get_date()
                df = self.analytics.get_promotion_effectiveness(start_date=start_date, end_date=end_date, promotion_type=promotion_type, status=status)
            else:
                days = int(period.split('_')[0])
                df = self.analytics.get_promotion_effectiveness(days=days, promotion_type=promotion_type, status=status)
            
            if not df.empty:
                report_gen = ManagerReportGenerator()
                data_sections = {"Promotion Effectiveness": df}
                report_gen.generate_excel_report("Promotion Effectiveness Report", data_sections)
                messagebox.showinfo("Export Success", "Promotion effectiveness exported to Excel successfully!")
            else:
                messagebox.showwarning("No Data", "No data available to export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def refresh_data(self):
        self.load_data()
