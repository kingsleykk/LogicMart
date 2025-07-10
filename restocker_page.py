import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from analytics_engine import RestockerAnalytics
import seaborn as sns

# Set matplotlib style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class RestockerDataFrame(tk.Frame):
    """Base class for restocker analytics displays"""
    
    def __init__(self, master, title):
        super().__init__(master, bg="#f0f0f0")
        self.title = title
        self.analytics = RestockerAnalytics()
        self.create_header()
        
    def create_header(self):
        """Create header with title and action buttons"""
        header_frame = tk.Frame(self, bg="#f0f0f0")
        header_frame.pack(fill="x", padx=20, pady=10)
        
        # Title
        title_label = tk.Label(header_frame, text=self.title, 
                              font=("Segoe UI", 18, "bold"), 
                              bg="#f0f0f0", fg="#2c3e50")
        title_label.pack(side="left")
        
        # Action buttons
        action_frame = tk.Frame(header_frame, bg="#f0f0f0")
        action_frame.pack(side="right")
        
        tk.Button(action_frame, text="📊 Export Report", 
                 command=self.export_report, bg="#3498db", fg="white",
                 font=("Segoe UI", 9), relief="flat", padx=10).pack(side="right", padx=5)
        
        tk.Button(action_frame, text="🔄 Refresh", 
                 command=self.refresh_data, bg="#e74c3c", fg="white",
                 font=("Segoe UI", 9), relief="flat", padx=10).pack(side="right", padx=5)
    
    def refresh_data(self):
        """Refresh the data display - to be implemented by subclasses"""
        # Clear current content
        for widget in self.winfo_children():
            if widget != self.winfo_children()[0]:  # Keep header
                widget.destroy()
        
        # Reload data
        self.load_data()
    
    def create_data_table(self, df, parent_frame):
        """Create a scrollable data table"""
        if df.empty:
            tk.Label(parent_frame, text="No data available", 
                    font=("Segoe UI", 12), bg="#f0f0f0").pack(pady=20)
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
        
        h_scrollbar = ttk.Scrollbar(parent_frame, orient="horizontal", command=tree.xview)
        h_scrollbar.pack(side="bottom", fill="x")
        tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Configure columns
        tree["columns"] = list(df.columns)
        tree["show"] = "headings"
        
        for col in df.columns:
            tree.heading(col, text=col.replace('_', ' ').title())
            tree.column(col, width=120, anchor="center")
        
        # Insert data with color coding for stock status
        for index, row in df.iterrows():
            values = [str(val)[:50] + "..." if len(str(val)) > 50 else str(val) for val in row]
            item_id = tree.insert("", "end", values=values)
            
            # Color code based on stock status if available
            if 'stock_status' in df.columns:
                status = row['stock_status']
                if status == 'Out of Stock':
                    tree.set(item_id, 'stock_status', '🔴 Out of Stock')
                elif status == 'Critical':
                    tree.set(item_id, 'stock_status', '🟠 Critical')
                elif status == 'Low':
                    tree.set(item_id, 'stock_status', '🟡 Low')
        
        return tree
    
    def export_report(self):
        messagebox.showinfo("Export", "Report export - override in child class")
    
    def refresh_data(self):
        messagebox.showinfo("Refresh", "Data refreshed!")


class LowStock(RestockerDataFrame):
    def __init__(self, master):
        super().__init__(master, "Low Stock Product Reports")
        self.load_data()
    
    def load_data(self):
        """Load and display low stock data"""
        try:
            df = self.analytics.get_low_stock_products()
            
            if not df.empty:
                main_frame = tk.Frame(self, bg="#f0f0f0")
                main_frame.pack(fill="both", expand=True)
                
                # Alert summary frame
                alert_frame = tk.Frame(main_frame, bg="#f8d7da", relief="solid", bd=1)
                alert_frame.pack(fill="x", padx=10, pady=5)
                
                # Count alerts by severity
                out_of_stock = len(df[df['stock_status'] == 'Out of Stock'])
                critical = len(df[df['stock_status'] == 'Critical'])
                low = len(df[df['stock_status'] == 'Low'])
                
                alert_text = f"🚨 INVENTORY ALERTS: {out_of_stock} Out of Stock | {critical} Critical | {low} Low Stock"
                tk.Label(alert_frame, text=alert_text, font=("Segoe UI", 12, "bold"), 
                        bg="#f8d7da", fg="#721c24").pack(pady=10)
                
                # Data table
                table_frame = tk.LabelFrame(main_frame, text="Low Stock Products", 
                                           font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
                table_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                self.create_data_table(df, table_frame)
                
                # Reorder suggestions
                if not df.empty:
                    suggestion_frame = tk.LabelFrame(main_frame, text="Reorder Suggestions", 
                                                   font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
                    suggestion_frame.pack(fill="x", padx=10, pady=5)
                    
                    urgent_items = df[df['stock_status'].isin(['Out of Stock', 'Critical'])].head(3)
                    if not urgent_items.empty:
                        for _, item in urgent_items.iterrows():
                            suggestion_text = f"📦 {item['product_name']} - Current: {item['current_stock']}, Reorder Level: {item['reorder_level']}"
                            tk.Label(suggestion_frame, text=suggestion_text, 
                                    font=("Segoe UI", 10), bg="#f0f0f0").pack(anchor="w", padx=10, pady=2)
            else:
                # No low stock items - good news!
                success_frame = tk.Frame(self, bg="#d4edda", relief="solid", bd=1)
                success_frame.pack(fill="both", expand=True, padx=20, pady=50)
                
                tk.Label(success_frame, text="✅ All Products Well Stocked!", 
                        font=("Segoe UI", 20, "bold"), bg="#d4edda", fg="#155724").pack(pady=30)
                tk.Label(success_frame, text="No products require immediate restocking", 
                        font=("Segoe UI", 14), bg="#d4edda", fg="#155724").pack()
        except Exception as e:
            print(f"Error loading low stock data: {e}")
            # Show error frame
            error_frame = tk.Frame(self, bg="#f8d7da", relief="solid", bd=1)
            error_frame.pack(fill="both", expand=True, padx=20, pady=50)
            
            tk.Label(error_frame, text="⚠️ Connection Error", 
                    font=("Segoe UI", 20, "bold"), bg="#f8d7da", fg="#721c24").pack(pady=20)
            tk.Label(error_frame, text="Unable to load inventory data. Please check your connection and try again.", 
                    font=("Segoe UI", 12), bg="#f8d7da", fg="#721c24").pack(pady=10)
            
            retry_button = tk.Button(error_frame, text="🔄 Retry", 
                                   command=self.refresh_data, bg="#dc3545", fg="white",
                                   font=("Segoe UI", 11), relief="flat", padx=20)
            retry_button.pack(pady=10)

    def export_report(self):
        """Export low stock report"""
        try:
            df = self.analytics.get_low_stock_products()
            if not df.empty:
                from report_generator import RestockerReportGenerator
                report_gen = RestockerReportGenerator()
                report_gen.generate_inventory_report({"low_stock": df}, 'pdf')
            else:
                messagebox.showinfo("No Issues", "No low stock products to export - all items are well stocked!")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report: {str(e)}")


class InventoryTrends(RestockerDataFrame):
    def __init__(self, master):
        super().__init__(master, "Inventory Movement Trends")
        self.load_data()
    
    def load_data(self):
        """Load and display inventory trends"""
        try:
            df = self.analytics.get_inventory_movement_trends(30)
            
            if not df.empty:
                main_frame = tk.Frame(self, bg="#f0f0f0")
                main_frame.pack(fill="both", expand=True)
                
                # Chart frame
                chart_frame = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
                chart_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                # Create movement trends chart
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), facecolor='white')
                
                # Outbound by category
                ax1.bar(df['category'], df['total_outbound'], color='#e74c3c', alpha=0.8)
                ax1.set_title('Products Sold by Category')
                ax1.set_xlabel('Category')
                ax1.set_ylabel('Total Units Sold')
                ax1.tick_params(axis='x', rotation=45)
                
                # Inbound vs Outbound
                x_pos = range(len(df))
                width = 0.35
                ax2.bar([p - width/2 for p in x_pos], df['total_inbound'], width, 
                       label='Inbound', color='#27ae60', alpha=0.8)
                ax2.bar([p + width/2 for p in x_pos], df['total_outbound'], width, 
                       label='Outbound', color='#e74c3c', alpha=0.8)
                ax2.set_title('Inventory Flow by Category')
                ax2.set_xlabel('Category')
                ax2.set_ylabel('Units')
                ax2.set_xticks(x_pos)
                ax2.set_xticklabels(df['category'], rotation=45)
                ax2.legend()
                
                plt.tight_layout()
                
                canvas = FigureCanvasTkAgg(fig, chart_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
                
                # Data table
                table_frame = tk.LabelFrame(main_frame, text="Movement Data by Category", 
                                           font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
                table_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                self.create_data_table(df, table_frame)
            else:
                tk.Label(self, text="No inventory movement data available", 
                        font=("Segoe UI", 16), bg="#f0f0f0").pack(expand=True)
        except Exception as e:
            print(f"Error loading inventory trends: {e}")
            # Show error frame
            error_frame = tk.Frame(self, bg="#f8d7da", relief="solid", bd=1)
            error_frame.pack(fill="both", expand=True, padx=20, pady=50)
            
            tk.Label(error_frame, text="⚠️ Connection Error", 
                    font=("Segoe UI", 20, "bold"), bg="#f8d7da", fg="#721c24").pack(pady=20)
            tk.Label(error_frame, text="Unable to load inventory trends. Please check your connection and try again.", 
                    font=("Segoe UI", 12), bg="#f8d7da", fg="#721c24").pack(pady=10)
            
            retry_button = tk.Button(error_frame, text="🔄 Retry", 
                                   command=self.refresh_data, bg="#dc3545", fg="white",
                                   font=("Segoe UI", 11), relief="flat", padx=20)
            retry_button.pack(pady=10)
    
    def export_report(self):
        """Export inventory trends report"""
        try:
            df = self.analytics.get_inventory_movement_trends(30)
            if not df.empty:
                from report_generator import RestockerReportGenerator
                report_gen = RestockerReportGenerator()
                report_gen.generate_inventory_report({"movement_trends": df}, 'pdf')
            else:
                messagebox.showwarning("No Data", "No inventory movement data available for export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report: {str(e)}")


class ForecastDemand(RestockerDataFrame):
    def __init__(self, master):
        super().__init__(master, "High Demand Product Forecasts")
        self.load_data()
    
    def load_data(self):
        """Load and display demand forecast data"""
        try:
            df = self.analytics.get_predicted_high_demand_products(30)
            
            if not df.empty:
                main_frame = tk.Frame(self, bg="#f0f0f0")
                main_frame.pack(fill="both", expand=True)
                
                # Risk summary frame
                risk_frame = tk.Frame(main_frame, bg="#fff3cd", relief="solid", bd=1)
                risk_frame.pack(fill="x", padx=10, pady=5)
                
                # Count risk levels
                high_risk = len(df[df['demand_risk'] == 'High Demand Risk'])
                medium_risk = len(df[df['demand_risk'] == 'Medium Demand Risk'])
                low_risk = len(df[df['demand_risk'] == 'Low Demand Risk'])
                
                risk_text = f"⚠️ DEMAND FORECAST: {high_risk} High Risk | {medium_risk} Medium Risk | {low_risk} Low Risk"
                tk.Label(risk_frame, text=risk_text, font=("Segoe UI", 12, "bold"), 
                        bg="#fff3cd", fg="#856404").pack(pady=10)
                
                # Chart frame for high-risk items
                if high_risk > 0:
                    chart_frame = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
                    chart_frame.pack(fill="both", expand=True, padx=10, pady=5)
                    
                    high_risk_items = df[df['demand_risk'] == 'High Demand Risk'].head(5)
                    
                    fig, ax = plt.subplots(figsize=(12, 6), facecolor='white')
                    bars = ax.bar(high_risk_items['product_name'], high_risk_items['current_stock'], 
                                 color='#e74c3c', alpha=0.8, label='Current Stock')
                    ax.bar(high_risk_items['product_name'], high_risk_items['suggested_reorder_quantity'], 
                          bottom=high_risk_items['current_stock'], color='#27ae60', alpha=0.8, 
                          label='Suggested Reorder')
                    
                    ax.set_title('High Risk Products - Current vs Suggested Stock')
                    ax.set_xlabel('Product Name')
                    ax.set_ylabel('Units')
                    ax.legend()
                    ax.tick_params(axis='x', rotation=45)
                    plt.tight_layout()
                    
                    canvas = FigureCanvasTkAgg(fig, chart_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
                
                # Data table
                table_frame = tk.LabelFrame(main_frame, text="Demand Forecast Data", 
                                           font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
                table_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                self.create_data_table(df, table_frame)
            else:
                tk.Label(self, text="Insufficient sales data for demand forecasting", 
                        font=("Segoe UI", 16), bg="#f0f0f0").pack(expand=True)
        except Exception as e:
            print(f"Error loading demand forecast: {e}")
            # Show error frame
            error_frame = tk.Frame(self, bg="#f8d7da", relief="solid", bd=1)
            error_frame.pack(fill="both", expand=True, padx=20, pady=50)
            
            tk.Label(error_frame, text="⚠️ Connection Error", 
                    font=("Segoe UI", 20, "bold"), bg="#f8d7da", fg="#721c24").pack(pady=20)
            tk.Label(error_frame, text="Unable to load demand forecast data. Please check your connection and try again.", 
                    font=("Segoe UI", 12), bg="#f8d7da", fg="#721c24").pack(pady=10)
            
            retry_button = tk.Button(error_frame, text="🔄 Retry", 
                                   command=self.refresh_data, bg="#dc3545", fg="white",
                                   font=("Segoe UI", 11), relief="flat", padx=20)
            retry_button.pack(pady=10)

    def export_report(self):
        """Export demand forecast report"""
        try:
            df = self.analytics.get_predicted_high_demand_products(30)
            if not df.empty:
                from report_generator import RestockerReportGenerator
                report_gen = RestockerReportGenerator()
                report_gen.generate_inventory_report({"high_demand": df}, 'pdf')
            else:
                messagebox.showwarning("No Data", "Insufficient data for demand forecasting export")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report: {str(e)}")


class RestockerPage(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.controller.title("Restocker Page")

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

        self.low_stock_button = tk.Button(
            self.sidebar, text="Low Stock Product Reports", bg="#2c3e50", fg="#ecf0f1", activebackground="#34495e",
            activeforeground="white", bd=0, font=("Segoe UI", 11), anchor="w",
            padx=15, command=self.show_low_stock, wraplength=150, justify="left")

        self.inventory_trends_button = tk.Button(
            self.sidebar, text="Inventory Trends", bg="#2c3e50", fg="#ecf0f1", activebackground="#34495e",
            activeforeground="white", bd=0, font=("Segoe UI", 11), anchor="w",
            padx=15, command=self.show_inventory_trends)

        self.forecast_demand_button = tk.Button(
            self.sidebar, text="Forecast High Demand Product Data", bg="#2c3e50", fg="#ecf0f1",
            activebackground="#34495e", activeforeground="white", bd=0, font=("Segoe UI", 11), anchor="w",
            padx=15, command=self.show_forecast_demand, wraplength=150, justify="left")

        self.content = tk.Frame(self.container, bg=self.theme_colors['bg'])
        self.content.pack(side="left", fill="both", expand=True)

        self.bind_all("<Button-1>", self.click_outside)

        self.current_content = None
        
        # Show welcome message by default
        self.show_welcome()

    def apply_theme(self):
        """Apply current theme colors to the restocker page"""
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
        username = current_user.get('username', 'Restocker') if current_user else 'Restocker'
        
        # Welcome message
        welcome_label = tk.Label(center_frame, 
                                text=f"Welcome {username}",
                                font=("Segoe UI", 28, "bold"),
                                fg=self.theme_colors['fg'],
                                bg=self.theme_colors['bg'])
        welcome_label.pack(pady=20)
        
        # Subtitle
        subtitle_label = tk.Label(center_frame,
                                 text="Inventory Management Dashboard",
                                 font=("Segoe UI", 16),
                                 fg=self.theme_colors['fg'],
                                 bg=self.theme_colors['bg'])
        subtitle_label.pack(pady=10)
        
        # Instructions
        instructions_label = tk.Label(center_frame,
                                     text="Use the menu on the left to access inventory analytics and reports",
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
            self.low_stock_button.pack_forget()
            self.inventory_trends_button.pack_forget()
            self.forecast_demand_button.pack_forget()

            for sep in self.separators:
                sep.destroy()
            self.separators.clear()

        else:
            self.sidebar.config(width=200)
            self.toggle_button.config(text="<", anchor="e", font=("Segoe UI", 14, "bold"), padx=20,)
            self.logout_button.pack(side="bottom", fill="x", pady=(10, 20), padx=20)
            self.low_stock_button.pack(fill="x", pady=(10, 0))
            self.separator(self.sidebar)
            self.inventory_trends_button.pack(fill="x", pady=(10, 0))
            self.separator(self.sidebar)
            self.forecast_demand_button.pack(fill="x", pady=(10, 0))
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
        self.controller.state('normal')
        messagebox.showinfo("Logout", "You have been logged out successfully")
        self.controller.show_frame("LoginPage")
        self.controller.title("Login Page")

    def clear_content(self):
        if self.current_content:
            self.current_content.destroy()

    def show_low_stock(self):
        self.clear_content()
        self.current_content = LowStock(self.content)
        self.current_content.pack(fill="both", expand=True)

    def show_inventory_trends(self):
        self.clear_content()
        self.current_content = InventoryTrends(self.content)
        self.current_content.pack(fill="both", expand=True)

    def show_forecast_demand(self):
        self.clear_content()
        self.current_content = ForecastDemand(self.content)
        self.current_content.pack(fill="both", expand=True)

    def separator(self, parent):
        separator = tk.Frame(parent, height=1, bg="#bdc3c7")
        separator.pack(fill="x", padx=10, pady=(2, 5))
        self.separators.append(separator)
