import tkinter as tk


class LowStock(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#f0f0f0")
        tk.Label(self, text="Low Stock Product Reports", font=("Segoe UI", 16)).pack(pady=20)
        tk.Button(self, text="+ Folder", font=("Segoe UI", 14, "bold"), bg="#31CEE6", fg="white", padx=20, pady=10,
                  bd=0, activebackground="#3b76c4", activeforeground="white").place(anchor="center", relx=0.5, rely=0.5)


class InventoryTrends(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#f0f0f0")
        tk.Label(self, text="Inventory Trends", font=("Segoe UI", 16)).pack(pady=20)
        tk.Button(self, text="+ Folder", font=("Segoe UI", 14, "bold"), bg="#31CEE6", fg="white", padx=20, pady=10,
                  bd=0, activebackground="#3b76c4", activeforeground="white").place(anchor="center", relx=0.5, rely=0.5)


class ForecastDemand(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#f0f0f0")
        tk.Label(self, text="Forecast High Demand Product Data", font=("Segoe UI", 16)).pack(pady=20)
        tk.Button(self, text="+ Folder", font=("Segoe UI", 14, "bold"), bg="#31CEE6", fg="white", padx=20, pady=10,
                  bd=0, activebackground="#3b76c4", activeforeground="white").place(anchor="center", relx=0.5, rely=0.5)


class RestockerPage(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.controller.title("Restocker Page")

        self.sidebar_expand = False
        self.separators = []
        self.theme_bg = "#f0f0f0"
        self.accent = "#4a90e2"
        self.text_color = "#333333"
        self.font = ("Segoe UI", 12)

        self.container = tk.Frame(self, bg=self.theme_bg)
        self.container.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(self.container, bg="#2c3e50", width=50)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.toggle_button = tk.Button(self.sidebar, text="☰", fg="white", bg="#2c3e50",
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

        self.content = tk.Frame(self.container, bg=self.theme_bg)
        self.content.pack(side="left", fill="both", expand=True)

        self.bind_all("<Button-1>", self.click_outside)

        self.current_content = None

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
            self.logout_button.pack(side="bottom", fill="x", pady=20, padx=20)
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
