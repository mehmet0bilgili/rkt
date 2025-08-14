import csv
import os
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

# kurları tanımla ve işlem yöntemlerini belirle
CURRENCIES = ['TRY', 'EUR', 'USD', 'GBP']
INFLOW_METHODS = ['mail_order', 'credit_card', 'havale', 'cash']
# dosya adlarını tanımla
TRANSACTIONS_FILE = 'transactions.csv'
ARCHIVE_FILE_PREFIX = 'archive_'

# nakit ve girişleri initilize et
def load_balances_and_totals():
    balances = {currency: 0.0 for currency in CURRENCIES}
    inflow_totals = {method: {currency: 0.0 for currency in CURRENCIES} for method in INFLOW_METHODS}
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 6:
                    continue
                if row[0] == 'inflow':
                    method, currency, amount = row[1], row[3], float(row[4])
                    inflow_totals[method][currency] += amount
                    if method == 'cash':
                        balances[currency] += amount
                elif row[0] == 'outflow':
                    balances[row[2]] -= float(row[3])
    return balances, inflow_totals

balances, inflow_totals = load_balances_and_totals()

# işlemleri kaydetme fonksiyonu
def record_transaction(transaction_type, method=None, currency=None, amount=None):
    if transaction_type == 'inflow':
        if method not in INFLOW_METHODS:
            raise ValueError("Invalid inflow method.")
        inflow_totals[method][currency] += amount
        if method == 'cash':
            balances[currency] += amount
    elif transaction_type == 'outflow':
        if balances[currency] < amount:
            raise ValueError("Insufficient cash balance for outflow.")
        balances[currency] -= amount
        method = 'cash'  # giderler hep nakit tipinde kaydedilir
    else:
        raise ValueError("Invalid transaction type.")

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(TRANSACTIONS_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if transaction_type == 'inflow':
            writer.writerow([transaction_type, method, '', currency, amount, timestamp])
        else:
            writer.writerow([transaction_type, method, currency, amount, '', timestamp])

# özeti gösteren fonksiyon
def display_summary():
    summary_text = "Current Cash Balances:\n"
    for currency, balance in balances.items():
        summary_text += f"{currency}: {balance:.2f}\n"
    
    summary_text += "\nTotal Inflows by Payment Method:\n"
    for method in INFLOW_METHODS:
        summary_text += f"\n{method.replace('_', ' ').title()}:\n"
        for currency in CURRENCIES:
            amount = inflow_totals[method][currency]
            if amount > 0:
                summary_text += f"  {currency}: {amount:.2f}\n"
    
    summary_text += "\nRecent Transactions (last 10):\n"
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, 'r') as f:
            rows = list(csv.reader(f))[-10:]
            for row in rows:
                if len(row) < 6:
                    continue
                if row[0] == 'inflow':
                    summary_text += f"Inflow via {row[1]}: {row[4]} {row[3]} at {row[5]}\n"
                else:
                    summary_text += f"Outflow: {row[3]} {row[2]} at {row[5]}\n"
    else:
        summary_text += "No transactions recorded yet.\n"
    
    return summary_text

# günlük sıfırlama fonksiyonu daily reset
def daily_reset():
    if os.path.exists(TRANSACTIONS_FILE):
        archive_file = f"{ARCHIVE_FILE_PREFIX}{datetime.now().strftime('%Y%m%d')}.csv"
        os.rename(TRANSACTIONS_FILE, archive_file)
    global balances, inflow_totals
    balances = {currency: 0.0 for currency in CURRENCIES}
    inflow_totals = {method: {currency: 0.0 for currency in CURRENCIES} for method in INFLOW_METHODS}
    return f"Transactions archived to {archive_file}. Balances and totals reset for new day."

# kullanıcı arayüzü için tkinter uygulaması
class HotelCashTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hotel Cash Tracker")
        self.root.geometry("600x400")

        # Inflow Frame
        self.inflow_frame = tk.LabelFrame(root, text="Record Inflow", padx=10, pady=10)
        self.inflow_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(self.inflow_frame, text="Method:").grid(row=0, column=0, sticky="w")
        self.inflow_method = ttk.Combobox(self.inflow_frame, values=INFLOW_METHODS, state="readonly")
        self.inflow_method.grid(row=0, column=1, padx=5, pady=5)
        self.inflow_method.set(INFLOW_METHODS[0])

        tk.Label(self.inflow_frame, text="Currency:").grid(row=1, column=0, sticky="w")
        self.inflow_currency = ttk.Combobox(self.inflow_frame, values=CURRENCIES, state="readonly")
        self.inflow_currency.grid(row=1, column=1, padx=5, pady=5)
        self.inflow_currency.set(CURRENCIES[0])

        tk.Label(self.inflow_frame, text="Amount:").grid(row=2, column=0, sticky="w")
        self.inflow_amount = tk.Entry(self.inflow_frame)
        self.inflow_amount.grid(row=2, column=1, padx=5, pady=5)

        tk.Button(self.inflow_frame, text="Record Inflow", command=self.record_inflow).grid(row=3, column=0, columnspan=2, pady=10)

        # Outflow Frame
        self.outflow_frame = tk.LabelFrame(root, text="Record Outflow", padx=10, pady=10)
        self.outflow_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(self.outflow_frame, text="Currency:").grid(row=0, column=0, sticky="w")
        self.outflow_currency = ttk.Combobox(self.outflow_frame, values=CURRENCIES, state="readonly")
        self.outflow_currency.grid(row=0, column=1, padx=5, pady=5)
        self.outflow_currency.set(CURRENCIES[0])

        tk.Label(self.outflow_frame, text="Amount:").grid(row=1, column=0, sticky="w")
        self.outflow_amount = tk.Entry(self.outflow_frame)
        self.outflow_amount.grid(row=1, column=1, padx=5, pady=5)

        tk.Button(self.outflow_frame, text="Record Outflow", command=self.record_outflow).grid(row=2, column=0, columnspan=2, pady=10)

        # Action Buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(self.button_frame, text="View Summary", command=self.show_summary).pack(side="left", padx=5)
        tk.Button(self.button_frame, text="Daily Reset", command=self.perform_reset).pack(side="left", padx=5)
        tk.Button(self.button_frame, text="Exit", command=self.root.quit).pack(side="left", padx=5)

        # Summary Area
        self.summary_area = tk.Text(root, height=10, width=60, state="disabled")
        self.summary_area.pack(padx=10, pady=5)
        self.scrollbar = tk.Scrollbar(root, orient="vertical", command=self.summary_area.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.summary_area.config(yscrollcommand=self.scrollbar.set)

    def record_inflow(self):
        try:
            method = self.inflow_method.get()
            currency = self.inflow_currency.get()
            amount = float(self.inflow_amount.get())
            if amount <= 0:
                raise ValueError("Amount must be positive.")
            record_transaction('inflow', method, currency, amount)
            messagebox.showinfo("Success", "Inflow recorded successfully.")
            self.inflow_amount.delete(0, tk.END)
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")

    def record_outflow(self):
        try:
            currency = self.outflow_currency.get()
            amount = float(self.outflow_amount.get())
            if amount <= 0:
                raise ValueError("Amount must be positive.")
            record_transaction('outflow', currency=currency, amount=amount)
            messagebox.showinfo("Success", "Outflow recorded successfully.")
            self.outflow_amount.delete(0, tk.END)
        except ValueError as e:
            messagebox.showerror("Error", f"Error: {e}")

    def show_summary(self):
        self.summary_area.config(state="normal")
        self.summary_area.delete(1.0, tk.END)
        self.summary_area.insert(tk.END, display_summary())
        self.summary_area.config(state="disabled")

    def perform_reset(self):
        if messagebox.askyesno("Confirm", "Confirm daily reset? This will archive transactions and reset balances and totals."):
            message = daily_reset()
            messagebox.showinfo("Reset Complete", message)
            self.show_summary()

# csv dosyası yoksa oluştur
if not os.path.exists(TRANSACTIONS_FILE):
    with open(TRANSACTIONS_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['type', 'method', 'outflow_currency', 'outflow_amount', 'inflow_currency', 'inflow_amount', 'timestamp'])

# app i başlat
root = tk.Tk()
app = HotelCashTrackerApp(root)
root.mainloop()