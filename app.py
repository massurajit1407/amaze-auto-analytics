import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

FILE_NAME = "amaze_tech_log.csv"
TANK_CAPACITY = 35.0
FASTAG_TOTAL_TRIPS = 200
FASTAG_COST = 3000

# -----------------------------
# CSV INITIALIZATION
# -----------------------------
if not os.path.exists(FILE_NAME):
    df_init = pd.DataFrame(columns=[
        "Entry_ID",
        "Date",
        "Drive_Profile",
        "AC_Mode",
        "Liters_Added",
        "Cost_per_Liter",
        "Full_Tank",
        "Odometer",
        "State_Toll",
        "Private_Toll",
        "Service_Cost",
        "Service_Desc",
        "Timestamp_Created",
        "Timestamp_Edited"
    ])
    df_init.to_csv(FILE_NAME, index=False)

df = pd.read_csv(FILE_NAME)

if not df.empty:
    df["Date"] = pd.to_datetime(df["Date"])

# -----------------------------
# SIDEBAR NAVIGATION
# -----------------------------
menu = st.sidebar.radio("Navigation", [
    "Fuel Entry",
    "Transit & Maintenance",
    "Dashboard",
    "Reports"
])

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def save_df():
    df.to_csv(FILE_NAME, index=False)

def calculate_efficiency():
    if df.empty:
        return 15  # default initial estimate
    
    full_tanks = df[df["Full_Tank"] == True]
    if len(full_tanks) < 2:
        return 15
    
    efficiencies = []
    for i in range(1, len(full_tanks)):
        prev = full_tanks.iloc[i-1]
        curr = full_tanks.iloc[i]
        distance = curr["Odometer"] - prev["Odometer"]
        fuel = curr["Liters_Added"]
        if fuel > 0:
            efficiencies.append(distance / fuel)
    if efficiencies:
        return np.mean(efficiencies)
    return 15

def current_fuel_level():
    if df.empty:
        return 0
    
    last_full_index = df[df["Full_Tank"] == True].last_valid_index()
    if last_full_index is None:
        return 0
    
    fuel = TANK_CAPACITY
    for i in range(last_full_index+1, len(df)):
        row = df.iloc[i]
        fuel += row["Liters_Added"]
        distance = row["Odometer"] - df.iloc[i-1]["Odometer"]
        eff = calculate_efficiency()
        fuel -= distance / eff
    
    return max(0, min(TANK_CAPACITY, fuel))

# -----------------------------
# FUEL ENTRY PAGE
# -----------------------------
if menu == "Fuel Entry":

    st.header("⛽ Fuel Log Entry")

    with st.form("fuel_form"):
        date = st.date_input("Date")
        profile = st.selectbox("Drive Profile", ["City", "Highway"])
        ac = st.selectbox("AC Usage", ["Mostly AC", "Mixed", "No AC"])
        liters = st.number_input("Liters Added", min_value=0.0, format="%.2f")
        cost = st.number_input("Cost per Liter", min_value=0.0, format="%.2f")
        full = st.checkbox("Full Tank (Autocut)")
        odo = st.number_input("Current Odometer", min_value=0)
        submit = st.form_submit_button("Save Entry")

        if submit:
            if not df.empty and odo <= df["Odometer"].max():
                st.error("Odometer must be greater than previous entry.")
            else:
                new_entry = {
                    "Entry_ID": len(df)+1,
                    "Date": date,
                    "Drive_Profile": profile,
                    "AC_Mode": ac,
                    "Liters_Added": liters,
                    "Cost_per_Liter": cost,
                    "Full_Tank": full,
                    "Odometer": odo,
                    "State_Toll": 0,
                    "Private_Toll": 0,
                    "Service_Cost": 0,
                    "Service_Desc": "",
                    "Timestamp_Created": datetime.now(),
                    "Timestamp_Edited": ""
                }
                df.loc[len(df)] = new_entry
                save_df()
                st.success("Entry Saved Successfully")

# -----------------------------
# TRANSIT & MAINTENANCE
# -----------------------------
elif menu == "Transit & Maintenance":

    st.header("🛣 Transit & Maintenance")

    if not df.empty:
        selected = st.selectbox("Select Entry ID", df["Entry_ID"])
        row_index = df[df["Entry_ID"] == selected].index[0]

        with st.form("update_form"):
            state_toll = st.number_input("State Toll", min_value=0.0, format="%.2f")
            private_toll = st.number_input("Private Toll", min_value=0.0, format="%.2f")
            service_cost = st.number_input("Service Cost", min_value=0.0, format="%.2f")
            service_desc = st.text_input("Service Description")
            update = st.form_submit_button("Update Entry")

            if update:
                df.at[row_index, "State_Toll"] = state_toll
                df.at[row_index, "Private_Toll"] = private_toll
                df.at[row_index, "Service_Cost"] = service_cost
                df.at[row_index, "Service_Desc"] = service_desc
                df.at[row_index, "Timestamp_Edited"] = datetime.now()
                save_df()
                st.success("Updated Successfully")

# -----------------------------
# DASHBOARD
# -----------------------------
elif menu == "Dashboard":

    st.header("📊 Fuel & Financial Dashboard")

    if not df.empty:

        efficiency = calculate_efficiency()
        fuel_level = current_fuel_level()
        dte = fuel_level * efficiency

        col1, col2, col3 = st.columns(3)
        col1.metric("Average Mileage (KM/L)", f"{efficiency:.2f}")
        col2.metric("Fuel Remaining (L)", f"{fuel_level:.2f}")
        col3.metric("Distance To Empty (KM)", f"{dte:.0f}")

        # Fuel Bars
        bars = int((fuel_level / TANK_CAPACITY) * 10)
        st.write("Fuel Level:", "🟩"*bars + "⬜"*(10-bars))

        # Cost Per KM
        total_distance = df["Odometer"].max() - df["Odometer"].min()
        total_fuel_cost = (df["Liters_Added"] * df["Cost_per_Liter"]).sum()
        total_toll = df["State_Toll"].sum() + df["Private_Toll"].sum()
        total_service = df["Service_Cost"].sum()

        fastag_used = len(df[df["State_Toll"] > 0])
        fastag_amortized = (fastag_used / FASTAG_TOTAL_TRIPS) * FASTAG_COST

        total_cost = total_fuel_cost + total_toll + total_service + fastag_amortized

        if total_distance > 0:
            cpk = total_cost / total_distance
            st.metric("Total Cost Per KM", f"₹ {cpk:.2f}")

# -----------------------------
# REPORTS
# -----------------------------
elif menu == "Reports":

    st.header("📅 Custom Date Report (Max 1 Year)")

    if not df.empty:
        start = st.date_input("Start Date")
        end = st.date_input("End Date")

        if end >= start and (end - start) <= timedelta(days=365):
            filtered = df[(df["Date"] >= pd.to_datetime(start)) &
                          (df["Date"] <= pd.to_datetime(end))]
            st.dataframe(filtered)

            if not filtered.empty:
                csv = filtered.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", csv, "custom_report.csv")
        else:
            st.warning("Select valid date range (max 1 year)")
