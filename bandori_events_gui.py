import json
import os
import tkinter as tk
from tkinter import ttk, messagebox


FILE_PATH = os.path.join(os.path.dirname(__file__), "bandori_events.json")
FIELDS = [
    ("event", "活动名称"),
    ("date", "日期"),
    ("raw_text", "地点/原始文本"),
    ("project", "项目"),
    ("image", "图片文件"),
    ("offical", "官方"),
]


class BandoriEventsApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Bandori Events JSON 管理器")
        self.root.geometry("1400x820")
        self.root.minsize(1200, 720)

        self.records = []
        self.entries = {}
        self.variables = {}
        self.selected_tree_item = None

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.LabelFrame(main_frame, text="活动列表", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.LabelFrame(main_frame, text="活动编辑", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        right_frame.configure(width=340)
        right_frame.pack_propagate(False)

        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(search_frame, text="搜索：").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 6))
        search_entry.bind("<KeyRelease>", lambda event: self.refresh_tree())

        ttk.Button(search_frame, text="刷新", command=self.load_data).pack(side=tk.LEFT)

        columns = [field for field, _ in FIELDS]
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=26)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        for field, label in FIELDS:
            self.tree.heading(field, text=label)
            width = 130
            if field == "event":
                width = 320
            elif field in {"raw_text", "image"}:
                width = 190
            self.tree.column(field, width=width, anchor=tk.W)

        form_frame = ttk.Frame(right_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)

        for row_index, (field, label) in enumerate(FIELDS):
            ttk.Label(form_frame, text=f"{label}：").grid(row=row_index, column=0, sticky=tk.W, pady=6)

            if field == "offical":
                variable = tk.BooleanVar(value=True)
                widget = ttk.Checkbutton(form_frame, variable=variable, text="官方活动")
                self.variables[field] = variable
            else:
                widget = ttk.Entry(form_frame, width=38)

            widget.grid(row=row_index, column=1, sticky=tk.EW, pady=6)
            self.entries[field] = widget

        form_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=(12, 0))

        ttk.Button(button_frame, text="新增", command=self.add_record).pack(fill=tk.X, pady=4)
        ttk.Button(button_frame, text="修改", command=self.update_record).pack(fill=tk.X, pady=4)
        ttk.Button(button_frame, text="删除", command=self.delete_record).pack(fill=tk.X, pady=4)
        ttk.Button(button_frame, text="清空表单", command=self.clear_form).pack(fill=tk.X, pady=4)

        tip_text = (
            "说明：\n"
            "1. 左侧显示 bandori_events.json 中的 events 列表。\n"
            "2. 选中记录后可在右侧修改。\n"
            "3. offical 使用勾选框，保存为 1/0。\n"
            "4. project 留空时默认填 bandori。\n"
            "5. 支持新增、修改、删除和搜索。"
        )
        ttk.Label(right_frame, text=tip_text, justify=tk.LEFT).pack(anchor=tk.W, pady=(12, 0))

    def load_data(self):
        data = self.read_json()
        self.records = data.get("events", [])
        self.refresh_tree()
        self.clear_form()

    def read_json(self):
        if not os.path.exists(FILE_PATH):
            return {"events": []}

        with open(FILE_PATH, "r", encoding="utf-8") as file:
            return json.load(file)

    def write_json(self):
        payload = {"events": self.records}
        with open(FILE_PATH, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=4)

    def refresh_tree(self):
        keyword = self.search_var.get().strip().lower()
        self.tree.delete(*self.tree.get_children())

        for record in self.records:
            searchable_text = json.dumps(record, ensure_ascii=False).lower()
            if keyword and keyword not in searchable_text:
                continue

            values = [record.get(field, "") for field, _ in FIELDS]
            self.tree.insert("", tk.END, values=values)

    def on_tree_select(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        selected_item = selected_items[0]
        values = self.tree.item(selected_item, "values")

        self.clear_form(reset_selection=False)
        self.selected_tree_item = selected_item
        for index, (field, _) in enumerate(FIELDS):
            self.set_field_value(field, values[index])

    def clear_form(self, reset_selection=True):
        if reset_selection:
            self.selected_tree_item = None
            self.tree.selection_remove(self.tree.selection())

        for field, widget in self.entries.items():
            if field == "offical":
                self.variables[field].set(True)
                continue

            widget.delete(0, tk.END)

        self.entries["project"].insert(0, "bandori")

    def set_field_value(self, field, value):
        if field == "offical":
            if isinstance(value, str):
                self.variables[field].set(value.strip().lower() in {"1", "true", "yes"})
            else:
                self.variables[field].set(bool(value))
            return

        widget = self.entries[field]
        widget.delete(0, tk.END)
        widget.insert(0, str(value))

    def get_form_data(self):
        record = {}
        for field, _ in FIELDS:
            if field == "offical":
                record[field] = 1 if self.variables[field].get() else 0
            else:
                record[field] = self.entries[field].get().strip()

        if not record["event"]:
            raise ValueError("活动名称不能为空")
        if not record["date"]:
            raise ValueError("日期不能为空")
        if not record["raw_text"]:
            raise ValueError("地点/原始文本不能为空")

        record["project"] = record["project"] or "bandori"
        return record

    def get_selected_record_index(self):
        if self.selected_tree_item is None:
            return None

        selected_values = self.tree.item(self.selected_tree_item, "values")
        selected_event = selected_values[0]
        selected_date = selected_values[1]

        for index, item in enumerate(self.records):
            if item.get("event") == selected_event and item.get("date") == selected_date:
                return index

        return None

    def add_record(self):
        try:
            record = self.get_form_data()
        except ValueError as error:
            messagebox.showerror("新增失败", str(error))
            return

        self.records.append(record)
        self.write_json()
        self.refresh_tree()
        self.clear_form()
        messagebox.showinfo("新增成功", "活动记录已新增并保存到 JSON 文件")

    def update_record(self):
        try:
            record = self.get_form_data()
        except ValueError as error:
            messagebox.showerror("修改失败", str(error))
            return

        record_index = self.get_selected_record_index()
        if record_index is None:
            messagebox.showwarning("修改失败", "请先在左侧选择一条记录")
            return

        self.records[record_index] = record
        self.write_json()
        self.refresh_tree()
        self.clear_form()
        messagebox.showinfo("修改成功", "活动记录已更新并保存到 JSON 文件")

    def delete_record(self):
        record_index = self.get_selected_record_index()
        if record_index is None:
            messagebox.showwarning("删除失败", "请先在左侧选择一条记录")
            return

        record = self.records[record_index]
        if not messagebox.askyesno("确认删除", f"确定删除活动“{record.get('event', '')}”吗？"):
            return

        del self.records[record_index]
        self.write_json()
        self.refresh_tree()
        self.clear_form()
        messagebox.showinfo("删除成功", "活动记录已删除并保存到 JSON 文件")


def main():
    root = tk.Tk()
    app = BandoriEventsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
