import tkinter as tk
from login_page import LoginPage
from manager_page import ManagerPage
from sales_manager_page import SManagerPage
from restocker_page import RestockerPage


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LogicMart Analytics System - Login")

        self.login_geometry = "800x600"
        self.fullscreen_geometry = None
        self.geometry(self.login_geometry)
        self.minsize(800, 600)
        self.resizable(True, True)
        self.center_window()
        
        self.frames = {
            "LoginPage": LoginPage,
            "ManagerPage": ManagerPage,
            "SManagerPage": SManagerPage,
            "RestockerPage": RestockerPage
        }

        self.current_frame = None
        self.current_user = None  
        self.is_logged_in = False
        

        self.configure(bg='#f0f0f0')
        
        self.show_frame("LoginPage")

    def center_window(self):
        self.update_idletasks()
        self.after(10, self._do_center)
    
    def _do_center(self):
        width = self.winfo_width()
        height = self.winfo_height()
        pos_x = (self.winfo_screenwidth() // 2) - (width // 2)
        pos_y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def maximize_window_after_login(self):
        self.is_logged_in = True
        self.fullscreen_geometry = self.geometry()
        self.state('zoomed')
        self.minsize(1200, 800)

    def restore_login_window(self):
        self.is_logged_in = False
        self.state('normal')
        self.geometry(self.login_geometry)
        self.minsize(800, 600)
        self.center_window()

    def set_current_user(self, user_info):
        self.current_user = user_info

    def get_current_user(self):
        return self.current_user

    def show_frame(self, page_name):
        page_class = self.frames[page_name]
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = page_class(self, self)

        if page_name == "LoginPage":
            self.title("LogicMart Analytics System - Login")
            if self.is_logged_in:
                self.restore_login_window()
        else:
            self.title("LogicMart Analytics System")
            if not self.is_logged_in:
                self.maximize_window_after_login()

        if page_name == "WelcomePage" and self.current_user:
            self.current_frame.set_user(self.current_user)
        
        self.current_frame.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = App()
    app.mainloop()
