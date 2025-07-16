import streamlit as st
import sqlite3
from datetime import datetime
from fpdf import FPDF

# --- Connect SQLite ---
conn = sqlite3.connect("payments.db", check_same_thread=False)
c = conn.cursor()

# --- Create Tables ---
c.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT,
        client_name TEXT,
        total_amount REAL,
        created_date TEXT
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        amount REAL,
        date TEXT,
        FOREIGN KEY(client_id) REFERENCES clients(id)
    )
''')
conn.commit()

# --- Title ---
st.title("💰 Smart Payment Tracker")

# --- Add New Project ---
st.header("➕ Add New Project")
col1, col2, col3 = st.columns(3)
with col1:
    project_name = st.text_input("Project Name")
with col2:
    client_name = st.text_input("Client Name")
with col3:
    total_amount = st.number_input("Total Quotation Amount", min_value=0.0)

if st.button("Add Project"):
    if project_name and client_name and total_amount > 0:
        created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO clients (project_name, client_name, total_amount, created_date) VALUES (?, ?, ?, ?)",
                  (project_name, client_name, total_amount, created_date))
        conn.commit()
        st.success(f"Added project '{project_name}' for client '{client_name}'.")
    else:
        st.warning("Please fill in all fields with valid values.")

# --- Show All Projects ---
st.header("📋 All Projects")

clients = c.execute("SELECT id, project_name, client_name, total_amount, created_date FROM clients").fetchall()

if clients:
    for client in clients:
        client_id = client[0]
        project_name = client[1]
        client_name = client[2]
        total_amount = client[3]
        created_date = client[4]

        payments = c.execute("SELECT amount, date FROM payments WHERE client_id = ?", (client_id,)).fetchall()
        total_paid = sum(p[0] for p in payments)
        remaining = total_amount - total_paid

        with st.expander(f"📌 {project_name} — {client_name}"):
            st.write(f"**Created Date:** {created_date}")
            st.write(f"**Total Quotation:** ₹{total_amount:.2f}")
            st.write(f"**Total Paid:** ₹{total_paid:.2f}")
            st.write(f"**Remaining Due:** ₹{remaining:.2f}")

            if payments:
                st.write("**Payment History:**")
                st.table([{"Date": p[1], "Amount": f"₹{p[0]:.2f}"} for p in payments])
            else:
                st.info("No payments yet.")

            # --- Add Payment ---
            new_payment = st.number_input(f"Add Payment for {project_name}", min_value=0.0, key=f"payment_{client_id}")
            if st.button(f"Add Payment for {project_name}"):
                if new_payment > 0:
                    payment_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO payments (client_id, amount, date) VALUES (?, ?, ?)",
                              (client_id, new_payment, payment_date))
                    conn.commit()
                    st.success(f"Added payment of ₹{new_payment:.2f} for {project_name}.")
                else:
                    st.warning("Enter a valid payment amount.")

            # --- Generate PDF ---
            def generate_pdf():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, "Quotation / Receipt", ln=True, align="C")

                pdf.set_font("Arial", '', 12)
                pdf.cell(200, 10, f"Project: {project_name}", ln=True)
                pdf.cell(200, 10, f"Client: {client_name}", ln=True)
                pdf.cell(200, 10, f"Created: {created_date}", ln=True)
                pdf.cell(200, 10, f"Total Quotation: ₹{total_amount:.2f}", ln=True)
                pdf.cell(200, 10, f"Total Paid: ₹{total_paid:.2f}", ln=True)
                pdf.cell(200, 10, f"Remaining Due: ₹{remaining:.2f}", ln=True)

                pdf.ln(10)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(60, 10, "Payment Date", 1)
                pdf.cell(60, 10, "Amount (₹)", 1)
                pdf.ln()

                pdf.set_font("Arial", '', 12)
                for p in payments:
                    pdf.cell(60, 10, p[1], 1)
                    pdf.cell(60, 10, f"₹{p[0]:.2f}", 1)
                    pdf.ln()

                return pdf.output(dest='S').encode('latin1', 'replace')

            if payments:
                pdf_bytes = generate_pdf()
                st.download_button(
                    label=f"📄 Download PDF for {project_name}",
                    data=pdf_bytes,
                    file_name=f"{project_name}_receipt.pdf",
                    mime="application/pdf"
                )

            # --- Delete Project ---
            if st.button(f"❌ Delete Project: {project_name}"):
                c.execute("DELETE FROM payments WHERE client_id = ?", (client_id,))
                c.execute("DELETE FROM clients WHERE id = ?", (client_id,))
                conn.commit()
                st.success(f"Deleted project '{project_name}' and all related payments.")
                st.experimental_rerun()

else:
    st.info("No projects found. Add a project above.")

# --- Backup DB ---
st.header("🗂️ Backup Your Database")

with open("payments.db", "rb") as f:
    db_bytes = f.read()

st.download_button(
    label="⬇️ Download Full Database Backup",
    data=db_bytes,
    file_name="payments_backup.db",
    mime="application/octet-stream"
)
