import streamlit as st
import sqlite3
from datetime import datetime
from fpdf import FPDF

# ✅ Initialize DB connection
conn = sqlite3.connect('payments.db', check_same_thread=False)
c = conn.cursor()

# ✅ Create tables if not exist
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

# ✅ Title
st.title("📑 Smart Payment Tracker")

# ✅ Add new project
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

# ✅ Fetch projects
c.execute("SELECT * FROM projects")
projects = c.fetchall()

if not projects:
    st.info("No projects found. Add one above!")
else:
    for project in projects:
        proj_id, name, client, quotation, created_at = project

        # ✅ Get total paid
        c.execute("SELECT SUM(amount) FROM payments WHERE project_id = ?", (proj_id,))
        total_paid = c.fetchone()[0] or 0
        due = quotation - total_paid

        with st.expander(f"📌 {name} — {client}"):
            st.write(f"**Created Date:** {created_at}")
            st.write(f"**Quotation:** Rs.{quotation:,.2f}")
            st.write(f"**Paid:** Rs.{total_paid:,.2f}")
            st.write(f"**Remaining Due:** Rs.{due:,.2f}")

            # ✅ List payments
            c.execute("SELECT * FROM payments WHERE project_id = ?", (proj_id,))
            payments = c.fetchall()
            if payments:
                st.markdown("**Payments:**")
                for p in payments:
                    st.write(f"Rs.{p[2]:,.2f} on {p[3]}")
            else:
                st.info("No payments yet.")

            # ✅ Add payment
            payment_amount = st.number_input(f"Add Payment for {name}", min_value=0.0, key=f"{proj_id}_pay")
            if st.button(f"Add Payment for {name}", key=f"{proj_id}_pay_btn"):
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO payments (project_id, amount, paid_at) VALUES (?, ?, ?)",
                          (proj_id, payment_amount, now))
                conn.commit()
                st.success(f"✅ Payment Rs.{payment_amount:,.2f} added for {name}!")

            # ✅ PDF generator with centered logo
            def generate_pdf():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)

                # ✅ Centered logo as letterhead
                try:
                    logo_width = 50  # adjust for your logo size
                    page_width = pdf.w - 2 * pdf.l_margin
                    x_center = (page_width - logo_width) / 2
                    pdf.image("logo.jpg", x=x_center, y=10, w=logo_width)
                except:
                    pass  # no logo, skip

                pdf.ln(40)  # space below logo

                pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, f"Project Quotation Summary", ln=True, align='C')
                pdf.ln(5)

                pdf.set_font("Arial", "", 12)

                def add_row(label, value):
                    pdf.cell(50, 10, label, 1)
                    pdf.cell(0, 10, str(value), 1, ln=True)

                add_row("Project Name:", name)
                add_row("Client Name:", client)
                add_row("Quotation:", f"Rs.{quotation:,.2f}")
                add_row("Total Paid:", f"Rs.{total_paid:,.2f}")
                add_row("Remaining Due:", f"Rs.{due:,.2f}")
                add_row("Created:", created_at)

                pdf.ln(10)

                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Payments", ln=True)
                pdf.set_font("Arial", "", 12)

                if payments:
                    pdf.cell(50, 10, "Amount", 1)
                    pdf.cell(0, 10, "Date", 1, ln=True)
                    for p in payments:
                        pdf.cell(50, 10, f"Rs.{p[2]:,.2f}", 1)
                        pdf.cell(0, 10, p[3], 1, ln=True)
                else:
                    pdf.cell(0, 10, "No payments yet.", 1, ln=True)

                return pdf.output(dest='S').encode('latin1', 'replace')

            pdf_bytes = generate_pdf()
            st.download_button(
                label="📄 Download PDF",
                data=pdf_bytes,
                file_name=f"{name}_quotation.pdf",
                mime="application/pdf",
                key=f"{proj_id}_pdf"
            )

            # ✅ Delete project
            if st.button(f"❌ Delete Project: {name}", key=f"{proj_id}_del"):
                c.execute("DELETE FROM payments WHERE project_id = ?", (proj_id,))
                c.execute("DELETE FROM projects WHERE id = ?", (proj_id,))
                conn.commit()
                st.warning(f"❌ Project '{name}' deleted!")

# ✅ DB backup
st.markdown("### 📦 Backup")
with open('payments.db', 'rb') as f:
    st.download_button("Download Database File", f, file_name="payments.db")
