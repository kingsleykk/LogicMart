import tkinter as tk
from login_page import LoginPage
from manager_page import ManagerPage
from sales_manager_page import SManagerPage
from restocker_page import RestockerPage


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Login Page")
        self.geometry("1000x600")
        self.resizable(False, False)
        self.frames = {
            "LoginPage": LoginPage,
            "ManagerPage": ManagerPage,
            "SManagerPage": SManagerPage,
            "RestockerPage": RestockerPage
        }

        self.current_frame = None
        self.show_frame("LoginPage")

    def show_frame(self, page_name):
        page_class = self.frames[page_name]
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = page_class(self, self)
        self.current_frame.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = App()
    app.mainloop()
