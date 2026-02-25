import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Amaze Analytics Engine", layout="wide")

FILE_NAME = "amaze_tech_log.csv"
TANK_CAPACITY = 35

# ----------------------------
# Initialize CSV
# ----------------------------
if not os.path.exists(FILE_NAME):
    df_init = pd.DataFrame(columns=[
        "Entry_ID",
        "Date",
        "Drive_Profile",
        "AC_Usage",
        "Liters",
        "Cost_per_Liter",
        "Full_Tank",
        "Odometer",
        "Timestamp_Created",
        "Timestamp_Edited",
        "Entry_Type",
        "Description",
        "Amount"
    ])
    df_init.to_csv(FILE_NAME, index=False)

df = pd.read_csv(FILE_NAME)

# ----------------------------
# Sidebar Navigation
# ----------------------------
st.sidebar.title("🚗 Amaze Analytics Engine")
menu = st.sidebar.radio("Select Module", [
    "Fuel Log",
    "Transit / FASTag",
    "Maintenance",
    "Dashboard",
    "Reports"
])

# ==========================================================
# FUEL MODULE
# ==========================================================
if menu == "Fuel Log":

    st.header("⛽ Fuel Entry")

    with st.form("fuel_form"):

        date = st.date_input("Select Date")
        drive_profile = st.selectbox("Drive Profile", ["City", "Highway"])
        ac_usage = st.selectbox("AC Usage", ["Mostly AC", "Mixed", "No AC"])
        liters = st.number_input("Liters Added", min_value=0.0, format="%.2f")
        cost_per_liter = st.number_input("Cost per Liter (₹)", min_value=0.0, format="%.2f")
        full_tank = st.selectbox("Full Tank (Autocut)?", ["No", "Yes"])
        odometer = st.number_input("Current Odometer", min_value=0, step=1)

        submitted = st.form_submit_button("Save Entry")

        if submitted:
            entry_id = len(df) + 1
            timestamp = datetime.now()

            new_row = {
                "Entry_ID": entry_id,
                "Date": date,
                "Drive_Profile": drive_profile,
                "AC_Usage": ac_usage,
                "Liters": liters,
                "Cost_per_Liter": cost_per_liter,
                "Full_Tank": full_tank,
                "Odometer": odometer,
                "Timestamp_Created": timestamp,
                "Timestamp_Edited": "",
                "Entry_Type": "Fuel",
                "Description": "",
                "Amount": liters * cost_per_liter
            }

            df = pd.concat([df, pd.DataFrame([new_row])])
            df.to_csv(FILE_NAME, index=False)
            st.success("Fuel Entry Saved Successfully!")

# ==========================================================
# FASTAG MODULE
# ==========================================================
elif menu == "Transit / FASTag":

    st.header("🛣 Transit / Toll Entry")

    with st.form("toll_form"):
        date = st.date_input("Select Date")
        nhai_trip = st.checkbox("NHAI Annual Pass Trip (200 Trips ₹3000)")
        state_toll = st.number_input("State Toll (₹)", min_value=0.0, format="%.2f")
        private_toll = st.number_input("Private Toll (₹)", min_value=0.0, format="%.2f")

        submitted = st.form_submit_button("Save Transit Entry")

        if submitted:
            entry_id = len(df) + 1
            timestamp = datetime.now()

            nhai_cost = 3000 / 200 if nhai_trip else 0
            total = nhai_cost + state_toll + private_toll

            new_row = {
                "Entry_ID": entry_id,
                "Date": date,
                "Drive_Profile": "",
                "AC_Usage": "",
                "Liters": 0,
                "Cost_per_Liter": 0,
                "Full_Tank": "",
                "Odometer": "",
                "Timestamp_Created": timestamp,
                "Timestamp_Edited": "",
                "Entry_Type": "Transit",
                "Description": "Toll Entry",
                "Amount": total
            }

            df = pd.concat([df, pd.DataFrame([new_row])])
            df.to_csv(FILE_NAME, index=False)
            st.success("Transit Entry Saved!")

# ==========================================================
# MAINTENANCE MODULE
# ==========================================================
elif menu == "Maintenance":

    st.header("🔧 Maintenance Entry")

    with st.form("maintenance_form"):
        date = st.date_input("Select Date")
        description = st.text_input("Service Description")
        amount = st.number_input("Cost (₹)", min_value=0.01, format="%.2f")

        submitted = st.form_submit_button("Save Maintenance")

        if submitted:
            entry_id = len(df) + 1
            timestamp = datetime.now()

            new_row = {
                "Entry_ID": entry_id,
                "Date": date,
                "Drive_Profile": "",
                "AC_Usage": "",
                "Liters": 0,
                "Cost_per_Liter": 0,
                "Full_Tank": "",
                "Odometer": "",
                "Timestamp_Created": timestamp,
                "Timestamp_Edited": "",
                "Entry_Type": "Maintenance",
                "Description": description,
                "Amount": amount
            }

            df = pd.concat([df, pd.DataFrame([new_row])])
            df.to_csv(FILE_NAME, index=False)
            st.success("Maintenance Entry Saved!")

# ==========================================================
# DASHBOARD
# ==========================================================
elif menu == "Dashboard":

    st.header("📊 Fuel Dashboard")

    fuel_df = df[df["Entry_Type"] == "Fuel"]

    if not fuel_df.empty:

        fuel_df = fuel_df.sort_values("Odometer")

        if len(fuel_df) > 1:
            distance = fuel_df["Odometer"].iloc[-1] - fuel_df["Odometer"].iloc[0]
            total_liters = fuel_df["Liters"].sum()
            avg_mileage = distance / total_liters if total_liters > 0 else 0

            st.metric("Average Mileage (KM/L)", round(avg_mileage, 2))

            # Fuel Bar Display
            last_liters = fuel_df["Liters"].iloc[-1]
            fuel_percent = min((last_liters / TANK_CAPACITY) * 100, 100)

            st.progress(int(fuel_percent))
            st.write(f"Fuel Level: {round(fuel_percent,2)} %")

            # Distance to Empty
            dte = avg_mileage * last_liters
            st.metric("Estimated Distance to Empty (KM)", round(dte, 2))

    else:
        st.info("No fuel data available.")

# ==========================================================
# REPORTS
# ==========================================================
elif menu == "Reports":

    st.header("📈 Trend Analytics")

    fuel_df = df[df["Entry_Type"] == "Fuel"]

    if len(fuel_df) > 1:

        fuel_df = fuel_df.sort_values("Odometer")
        fuel_df["Distance"] = fuel_df["Odometer"].diff()

        fuel_df["Mileage"] = fuel_df["Distance"] / fuel_df["Liters"]

        st.subheader("Mileage Trend")
        fig, ax = plt.subplots()
        ax.plot(fuel_df["Mileage"])
        ax.set_ylabel("KM/L")
        st.pyplot(fig)

        total_cost = df["Amount"].sum()
        total_distance = fuel_df["Odometer"].iloc[-1] - fuel_df["Odometer"].iloc[0]

        cpk = total_cost / total_distance if total_distance > 0 else 0

        st.metric("Total Cost Per KM (₹)", round(cpk, 2))

    else:
        st.info("Not enough data to generate report.")
