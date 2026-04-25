import tkinter as tk
from ui.config import CJK_FONT


class WarehousePage(tk.Frame):
    """仓库页面 — 包含物品仓库和蓝图仓库两个子页面"""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 顶部二级导航栏
        nav = tk.Frame(self)
        nav.grid(row=0, column=0, sticky="ew")
        btn_item = tk.Button(nav, text="物品仓库", font=CJK_FONT,
                             command=lambda: self.show_subpage("item"))
        btn_blueprint = tk.Button(nav, text="蓝图仓库", font=CJK_FONT,
                                  command=lambda: self.show_subpage("blueprint"))
        btn_item.pack(side="left", expand=True, fill="x")
        btn_blueprint.pack(side="left", expand=True, fill="x")

        # 二级页面容器
        self.subpages = {}
        self.subpage_container = tk.Frame(self)
        self.subpage_container.grid(row=1, column=0, sticky="nsew")
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self.subpages["item"] = ItemWarehousePage(self.subpage_container)
        self.subpages["blueprint"] = BlueprintWarehousePage(self.subpage_container)
        self.subpages["item"].grid(row=0, column=0, sticky="nsew")
        self.subpages["blueprint"].grid(row=0, column=0, sticky="nsew")

        self.show_subpage("item")

    def show_subpage(self, name):
        self.subpages[name].tkraise()


class ItemWarehousePage(tk.Frame):
    """物品仓库子页面"""

    def __init__(self, parent):
        super().__init__(parent)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        import_btn = tk.Button(
            self, text="从剪贴板读取数据并导入物品",
            font=CJK_FONT, command=self.import_from_clipboard
        )
        import_btn.grid(row=0, column=0, pady=10, sticky="ew")

        self.text = tk.Text(self, height=20, font=CJK_FONT)
        self.text.grid(row=1, column=0, sticky="nsew")

    def import_from_clipboard(self):
        try:
            data = self.clipboard_get()
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, f"导入物品数据：\n{data}")
        except Exception as e:
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, f"读取剪贴板失败: {e}")


class BlueprintWarehousePage(tk.Frame):
    """蓝图仓库子页面"""

    def __init__(self, parent):
        super().__init__(parent)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        import_btn = tk.Button(
            self, text="从剪贴板读取数据并导入蓝图",
            font=CJK_FONT, command=self.import_from_clipboard
        )
        import_btn.grid(row=0, column=0, pady=10, sticky="ew")

        self.text = tk.Text(self, height=20, font=CJK_FONT)
        self.text.grid(row=1, column=0, sticky="nsew")

    def import_from_clipboard(self):
        try:
            data = self.clipboard_get()
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, f"导入蓝图数据：\n{data}")
        except Exception as e:
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, f"读取剪贴板失败: {e}")
