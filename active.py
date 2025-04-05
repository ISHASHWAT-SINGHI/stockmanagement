import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime

# Database setup
def setup_database():
    conn = sqlite3.connect('stock_management.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY,
            name TEXT,
            gst_number TEXT,
            contact TEXT
        )
    ''')
    # cursor.execute('DROP TABLE IF EXISTS purchases')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            address TEXT,
            gst_number TEXT,
            contact TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            company_id INTEGER,
            brand TEXT,
            product_name TEXT,
            quantity INTEGER,
            unit_price REAL,
            cgst REAL,
            sgst REAL,
            cess REAL,
            purchase_date TEXT,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gst_slabs (
            id INTEGER PRIMARY KEY,
            gst_rate REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            year INTEGER PRIMARY KEY,
            last_invoice_number INTEGER
        )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT,
    product_name TEXT,
    quantity INTEGER,
    unit_price REAL,
    total_price REAL,
    purchase_date DATETIME
    );
    ''')
                   
    # Create billing table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS billing (
            bill_number INTEGER PRIMARY KEY,
            customer_name TEXT,
            total_amount REAL,
            bill_date TEXT
        )
    ''')
    # Initialize the settings table for the current year
    current_year = datetime.now().year
    cursor.execute("INSERT OR IGNORE INTO settings (year, last_invoice_number) VALUES (?, ?)", (current_year, 0))

    conn.commit()
    conn.close()

# Main Application Class
class StockManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stock Management System")
        self.root.geometry("800x600")

        # Initialize total CGST and SGST
        self.total_cgst = 0.0
        self.total_sgst = 0.0

        # List to store added items
        self.added_items = []
        
        self.company_window = None
        self.product_window = None
        self.customer_window = None
        self.temp_products = [] # Temporary list to store products
        self.setup_menu()  # Set up the menu
        self.setup_ui()
        setup_database()
    
    def setup_menu(self):
        # Create a menu bar
        menubar = tk.Menu(self.root)
        
        # Create a 'File' menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Add GST Slab", command=self.add_gst_slab)
        file_menu.add_command(label="View Purchases", command=self.open_purchases_window)  # New method
        file_menu.add_command(label="View Bills", command=self.open_bills_window)  # New method
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="☰", menu=file_menu)

        # Configure the menu
        self.root.config(menu=menubar)

    def setup_ui(self):
        # Main Frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Product List
        self.product_list = ttk.Treeview(self.main_frame, columns=("Company", "Brand", "Product Name", "Quantity", "Unit Price", "CGST", "SGST", "CESS", "Purchase Date"), show='headings')
        for col in self.product_list["columns"]:
            self.product_list.heading(col, text=col)
        self.product_list.pack(fill=tk.BOTH, expand=True)

        # Buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Add Company", command=self.add_company).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_frame, text="Add Customer", command=self.add_customer).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_frame, text="Add Stock", command=self.add_product).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_frame, text="Generate Bill", command=self.generate_bill).pack(side=tk.LEFT, padx=5, pady=5)

        # Load products on startup 
        self.load_products()

    def add_gst_slab(self):
        # Function to add GST Slab
        slab = simpledialog.askstring("Input", "Enter GST Slab:")
        rate = simpledialog.askfloat("Input", "Enter GST Rate (%):")
        
        if slab and rate is not None:
            # Insert into the database
            conn = sqlite3.connect('stock_management.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO gst_slabs (gst_rate) VALUES (?)", (rate,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", f"GST Slab {slab} with rate {rate}% added successfully.")
        else:
            messagebox.showwarning("Input Error", "Please enter valid slab and rate.")

    def load_products(self):
        # Clear the current items in the Treeview
        for item in self.product_list.get_children():
            self.product_list.delete(item)

        # Fetch products from the database
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.name, p.brand, p.product_name, p.quantity, p.unit_price, p.cgst, p.sgst, p.cess, p.purchase_date
            FROM products p
            JOIN companies c ON p.company_id = c.id
        ''')
        products = cursor.fetchall()
        conn.close()

        # Insert fetched products into the Treeview
        for product in products:
            self.product_list.insert("", "end", values=product)

    def save_purchase(self, product_name, quantity, unit_price, total_price):
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO purchases (product_name, quantity, unit_price, total_price, purchase_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_name, quantity, unit_price, total_price, datetime.now()))
        conn.commit()
        conn.close()

    def save_bill(self, customer_name, total_amount):
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO billing (customer_name, total_amount, bill_date)
            VALUES (?, ?, ?)
        ''', (customer_name, total_amount, datetime.now()))
        conn.commit()
        conn.close()

    def open_purchases_window(self):
        purchases_window = tk.Toplevel(self.root)
        purchases_window.title("Purchases")

        # Create a Treeview for displaying purchases
        self.purchases_tree = ttk.Treeview(purchases_window, columns=("Transaction ID", "Product Name", "Quantity", "Unit Price", "Total Price", "Purchase Date"), show='headings')
        for col in self.purchases_tree["columns"]:
            self.purchases_tree.heading(col, text=col)
        self.purchases_tree.pack(fill=tk.BOTH, expand=True)

        # Load purchases into the Treeview
        self.load_purchases()

    def load_purchases(self):
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM purchases')
        purchases = cursor.fetchall()
        conn.close()

        # Clear existing entries in the Treeview
        for row in self.purchases_tree.get_children():
            self.purchases_tree.delete(row)

        # Insert new entries
        for purchase in purchases:
            self.purchases_tree.insert("", tk.END, values=(purchase[0], purchase[1], purchase[2], purchase[3], purchase[4], purchase[5]))

    def add_company(self):
        if self.company_window is not None and self.company_window.winfo_exists():
            messagebox.showwarning("Warning", "The company window is already open.")
            return

        # Create a new window for adding company details
        self.company_window = tk.Toplevel(self.root)
        self.company_window.title("Add Company")
        self.company_window.geometry("400x300")

        # Company Name
        tk.Label(self.company_window, text="Company Name:").pack(pady=5)
        self.company_name_entry = tk.Entry(self.company_window)
        self.company_name_entry.pack(pady=5)

        # GST Number
        tk.Label(self.company_window, text="GST Number:").pack(pady=5)
        self.gst_number_entry = tk.Entry(self.company_window)
        self.gst_number_entry.pack(pady=5)

        # Contact
        tk.Label(self.company_window, text="Contact:").pack(pady=5)
        self.contact_entry = tk.Entry(self.company_window)
        self.contact_entry.pack(pady=5)

        # Save Button
        ttk.Button(self.company_window, text="Save", command=self.save_company).pack(pady=20)

    def save_company(self):
        # Get the values from the entry fields
        company_name = self.company_name_entry.get()
        gst_number = self.gst_number_entry.get()
        contact = self.contact_entry.get()

        # Insert the company data into the database
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO companies (name, gst_number, contact) VALUES (?, ?, ?)
        ''', (company_name, gst_number, contact))
        conn.commit()
        conn.close()

        # Clear the entry fields
        self.company_name_entry.delete(0, tk.END)
        self.gst_number_entry.delete(0, tk.END)
        self.contact_entry.delete(0, tk.END)

        # Close the company window
        if self.company_window is not None:
            self.company_window.destroy()
            self.company_window = None
        # Show a success message
        messagebox.showinfo("Success", "Company added successfully!")

    def add_customer(self):
        # Check if the customer window is already open
        if self.customer_window is not None and self.customer_window.winfo_exists():
            messagebox.showwarning("Warning", "The customer window is already open.")
            return

        # Create a new window for adding customer details
        self.customer_window = tk.Toplevel(self.root)
        self.customer_window.title("Add Customer")
        self.customer_window.geometry("400x400")

        # Create a canvas and a scrollbar
        canvas = tk.Canvas(self.customer_window)
        scrollbar = ttk.Scrollbar(self.customer_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Configure the canvas
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Set the scrollbar to the canvas
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack the canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # UI elements for customer entry
        tk.Label(scrollable_frame, text="Customer Name:").pack(pady=5)
        self.customer_name_entry = tk.Entry(scrollable_frame)
        self.customer_name_entry.pack(pady=5)

        tk.Label(scrollable_frame, text="GST Number (optional):").pack(pady=5)
        self.gst_number_entry = tk.Entry(scrollable_frame)
        self.gst_number_entry.pack(pady=5)

        tk.Label(scrollable_frame, text="Contact Number:").pack(pady=5)
        self.contact_number_entry = tk.Entry(scrollable_frame)
        self.contact_number_entry.pack(pady=5)

        tk.Label(scrollable_frame, text="Address:").pack(pady=5)
        self.address_entry = tk.Entry(scrollable_frame)
        self.address_entry.pack(pady=5)

        # Button to save the customer
        ttk.Button(scrollable_frame, text="Add Customer", command=self.save_customer).pack(pady=20)
    
    def save_customer(self):
        customer_name = self.customer_name_entry.get()
        contact_number = self.contact_number_entry.get()
        address = self.address_entry.get()

        # Validate inputs
        if not customer_name or not contact_number or not address:
            messagebox.showerror("Error", "Please fill in all required fields.")
            return

        # Connect to the database and insert the customer
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO customers (name, contact, address, gst_number) VALUES (?, ?, ?, ?)
        ''', (customer_name, contact_number, address, ""))  # Assuming gst_number is optional
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Customer added successfully!")

        # Clear the entry fields
        self.customer_name_entry.delete(0, tk.END)
        self.contact_number_entry.delete(0, tk.END)
        self.address_entry.delete(0, tk.END)
        self.gst_number_entry.delete(0, tk.END)  # Clear GST number field

        # Close the customer window
        if self.customer_window is not None:
            self.customer_window.destroy()
            self.customer_window = None  # Reset the reference

    def add_product(self):
        # Check if the product window is already open
        if self.product_window is not None and self.product_window.winfo_exists():
            messagebox.showwarning("Warning", "The product window is already open.")
            return

        # Create a new window for adding product details
        self.product_window = tk.Toplevel(self.root)
        self.product_window.title("Add Product")
        self.product_window.geometry("600x500")

        # Create a canvas and a scrollbar
        canvas = tk.Canvas(self.product_window)
        scrollbar = ttk.Scrollbar(self.product_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Configure the canvas
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Set the scrollbar to the canvas
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack the canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Transaction ID
        tk.Label(scrollable_frame, text="Transaction ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.transaction_id_entry = tk.Entry(scrollable_frame)
        self.transaction_id_entry.grid(row=0, column=1, padx=5, pady=5)

        # Company selection
        tk.Label(scrollable_frame, text="Select Company:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.company_combobox = ttk.Combobox(scrollable_frame)
        self.company_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.load_companies()  # Load companies into the combobox

        # UI elements for product entry
        tk.Label(scrollable_frame, text="Brand:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.brand_entry = tk.Entry(scrollable_frame)
        self.brand_entry.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(scrollable_frame, text="Product Name:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.product_name_entry = tk.Entry(scrollable_frame)
        self.product_name_entry.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(scrollable_frame, text="Quantity:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.quantity_entry = tk.Entry(scrollable_frame)
        self.quantity_entry.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(scrollable_frame, text="Unit Price:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.unit_price_entry = tk.Entry(scrollable_frame)
        self.unit_price_entry.grid(row=5, column=1, padx=5, pady=5)

        # GST Slab Selection
        tk.Label(scrollable_frame, text="Select GST Slab:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.gst_slab_combobox = ttk.Combobox(scrollable_frame)
        self.gst_slab_combobox.grid(row=6, column=1, padx=5, pady=5)
        self.load_gst_slabs()  # Load GST slabs into the combobox
        self.gst_slab_combobox.bind("<<ComboboxSelected>>", self.update_gst_values)

        tk.Label(scrollable_frame, text="CGST:").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        self.cgst_entry = tk.Entry(scrollable_frame)
        self.cgst_entry.grid(row=7, column=1, padx=5, pady=5)

        tk.Label(scrollable_frame, text="SGST:").grid(row=8, column=0, padx=5, pady=5, sticky="w")
        self.sgst_entry = tk.Entry(scrollable_frame)
        self.sgst_entry.grid(row=8, column=1, padx=5, pady=5)

        tk.Label(scrollable_frame, text="CESS:").grid(row=9, column=0, padx=5, pady=5, sticky="w")
        self.cess_entry = tk.Entry(scrollable_frame)
        self.cess_entry.grid(row=9, column=1, padx=5, pady=5)

        # Create a Treeview for displaying added products
        self.temp_products_tree = ttk.Treeview(scrollable_frame, columns=("Transaction ID", "Brand", "Product Name", "Quantity", "Unit Price"), show='headings')
        self.temp_products_tree.heading("Transaction ID", text="Transaction ID")
        self.temp_products_tree.heading("Brand", text="Brand")
        self.temp_products_tree.heading("Product Name", text="Product Name")
        self.temp_products_tree.heading("Quantity", text="Quantity")
        self.temp_products_tree.heading("Unit Price", text="Unit Price")

        # Use sticky to make the Treeview expand in all directions
        self.temp_products_tree.grid(row=10, column=0, columnspan=2, sticky="nsew", pady=10)

        # Configure grid weights to allow the Treeview to expand
        scrollable_frame.grid_rowconfigure(10, weight=1)
        scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(1, weight=1)

        # Button frame for actions
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=11, column=0, columnspan=2, pady=5)

        # Button to add product to the temporary list
        ttk.Button(button_frame, text="Add Product", command=self.add_product_to_list).pack(side=tk.LEFT, padx=5)

        # Button to finalize the purchase
        ttk.Button(button_frame, text="Finalize Purchase", command=self.finalize_purchase).pack(side=tk.LEFT, padx=5)

        # Ensure the window is properly sized
        self.product_window.update_idletasks()
        self.product_window.minsize(600, 500)

    
    def add_product_to_list(self):
        transaction_id = self.transaction_id_entry.get()
        brand = self.brand_entry.get()
        product_name = self.product_name_entry.get()
        quantity = self.quantity_entry.get()
        unit_price = self.unit_price_entry.get()
        cgst = self.cgst_entry.get()  # Get CGST value
        sgst = self.sgst_entry.get()  # Get SGST value
        cess = self.cess_entry.get()  # Get CESS value

        # Validate inputs
        if not transaction_id or not brand or not product_name or not quantity or not unit_price:
            messagebox.showerror("Error", "Please fill in all required fields.")
            return

        try:
            quantity = int(quantity)
            unit_price = float(unit_price)
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for quantity and unit price.")
            return

        # Add product details to the Treeview, including CGST, SGST, and CESS
        self.temp_products_tree.insert("", "end", values=(transaction_id, brand, product_name, quantity, unit_price, cgst, sgst, cess))

        # Refresh the Treeview
        self.temp_products_tree.update_idletasks()

        # Clear the entry fields for the next product, but keep transaction_id
        self.brand_entry.delete(0, tk.END)
        self.product_name_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
        self.unit_price_entry.delete(0, tk.END)
        self.cgst_entry.delete(0, tk.END)
        self.sgst_entry.delete(0, tk.END)
        self.cess_entry.delete(0, tk.END)

        # Debugging: Print the current items in the Treeview
        print("Current items in Treeview:")
        for item in self.temp_products_tree.get_children():
            print(self.temp_products_tree.item(item, "values"))

    def finalize_purchase(self):
        # Check if there are any products in the temporary Treeview
        if not self.temp_products_tree.get_children():
            messagebox.showwarning("Warning", "No products to finalize.")
            return

        # Get the transaction ID from the entry field
        transaction_id = self.transaction_id_entry.get()

        # Validate transaction ID
        if not transaction_id:
            messagebox.showerror("Error", "Transaction ID cannot be empty.")
            return

        # Connect to the database
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()

        for item in self.temp_products_tree.get_children():
            values = self.temp_products_tree.item(item, "values")

            # Unpack all values from the Treeview
            transaction_id, brand, product_name, quantity, unit_price, cgst, sgst, cess = values

            # Convert quantity and unit_price to appropriate types
            try:
                quantity = int(quantity)
                unit_price = float(unit_price)
                cgst = float(cgst)
                sgst = float(sgst)
                cess = float(cess)
            except ValueError:
                messagebox.showerror("Error", "Quantity, Unit Price, and tax values must be valid numbers.")
                return

            # Format the current datetime as a string
            purchase_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Check if the product already exists in the products table based on name, brand, and company
            cursor.execute('''
                SELECT id, unit_price FROM products 
                WHERE product_name = ? AND brand = ? AND company_id = ?
            ''', (product_name, brand, self.company_combobox.get()))
            product_data = cursor.fetchone()

            if product_data:
                # Product exists
                product_id, existing_price = product_data

                if existing_price != unit_price:
                    # If the price has changed, insert a new product record
                    cursor.execute('''
                        INSERT INTO products (company_id, brand, product_name, quantity, unit_price, cgst, sgst, cess, purchase_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (self.company_combobox.get(), brand, product_name, quantity, unit_price, cgst, sgst, cess, purchase_date))
                else:
                    # If the price is the same, just update the quantity
                    cursor.execute('''
                        UPDATE products
                        SET quantity = quantity + ?
                        WHERE id = ?
                    ''', (quantity, product_id))
            else:
                # Product does not exist, insert it as a new product
                cursor.execute('''
                    INSERT INTO products (company_id, brand, product_name, quantity, unit_price, cgst, sgst, cess, purchase_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.company_combobox.get(), brand, product_name, quantity, unit_price, cgst, sgst, cess, purchase_date))

            # Save purchase to the database
            cursor.execute('''
                INSERT INTO purchases (transaction_id, product_name, quantity, unit_price, total_price, purchase_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (transaction_id, product_name, quantity, unit_price, quantity * unit_price, purchase_date))

            # Update the main product list with relevant data
            # Assuming you have a way to get the company name, e.g., from the combobox
            selected_company = self.company_combobox.get()  # Get selected company
            self.product_list.insert("", "end", values=(selected_company, brand, product_name, quantity, unit_price, cgst, sgst, cess, purchase_date))

        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "All products have been finalized and saved successfully!")

        # Clear the temporary Treeview after finalization
        for item in self.temp_products_tree.get_children():
            self.temp_products_tree.delete(item)
    

    def load_companies(self):
        # Load companies from the database into the combobox
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM companies")
        companies = cursor.fetchall()
        self.company_combobox['values'] = [company[0] for company in companies]
        conn.close()

    def load_gst_slabs(self):
        # Load GST slabs from the database into the combobox
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()
        cursor.execute("SELECT gst_rate FROM gst_slabs")
        gst_slabs = cursor.fetchall()
        self.gst_slab_combobox['values'] = [gst[0] for gst in gst_slabs]
        conn.close()

    def update_gst_values(self, event):
        # Get the selected GST slab and update CGST and SGST
        selected_gst = self.gst_slab_combobox.get()
        if selected_gst:
            gst_rate = float(selected_gst)
            self.cgst_entry.delete(0, tk.END)
            self.cgst_entry.insert(0, f"{gst_rate / 2:.2f}")
            self.sgst_entry.delete(0, tk.END)
            self.sgst_entry.insert(0, f"{gst_rate / 2:.2f}")

    def calculate_total(self):
        # Calculate total price based on quantity, unit price, CGST, SGST, and CESS
        try:
            quantity = int(self.quantity_entry.get())
            unit_price = float(self.unit_price_entry.get())
            cgst = float(self.cgst_entry.get())
            sgst = float(self.sgst_entry.get())
            cess = float(self.cess_entry.get())
            cgstrate = cgst/100
            sgstrate = sgst/100
            cessrate = cess/100
            cgst_levied = unit_price*cgstrate
            sgst_levied = unit_price*sgstrate
            cess_levied = unit_price*cessrate
            gst=cgst_levied+sgst_levied
            total = (unit_price+cgst_levied+sgst_levied+cess_levied) * quantity
            self.total_price_label.config(text=f"{total:.2f}")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for quantity, unit price, and taxes.")

    def generate_bill(self):
        # Create a new window for bill generation
        self.bill_window = tk.Toplevel(self.root)
        self.bill_window.title("Generate Bill")
        self.bill_window.geometry("500x400")  # Set a reasonable size
        self.bill_window.minsize(400, 300)  # Set a minimum size

        # Customer selection dropdown
        tk.Label(self.bill_window, text="Select Customer:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.customer_dropdown = ttk.Combobox(self.bill_window, values=self.fetch_customers())
        self.customer_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Bind the customer selection event to update the address
        self.customer_dropdown.bind("<<ComboboxSelected>>", self.on_customer_select)

        # Display customer address
        tk.Label(self.bill_window, text="Customer Address:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.customer_address_label = tk.Label(self.bill_window, text="")
        self.customer_address_label.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Product selection Treeview
        tk.Label(self.bill_window, text="Available Products:").grid(row=2, column=0, padx=5, pady=5, sticky="w", columnspan=2)
        self.product_treeview = ttk.Treeview(self.bill_window, columns=("Brand", "Product Name", "Quantity", "Unit Price"), show='headings')
        self.product_treeview.heading("Brand", text="Brand")
        self.product_treeview.heading("Product Name", text="Product Name")
        self.product_treeview.heading("Quantity", text="Quantity")
        self.product_treeview.heading("Unit Price", text="Unit Price")
        self.product_treeview.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # Configure grid weights for resizing
        self.bill_window.grid_rowconfigure(3, weight=1)  # Allow the Treeview to expand
        self.bill_window.grid_columnconfigure(1, weight=1)  # Allow the customer dropdown to expand

        # Load products into the Treeview
        self.load_products_into_treeview()

        # Bind selection event
        self.product_treeview.bind("<<TreeviewSelect>>", self.on_product_select)

        # Quantity entry
        tk.Label(self.bill_window, text="Quantity:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.quantity_entry = tk.Entry(self.bill_window, width=10)  # Limit width
        self.quantity_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        # Selling price entry
        tk.Label(self.bill_window, text="Selling Price:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.selling_price_entry = tk.Entry(self.bill_window, width=10)  # Limit width
        self.selling_price_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        # Button to add item to bill
        ttk.Button(self.bill_window, text="Add Item", command=self.add_item_to_bill).grid(row=6, column=0, columnspan=2, padx=5, pady=10)

        # Create a frame to hold the text area and scrollbars
        bill_frame = ttk.Frame(self.bill_window)
        bill_frame.grid(row=7, column=0, columnspan=2, padx=5, pady=10, sticky="nsew")
        
        # Create a vertical scrollbar
        self.bill_scrollbar = ttk.Scrollbar(bill_frame, orient="vertical")
        self.bill_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create the text area
        self.bill_text_area = tk.Text(bill_frame, height=10, width=50, yscrollcommand=self.bill_scrollbar.set)
        self.bill_text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure the scrollbar
        self.bill_scrollbar.config(command=self.bill_text_area.yview)

        # Button to generate the final bill
        ttk.Button(self.bill_window, text="Generate Bill", command=self.finalize_bill).grid(row=8, column=0, columnspan=2, padx=5, pady=10)
    
    def save_bill(self, invoice_number, customer_name):
        # Save the bill details to a file or database
        with open(f"bill_{invoice_number}.txt", "w") as bill_file:
            bill_file.write(self.bill_text_area.get("1.0", tk.END))
        messagebox.showinfo("Success", f"Bill saved as bill_{invoice_number}.txt")
    
    def open_bills_window(self):
        bills_window = tk.Toplevel(self.root)
        bills_window.title("Bills")

        # Create a Treeview for displaying bills
        self.bills_tree = ttk.Treeview(bills_window, columns=("Bill Number", "Customer Name", "Total Amount", "Bill Date"), show='headings')
        for col in self.bills_tree["columns"]:
            self.bills_tree.heading(col, text=col)
        self.bills_tree.pack(fill=tk.BOTH, expand=True)

        # Add a filter section
        filter_frame = ttk.Frame(bills_window)
        filter_frame.pack(pady=10)

        ttk.Label(filter_frame, text="Filter by Customer Name:").grid(row=0, column=0, padx=5)
        self.customer_filter_entry = ttk.Entry(filter_frame)
        self.customer_filter_entry.grid(row=0, column=1, padx=5)

        ttk.Button(filter_frame, text="Apply Filter", command=self.filter_bills).grid(row=0, column=2, padx=5)

        # Load bills into the Treeview
        self.load_bills()

    def load_bills(self):
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM billing')
        bills = cursor.fetchall()
        conn.close()
    
        # Clear existing entries in the Treeview
        for row in self.bills_tree.get_children():
            self.bills_tree.delete(row)
    
        # Insert new entries
        for bill in bills:
            self.bills_tree.insert("", tk.END, values=(bill[0], bill[1], bill[2], bill[3]))

    def filter_bills(self):
        customer_name = self.customer_filter_entry.get()
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()

        # Query to filter bills by customer name
        cursor.execute('SELECT * FROM billing WHERE customer_name LIKE ?', ('%' + customer_name + '%',))
        filtered_bills = cursor.fetchall()
        conn.close()

        # Clear existing entries in the Treeview
        for row in self.bills_tree.get_children():
            self.bills_tree.delete(row)

        # Insert filtered entries
        for bill in filtered_bills:
            self.bills_tree.insert("", tk.END, values=(bill[0], bill[1], bill[2], bill[3]))

    def load_products_into_treeview(self):
        # Clear the current items in the Treeview
        for item in self.product_treeview.get_children():
            self.product_treeview.delete(item)

        # Fetch products from the database
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.brand, p.product_name, p.quantity, p.unit_price
            FROM products p
        ''')
        products = cursor.fetchall()
        conn.close()

        # Insert fetched products into the Treeview
        for product in products:
            self.product_treeview.insert("", "end", values=product)

        # Set column widths
        self.product_treeview.column("Brand", width=100, anchor="center")
        self.product_treeview.column("Product Name", width=150, anchor="w")
        self.product_treeview.column("Quantity", width=80, anchor="center")
        self.product_treeview.column("Unit Price", width=100, anchor="e")

        # Set header styles
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#f0f0f0")
        style.configure("Treeview", rowheight=25)  # Increase row height for better spacing
    
    def sort_treeview_column(self, col, reverse):
        # Get the data from the Treeview
        data = [(self.product_treeview.item(item)["values"], item) for item in self.product_treeview.get_children()]

        # Sort the data
        data.sort(reverse=reverse, key=lambda x: x[0][col])

        # Reinsert the sorted data into the Treeview
        for index, (values, item) in enumerate(data):
            self.product_treeview.item(item, values=values)

        # Reverse the sort order for the next click
        self.product_treeview.heading(col, command=lambda: self.sort_treeview_column(col, not reverse))

        # Bind the sorting function to the column headers
        self.product_treeview.heading("Brand", command=lambda: self.sort_treeview_column(0, False))
        self.product_treeview.heading("Product Name", command=lambda: self.sort_treeview_column(1, False))
        self.product_treeview.heading("Quantity", command=lambda: self.sort_treeview_column(2, False))
        self.product_treeview.heading("Unit Price", command=lambda: self.sort_treeview_column(3, False))
    
    def on_product_select(self, event):
        selected_item = self.product_treeview.selection()
        if selected_item:
            item_values = self.product_treeview.item(selected_item, "values")
            # Assuming item_values is in the format (Brand, Product Name, Quantity, Unit Price)
            self.selected_product_name = item_values[1]  # Product Name
            self.selected_product_price = float(item_values[3])  # Unit Price
            self.quantity_entry.delete(0, tk.END)  # Clear previous quantity
    
    def on_customer_select(self, event):
        selected_customer = self.customer_dropdown.get()
        if selected_customer:
            conn = sqlite3.connect('stock_management.db')
            cursor = conn.cursor()
            cursor.execute("SELECT address FROM customers WHERE name=?", (selected_customer,))
            address = cursor.fetchone()
            conn.close()
            if address:
                self.customer_address_label.config(text=address[0])
            else:
                self.customer_address_label.config(text="")

    def fetch_customers(self):
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM customers")
        customers = [row[0] for row in cursor.fetchall()]
        conn.close()
        return customers

    def fetch_products(self):
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()
        cursor.execute("SELECT product_name FROM products")
        products = [row[0] for row in cursor.fetchall()]
        conn.close()
        return products
    
    def add_item_to_bill(self):
        quantity = self.quantity_entry.get()
        selling_price = self.selling_price_entry.get()

        if not self.selected_product_name or not quantity.isdigit() or not selling_price:
            messagebox.showerror("Error", "Please select a product and enter valid quantity and selling price.")
            return

        quantity = int(quantity)
        selling_price = float(selling_price)

        # Fetch available stock for the selected product
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()
        cursor.execute("SELECT quantity, cgst, sgst FROM products WHERE product_name=?", (self.selected_product_name,))
        product_data = cursor.fetchone()
        conn.close()

        if product_data is None:
            messagebox.showerror("Error", "Product not found.")
            return

        available_stock = product_data[0]
        cgst_rate = product_data[1]
        sgst_rate = product_data[2]

        # Check if requested quantity exceeds available stock
        if quantity > available_stock:
            messagebox.showerror("Error", f"Requested quantity exceeds available stock. Available: {available_stock}")
            return

        # Calculate GST for the product
        cgst_amount = (selling_price * cgst_rate) / 100
        sgst_amount = (selling_price * sgst_rate) / 100
        total_price = (selling_price + cgst_amount + sgst_amount) * quantity

        # Update total CGST and SGST
        self.total_cgst += cgst_amount * quantity
        self.total_sgst += sgst_amount * quantity

        # Store the added item
        self.added_items.append((self.selected_product_name, quantity, selling_price, cgst_amount, sgst_amount, total_price))

        # Display the item in the bill text area
        self.bill_text_area.insert(tk.END, f"{self.selected_product_name:<25} {quantity:<10} {selling_price:<15.2f} {cgst_amount:<10.2f} {sgst_amount:<10.2f} {total_price:<10.2f}\n")

    def finalize_bill(self):
        # Generate bill number
        bill_number = self.get_bill_number()

        # Fetch customer details
        customer_name = self.customer_dropdown.get()

        # Clear the bill text area and add headings
        self.bill_text_area.delete("1.0", tk.END)  # Clear previous bill
        self.bill_text_area.insert(tk.END, "Bill Number: {}\n".format(bill_number))
        self.bill_text_area.insert(tk.END, "Customer: {}\n".format(customer_name))
        self.bill_text_area.insert(tk.END, "\nItems:\n")
        self.bill_text_area.insert(tk.END, "--------------------------------------------------\n")

        total_amount = 0  # Initialize total amount

        # Display the added items
        for item in self.added_items:
            product_name, quantity, selling_price, item_total = item  # Unpack values
            total_amount += item_total

            # Save purchase to the database
            self.save_purchase(product_name, quantity, selling_price, item_total)

            self.bill_text_area.insert(tk.END, f"{product_name} {quantity} {selling_price:.2f} {item_total:.2f}\n")

        # Final total
        self.bill_text_area.insert(tk.END, "Total Amount: {:.2f}\n".format(total_amount))

        # Save the bill to the database
        self.save_bill(customer_name, total_amount)

    def update_stock(self, product_name, quantity):
        # Logic to update stock based on the product name and quantity sold
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()

        # Update the quantity in the products table
        cursor.execute("UPDATE products SET quantity = quantity - ? WHERE product_name = ?", (quantity, product_name))

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

    def get_invoice_number(self):
        current_year = datetime.now().year
        conn = sqlite3.connect('stock_management.db')
        cursor = conn.cursor()
        cursor.execute("SELECT last_invoice_number FROM settings WHERE year=?", (current_year,))
        result = cursor.fetchone()

        if result is None:
            # If no record exists for the current year, initialize it
            cursor.execute("INSERT INTO settings (year, last_invoice_number) VALUES (?, ?)", (current_year, 0))
            conn.commit()
            last_invoice_number = 0
        else:
            last_invoice_number = result[0]

        new_invoice_number = last_invoice_number + 1

        # Reset on April 1st
        if datetime.now().month == 4 and datetime.now().day == 1:
            new_invoice_number = 1

        cursor.execute("UPDATE settings SET last_invoice_number=? WHERE year=?", (new_invoice_number, current_year))
        conn.commit()
        conn.close()
        return new_invoice_number

if __name__ == "__main__":
    root = tk.Tk()
    app = StockManagementApp(root)
    root.mainloop()