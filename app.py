import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

st.set_page_config(page_title="Amaze Auto Analytics", layout="wide")

st.title("🚗 Amaze Auto Analytics")
st.markdown("Light Theme | Currency: ₹ INR")

# -----------------------------
# DATABASE SETUP
# -----------------------------
conn = sqlite3.connect("amaze_auto.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    customer_name TEXT,
    service_type TEXT,
    amount REAL
)
""")
conn.commit()


# -----------------------------
# FUNCTIONS
# -----------------------------
def load_data():
    df = pd.read_sql("SELECT * FROM services", conn)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


def insert_data(date, name, service, amount):
    cursor.execute(
        "INSERT INTO services (date, customer_name, service_type, amount) VALUES (?, ?, ?, ?)",
        (date, name, service, amount),
    )
    conn.commit()


def update_data(id, date, name, service, amount):
    cursor.execute(
        "UPDATE services SET date=?, customer_name=?, service_type=?, amount=? WHERE id=?",
        (date, name, service, amount, id),
    )
    conn.commit()


def delete_data(id):
    cursor.execute("DELETE FROM services WHERE id=?", (id,))
    conn.commit()


def replace_database(df):
    cursor.execute("DELETE FROM services")
    conn.commit()
    df.to_sql("services", conn, if_exists="append", index=False)


# -----------------------------
# CSV UPLOAD
# -----------------------------
st.header("📂 Upload CSV")

uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file is not None:
    df_upload = pd.read_csv(uploaded_file)

    df_upload.columns = [col.lower().replace(" ", "_") for col in df_upload.columns]

    if st.button("Replace Entire Database"):
        replace_database(df_upload)
        st.success("Database replaced successfully!")

    if st.button("Append to Existing Database"):
        df_upload.to_sql("services", conn, if_exists="append", index=False)
        st.success("Data appended successfully!")


# -----------------------------
# ADD ENTRY
# -----------------------------
st.header("➕ Add New Entry")

with st.form("add_form"):
    date = st.date_input("Date", datetime.today())
    name = st.text_input("Customer Name")
    service = st.text_input("Service Type")
    amount = st.number_input("Amount (INR)", min_value=0.0)

    submitted = st.form_submit_button("Add Entry")

    if submitted:
        insert_data(str(date), name, service, amount)
        st.success("Entry added successfully!")


# -----------------------------
# LOAD DATA
# -----------------------------
df = load_data()

# -----------------------------
# DASHBOARD SUMMARY
# -----------------------------
st.header("📊 Dashboard Summary")

if not df.empty:
    total_revenue = df["amount"].sum()
    total_jobs = len(df)
    avg_invoice = df["amount"].mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"₹ {total_revenue:,.2f}")
    col2.metric("Total Jobs", total_jobs)
    col3.metric("Average Invoice", f"₹ {avg_invoice:,.2f}")

    # Monthly Revenue
    df["month"] = df["date"].dt.to_period("M")
    monthly = df.groupby("month")["amount"].sum().reset_index()

    st.subheader("📅 Monthly Revenue")
    st.line_chart(monthly.set_index("month"))

    # Service Wise Revenue
    st.subheader("🔧 Service-wise Revenue")
    service_rev = df.groupby("service_type")["amount"].sum().reset_index()
    st.bar_chart(service_rev.set_index("service_type"))

    # Service Wise Monthly Trend
    st.subheader("📈 Service-wise Monthly Trend")
    pivot = df.pivot_table(
        index="month",
        columns="service_type",
        values="amount",
        aggfunc="sum",
    ).fillna(0)
    st.line_chart(pivot)

else:
    st.info("No data available.")


# -----------------------------
# DATE RANGE REPORT (Max 1 Year)
# -----------------------------
st.header("📅 Generate Report Between Dates")

if not df.empty:
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")

    if end_date >= start_date and (end_date - start_date) <= timedelta(days=365):
        filtered = df[
            (df["date"] >= pd.to_datetime(start_date))
            & (df["date"] <= pd.to_datetime(end_date))
        ]

        st.dataframe(filtered)

        if not filtered.empty:
            csv = filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Report CSV",
                csv,
                "custom_report.csv",
                "text/csv",
            )
    else:
        st.warning("Select valid date range (max 1 year).")


# -----------------------------
# EDIT / DELETE
# -----------------------------
st.header("✏ Edit or Delete Entry")

if not df.empty:
    selected_id = st.selectbox("Select Entry ID", df["id"])

    selected_row = df[df["id"] == selected_id].iloc[0]

    with st.form("edit_form"):
        edit_date = st.date_input("Edit Date", selected_row["date"])
        edit_name = st.text_input("Edit Customer Name", selected_row["customer_name"])
        edit_service = st.text_input("Edit Service Type", selected_row["service_type"])
        edit_amount = st.number_input(
            "Edit Amount (INR)", value=float(selected_row["amount"])
        )

        col1, col2 = st.columns(2)

        update_btn = col1.form_submit_button("Update")
        delete_btn = col2.form_submit_button("Delete")

        if update_btn:
            update_data(
                selected_id,
                str(edit_date),
                edit_name,
                edit_service,
                edit_amount,
            )
            st.success("Entry updated successfully!")

        if delete_btn:
            delete_data(selected_id)
            st.success("Entry deleted successfully!")
