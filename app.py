import streamlit as st
import sqlite3
from datetime import datetime
from fpdf import FPDF

# ✅ Connect to SQLite database
conn = sqlite3.connect('payments.db', check_same_thread=False)
c = conn.cursor()

# ✅ Create tables if they don't exist
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

# ✅ App title
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

        c.execute("SELECT SUM(amount) FROM payments WHERE project_id = ?", (proj_id,))
        total_paid = c.fetchone()[0] or 0
        due = quotation - total_paid

        with st.expander(f"📌 {name} — {client}"):
            st.write(f"**Created Date:** {created_at}")
            st.write(f"**Quotation:** Rs.{quotation:,.2f}")
            st.write(f"**Paid:** Rs.{total_paid:,.2f}")
            st.write(f"**Remaining Due:** Rs.{due:,.2f}")

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

            # ✅ Generate PDF with centered logo & table
            def generate_pdf():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.set_font("Arial", size=12)

                try:
                    # ✅ Centered logo like letterhead
                    logo_width = 50
                    page_width = pdf.w - 2 * pdf.l_margin
                    x_center = (pdf.w - logo_width) / 2
                    pdf.image("logo.jpg", x=x_center, y=15, w=logo_width)
                except Exception as e:
                    print("Logo error:", e)

                # Space below logo
                pdf.ln(60)

                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "Project Quotation Summary", ln=True, align='C')
                pdf.ln(5)

                pdf.set_font("Arial", "", 12)
                pdf.cell(50, 8, "Project Name:", 0)
                pdf.cell(0, 8, name, 0, ln=True)
                pdf.cell(50, 8, "Client Name:", 0)
                pdf.cell(0, 8, client, 0, ln=True)
                pdf.cell(50, 8, "Quotation:", 0)
                pdf.cell(0, 8, f"Rs.{quotation:,.2f}", 0, ln=True)
                pdf.cell(50, 8, "Total Paid:", 0)
                pdf.cell(0, 8, f"Rs.{total_paid:,.2f}", 0, ln=True)
                pdf.cell(50, 8, "Remaining Due:", 0)
                pdf.cell(0, 8, f"Rs.{due:,.2f}", 0, ln=True)
                pdf.cell(50, 8, "Created:", 0)
                pdf.cell(0, 8, created_at, 0, ln=True)

                pdf.ln(10)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Payments", ln=True)
                pdf.set_font("Arial", "", 12)

                if payments:
                    pdf.set_fill_color(200, 200, 200)
                    pdf.cell(50, 8, "Amount", 1, 0, 'C', 1)
                    pdf.cell(70, 8, "Date", 1, 1, 'C', 1)
                    for p in payments:
                        pdf.cell(50, 8, f"Rs.{p[2]:,.2f}", 1)
                        pdf.cell(70, 8, p[3], 1, ln=True)
                else:
                    pdf.cell(0, 8, "No payments yet.", 1, ln=True)

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

# ✅ DB backup download
st.markdown("### 📦 Backup")
with open('payments.db', 'rb') as f:
    st.download_button("Download Database File", f, file_name="payments.db")
