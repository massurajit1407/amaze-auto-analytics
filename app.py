import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
import matplotlib.pyplot as plt

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Honda Amaze Tech-Log", layout="wide")

DATA_FILE = "amaze_tech_log.csv"
TANK_CAPACITY = 35.0
FASTAG_PASS_COST = 3000
FASTAG_TOTAL_TRIPS = 200
FASTAG_COST_PER_TRIP = FASTAG_PASS_COST / FASTAG_TOTAL_TRIPS

# =========================
# LOAD DATABASE
# =========================
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(
                df["Date"],
                errors="coerce",
                dayfirst=True
            )
            df = df.dropna(subset=["Date"])

        return df
    else:
        return pd.DataFrame()

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

# =========================
# SIDEBAR NAVIGATION
# =========================
menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Fuel Entry",
        "FASTag / Toll Entry",
        "Maintenance Entry",
        "Dashboard",
        "Reports",
        "Database Tools"
    ]
)

# =========================
# FUEL ENTRY
# =========================
if menu == "Fuel Entry":

    st.header("Fuel Log Entry")

    with st.form("fuel_form"):
        date = st.date_input("Date")
        drive_profile = st.selectbox("Drive Profile", ["City", "Highway"])
        ac_usage = st.selectbox("AC Usage", ["Mostly AC", "Mixed", "No AC"])

        liters = st.number_input("Liters Added", min_value=0.0, step=0.01)
        cost_per_liter = st.number_input("Cost per Liter (₹)", min_value=0.0, step=0.01)
        full_tank = st.selectbox("Full Tank?", ["No", "Yes"])
        odometer = st.number_input("Current Odometer", min_value=0)

        submitted = st.form_submit_button("Save Entry")

    if submitted:
        total_cost = liters * cost_per_liter
        timestamp_created = datetime.now()

        new_row = {
            "Date": date,
            "Type": "Fuel",
            "Drive_Profile": drive_profile,
            "AC_Usage": ac_usage,
            "Liters": liters,
            "Cost_per_Liter": cost_per_liter,
            "Fuel_Cost": total_cost,
            "Full_Tank": full_tank,
            "Odometer": odometer,
            "FASTag_Trips": 0,
            "State_Toll": 0,
            "Private_Toll": 0,
            "Service_Cost": 0,
            "Service_Description": "",
            "Timestamp_Created": timestamp_created,
            "Timestamp_Edited": ""
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("Fuel entry saved successfully!")

# =========================
# FASTAG / TOLL ENTRY
# =========================
elif menu == "FASTag / Toll Entry":

    st.header("FASTag / Toll Entry")

    with st.form("toll_form"):
        date = st.date_input("Date")
        fastag_trip = st.number_input("NHAI Trips Used", min_value=0)
        state_toll = st.number_input("State Toll ₹", min_value=0.0, step=0.01)
        private_toll = st.number_input("Private Toll ₹", min_value=0.0, step=0.01)

        submitted = st.form_submit_button("Save Toll Entry")

    if submitted:
        total_fastag_cost = fastag_trip * FASTAG_COST_PER_TRIP
        timestamp_created = datetime.now()

        new_row = {
            "Date": date,
            "Type": "Toll",
            "Drive_Profile": "",
            "AC_Usage": "",
            "Liters": 0,
            "Cost_per_Liter": 0,
            "Fuel_Cost": 0,
            "Full_Tank": "",
            "Odometer": 0,
            "FASTag_Trips": fastag_trip,
            "State_Toll": state_toll,
            "Private_Toll": private_toll,
            "Service_Cost": 0,
            "Service_Description": "",
            "Timestamp_Created": timestamp_created,
            "Timestamp_Edited": ""
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("Toll entry saved!")

# =========================
# MAINTENANCE ENTRY
# =========================
elif menu == "Maintenance Entry":

    st.header("Maintenance Entry")

    with st.form("service_form"):
        date = st.date_input("Date")
        description = st.text_input("Service Description")
        cost = st.number_input("Service Cost ₹", min_value=0.0, step=0.01)

        submitted = st.form_submit_button("Save Maintenance Entry")

    if submitted:
        timestamp_created = datetime.now()

        new_row = {
            "Date": date,
            "Type": "Service",
            "Drive_Profile": "",
            "AC_Usage": "",
            "Liters": 0,
            "Cost_per_Liter": 0,
            "Fuel_Cost": 0,
            "Full_Tank": "",
            "Odometer": 0,
            "FASTag_Trips": 0,
            "State_Toll": 0,
            "Private_Toll": 0,
            "Service_Cost": cost,
            "Service_Description": description,
            "Timestamp_Created": timestamp_created,
            "Timestamp_Edited": ""
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("Maintenance entry saved!")

# =========================
# DASHBOARD
# =========================
elif menu == "Dashboard":

    st.header("Amaze Financial Dashboard")

    if df.empty:
        st.warning("No data available.")
    else:

        # Sort latest first
        df_sorted = df.sort_values(by="Date", ascending=False)

        # =====================
        # COST SUMMARY
        # =====================
        total_fuel = df["Fuel_Cost"].sum()
        total_service = df["Service_Cost"].sum()
        total_toll = df["State_Toll"].sum() + df["Private_Toll"].sum()
        total_fastag = df["FASTag_Trips"].sum() * FASTAG_COST_PER_TRIP

        total_cost = total_fuel + total_service + total_toll + total_fastag

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Fuel ₹", round(total_fuel, 2))
        col2.metric("Total Service ₹", round(total_service, 2))
        col3.metric("Total Toll ₹", round(total_toll + total_fastag, 2))
        col4.metric("Grand Total ₹", round(total_cost, 2))

        st.divider()

        # =====================
        # MONTHLY SERVICE TREND
        # =====================
        st.subheader("Monthly Service Trend")

        service_df = df[df["Type"] == "Service"].copy()

        if not service_df.empty:
            service_df["Month"] = service_df["Date"].dt.to_period("M")
            monthly = service_df.groupby("Month")["Service_Cost"].sum()

            fig, ax = plt.subplots()
            monthly.plot(kind="bar", ax=ax)
            ax.set_ylabel("Service Cost ₹")
            ax.set_xlabel("Month")
            st.pyplot(fig)
        else:
            st.info("No service data available.")

        st.divider()

        # =====================
        # SHOW COMPLETE DATABASE
        # =====================
        st.subheader("Complete Database Records")

        # Clean display version (hide internal timestamps if needed)
        display_df = df_sorted.copy()

        st.dataframe(display_df, use_container_width=True)

# =========================
# REPORTS
# =========================
elif menu == "Reports":

    st.header("Date Range Report")

    if df.empty:
        st.warning("No data available.")
    else:
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")

        if start_date <= end_date:
            mask = (df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))
            report_df = df.loc[mask]

            st.dataframe(report_df)

            total_cost = (
                report_df["Fuel_Cost"].sum() +
                report_df["Service_Cost"].sum() +
                report_df["State_Toll"].sum() +
                report_df["Private_Toll"].sum() +
                report_df["FASTag_Trips"].sum() * FASTAG_COST_PER_TRIP
            )

            st.metric("Total Cost in Period ₹", round(total_cost, 2))

# =========================
# DATABASE TOOLS
# =========================
elif menu == "Database Tools":

    st.header("Database Tools")

    uploaded_file = st.file_uploader("Upload CSV to Replace Database", type=["csv"])

    if uploaded_file:
        new_df = pd.read_csv(uploaded_file)
        save_data(new_df)
        st.success("Database replaced successfully!")
        st.experimental_rerun()

    st.download_button(
        "Download Current Database",
        df.to_csv(index=False),
        file_name="amaze_tech_log_backup.csv"
    )
