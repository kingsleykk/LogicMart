import tkinter as tk


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("1000x600")
        self.title("Collapsible Sidebar Example")

        self.sidebar_expanded = False

        # Main container frame
        self.container = tk.Frame(self, bg="white")
        self.container.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = tk.Frame(self.container, bg="#2c3e50", width=50)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Sidebar toggle button
        self.toggle_button = tk.Button(self.sidebar, text="☰", fg="white", bg="#2c3e50",
                                       command=self.toggle_sidebar, bd=0, font=("Segoe UI", 14))
        self.toggle_button.pack(pady=10)

        # Main content area
        self.content = tk.Frame(self.container, bg="white")
        self.content.pack(side="left", fill="both", expand=True)

        self.bind("<Button-1>", self.click_outside)

    def toggle_sidebar(self):
        if self.sidebar_expanded:
            self.sidebar.config(width=50)
        else:
            self.sidebar.config(width=200)
        self.sidebar_expanded = not self.sidebar_expanded

    def click_outside(self, event):
        # Collapse sidebar if expanded and clicked outside sidebar
        if self.sidebar_expanded:
            x, y = event.x_root, event.y_root
            sidebar_x = self.sidebar.winfo_rootx()
            sidebar_w = self.sidebar.winfo_width()

            if x > sidebar_x + sidebar_w:
                self.toggle_sidebar()


if __name__ == "__main__":
    app = App()
    app.mainloop()
