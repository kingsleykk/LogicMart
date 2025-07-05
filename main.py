import tkinter as tk
from login_page import LoginPage
from manager_page import ManagerPage
from sales_manager_page import SManagerPage
from restocker_page import RestockerPage


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LogicMart Analytics System")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        self.resizable(True, True)
        
        self.frames = {
            "LoginPage": LoginPage,
            "ManagerPage": ManagerPage,
            "SManagerPage": SManagerPage,
            "RestockerPage": RestockerPage
        }

        self.current_frame = None
        self.current_user = None  # Store current user info
        
        # Apply default light theme colors
        self.configure(bg='#f0f0f0')
        
        self.show_frame("LoginPage")

    def set_current_user(self, user_info):
        """Set the current logged-in user"""
        self.current_user = user_info

    def get_current_user(self):
        """Get the current logged-in user"""
        return self.current_user

    def show_frame(self, page_name):
        page_class = self.frames[page_name]
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = page_class(self, self)
        
        # Pass user info to welcome page if it's being shown
        if page_name == "WelcomePage" and self.current_user:
            self.current_frame.set_user(self.current_user)
        
        self.current_frame.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = App()
    app.mainloop()
