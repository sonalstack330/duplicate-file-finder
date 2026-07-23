# noinspection PyTypeChecker,PyUnresolvedReference
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

from duplicate_finder import find_duplicates, format_size

#GUI application

class DuplicateFinderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Duplicate File Finder")
        self.root.geometry("750x550")

        #Data storage
        self.duplicates = {}       # stores the last scan's results
        self.selected_dir = tk.StringVar()
        self.file_map = []

        #UI widgets (initialized to None, created in build_widgets
        self.results_list = None
        self.detail_label = None
        self.status_label = None

        self.build_widgets()

    def build_widgets(self):
        # --- Top row: folder picker ---
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=10)

        tk.Entry(top_frame, textvariable=self.selected_dir, width=60).pack(side="left", padx=(0, 5))
        tk.Button(top_frame, text="Browse...", command=self.browse_folder).pack(side="left")
        tk.Button(top_frame, text="Scan", command=self.run_scan, bg="#4CAF50", fg="white").pack(side="left", padx=5)

        # --- Middle: results list with checkboxes ---
        mid_frame = tk.Frame(self.root)
        mid_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        scrollbar = tk.Scrollbar(mid_frame)
        scrollbar.pack(side="right", fill="y")

        self.results_list = tk.Listbox(mid_frame, selectmode="browse", yscrollcommand=scrollbar.set)
        self.results_list.pack(fill="both", expand=True)
        scrollbar.config(command=self.results_list.yview)

        # Detail panel: shows full path of whatever is clicked
        self.detail_label = tk.Label(self.root, text="Click a file to see its full path here.",
                                     anchor="w", wraplength=730, justify="left",
                                     bg="#f0f0f0", relief="sunken", padx=5, pady=3)
        self.detail_label.pack(fill="x", padx=10, pady=(0, 5))

        self.results_list.bind("<<ListboxSelect>>", self.show_full_path)

        # --- Bottom: status + action buttons ---
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.status_label = tk.Label(bottom_frame, text="No scan run yet.", anchor="w")
        self.status_label.pack(side="left")

        tk.Button(bottom_frame, text="Move Selected to RecycleBin",
                  command=self.recycle_selected, bg="#2196F3", fg="white").pack(side="right", padx=5)
        tk.Button(bottom_frame, text="Delete Selected Permanently",
                  command=self.delete_selected, bg="#f44336", fg="white").pack(side="right")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.selected_dir.set(folder)

    def run_scan(self):
        folder = self.selected_dir.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder first.")
            return

        self.status_label.config(text="Scanning...")
        self.root.update_idletasks()   # force the label to redraw before the (blocking) scan starts

        self.duplicates = find_duplicates(folder)
        self.populate_results()

    def populate_results(self):
        self.results_list.delete(0, tk.END)   # clear old results
        self.file_map = {}   # parallel list: maps listbox row index -> actual file path

        if not self.duplicates:
            self.status_label.config(text="No duplicates found.")
            return

        # Build a list of (wasted_space, file_hash, paths) so we can sort by wasted space
        groups_with_waste = []
        for file_hash, paths in self.duplicates.items():
            size = os.path.getsize(paths[0])
            wasted = size * (len(paths) - 1)
            groups_with_waste.append((wasted, file_hash, paths))

        # Sort biggest wasted space first
        groups_with_waste.sort(key=lambda x: x[0], reverse=True)

        total_wasted = 0
        for group_num, (wasted, file_hash, paths) in enumerate(groups_with_waste, start=1):
            size = os.path.getsize(paths[0])
            total_wasted += wasted

            self.results_list.insert(tk.END, f"--- Group #{group_num} ({format_size(size)} each) ---")
            self.file_map.append(None)   # header row, not selectable/deletable

            for i, path in enumerate(paths):
                filename = os.path.basename(path) # just the filename not the full path
                tag = "[KEEP]" if i == 0 else "[DUPLICATE]"
                self.results_list.insert(tk.END, f"   {tag} {filename}")  # show filename only
                self.file_map.append(path if i > 0 else None)  # full path still stored here

        self.status_label.config(
            text=f"{len(self.duplicates)} duplicate groups • {format_size(total_wasted)} can be freed"
        )

    def show_full_path(self, _event = None):
        """Show the full path of whatever row is currently selected, in the detail panel below the list."""
        selected_indices = self.results_list.curselection()
        if not selected_indices:
            return

        index = selected_indices[0]  # just show the first selected one if multiple are selected
        path = str(self.file_map[index]) if self.file_map[index] else None

        if path is None:
            self.detail_label.config(text="(This is a group header — select a file row instead.)")
        else:
            self.detail_label.config(text=path)

    def get_selected_paths(self):
        """Return actual file paths for whatever rows the user has checked/selected."""
        selected_indices = self.results_list.curselection()
        paths = [str(self.file_map[i]) for i in selected_indices if self.file_map[i] is not None]
        return paths

    def delete_selected(self):
        paths = self.get_selected_paths()
        if not paths:
            messagebox.showinfo("Nothing selected", "Select one or more duplicate files first.")
            return

        confirm = messagebox.askyesno(
            "Confirm delete",
            f"Permanently delete {len(paths)} file(s)? This cannot be undone."
        )
        if not confirm:
            return

        for file_path in paths:  # Changed 'path' to 'file_path'
            try:
                os.remove(file_path)
            except OSError as e:
                messagebox.showwarning("Error", f"Could not delete {file_path}: {e}")

        messagebox.showinfo("Done", f"Deleted {len(paths)} file(s).")
        self.run_scan()

    def recycle_selected(self):
        paths = self.get_selected_paths()
        if not paths:
            messagebox.showinfo("Nothing selected", "Select one or more duplicate files first.")
            return

        recycle_dir = "recycleBin"
        os.makedirs(recycle_dir, exist_ok=True)

        moved = 0
        for path in paths:
            path = str(path)  # inside the loop
            filename = os.path.basename(path)
            destination = os.path.join(recycle_dir, filename)
            counter = 1
            while os.path.exists(destination):
                name, ext = os.path.splitext(filename)
                destination = os.path.join(recycle_dir, f"{name}_{counter}{ext}")
                counter += 1
            try:
                shutil.move(path, destination)
                moved += 1
            except OSError as e:
                messagebox.showwarning("Error", f"Could not move {path}: {e}")

        messagebox.showinfo("Done", f"Moved {moved} file(s) to '{recycle_dir}'.")
        self.run_scan()

if __name__ == "__main__":
    main_window = tk.Tk()
    app = DuplicateFinderGUI(main_window)
    main_window.mainloop()