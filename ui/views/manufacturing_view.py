import tkinter as tk
from ui.config import CJK_LARGE


class IndustryPage(tk.Frame):
    """制造 / 工业页面（待实现）"""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        label = tk.Label(self, text="工业页面", font=CJK_LARGE)
        label.grid(row=0, column=0, pady=20, sticky="n")
