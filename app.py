import streamlit as st
import sqlite3
from datetime import datetime
from fpdf import FPDF

# Initialize DB
conn = sqlite3.connect('payments.db', check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
c.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY,
        name TEXT,
        client TEXT,
        quotation REAL,
        created_at TEXT
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        project_id INTEGER,
        amount REAL,
        paid_at TEXT
    )
''')

conn.commit()

# Title
st.title("📑 Smart Payment Tracker")

# Add new project
with st.form("new_project"):
    name = st.text_input("Project Name")
    client = st.text_input("Client Name")
    quotation = st.number_input("Quotation Amount", min_value=0.0)
    submitted = st.form_submit_button("Add Project")
    if submitted:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO projects (name, client, quotation, created_at) VALUES (?, ?, ?, ?)",
                  (name, client, quotation, now))
        conn.commit()
        st.success(f"✅ Project '{name}' added!")

# Show all projects
c.execute("SELECT * FROM projects")
projects = c.fetchall()

for project in projects:
    proj_id, name, client, quotation, created_at = project

    # Payments summary
    c.execute("SELECT SUM(amount) FROM payments WHERE project_id = ?", (proj_id,))
    total_paid = c.fetchone()[0] or 0
    due = quotation - total_paid

    with st.expander(f"📌 {name} — {client}"):
        st.write(f"**Created Date:** {created_at}")
        st.write(f"**Quotation:** Rs.{quotation:,.2f}")
        st.write(f"**Paid:** Rs.{total_paid:,.2f}")
        st.write(f"**Remaining Due:** Rs.{due:,.2f}")

        # Payment history
        c.execute("SELECT * FROM payments WHERE project_id = ?", (proj_id,))
        payments = c.fetchall()
        if payments:
            st.markdown("**Payments:**")
            for p in payments:
                st.write(f"Rs.{p[2]:,.2f} on {p[3]}")
        else:
            st.info("No payments yet.")

        # Add new payment
        payment_amount = st.number_input(f"Add Payment for {name}", min_value=0.0, key=f"{proj_id}_pay")
        if st.button(f"Add Payment for {name}", key=f"{proj_id}_pay_btn"):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO payments (project_id, amount, paid_at) VALUES (?, ?, ?)",
                      (proj_id, payment_amount, now))
            conn.commit()
            st.success(f"✅ Payment Rs.{payment_amount:,.2f} added for {name}!")

        # ✅ PDF generation with Rs.
        def generate_pdf():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Project: {name}", ln=True)
            pdf.cell(200, 10, txt=f"Client: {client}", ln=True)
            pdf.cell(200, 10, txt=f"Quotation: Rs.{quotation:,.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Total Paid: Rs.{total_paid:,.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Remaining Due: Rs.{due:,.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Created: {created_at}", ln=True)

            pdf.cell(200, 10, txt="Payments:", ln=True)
            if payments:
                for p in payments:
                    pdf.cell(200, 10, txt=f"Rs.{p[2]:,.2f} on {p[3]}", ln=True)
            else:
                pdf.cell(200, 10, txt="No payments yet.", ln=True)

            return pdf.output(dest='S').encode('latin1', 'replace')

        pdf_bytes = generate_pdf()
        st.download_button(
            label="📄 Download PDF",
            data=pdf_bytes,
            file_name=f"{name}_quotation.pdf",
            mime="application/pdf"
        )

        # Delete project
        if st.button(f"❌ Delete Project: {name}", key=f"{proj_id}_del"):
            c.execute("DELETE FROM payments WHERE project_id = ?", (proj_id,))
            c.execute("DELETE FROM projects WHERE id = ?", (proj_id,))
            conn.commit()
            st.warning(f"❌ Project '{name}' deleted!")

# DB backup
st.markdown("### 📦 Backup")
with open('payments.db', 'rb') as f:
    st.download_button("Download Database File", f, file_name="payments.db")
