import tkinter as tk
from ui.config import CJK_LARGE


class TradePage(tk.Frame):
    """贸易页面（待实现）"""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        label = tk.Label(self, text="贸易页面", font=CJK_LARGE)
        label.grid(row=0, column=0, pady=20, sticky="n")
