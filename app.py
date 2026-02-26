import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

st.set_page_config(page_title="Amaze Auto Analytics", layout="wide")

st.title("🚗 Amaze Auto Analytics System")
st.markdown("Currency: ₹ INR")

# ==============================
# DATABASE CONNECTION
# ==============================
conn = sqlite3.connect("amaze_auto.db", check_same_thread=False)
cursor = conn.cursor()

# Create Tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    description TEXT,
    amount REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS fuel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    litres REAL,
    amount REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS toll (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    location TEXT,
    amount REAL
)
""")

conn.commit()

# ==============================
# HELPER FUNCTIONS
# ==============================
def load_table(table):
    df = pd.read_sql(f"SELECT * FROM {table}", conn)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df

def delete_row(table, id):
    cursor.execute(f"DELETE FROM {table} WHERE id=?", (id,))
    conn.commit()

def update_row(table, id, values):
    if table == "maintenance":
        cursor.execute("UPDATE maintenance SET date=?, description=?, amount=? WHERE id=?",
                       (*values, id))
    elif table == "fuel":
        cursor.execute("UPDATE fuel SET date=?, litres=?, amount=? WHERE id=?",
                       (*values, id))
    elif table == "toll":
        cursor.execute("UPDATE toll SET date=?, location=?, amount=? WHERE id=?",
                       (*values, id))
    conn.commit()

# ==============================
# SIDEBAR NAVIGATION
# ==============================
menu = st.sidebar.radio("Navigation", 
                        ["Dashboard", "Maintenance", "Fuel", "Toll", "Reports"])

# ==============================
# MAINTENANCE PAGE
# ==============================
if menu == "Maintenance":

    st.header("🔧 Maintenance Entry")

    with st.form("maint_form"):
        date = st.date_input("Date", datetime.today())
        desc = st.text_input("Description")
        amount = st.number_input("Amount (₹)", min_value=0.0)
        submit = st.form_submit_button("Add")

        if submit:
            cursor.execute("INSERT INTO maintenance (date, description, amount) VALUES (?, ?, ?)",
                           (str(date), desc, amount))
            conn.commit()
            st.success("Maintenance entry added")

    df = load_table("maintenance")

    if not df.empty:
        st.dataframe(df)

        selected = st.selectbox("Select ID to Edit/Delete", df["id"])
        row = df[df["id"] == selected].iloc[0]

        col1, col2 = st.columns(2)

        if col1.button("Delete"):
            delete_row("maintenance", selected)
            st.success("Deleted")

        if col2.button("Load for Edit"):
            with st.form("edit_maint"):
                edate = st.date_input("Edit Date", row["date"])
                edesc = st.text_input("Edit Description", row["description"])
                eamount = st.number_input("Edit Amount", value=float(row["amount"]))
                update = st.form_submit_button("Update")

                if update:
                    update_row("maintenance", selected,
                               (str(edate), edesc, eamount))
                    st.success("Updated")

# ==============================
# FUEL PAGE
# ==============================
elif menu == "Fuel":

    st.header("⛽ Fuel Entry")

    with st.form("fuel_form"):
        date = st.date_input("Date", datetime.today())
        litres = st.number_input("Litres", min_value=0.0)
        amount = st.number_input("Amount (₹)", min_value=0.0)
        submit = st.form_submit_button("Add")

        if submit:
            cursor.execute("INSERT INTO fuel (date, litres, amount) VALUES (?, ?, ?)",
                           (str(date), litres, amount))
            conn.commit()
            st.success("Fuel entry added")

    df = load_table("fuel")

    if not df.empty:
        st.dataframe(df)

        selected = st.selectbox("Select ID", df["id"])
        row = df[df["id"] == selected].iloc[0]

        if st.button("Delete Fuel"):
            delete_row("fuel", selected)
            st.success("Deleted")

# ==============================
# TOLL PAGE
# ==============================
elif menu == "Toll":

    st.header("🛣 Toll Entry")

    with st.form("toll_form"):
        date = st.date_input("Date", datetime.today())
        location = st.text_input("Location")
        amount = st.number_input("Amount (₹)", min_value=0.0)
        submit = st.form_submit_button("Add")

        if submit:
            cursor.execute("INSERT INTO toll (date, location, amount) VALUES (?, ?, ?)",
                           (str(date), location, amount))
            conn.commit()
            st.success("Toll entry added")

    df = load_table("toll")

    if not df.empty:
        st.dataframe(df)

        selected = st.selectbox("Select ID", df["id"])
        if st.button("Delete Toll"):
            delete_row("toll", selected)
            st.success("Deleted")

# ==============================
# DASHBOARD
# ==============================
elif menu == "Dashboard":

    st.header("📊 Financial Dashboard")

    maint = load_table("maintenance")
    fuel = load_table("fuel")
    toll = load_table("toll")

    total = 0
    if not maint.empty:
        total += maint["amount"].sum()
    if not fuel.empty:
        total += fuel["amount"].sum()
    if not toll.empty:
        total += toll["amount"].sum()

    st.metric("Total Expense", f"₹ {total:,.2f}")

    # Monthly combined chart
    combined = pd.concat([
        maint[["date", "amount"]],
        fuel[["date", "amount"]],
        toll[["date", "amount"]],
    ])

    if not combined.empty:
        combined["month"] = combined["date"].dt.to_period("M")
        monthly = combined.groupby("month")["amount"].sum()
        st.line_chart(monthly)

# ==============================
# REPORTS
# ==============================
elif menu == "Reports":

    st.header("📅 Custom Report (Max 1 Year)")

    start = st.date_input("Start Date")
    end = st.date_input("End Date")

    if end >= start and (end - start) <= timedelta(days=365):

        maint = load_table("maintenance")
        fuel = load_table("fuel")
        toll = load_table("toll")

        combined = pd.concat([
            maint.assign(type="Maintenance"),
            fuel.assign(type="Fuel"),
            toll.assign(type="Toll")
        ])

        filtered = combined[
            (combined["date"] >= pd.to_datetime(start)) &
            (combined["date"] <= pd.to_datetime(end))
        ]

        st.dataframe(filtered)

        if not filtered.empty:
            csv = filtered.to_csv(index=False).encode("utf-8")
            st.download_button("Download Report", csv, "report.csv")

    else:
        st.warning("Select valid range (max 1 year)")
