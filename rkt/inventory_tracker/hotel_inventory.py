import json
import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# File paths
INVENTORY_FILE = 'inventory.json'
HISTORY_FILE = 'inventory_log.json'

def load_inventory():
    """Load inventory from file if it exists, otherwise return empty dict."""
    if os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_inventory(inventory):
    """Save inventory to file."""
    with open(INVENTORY_FILE, 'w') as file:
        json.dump(inventory, file, indent=4)

def load_history():
    """Load history from file if it exists, otherwise return empty list."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as file:
            return json.load(file)
    return []

def save_history(history):
    """Save history to file."""
    with open(HISTORY_FILE, 'w') as file:
        json.dump(history, file, indent=4)

def log_action(history, action, product, quantity=0):
    """Log an action with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history.append({"timestamp": timestamp, "action": action, "product": product, "quantity": quantity})
    save_history(history)

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hotel Inventory Management")
        self.inventory = load_inventory()
        self.history = load_history()

        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Inventory table
        self.tree = ttk.Treeview(
            self.main_frame,
            columns=("Product", "Added", "Used", "Remaining", "Threshold"),
            show="headings",
            height=10
        )
        self.tree.heading("Product", text="Product")
        self.tree.heading("Added", text="Added")
        self.tree.heading("Used", text="Used")
        self.tree.heading("Remaining", text="Remaining")
        self.tree.heading("Threshold", text="Threshold")
        self.tree.column("Product", width=150)
        self.tree.column("Added", width=80)
        self.tree.column("Used", width=80)
        self.tree.column("Remaining", width=80)
        self.tree.column("Threshold", width=80)
        self.tree.grid(row=0, column=0, columnspan=7, pady=5)
        self.tree.tag_configure("low_stock", background="red", foreground="white")

        # Scrollbar for table
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=7, sticky=(tk.N, tk.S))

        # Buttons
        ttk.Button(self.main_frame, text="Add Product", command=self.add_product).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(self.main_frame, text="Add Stock", command=self.add_stock).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(self.main_frame, text="Use Stock", command=self.use_stock).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(self.main_frame, text="Delete Product", command=self.delete_product).grid(row=1, column=3, padx=5, pady=5)
        ttk.Button(self.main_frame, text="View History", command=self.view_history).grid(row=1, column=4, padx=5, pady=5)
        ttk.Button(self.main_frame, text="View Chart", command=self.view_chart).grid(row=1, column=5, padx=5, pady=5)
        ttk.Button(self.main_frame, text="Export Report", command=self.export_report).grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(self.main_frame, text="Backup", command=self.backup_inventory).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(self.main_frame, text="Restore", command=self.restore_inventory).grid(row=2, column=2, padx=5, pady=5)
        ttk.Button(self.main_frame, text="Exit", command=self.exit_app).grid(row=2, column=3, padx=5, pady=5)

        # Initial table update and low stock check
        self.update_table()
        self.check_low_stock()

    def update_table(self):
        """Update the inventory table display."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        for product, data in self.inventory.items():
            remaining = data['added'] - data['used']
            tags = ("low_stock",) if remaining <= data.get('threshold', 0) else ()
            self.tree.insert("", tk.END, values=(
                product.capitalize(), data['added'], data['used'], remaining, data['threshold']
            ), tags=tags)

    def check_low_stock(self):
        """Check for low stock and display alert."""
        low_stock = [
            product for product, data in self.inventory.items()
            if (data['added'] - data['used']) <= data.get('threshold', 0)
        ]
        if low_stock:
            messagebox.showwarning(
                "Low Stock Alert",
                f"Low stock for: {', '.join(product.capitalize() for product in low_stock)}"
            )

    def add_product(self):
        """Open a dialog to add a new product."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Product")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Product Name:").pack(pady=5)
        entry = ttk.Entry(dialog)
        entry.pack(pady=5)
        ttk.Label(dialog, text="Low Stock Threshold:").pack(pady=5)
        threshold_entry = ttk.Entry(dialog)
        threshold_entry.pack(pady=5)

        def submit():
            product = entry.get().strip().lower()
            try:
                threshold = int(threshold_entry.get())
                if threshold < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Please enter a non-negative integer for threshold.", parent=dialog)
                return
            if not product:
                messagebox.showerror("Error", "Product name cannot be empty.", parent=dialog)
                return
            if product in self.inventory:
                messagebox.showerror("Error", f"Product '{product}' already exists.", parent=dialog)
            else:
                self.inventory[product] = {'added': 0, 'used': 0, 'threshold': threshold}
                log_action(self.history, "add_product", product)
                save_inventory(self.inventory)
                self.update_table()
                self.check_low_stock()
                messagebox.showinfo("Success", f"Product '{product}' added.", parent=dialog)
                dialog.destroy()

        ttk.Button(dialog, text="Submit", command=submit).pack(pady=5)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)

    def add_stock(self):
        """Open a dialog to add stock to a product."""
        if not self.inventory:
            messagebox.showerror("Error", "No products in inventory.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Add Stock")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Select Product:").pack(pady=5)
        product_var = tk.StringVar()
        product_menu = ttk.Combobox(dialog, textvariable=product_var, values=list(self.inventory.keys()))
        product_menu.pack(pady=5)

        ttk.Label(dialog, text="Quantity to Add:").pack(pady=5)
        quantity_entry = ttk.Entry(dialog)
        quantity_entry.pack(pady=5)

        def submit():
            product = product_var.get().lower()
            if not product:
                messagebox.showerror("Error", "Please select a product.", parent=dialog)
                return
            try:
                quantity = int(quantity_entry.get())
                if quantity <= 0:
                    raise ValueError
                self.inventory[product]['added'] += quantity
                log_action(self.history, "add_stock", product, quantity)
                save_inventory(self.inventory)
                self.update_table()
                self.check_low_stock()
                messagebox.showinfo("Success", f"Added {quantity} units to '{product}'.", parent=dialog)
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a positive integer for quantity.", parent=dialog)

        ttk.Button(dialog, text="Submit", command=submit).pack(pady=5)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)

    def use_stock(self):
        """Open a dialog to record stock usage."""
        if not self.inventory:
            messagebox.showerror("Error", "No products in inventory.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Use Stock")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Select Product:").pack(pady=5)
        product_var = tk.StringVar()
        product_menu = ttk.Combobox(dialog, textvariable=product_var, values=list(self.inventory.keys()))
        product_menu.pack(pady=5)

        ttk.Label(dialog, text="Quantity Used:").pack(pady=5)
        quantity_entry = ttk.Entry(dialog)
        quantity_entry.pack(pady=5)

        def submit():
            product = product_var.get().lower()
            if not product:
                messagebox.showerror("Error", "Please select a product.", parent=dialog)
                return
            try:
                quantity = int(quantity_entry.get())
                if quantity <= 0:
                    raise ValueError
                remaining = self.inventory[product]['added'] - self.inventory[product]['used']
                if quantity > remaining:
                    messagebox.showerror("Error", f"Insufficient stock. Only {remaining} units left for '{product}'.", parent=dialog)
                    return
                self.inventory[product]['used'] += quantity
                log_action(self.history, "use_stock", product, quantity)
                save_inventory(self.inventory)
                self.update_table()
                self.check_low_stock()
                messagebox.showinfo("Success", f"Used {quantity} units from '{product}'.", parent=dialog)
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a positive integer for quantity.", parent=dialog)

        ttk.Button(dialog, text="Submit", command=submit).pack(pady=5)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)

    def delete_product(self):
        """Open a dialog to delete a product."""
        if not self.inventory:
            messagebox.showerror("Error", "No products in inventory.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Delete Product")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Select Product to Delete:").pack(pady=5)
        product_var = tk.StringVar()
        product_menu = ttk.Combobox(dialog, textvariable=product_var, values=list(self.inventory.keys()))
        product_menu.pack(pady=5)

        def submit():
            product = product_var.get().lower()
            if not product:
                messagebox.showerror("Error", "Please select a product.", parent=dialog)
                return
            if messagebox.askyesno("Confirm", f"Are you sure you want to delete '{product}'?", parent=dialog):
                del self.inventory[product]
                log_action(self.history, "delete_product", product)
                save_inventory(self.inventory)
                self.update_table()
                messagebox.showinfo("Success", f"Product '{product}' deleted.", parent=dialog)
                dialog.destroy()

        ttk.Button(dialog, text="Submit", command=submit).pack(pady=5)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)

    def view_history(self):
        """Open a dialog to view history log."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Inventory History")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()

        tree = ttk.Treeview(
            dialog,
            columns=("Timestamp", "Action", "Product", "Quantity"),
            show="headings",
            height=15
        )
        tree.heading("Timestamp", text="Timestamp")
        tree.heading("Action", text="Action")
        tree.heading("Product", text="Product")
        tree.heading("Quantity", text="Quantity")
        tree.column("Timestamp", width=150)
        tree.column("Action", width=100)
        tree.column("Product", width=150)
        tree.column("Quantity", width=100)
        tree.pack(pady=10, padx=10)

        scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for entry in self.history:
            tree.insert("", tk.END, values=(
                entry['timestamp'],
                entry['action'],
                entry['product'].capitalize(),
                entry['quantity']
            ))

        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=5)

    def view_chart(self):
        """Open a dialog to display a bar chart of remaining stock."""
        if not self.inventory:
            messagebox.showerror("Error", "No products in inventory.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Inventory Chart")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()

        products = list(self.inventory.keys())
        remaining = [self.inventory[p]['added'] - self.inventory[p]['used'] for p in products]

        fig, ax = plt.subplots()
        ax.bar(products, remaining)
        ax.set_xlabel("Products")
        ax.set_ylabel("Remaining Stock")
        ax.set_title("Inventory Levels")
        plt.xticks(rotation=45, ha="right")

        canvas = FigureCanvasTkAgg(fig, master=dialog)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10)

        ttk.Button(dialog, text="Close", command=lambda: [plt.close(fig), dialog.destroy()]).pack(pady=5)

    def export_report(self):
        """Export inventory or history as CSV."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Export Report")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Select Report Type:").pack(pady=5)
        report_type = tk.StringVar(value="inventory")
        ttk.Radiobutton(dialog, text="Inventory", value="inventory", variable=report_type).pack()
        ttk.Radiobutton(dialog, text="History", value="history", variable=report_type).pack()

        def submit():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                parent=dialog
            )
            if not file_path:
                return
            if report_type.get() == "inventory":
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Product", "Added", "Used", "Remaining", "Threshold"])
                    for product, data in self.inventory.items():
                        remaining = data['added'] - data['used']
                        writer.writerow([product.capitalize(), data['added'], data['used'], remaining, data['threshold']])
            else:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Action", "Product", "Quantity"])
                    for entry in self.history:
                        writer.writerow([entry['timestamp'], entry['action'], entry['product'], entry['quantity']])
            messagebox.showinfo("Success", f"Report exported to {file_path}.", parent=dialog)
            dialog.destroy()

        ttk.Button(dialog, text="Export", command=submit).pack(pady=5)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)

    def backup_inventory(self):
        """Create a timestamped backup of the inventory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"inventory_backup_{timestamp}.json"
        with open(backup_file, 'w') as f:
            json.dump(self.inventory, f, indent=4)
        messagebox.showinfo("Success", f"Backup created: {backup_file}")

    def restore_inventory(self):
        """Restore inventory from a backup file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            parent=self.root
        )
        if not file_path:
            return
        try:
            with open(file_path, 'r') as f:
                restored_inventory = json.load(f)
            self.inventory = restored_inventory
            save_inventory(self.inventory)
            self.update_table()
            self.check_low_stock()
            log_action(self.history, "restore_inventory", "all")
            messagebox.showinfo("Success", f"Inventory restored from {file_path}.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore inventory: {str(e)}")

    def exit_app(self):
        """Save inventory and history, then exit."""
        save_inventory(self.inventory)
        save_history(self.history)
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()