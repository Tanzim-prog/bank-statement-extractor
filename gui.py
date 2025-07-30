import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from extractors import auto_extract_with_metrics

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bank Statement Extractor")
        self.geometry("800x600")
        self.df = None
        self.extractor_name = None
        self._build_widgets()

    def _build_widgets(self):
        frm_pdf = ttk.LabelFrame(self, text="Step 1: Select PDF", padding=10)
        frm_pdf.pack(fill=tk.X, padx=10, pady=5)
        self.pdf_path = tk.StringVar()
        ttk.Entry(frm_pdf, textvariable=self.pdf_path, width=60).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(frm_pdf, text="Browse…", command=self._browse_pdf).pack(side=tk.LEFT)

        frm_btns = ttk.Frame(self, padding=10)
        frm_btns.pack(fill=tk.X, padx=10)
        self.btn_extract = ttk.Button(frm_btns, text="Extract", command=self._on_extract)
        self.btn_extract.pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(frm_btns, text="Exit", command=self.destroy).pack(side=tk.LEFT)

        frm_save = ttk.LabelFrame(self, text="Step 2: Save Output", padding=10)
        frm_save.pack(fill=tk.X, padx=10, pady=5)
        self.format_option = tk.StringVar(value="csv")
        ttk.Radiobutton(frm_save, text="CSV", variable=self.format_option, value="csv").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(frm_save, text="Excel", variable=self.format_option, value="xlsx").pack(side=tk.LEFT, padx=5)
        self.btn_save = ttk.Button(frm_save, text="Save…", command=self._on_save, state=tk.DISABLED)
        self.btn_save.pack(side=tk.LEFT, padx=(20,0))

        frm_status = ttk.Frame(self, padding=10)
        frm_status.pack(fill=tk.X, padx=10)
        self.status = tk.StringVar(value="Ready")
        ttk.Label(frm_status, textvariable=self.status).pack(side=tk.LEFT)
        self.progress = ttk.Progressbar(frm_status, length=200, maximum=1)
        self.progress.pack(side=tk.LEFT, padx=10)

        frm_out = ttk.LabelFrame(self, text="Metrics & Preview", padding=10)
        frm_out.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.txt = tk.Text(frm_out, wrap=tk.NONE)
        self.txt.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        yscr = ttk.Scrollbar(frm_out, orient=tk.VERTICAL, command=self.txt.yview)
        xscr = ttk.Scrollbar(frm_out, orient=tk.HORIZONTAL, command=self.txt.xview)
        self.txt.configure(yscrollcommand=yscr.set, xscrollcommand=xscr.set)
        yscr.pack(fill=tk.Y, side=tk.RIGHT)
        xscr.pack(fill=tk.X, side=tk.BOTTOM)

    def _browse_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files","*.pdf")])
        if path:
            self.pdf_path.set(path)

    def _on_extract(self):
        pdf = self.pdf_path.get().strip()
        if not pdf or not os.path.isfile(pdf):
            messagebox.showerror("Error", "Please select a valid PDF.")
            return

        self.btn_extract.config(state=tk.DISABLED)
        self.btn_save.config(state=tk.DISABLED)
        self.txt.delete("1.0", tk.END)
        self.progress['value'] = 0

        threading.Thread(target=self._run_extract, args=(pdf,), daemon=True).start()

    def _run_extract(self, pdf):
        try:
            self._update_status("Extracting…", 0)
            name, df, total, found, pct = auto_extract_with_metrics(pdf)
            self.df = df
            self._update_status("Done", 1)
            self.after(0, lambda: self._show_metrics(name, total, found, pct, df))
            if not df.empty:
                self.btn_save.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Extraction Error", str(e))
        finally:
            self.btn_extract.config(state=tk.NORMAL)

    def _show_metrics(self, name, total, found, pct, df):
        self.txt.insert(tk.END, f"Layout: {name or 'unknown'}\n")
        self.txt.insert(tk.END, f"Possible rows: {total}\n")
        self.txt.insert(tk.END, f"Extracted rows: {found}\n")
        self.txt.insert(tk.END, f"Accuracy: {pct:.1f}%\n\n")
        if not df.empty:
            self.txt.insert(tk.END, df.head(10).to_string(index=False))
        else:
            self.txt.insert(tk.END, "No data extracted.\n")

    def _on_save(self):
        if self.df is None or self.df.empty:
            return
        fmt = self.format_option.get()
        ext = f".{fmt}"
        ftypes = [("CSV","*.csv")] if fmt=="csv" else [("Excel","*.xlsx")]
        path = filedialog.asksaveasfilename(defaultextension=ext, filetypes=ftypes)
        if not path:
            return

        self.btn_save.config(state=tk.DISABLED)
        self._update_status("Saving…", 0)
        threading.Thread(target=self._run_save, args=(path,fmt), daemon=True).start()

    def _run_save(self, path, fmt):
        try:
            if fmt=="csv":
                self.df.to_csv(path, index=False, encoding='utf-8-sig')
            else:
                self.df.to_excel(path, index=False)
            self._update_status(f"Saved: {os.path.basename(path)}", 1)
            self.after(0, lambda: messagebox.showinfo("Saved", f"File saved to:\n{path}"))
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
        finally:
            self.btn_save.config(state=tk.NORMAL)

    def _update_status(self, text, prog):
        self.after(0, lambda: (self.status.set(text),
                               self.progress.config(value=prog)))

if __name__ == "__main__":
    app = App()
    app.mainloop()