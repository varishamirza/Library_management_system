import sqlite3
from datetime import datetime, timedelta
import hashlib

# Category mapping for serial numbers
category_map = {
    'Science': 'SC',
    'Economics': 'EC',
    'Fiction': 'FC',
    'Children': 'CH',
    'Personal Development': 'PD'
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_db():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, is_admin INTEGER, is_active INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS members
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT, last_name TEXT, contact_name TEXT, 
                  contact_address TEXT, aadhar_no TEXT, start_date DATE, end_date DATE, status TEXT, pending_fine REAL DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, name TEXT, author TEXT, category TEXT, 
                  status TEXT DEFAULT 'Available', cost REAL, procurement_date DATE, serial_no TEXT UNIQUE)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS issues
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, member_id INTEGER, issue_date DATE, 
                  return_date DATE, actual_return_date DATE, fine_amount REAL DEFAULT 0, fine_paid INTEGER DEFAULT 0, 
                  remarks TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS requests
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER, product_name TEXT, requested_date DATE, 
                  fulfilled_date DATE)''')

    # Default users
    c.execute("INSERT OR IGNORE INTO users (username, password, is_admin, is_active) VALUES (?, ?, 1, 1)", 
              ('adm', hash_password('adm')))
    c.execute("INSERT OR IGNORE INTO users (username, password, is_admin, is_active) VALUES (?, ?, 0, 1)", 
              ('user', hash_password('user')))

    conn.commit()
    conn.close()

def validate_date(date_str, field_name="Date"):
    if not date_str:
        print(f"{field_name} is required.")
        return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if dt.year < 2000 or dt.year > 2035:
            raise ValueError
        return dt
    except ValueError:
        print(f"Invalid {field_name}. Use YYYY-MM-DD (example: 2025-04-15)")
        return None

def login():
    print("\n=== Library Management System Login ===")
    user_id = input("User ID: ").strip()
    password = input("Password: ").strip()
    
    if not user_id or not password:
        print("Both fields required.")
        return None
    
    hashed = hash_password(password)
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username = ? AND password = ? AND is_active = 1", 
              (user_id, hashed))
    result = c.fetchone()
    conn.close()
    
    if result:
        return result[0]  # 1 = admin, 0 = user
    print("Invalid credentials.")
    return None

def main_menu(is_admin):
    while True:
        print("\n=== Home Page ===")
        if is_admin:
            print("1. Maintenance")
        print("2. Reports")
        print("3. Transactions")
        print("4. Log Out")
        choice = input("Choose: ").strip()
        
        if choice == '1' and is_admin:
            maintenance_menu()
        elif choice == '2':
            reports_menu()
        elif choice == '3':
            transactions_menu()
        elif choice == '4':
            print("Logged out.")
            break
        else:
            print("Invalid choice.")

# ────────────────────────────────────────────────
# MAINTENANCE
# ────────────────────────────────────────────────
def maintenance_menu():
    while True:
        print("\n=== Maintenance ===")
        print("1. Add Membership")
        print("2. Update Membership")
        print("3. Add Book/Movie")
        print("4. Update Book/Movie Status")
        print("5. Back")
        choice = input("Choose: ").strip()
        
        if choice == '1': add_membership()
        elif choice == '2': update_membership()
        elif choice == '3': add_product()
        elif choice == '4': update_product_status()
        elif choice == '5': break
        else: print("Invalid.")

def add_membership():
    print("\n--- Add Membership ---")
    first = input("First Name: ").strip()
    last = input("Last Name: ").strip()
    contact = input("Contact Person: ").strip()
    address = input("Address: ").strip()
    aadhar = input("Aadhar No: ").strip()
    start = input("Start Date (YYYY-MM-DD): ").strip()
    
    print("1. 6 months   2. 1 year   3. 2 years")
    mtype = input("Membership type: ").strip()
    days = {'1':180, '2':365, '3':730}.get(mtype)
    if not days:
        print("Invalid type.")
        return
    
    start_dt = validate_date(start, "Start Date")
    if not start_dt: return
    
    end_date = (start_dt + timedelta(days=days)).strftime("%Y-%m-%d")
    
    if not all([first, last, contact, address, aadhar, start]):
        print("All fields required.")
        return
    
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("""INSERT INTO members (first_name, last_name, contact_name, contact_address, aadhar_no, start_date, end_date, status)
                 VALUES (?,?,?,?,?,?,?,'Active')""",
              (first, last, contact, address, aadhar, start, end_date))
    conn.commit()
    print(f"Member added. ID = {c.lastrowid}")
    conn.close()

def update_membership():
    mid = input("Member ID: ").strip()
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT end_date, status FROM members WHERE id = ?", (mid,))
    row = c.fetchone()
    if not row:
        print("Member not found.")
        conn.close()
        return
    
    print(f"Current end date: {row[0]} | Status: {row[1]}")
    action = input("1. Extend   2. Cancel membership   3. Cancel: ").strip()
    
    if action == '1':
        print("1. +6 months   2. +1 year   3. +2 years")
        ext = input("Extend by: ").strip()
        days = {'1':180, '2':365, '3':730}.get(ext)
        if not days:
            print("Invalid.")
            conn.close()
            return
        new_end = (datetime.strptime(row[0], "%Y-%m-%d") + timedelta(days=days)).strftime("%Y-%m-%d")
        c.execute("UPDATE members SET end_date = ? WHERE id = ?", (new_end, mid))
        print("Membership extended.")
    
    elif action == '2':
        c.execute("UPDATE members SET status = 'Inactive' WHERE id = ?", (mid,))
        print("Membership cancelled.")
    
    else:
        conn.close()
        return
    
    conn.commit()
    conn.close()

def add_product():
    print("\n--- Add Book / Movie ---")
    typ = input("1 = Book   2 = Movie: ").strip()
    if typ == '1': ptype, code = 'Book', 'B'
    elif typ == '2': ptype, code = 'Movie', 'M'
    else:
        print("Invalid.")
        return
    
    name = input("Title: ").strip()
    author = input("Author / Director: ").strip()
    cat = input("Category (Science/Economics/Fiction/Children/Personal Development): ").strip()
    if cat not in category_map:
        print("Invalid category.")
        return
    cost = input("Cost/Price: ").strip()
    proc_date = input("Procurement Date (YYYY-MM-DD): ").strip()
    qty = input("Quantity (default 1): ").strip() or "1"
    
    try:
        qty = int(qty)
        cost = float(cost)
        validate_date(proc_date, "Procurement Date")
    except:
        print("Invalid number or date.")
        return
    
    if not all([name, author, proc_date]):
        print("Required fields missing.")
        return
    
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # Get the highest serial number from ALL products
    c.execute("SELECT MAX(CAST(serial_no AS INTEGER)) FROM products")
    max_serial = c.fetchone()[0] or 0
    
    for i in range(qty):
        # Generate simple unique serial numbers: 01, 02, 03, etc.
        serial = f"{max_serial + i + 1:02d}"
        
        c.execute("""INSERT INTO products (type, name, author, category, cost, procurement_date, serial_no)
                     VALUES (?,?,?,?,?,?,?)""",
                  (ptype, name, author, cat, cost, proc_date, serial))
    
    conn.commit()
    print(f"{qty} item(s) added. (Serial: {max_serial + 1:02d} to {max_serial + qty:02d})")
    conn.close()

def update_product_status():
    serial = input("Serial Number: ").strip()
    new_status = input("New status (Available / Issued): ").strip().capitalize()
    if new_status not in ['Available', 'Issued']:
        print("Invalid status.")
        return
    
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("UPDATE products SET status = ? WHERE serial_no = ?", (new_status, serial))
    if c.rowcount == 0:
        print("Serial not found.")
    else:
        print("Status updated.")
    conn.commit()
    conn.close()

# ────────────────────────────────────────────────
# TRANSACTIONS
# ────────────────────────────────────────────────
def transactions_menu():
    while True:
        print("\n=== Transactions ===")
        print("1. Check availability")
        print("2. Issue book/movie")
        print("3. Return book/movie")
        print("4. Pay fine")
        print("5. Back")
        ch = input("Choose: ").strip()
        if ch == '1': check_availability()
        elif ch == '2': issue_item()
        elif ch == '3': return_item()
        elif ch == '4': pay_fine()
        elif ch == '5': break
        else: print("Invalid.")

def check_availability():
    name = input("Title (partial ok): ").strip()
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT serial_no, name, author, status FROM products WHERE name LIKE ? ORDER BY name",
              (f"%{name}%",))
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        print("No items found.")
        return
    print("\nSerial        Title                           Author                  Status")
    print("-"*75)
    for r in rows:
        print(f"{r[0]:<13} {r[1]:<30} {r[2]:<22} {r[3]}")

def issue_item():
    serial = input("Serial Number: ").strip()
    member_id = input("Member ID: ").strip()
    issue_d = input("Issue Date (YYYY-MM-DD): ").strip()
    return_d = input("Return Date (YYYY-MM-DD): ").strip()
    remarks = input("Remarks (optional): ").strip()
    
    issue_dt = validate_date(issue_d, "Issue Date")
    return_dt = validate_date(return_d, "Return Date")
    if not issue_dt or not return_dt: return
    
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT id, status FROM products WHERE serial_no = ?", (serial,))
    prod = c.fetchone()
    if not prod or prod[1] != 'Available':
        print("Item not available or not found.")
        conn.close()
        return
    
    c.execute("INSERT INTO issues (product_id, member_id, issue_date, return_date, remarks) VALUES (?,?,?,?,?)",
              (prod[0], member_id, issue_d, return_d, remarks))
    c.execute("UPDATE products SET status = 'Issued' WHERE id = ?", (prod[0],))
    conn.commit()
    print("Item issued.")
    conn.close()

def return_item():
    serial = input("Serial Number: ").strip()
    ret_date = input("Actual Return Date (YYYY-MM-DD): ").strip()
    remarks = input("Remarks (optional): ").strip()
    
    ret_dt = validate_date(ret_date, "Return Date")
    if not ret_dt: return
    
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("""SELECT i.id, i.return_date, i.member_id, p.id 
                 FROM issues i JOIN products p ON i.product_id = p.id 
                 WHERE p.serial_no = ? AND i.actual_return_date IS NULL""", (serial,))
    issue = c.fetchone()
    if not issue:
        print("No active issue found or already returned.")
        conn.close()
        return
    
    expected = datetime.strptime(issue[1], "%Y-%m-%d")
    actual = ret_dt
    fine = max(0, (actual - expected).days) * 1.0  # ₹1 per day late
    
    c.execute("UPDATE issues SET actual_return_date = ?, fine_amount = ?, remarks = ? WHERE id = ?",
              (ret_date, fine, remarks, issue[0]))
    c.execute("UPDATE products SET status = 'Available' WHERE id = ?", (issue[3],))
    if fine > 0:
        c.execute("UPDATE members SET pending_fine = pending_fine + ? WHERE id = ?", (fine, issue[2]))
        print(f"Item returned. Late fine: ₹{fine:.2f}")
    else:
        print("Item returned on time.")
    
    conn.commit()
    conn.close()

def pay_fine():
    member_id = input("Member ID: ").strip()
    amount = input("Amount to pay: ").strip()
    
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except:
        print("Invalid amount.")
        return
    
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT pending_fine FROM members WHERE id = ?", (member_id,))
    row = c.fetchone()
    if not row:
        print("Member not found.")
        conn.close()
        return
    
    current = row[0]
    if amount > current:
        print(f"Cannot pay more than pending (₹{current:.2f})")
        conn.close()
        return
    
    new_fine = current - amount
    c.execute("UPDATE members SET pending_fine = ? WHERE id = ?", (new_fine, member_id))
    conn.commit()
    print(f"Payment accepted. Remaining fine: ₹{new_fine:.2f}")
    conn.close()

# ────────────────────────────────────────────────
# REPORTS
# ────────────────────────────────────────────────
def reports_menu():
    while True:
        print("\n=== Reports ===")
        print("1. Books List")
        print("2. Movies List")
        print("3. Active Issues")
        print("4. Overdue Items")
        print("5. Back")
        ch = input("Choose: ").strip()
        if ch == '1': master_list('Book')
        elif ch == '2': master_list('Movie')
        elif ch == '3': active_issues()
        elif ch == '4': overdue_items()
        elif ch == '5': break
        else: print("Invalid.")

def master_list(typ):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT serial_no, name, author, category, status, cost FROM products WHERE type = ? ORDER BY name", (typ,))
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        print(f"No {typ.lower()}s found.")
        return
    
    print(f"\n=== {typ}s Master List ===")
    print("Serial         Title                            Author                   Cat         Status    Cost")
    print("-"*90)
    for r in rows:
        print(f"{r[0]:<14} {r[1]:<32} {r[2]:<24} {r[3]:<11} {r[4]:<9} ₹{r[5]:.2f}")

def active_issues():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("""SELECT p.serial_no, p.name, i.member_id, i.issue_date, i.return_date 
                 FROM issues i JOIN products p ON i.product_id = p.id 
                 WHERE i.actual_return_date IS NULL""")
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        print("No active issues.")
        return
    
    print("\n=== Active Issues ===")
    print("Serial         Title                            Member   Issue       Due")
    print("-"*70)
    for r in rows:
        print(f"{r[0]:<14} {r[1]:<32} {r[2]:<8} {r[3]}   {r[4]}")

def overdue_items():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("""SELECT p.serial_no, p.name, i.member_id, i.issue_date, i.return_date,
                        (julianday(?) - julianday(i.return_date)) AS days_late
                 FROM issues i JOIN products p ON i.product_id = p.id 
                 WHERE i.actual_return_date IS NULL AND i.return_date < ?""", (today, today))
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        print("No overdue items.")
        return
    
    print("\n=== Overdue Items ===")
    print("Serial         Title                            Member   Issue       Due        Days late")
    print("-"*85)
    for r in rows:
        print(f"{r[0]:<14} {r[1]:<32} {r[2]:<8} {r[3]}   {r[4]}   {int(r[5])}")

if __name__ == "__main__":
    create_db()
    role = login()
    if role is not None:
        main_menu(role)