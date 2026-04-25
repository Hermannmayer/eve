import tkinter as tk
import sqlite3
from ui.config import CJK_FONT, CJK_LARGE, DB_PATH


class QueryPage(tk.Frame):
    """物品查询页面"""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 居中Label
        label = tk.Label(self, text="查询物品", font=CJK_LARGE)
        label.grid(row=0, column=0, pady=10, sticky="n")

        # 搜索框和按钮（居中）
        search_frame = tk.Frame(self)
        search_frame.grid(row=1, column=0, pady=5, sticky="n")
        self.search_var = tk.StringVar()
        entry = tk.Entry(search_frame, textvariable=self.search_var, width=30, justify="center")
        entry.pack(side="left", padx=5)
        search_btn = tk.Button(search_frame, text="搜索", command=self.search_item)
        search_btn.pack(side="left")

        # 查询结果显示（居中）
        self.result_text = tk.Text(self, height=10, width=40, font=CJK_FONT)
        self.result_text.grid(row=2, column=0, pady=10, sticky="n")
        self.result_text.tag_configure("center", justify='center')

    def search_item(self):
        query = self.search_var.get()
        self.result_text.delete(1.0, tk.END)
        if not query:
            self.result_text.insert(tk.END, "请输入搜索内容。", "center")
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT type_id, en_name, zh_name, en_group_name, zh_group_name, volume "
                "FROM item WHERE en_name LIKE ? OR zh_name LIKE ?",
                ('%' + query + '%', '%' + query + '%')
            )
            results = cursor.fetchall()
            if results:
                for row in results:
                    tid, en, zh, eng, zhg, vol = row
                    self.result_text.insert(
                        tk.END,
                        f"  [{tid}] {en} / {zh}  |  {zhg or eng}  |  {vol} m³\n",
                        "center"
                    )
            else:
                self.result_text.insert(tk.END, "未找到相关物品。", "center")
            conn.close()
        except Exception as e:
            self.result_text.insert(tk.END, f"查询出错: {e}", "center")
