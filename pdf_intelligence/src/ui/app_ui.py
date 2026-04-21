import tkinter as tk
from tkinter import ttk, filedialog
import threading
import os
from src.ui.styles import apply_theme
from src.ui.dialogs import show_info, show_error
from src.index.indexer import index_file
from src.search.searcher import execute_search
from src.index.schema import initialize_db

class AppUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Intelligence Offline")
        self.root.geometry("800x600")

        self.is_dark = False
        apply_theme(self.root, self.is_dark)

        initialize_db()

        self.setup_ui()

    def setup_ui(self):
        # Top Bar
        top_bar = ttk.Frame(self.root)
        top_bar.pack(fill='x', padx=5, pady=5)

        ttk.Button(top_bar, text="Toggle Theme", command=self.toggle_theme).pack(side='right')

        # Notebook for Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)

        # Tabs
        self.search_tab = ttk.Frame(self.notebook)
        self.library_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.search_tab, text="Search")
        self.notebook.add(self.library_tab, text="Library")

        self.build_search_tab()
        self.build_library_tab()

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        apply_theme(self.root, self.is_dark)

    def build_search_tab(self):
        # Search Bar
        search_frame = ttk.Frame(self.search_tab)
        search_frame.pack(fill='x', padx=10, pady=10)

        self.search_var = tk.StringVar()
        entry = ttk.Entry(search_frame, textvariable=self.search_var, font=('Arial', 12))
        entry.pack(side='left', expand=True, fill='x', padx=(0, 5))
        entry.bind('<Return>', lambda e: self.perform_search())

        ttk.Button(search_frame, text="Search", command=self.perform_search).pack(side='right')

        # Results area
        self.results_text = tk.Text(self.search_tab, wrap='word', state='disabled', font=('Arial', 10))
        self.results_text.pack(expand=True, fill='both', padx=10, pady=(0, 10))

    def build_library_tab(self):
        btn_frame = ttk.Frame(self.library_tab)
        btn_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(btn_frame, text="Add PDF/EPUB to Library", command=self.add_files).pack(side='left')

        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(btn_frame, textvariable=self.status_var).pack(side='right')

    def add_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=[("PDF/EPUB Files", "*.pdf *.epub"), ("All Files", "*.*")]
        )
        if not file_paths:
            return

        self.status_var.set(f"Indexing {len(file_paths)} files...")

        # Threaded indexing
        def process():
            success = 0
            for path in file_paths:
                try:
                    index_file(path)
                    success += 1
                except Exception as e:
                    print(f"Error indexing {path}: {e}")

            self.root.after(0, lambda: self.status_var.set(f"Indexed {success}/{len(file_paths)} files successfully."))
            self.root.after(0, lambda: show_info("Indexing Complete", f"Successfully indexed {success} files."))

        threading.Thread(target=process, daemon=True).start()

    def perform_search(self):
        query = self.search_var.get().strip()
        if not query:
            return

        self.results_text.config(state='normal')
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Searching...\n")
        self.results_text.config(state='disabled')

        def do_search():
            results = execute_search(query)
            self.root.after(0, lambda: self.display_results(results))

        threading.Thread(target=do_search, daemon=True).start()

    def display_results(self, results):
        self.results_text.config(state='normal')
        self.results_text.delete(1.0, tk.END)

        if not results:
            self.results_text.insert(tk.END, "No results found.\n")
        else:
            for r in results:
                self.results_text.insert(tk.END, f"Title: {r['title']}\n", "title")
                self.results_text.insert(tk.END, f"Score: {r['score']:.2f}\n", "score")
                self.results_text.insert(tk.END, f"{r['snippet']}\n\n", "snippet")

        self.results_text.tag_config("title", font=('Arial', 12, 'bold'))
        self.results_text.tag_config("score", foreground="gray")
        self.results_text.config(state='disabled')
