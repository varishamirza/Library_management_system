import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
from library_management import create_db, category_map
print("=== DEBUG: Starting library_app.py version 2025-02-18 fixed login ===")
print("Current working directory:", __import__('os').getcwd())
# ────────────────────────────────────────────────
#  Database & Helpers (copied from console version)
# ────────────────────────────────────────────────

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def get_connection():
    return sqlite3.connect('library.db', check_same_thread=False)

# Ensure DB and tables exist before any DB queries
create_db()

# ────────────────────────────────────────────────
# Initialize default users (without destroying existing data)
# ────────────────────────────────────────────────
def reset_default_users():
    conn = get_connection()
    c = conn.cursor()
    
    # Create table if not exists (preserve existing data)
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, is_admin INTEGER, is_active INTEGER)''')
    
    # Insert default credentials ONLY if they don't exist
    c.execute("INSERT OR IGNORE INTO users (username, password, is_admin, is_active) VALUES (?, ?, 1, 1)",
              ('adm', hash_password('adm')))
    c.execute("INSERT OR IGNORE INTO users (username, password, is_admin, is_active) VALUES (?, ?, 0, 1)",
              ('user', hash_password('user')))
    
    conn.commit()
    conn.close()
    print("DEBUG: Default users initialized (adm/adm & user/user if not already present)")

# Call it once at startup
reset_default_users()

# Then the rest of your if __name__ == "__main__": block remains empty or just pass

def check_login(username, password):
    """Check if user exists and password is correct (case-insensitive username)."""
    hashed = hash_password(password)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE LOWER(username) = LOWER(?) AND password = ? AND is_active = 1",
              (username, hashed))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# ────────────────────────────────────────────────
#  Streamlit App
# ────────────────────────────────────────────────

st.set_page_config(page_title="Library Management System", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.is_admin = False

if not st.session_state.logged_in:
    st.title("Library Management System")
    st.subheader("Login")

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("User ID")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            role = check_login(username.strip(), password.strip())
            if role is not None:
                st.session_state.logged_in = True
                st.session_state.is_admin = bool(role)
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")

else:
    # Sidebar
    with st.sidebar:
        st.title("Library System")
        if st.session_state.is_admin:
            pages = ["Home", "Maintenance", "Transactions", "Reports"]
        else:
            pages = ["Home", "Transactions", "Reports"]
        
        page = st.radio("Menu", pages)
        
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # ─── Home ───────────────────────────────────────
    if page == "Home":
        st.title("Welcome to the Library Management System")
        st.markdown("""
        Use the sidebar to navigate.
        
        **Features available:**
        - Check / Issue / Return items
        - View reports
        """ + ("- Manage members & items (admin only)" if st.session_state.is_admin else ""))

    # ─── Maintenance (Admin only) ───────────────────
    elif page == "Maintenance" and st.session_state.is_admin:
        st.title("Maintenance")
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Add Item", "Add Member", "Update Member", "Update Status", "Add User", "Update User"])

        with tab1:
            st.subheader("Add Book / Movie")
            with st.form("add_item_form"):
                ptype = st.selectbox("Type", ["Book", "Movie"])
                name = st.text_input("Title")
                author = st.text_input("Author / Director")
                category = st.selectbox("Category", list(category_map.keys()))
                cost = st.number_input("Cost", min_value=0.0, step=1.0)
                proc_date = st.date_input("Procurement Date")
                qty = st.number_input("Quantity", min_value=1, step=1)

                submitted = st.form_submit_button("Add Item(s)")
                if submitted:
                    if name and author and proc_date:
                        conn = get_connection()
                        c = conn.cursor()
                        
                        # Get the highest serial number from ALL products
                        c.execute("SELECT MAX(CAST(serial_no AS INTEGER)) FROM products")
                        max_serial = c.fetchone()[0] or 0
                        
                        for i in range(qty):
                            # Generate simple unique serial numbers: 01, 02, 03, etc.
                            serial = f"{max_serial + i + 1:02d}"
                            c.execute("""INSERT INTO products (type, name, author, category, cost, procurement_date, serial_no)
                                         VALUES (?,?,?,?,?,?,?)""",
                                      (ptype, name, author, category, cost, str(proc_date), serial))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ {qty} item(s) added successfully. (Serial: {max_serial + 1:02d} to {max_serial + qty:02d})")
                    else:
                        st.error("Please fill required fields.")

        with tab2:
            st.subheader("Add Member")
            with st.form("add_member_form"):
                first = st.text_input("First Name")
                last = st.text_input("Last Name")
                contact = st.text_input("Contact Person")
                address = st.text_area("Address")
                aadhar = st.text_input("Aadhar No")
                start_date = st.date_input("Membership Start")
                mtype = st.selectbox("Duration", ["6 months", "1 year", "2 years"])

                submitted = st.form_submit_button("Add Member")
                if submitted:
                    if first and last and contact and address and aadhar and start_date:
                        days = {"6 months":180, "1 year":365, "2 years":730}[mtype]
                        end_date = start_date + pd.Timedelta(days=days)
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("""INSERT INTO members (first_name, last_name, contact_name, contact_address, aadhar_no, start_date, end_date, status)
                                     VALUES (?,?,?,?,?,?,?,'Active')""",
                                  (first, last, contact, address, aadhar, str(start_date), str(end_date)))
                        conn.commit()
                        conn.close()
                        st.success("Member added.")
                    else:
                        st.error("Fill all required fields.")

        with tab3:
            st.subheader("Update Member Membership")
            member_id = st.text_input("Member ID", key="update_member_id")
            if st.button("Load Member", key="load_member_btn"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("SELECT end_date, status FROM members WHERE id = ?", (member_id,))
                member = c.fetchone()
                conn.close()
                if member:
                    st.session_state.member_data = {"end_date": member[0], "status": member[1]}
                else:
                    st.error("Member not found.")
                    st.session_state.member_data = None
            
            if hasattr(st.session_state, 'member_data') and st.session_state.member_data:
                data = st.session_state.member_data
                st.info(f"Current end date: {data['end_date']} | Status: {data['status']}")
                action = st.selectbox("Action", ["Extend Membership", "Cancel Membership"])
                
                if action == "Extend Membership":
                    ext_type = st.selectbox("Extend by", ["6 months", "1 year", "2 years"])
                    if st.button("Extend"):
                        days = {"6 months":180, "1 year":365, "2 years":730}[ext_type]
                        from datetime import datetime
                        old_date = datetime.strptime(data['end_date'], "%Y-%m-%d")
                        new_end = (old_date + pd.Timedelta(days=days)).strftime("%Y-%m-%d")
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("UPDATE members SET end_date = ? WHERE id = ?", (new_end, member_id))
                        conn.commit()
                        conn.close()
                        st.success(f"Membership extended to {new_end}.")
                        st.session_state.member_data = None
                
                elif action == "Cancel Membership":
                    if st.button("Confirm Cancel"):
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("UPDATE members SET status = 'Inactive' WHERE id = ?", (member_id,))
                        conn.commit()
                        conn.close()
                        st.success("Membership cancelled.")
                        st.session_state.member_data = None

        with tab4:
            st.subheader("Update Item Status")
            serial = st.text_input("Serial Number")
            new_status = st.selectbox("New Status", ["Available", "Issued"])
            if st.button("Update Status"):
                if serial:
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("UPDATE products SET status = ? WHERE serial_no = ?", (new_status, serial))
                    if c.rowcount > 0:
                        conn.commit()
                        st.success("Status updated.")
                    else:
                        st.error("Serial not found.")
                    conn.close()
                else:
                    st.warning("Enter serial number.")

        with tab5:
            st.subheader("Add New User Account")
            
            # Show all existing users
            if st.checkbox("Show existing users", key="show_users_add"):
                conn = get_connection()
                all_users = pd.read_sql_query("SELECT id, username, is_admin, is_active FROM users ORDER BY username", conn)
                conn.close()
                st.dataframe(all_users, use_container_width=True)
            
            with st.form("add_user_form"):
                username = st.text_input("Username", key="new_username")
                password = st.text_input("Password", type="password", key="new_password")
                confirm_pwd = st.text_input("Confirm Password", type="password", key="confirm_password")
                is_admin = st.checkbox("Administrator", key="new_is_admin")
                
                submitted = st.form_submit_button("Create User")
                if submitted:
                    if not all([username, password, confirm_pwd]):
                        st.error("All fields required.")
                    elif password != confirm_pwd:
                        st.error("Passwords do not match.")
                    elif len(password) < 4:
                        st.error("Password must be at least 4 characters.")
                    else:
                        conn = get_connection()
                        c = conn.cursor()
                        try:
                            # Check if username already exists (case-insensitive)
                            c.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username,))
                            if c.fetchone():
                                st.error(f"Username '{username}' already exists!")
                            else:
                                hashed = hash_password(password)
                                c.execute("INSERT INTO users (username, password, is_admin, is_active) VALUES (?, ?, ?, 1)",
                                          (username, hashed, 1 if is_admin else 0))
                                conn.commit()
                                st.success(f"✅ User '{username}' created successfully!")
                        except sqlite3.IntegrityError:
                            st.error("Username already exists (case-insensitive check failed).")
                        finally:
                            conn.close()

        with tab6:
            st.subheader("Update User Account")
            col1, col2 = st.columns([3, 1])
            with col1:
                username = st.text_input("Username to update", key="update_username")
            with col2:
                if st.button("Show All Users"):
                    conn = get_connection()
                    all_users = pd.read_sql_query("SELECT id, username, is_admin, is_active FROM users ORDER BY username", conn)
                    conn.close()
                    st.dataframe(all_users, use_container_width=True)
            
            if st.button("Load User", key="load_user_btn"):
                conn = get_connection()
                c = conn.cursor()
                # Case-insensitive search
                c.execute("SELECT id, is_admin, is_active FROM users WHERE LOWER(username) = LOWER(?)", (username,))
                user = c.fetchone()
                conn.close()
                if user:
                    st.session_state.user_data = {"id": user[0], "is_admin": user[1], "is_active": user[2]}
                    st.success(f"User '{username}' loaded successfully!")
                else:
                    st.error(f"User '{username}' not found. Click 'Show All Users' to see available usernames.")
                    st.session_state.user_data = None
            
            if hasattr(st.session_state, 'user_data') and st.session_state.user_data:
                data = st.session_state.user_data
                st.info(f"Admin: {bool(data['is_admin'])} | Active: {bool(data['is_active'])}")
                
                action = st.selectbox("Action", ["Change Password", "Toggle Admin", "Toggle Active Status"])
                
                if action == "Change Password":
                    new_pwd = st.text_input("New Password", type="password", key="update_password")
                    confirm_new = st.text_input("Confirm New Password", type="password", key="confirm_update_password")
                    if st.button("Update Password"):
                        if not all([new_pwd, confirm_new]):
                            st.error("Both fields required.")
                        elif new_pwd != confirm_new:
                            st.error("Passwords do not match.")
                        elif len(new_pwd) < 4:
                            st.error("Password must be at least 4 characters.")
                        else:
                            conn = get_connection()
                            c = conn.cursor()
                            hashed = hash_password(new_pwd)
                            c.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, data['id']))
                            conn.commit()
                            conn.close()
                            st.success(f"Password updated for '{username}'.")
                            st.session_state.user_data = None
                
                elif action == "Toggle Admin":
                    new_admin = not bool(data['is_admin'])
                    if st.button(f"Make {'Admin' if new_admin else 'Regular User'}"):
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("UPDATE users SET is_admin = ? WHERE id = ?", (1 if new_admin else 0, data['id']))
                        conn.commit()
                        conn.close()
                        st.success(f"User '{username}' is now {'admin' if new_admin else 'regular user'}.")
                        st.session_state.user_data = None
                
                elif action == "Toggle Active Status":
                    new_active = not bool(data['is_active'])
                    if st.button(f"{'Activate' if new_active else 'Deactivate'}"):
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if new_active else 0, data['id']))
                        conn.commit()
                        conn.close()
                        st.success(f"User '{username}' is now {'active' if new_active else 'inactive'}.")
                        st.session_state.user_data = None

    # ─── Transactions ───────────────────────────────
    elif page == "Transactions":
        st.title("Transactions")
        action = st.selectbox("Action", ["Check Availability", "Issue Item", "Return Item", "Pay Fine"])

        if action == "Check Availability":
            name = st.text_input("Title (partial search)")
            if st.button("Search"):
                conn = get_connection()
                df = pd.read_sql_query("SELECT serial_no, name, author, status FROM products WHERE name LIKE ?",
                                       conn, params=(f"%{name}%",))
                conn.close()
                if df.empty:
                    st.info("No items found.")
                else:
                    st.dataframe(df)

        elif action == "Issue Item":
            st.subheader("Issue Item to Member")
            
            # Show available items
            with st.expander("📚 Click to see available items", expanded=False):
                conn = get_connection()
                available = pd.read_sql_query(
                    "SELECT serial_no, name, author, type, COALESCE(status, 'Available') AS status FROM products WHERE COALESCE(status, 'Available') = 'Available' ORDER BY serial_no",
                    conn)
                conn.close()
                if available.empty:
                    st.warning("❌ No items available.")
                else:
                    st.dataframe(available, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                serial = st.text_input("Serial Number", placeholder="e.g., 01, 02, 03...")
            with col2:
                member_id = st.text_input("Member ID", placeholder="e.g., 1, 2, 3...")
            
            issue_date = st.date_input("Issue Date", value=datetime.today(), key="issue_date_picker")
            return_date = st.date_input("Expected Return Date", key="return_date_picker")
            remarks = st.text_area("Remarks (optional)", height=60, key="issue_remarks")
            
            if st.button("Issue Item", key="issue_btn"):
                if not serial:
                    st.error("❌ Enter serial number.")
                elif not member_id:
                    st.error("❌ Enter member ID.")
                elif return_date <= issue_date:
                    st.error("❌ Return date must be after issue date.")
                else:
                    conn = get_connection()
                    c = conn.cursor()
                    
                    # Check if member exists
                    c.execute("SELECT id, first_name, last_name FROM members WHERE id = ?", (member_id,))
                    member = c.fetchone()
                    if not member:
                        st.error(f"❌ Member ID {member_id} not found.")
                        conn.close()
                    else:
                        # Check if product exists and is available
                        c.execute("SELECT id, COALESCE(status, 'Available') as status, name FROM products WHERE serial_no = ?", (serial,))
                        prod = c.fetchone()
                        if not prod:
                            st.error(f"❌ Serial '{serial}' not found. See available items above.")
                            # Show similar serials for help
                            c.execute("SELECT serial_no FROM products WHERE serial_no LIKE ? LIMIT 5", (f"%{serial}%",))
                            similar = c.fetchall()
                            if similar:
                                st.info("💡 Did you mean: " + ", ".join([s[0] for s in similar]))
                        elif prod[1] != 'Available':
                            st.error(f"❌ Serial {serial} ({prod[2]}) is {prod[1]}. Cannot issue.")
                        else:
                            c.execute("INSERT INTO issues (product_id, member_id, issue_date, return_date, remarks) VALUES (?,?,?,?,?)",
                                      (prod[0], member_id, str(issue_date), str(return_date), remarks))
                            c.execute("UPDATE products SET status = 'Issued' WHERE id = ?", (prod[0],))
                            conn.commit()
                            member_name = f"{member[1]} {member[2]}"
                            st.success(f"""
                            ✅ **Item issued successfully!**
                            - Serial: {serial} ({prod[2]})
                            - Member: {member_name}
                            - Due: {return_date}
                            """)
                        conn.close()

        elif action == "Return Item":
            st.subheader("Return Item & Settle Fine")
            
            # Show active issues
            with st.expander("📋 Click to see active issues (items to return)", expanded=False):
                conn = get_connection()
                active = pd.read_sql_query("""
                    SELECT p.serial_no, p.name, m.first_name || ' ' || m.last_name AS member_name, 
                           i.issue_date, i.return_date
                    FROM issues i
                    JOIN products p ON i.product_id = p.id
                    LEFT JOIN members m ON i.member_id = m.id
                    WHERE i.actual_return_date IS NULL
                    ORDER BY i.return_date
                """, conn)
                conn.close()
                if active.empty:
                    st.info("No active issues.")
                else:
                    st.dataframe(active, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                serial = st.text_input("Serial Number to return", key="return_serial", placeholder="e.g., 01, 02...")
            with col2:
                st.empty()
            
            return_date = st.date_input("Actual Return Date", value=datetime.today(), key="return_date_input")
            remarks = st.text_area("Remarks (optional)", height=60, key="return_remarks")
            
            if st.button("Calculate Fine", key="calc_fine_btn"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("""SELECT i.id, i.return_date, i.member_id, p.id, m.pending_fine, p.name, m.first_name, m.last_name
                             FROM issues i 
                             JOIN products p ON i.product_id = p.id 
                             LEFT JOIN members m ON i.member_id = m.id
                             WHERE p.serial_no = ? AND i.actual_return_date IS NULL""", (serial,))
                issue = c.fetchone()
                conn.close()
                
                if issue:
                    issue_id, expected_str, member_id, prod_id, existing_fine, item_name, fname, lname = issue
                    # Use date-only arithmetic to avoid time-related issues
                    expected_date = datetime.strptime(expected_str, "%Y-%m-%d").date()
                    actual_date = return_date
                    new_fine = max(0, (actual_date - expected_date).days) * 1.0
                    existing_fine = existing_fine if existing_fine is not None else 0.0
                    total_fine = existing_fine + new_fine
                    
                    st.session_state.return_data = {
                        "issue_id": issue_id,
                        "prod_id": prod_id,
                        "member_id": member_id,
                        "new_fine": new_fine,
                        "existing_fine": existing_fine,
                        "total_fine": total_fine,
                        "return_date": str(return_date),
                        "remarks": remarks
                    }
                else:
                    st.error(f"❌ No active issue found for serial {serial}")
            
            if hasattr(st.session_state, 'return_data') and st.session_state.return_data:
                data = st.session_state.return_data
                
                st.divider()
                st.info(f"""
                **Fine Breakdown:**
                - New fine (from this return): ₹{data['new_fine']:.2f}
                - Existing pending fine: ₹{data['existing_fine']:.2f}
                - **Total fine due: ₹{data['total_fine']:.2f}**
                """)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Return without payment")
                    if st.button("Return Item Only", key="return_only_btn"):
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("UPDATE issues SET actual_return_date = ?, fine_amount = ?, remarks = ? WHERE id = ?",
                                  (data['return_date'], data['new_fine'], remarks, data['issue_id']))
                        c.execute("UPDATE products SET status = 'Available' WHERE id = ?", (data['prod_id'],))
                        if data['new_fine'] > 0:
                            c.execute("UPDATE members SET pending_fine = COALESCE(pending_fine, 0) + ? WHERE id = ?",
                                      (data['new_fine'], data['member_id']))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Item returned. Fine: ₹{data['new_fine']:.2f}")
                        st.session_state.return_data = None
                        st.rerun()
                
                with col2:
                    st.subheader("Return & Pay Fine")
                    pay_amount = st.number_input("Amount to pay now", min_value=0.0, max_value=data['total_fine'], 
                                                 step=1.0, value=data['total_fine'], key="pay_on_return")
                    
                    if st.button("Return & Pay Fine", key="return_pay_btn"):
                        if pay_amount > 0:
                            conn = get_connection()
                            c = conn.cursor()
                            # Update issue return
                            c.execute("UPDATE issues SET actual_return_date = ?, fine_amount = ?, remarks = ? WHERE id = ?",
                                      (data['return_date'], data['new_fine'], remarks, data['issue_id']))
                            c.execute("UPDATE products SET status = 'Available' WHERE id = ?", (data['prod_id'],))
                            
                            # Update member fine
                            new_pending = data['total_fine'] - pay_amount
                            c.execute("UPDATE members SET pending_fine = ? WHERE id = ?", (new_pending, data['member_id']))
                            
                            conn.commit()
                            conn.close()
                            
                            st.success(f"""
                            ✅ **Item returned successfully!**
                            - New fine from return: ₹{data['new_fine']:.2f}
                            - Payment received: ₹{pay_amount:.2f}
                            - Remaining balance: ₹{new_pending:.2f}
                            """)
                            st.session_state.return_data = None
                            st.rerun()
                        else:
                            st.warning("Enter amount to pay.")

        elif action == "Pay Fine":
            with st.form("pay_fine_form"):
                member_id = st.text_input("Member ID")
                amount = st.number_input("Amount to Pay", min_value=0.0, step=1.0)

                submitted = st.form_submit_button("Pay Fine")
                if submitted and amount > 0:
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("SELECT pending_fine FROM members WHERE id = ?", (member_id,))
                    row = c.fetchone()
                    if row:
                        current = row[0] if row[0] is not None else 0.0
                        if amount <= current:
                            new_fine = current - amount
                            c.execute("UPDATE members SET pending_fine = ? WHERE id = ?", (new_fine, member_id))
                            conn.commit()
                            st.success(f"✅ Payment accepted. Remaining: ₹{new_fine:.2f}")
                        else:
                            st.error(f"❌ Cannot pay more than pending (₹{current:.2f}). Amount to pay: ₹{amount:.2f}")
                    else:
                        st.error("Member not found.")
                    conn.close()

    # ─── Reports ────────────────────────────────────
    elif page == "Reports":
        st.title("Reports")
        report_type = st.selectbox("Select Report", [
            "Books Master List", "Movies Master List",
            "Members Master List", "Active Issues", "Overdue Items", "Pending Requests"
        ])

        if st.button("Generate Report"):
            conn = get_connection()
            if report_type == "Books Master List":
                df = pd.read_sql_query("SELECT serial_no, name, author, category, status, cost FROM products WHERE type='Book' ORDER BY name", conn)
            elif report_type == "Movies Master List":
                df = pd.read_sql_query("SELECT serial_no, name, author, category, status, cost FROM products WHERE type='Movie' ORDER BY name", conn)
            elif report_type == "Members Master List":
                df = pd.read_sql_query("""SELECT id, first_name, last_name, contact_name, aadhar_no, start_date, end_date, status, pending_fine 
                                          FROM members ORDER BY first_name, last_name""", conn)
            elif report_type == "Active Issues":
                df = pd.read_sql_query("""SELECT p.serial_no, p.name, p.type, m.first_name || ' ' || m.last_name AS member_name, 
                                                  i.member_id, i.issue_date, i.return_date 
                                          FROM issues i 
                                          JOIN products p ON i.product_id = p.id 
                                          LEFT JOIN members m ON i.member_id = m.id
                                          WHERE i.actual_return_date IS NULL
                                          ORDER BY i.issue_date""", conn)
            elif report_type == "Overdue Items":
                today = datetime.now().strftime("%Y-%m-%d")
                df = pd.read_sql_query(f"""SELECT p.serial_no, p.name, p.type, m.first_name || ' ' || m.last_name AS member_name,
                                                  i.member_id, i.issue_date, i.return_date,
                                                  CAST(julianday('{today}') - julianday(i.return_date) AS INTEGER) AS days_overdue
                                           FROM issues i 
                                           JOIN products p ON i.product_id = p.id 
                                           LEFT JOIN members m ON i.member_id = m.id
                                           WHERE i.actual_return_date IS NULL AND i.return_date < '{today}'
                                           ORDER BY i.return_date""", conn)
            elif report_type == "Pending Requests":
                df = pd.read_sql_query("""SELECT id, member_id, product_name, requested_date, fulfilled_date, 
                                          CASE WHEN fulfilled_date IS NULL THEN 'Pending' ELSE 'Fulfilled' END AS status
                                          FROM requests ORDER BY requested_date DESC""", conn)
            
            conn.close()

            if df.empty:
                st.info("No active issues found.")
                # Show books/movies with "Issued" status as reference
                conn = get_connection()
                issued_items = pd.read_sql_query("""SELECT serial_no, name, type, status FROM products WHERE status = 'Issued' ORDER BY name""", conn)
                conn.close()
                if not issued_items.empty:
                    st.subheader("Items marked as Issued (but no issue record):")
                    st.dataframe(issued_items)
                    st.warning("Items above are marked Issued but have no corresponding issue record. To record an issue, use Transactions → Issue Item.")
                else:
                    st.info("💡 Tip: To create active issues, go to Transactions → Issue Item. Then this report will show them.")
            else:
                st.dataframe(df)

# Initialize DB on first run
if __name__ == "__main__":
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password, is_admin, is_active) VALUES (?,?,1,1)",
                  ('adm', hash_password('adm')))
        c.execute("INSERT INTO users (username, password, is_admin, is_active) VALUES (?,?,0,1)",
                  ('user', hash_password('user')))
        conn.commit()
    conn.close()