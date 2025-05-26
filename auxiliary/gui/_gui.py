# -*- coding: utf-8 -*-
class ClickGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Click Command GUI")
        self.geometry("800x600")
        self.config(padx=20, pady=20)

        self.commands = ["format-code", "list-files", "repair-svg"]
        self.option_widgets = {}
        self.saved_inputs = {}

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Select Command:", font=("Arial", 12, "bold")).pack(anchor='w')
        self.command_var = tk.StringVar(value=self.commands[0])
        self.command_dropdown = ttk.Combobox(self, textvariable=self.command_var, values=self.commands, state="readonly")
        self.command_dropdown.pack(fill='x', pady=(0, 10))
        self.command_dropdown.bind("<<ComboboxSelected>>", self.on_command_change)

        ttk.Button(self, text="Load Command Options", command=self.load_command_options).pack(pady=(0, 20))

        self.form_frame = tk.Frame(self)
        self.form_frame.pack(fill='both', expand=True)

        self.run_btn = ttk.Button(self, text="Run Command", command=self.run_command)
        self.run_btn.pack(pady=(10, 0))

        self.load_command_options()

    def clear_form(self):
        for widget in self.form_frame.winfo_children():
            widget.destroy()

    def save_current_inputs(self):
        command = self.command_var.get()
        data = {}
        for key, widget in self.option_widgets.items():
            if isinstance(widget, tk.Entry):
                data[key] = widget.get()
            elif isinstance(widget, tk.BooleanVar):
                data[key] = widget.get()
            elif isinstance(widget, tk.Listbox):
                data[key] = [widget.get(i) for i in range(widget.size())]
            elif isinstance(widget, tk.StringVar):
                data[key] = widget.get()
        self.saved_inputs[command] = data

    def on_command_change(self, event=None):
        self.save_current_inputs()
        self.load_command_options()

    def load_command_options(self):
        self.clear_form()
        command = self.command_var.get()
        self.option_widgets = {}

        opts = config_file.get(command, {})
        saved_vals = self.saved_inputs.get(command, {})

        checkbox_frame = tk.Frame(self.form_frame)
        checkbox_frame.pack(fill='x', pady=5, anchor='w')
        checkbox_columns = [tk.Frame(checkbox_frame) for _ in range(3)]
        for col in checkbox_columns:
            col.pack(side='left', expand=True, fill='both')

        column_index = 0

        for i, (key, val) in enumerate(opts.items()):
            is_checkbox = isinstance(val, bool)
            target_frame = self.form_frame if not is_checkbox else checkbox_columns[column_index % 3]

            row = tk.Frame(target_frame)
            row.pack(fill='x', pady=5, anchor='w')

            label = tk.Label(row, text=key, width=20, anchor='w')
            label.pack(side='left')

            if is_checkbox:
                var = tk.BooleanVar(value=saved_vals.get(key, val))
                cb = tk.Checkbutton(row, variable=var)
                cb.pack(side='left')
                self.option_widgets[key] = var
                column_index += 1
            elif isinstance(val, list):
                listbox = tk.Listbox(row, height=4, selectmode=tk.MULTIPLE)
                for item in saved_vals.get(key, val):
                    listbox.insert(tk.END, item)
                listbox.pack(side='left', fill='x', expand=True)
                self.option_widgets[key] = listbox
                add_entry = tk.Entry(row)
                add_entry.pack(side='left', padx=5)
                add_btn = ttk.Button(row, text="Add", command=partial(self.add_to_listbox, listbox, add_entry))
                add_btn.pack(side='left')
            elif isinstance(val, (int, str)):
                entry = tk.Entry(row)
                entry.insert(0, str(saved_vals.get(key, val)))
                entry.pack(side='left', fill='x', expand=True)
                self.option_widgets[key] = entry

        if command == "list-files":
            self.add_radiobutton_group(
                label="Directories Option",
                varname="dirs_group",
                options=[("Use Ignored Dirs", "ignored_dirs"), ("Use All Dirs", "all_dirs")],
                saved_val=saved_vals.get("dirs_group", "ignored_dirs")
            )

    def add_to_listbox(self, listbox, entry):
        val = entry.get().strip()
        if val:
            listbox.insert(tk.END, val)
            entry.delete(0, tk.END)

    def add_radiobutton_group(self, label, varname, options, saved_val=None):
        frame = tk.LabelFrame(self.form_frame, text=label, padx=10, pady=5)
        frame.pack(fill='x', pady=10)

        var = tk.StringVar(value=saved_val or options[0][1])
        for text, value in options:
            rb = tk.Radiobutton(frame, text=text, variable=var, value=value)
            rb.pack(anchor='w')

        self.option_widgets[varname] = var

    def run_command(self):
        command = self.command_var.get()
        args = {}

        for key, widget in self.option_widgets.items():
            if isinstance(widget, tk.Entry):
                args[key] = widget.get()
            elif isinstance(widget, tk.BooleanVar):
                args[key] = widget.get()
            elif isinstance(widget, tk.Listbox):
                args[key] = [widget.get(i) for i in widget.curselection()]
            elif isinstance(widget, tk.StringVar):
                args[key] = widget.get()

        messagebox.showinfo("Command Execution", f"Would run: {command} with options:\n{args}")

if __name__ == '__main__':
    app = ClickGUI()
    app.mainloop()