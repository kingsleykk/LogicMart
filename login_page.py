import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

print(os.getcwd())
class LoginPage(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master, bg="#f0f0f0")
        self.entry_username = None
        self.entry_password = None
        self.show_var = None
        self.controller = controller
        self.user_data = {}
        self.load_data_from_file()

        self.theme_bg = "#f0f0f0"
        self.accent = "#4a90e2"
        self.text_color = "#333333"
        self.font = ("Segoe UI", 12)

        self.create_widget()

    def load_data_from_file(self):
        try:
            with open("user_credentials.txt", 'r') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        username, password, role = line.split(",")
                        self.user_data[username] = {
                            "password": password,
                            "role": role
                        }
        except FileNotFoundError:
            print("file not found!")

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()

        if username in self.user_data and self.user_data[username]["password"] == password:
            role = self.user_data[username]["role"]
            messagebox.showinfo("Login Successful", f"Welcome, {username}!")
            if role == "manager":
                self.controller.show_frame("ManagerPage")
            elif role == "sales_manager":
                self.controller.show_frame("SManagerPage")
            elif role == "restocker":
                self.controller.show_frame("RestockerPage")
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    def show_password(self):
        if self.show_var.get():
            self.entry_password.config(show="")
        else:
            self.entry_password.config(show="*")

    def create_widget(self):
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        left_frame = tk.Frame(self, bg="#d9eaf7")
        left_frame.grid(row=0, column=0, sticky="nsew")

        try:
            png = Image.open("analytics.png")
            resized = png.resize((400, 400), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(resized)
            label = tk.Label(left_frame, image=tk_img, bg="#d9eaf7")
            label.image = tk_img
            label.pack(fill="both", expand=True)
        except Exception:
            tk.Label(left_frame, text="Analysis picture", bg="#d9eaf7").pack()

        right_frame = tk.Frame(self, bg=self.theme_bg)
        right_frame.grid(row=0, column=1, sticky="nsew")
        form_frame = tk.Frame(right_frame, bg=self.theme_bg)
        form_frame.pack(padx=40, pady=100, anchor='nw')

        tk.Label(form_frame, text="Welcome Back!", font=("Segoe UI", 18, "bold"),
                 fg=self.text_color, bg=self.theme_bg).pack(anchor='w', pady=(0, 20))

        tk.Label(form_frame, text="Username", font=self.font, fg=self.text_color, bg=self.theme_bg).pack(anchor='w')
        self.entry_username = tk.Entry(form_frame, font=self.font, width=30)
        self.entry_username.pack(anchor='w', pady=(0, 15))

        tk.Label(form_frame, text="Password", font=self.font, fg=self.text_color, bg=self.theme_bg).pack(anchor='w')
        self.entry_password = tk.Entry(form_frame, show="*", font=self.font, width=30)
        self.entry_password.pack(anchor='w', pady=(0, 15))

        self.show_var = tk.BooleanVar()
        tk.Checkbutton(form_frame, text="Show Password", variable=self.show_var, command=self.show_password,
                       bg=self.theme_bg, font=self.font).pack(anchor='w', pady=(0, 20))

        tk.Button(form_frame, text="Login", command=self.login, font=self.font, bg=self.accent,
                  fg="white", relief="flat", padx=20, pady=5).pack(anchor="w")
