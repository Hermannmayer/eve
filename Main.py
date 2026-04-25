"""
EVE 制造助手 — 入口点
"""
import tkinter as tk
from ui.views import QueryPage, IndustryPage, TradePage, WarehousePage


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EVE 制造助手")
        self.geometry("1280x720")

        # 页面容器
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # 初始化所有页面
        self.frames = {}
        for F in (QueryPage, IndustryPage, TradePage, WarehousePage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("QueryPage")

        # 顶部导航栏
        nav = tk.Frame(self)
        nav.pack(side="top", fill="x")
        for text, page in [
            ("查询物品", "QueryPage"),
            ("工业", "IndustryPage"),
            ("贸易", "TradePage"),
            ("仓库", "WarehousePage"),
        ]:
            tk.Button(nav, text=text, command=lambda p=page: self.show_frame(p)).pack(
                side="left", expand=True, fill="x"
            )

    def show_frame(self, page_name):
        self.frames[page_name].tkraise()


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
