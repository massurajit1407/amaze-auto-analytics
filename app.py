import streamlit as st
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt

# ===================================
# CONFIGURATION
# ===================================
st.set_page_config(page_title="Amaze VX CVT Intelligence Log", layout="wide")

DATA_FILE = "amaze_tech_log.csv"
TANK_CAPACITY = 35.0
FASTAG_TOTAL_TRIPS = 200
FASTAG_PASS_COST = 3000
FASTAG_COST_PER_TRIP = FASTAG_PASS_COST / FASTAG_TOTAL_TRIPS

# ===================================
# DATABASE FUNCTIONS
# ===================================
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.dropna(subset=["Date"])
        return df
    else:
        return pd.DataFrame(columns=[
            "Date","Type","Drive_Profile","AC_Usage",
            "Liters","Cost_per_Liter","Fuel_Cost",
            "Full_Tank","Odometer",
            "FASTag_Trips","State_Toll","Private_Toll",
            "Service_Cost","Service_Description",
            "Timestamp_Created","Timestamp_Edited"
        ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

# ===================================
# METRICS FUNCTIONS
# ===================================
def calculate_distance_and_avg(df):
    fuel_df = df[df["Type"]=="Fuel"].sort_values("Odometer")
    if len(fuel_df) < 2:
        return 0,0
    distance = fuel_df["Odometer"].max() - fuel_df["Odometer"].min()
    total_liters = fuel_df["Liters"].sum()
    avg = distance / total_liters if total_liters>0 else 0
    return distance, round(avg,2)

def lifetime_cpk(df):
    fuel_cost = df["Fuel_Cost"].sum()
    toll_cost = df["State_Toll"].sum() + df["Private_Toll"].sum()
    fastag_cost = df["FASTag_Trips"].sum() * FASTAG_COST_PER_TRIP
    service_cost = df["Service_Cost"].sum()

    total_cost = fuel_cost + toll_cost + fastag_cost + service_cost

    fuel_df = df[df["Type"]=="Fuel"]
    if len(fuel_df)<2:
        return 0
    distance = fuel_df["Odometer"].max() - fuel_df["Odometer"].min()
    return round(total_cost/distance,2) if distance>0 else 0

def fuel_remaining(df):
    fuel_df = df[df["Type"]=="Fuel"].sort_values("Date")
    if fuel_df.empty:
        return 0
    last = fuel_df.iloc[-1]
    return min(last["Liters"], TANK_CAPACITY)

# ===================================
# TABS
# ===================================
tab1, tab2, tab3, tab4 = st.tabs([
    "Log Sortie",
    "Transit & Maintenance",
    "Dashboard & Analytics",
    "Database Management"
])

# ===================================
# TAB 1 — FUEL ENTRY
# ===================================
with tab1:
    st.header("Fuel Log Entry")

    with st.form("fuel_form"):
        date = st.date_input("Date")
        drive = st.selectbox("Drive Profile", ["City","Highway"])
        ac = st.selectbox("AC Usage", ["Mostly AC","Mixed","No AC"])
        liters = st.number_input("Liters Added", min_value=0.01, step=0.01)
        cost_per_liter = st.number_input("Cost per Liter (₹)", min_value=0.01, step=0.01)
        full = st.selectbox("Full Tank (Autocut)?", ["No","Yes"])
        odo = st.number_input("Current Odometer", min_value=1, step=1)

        submitted = st.form_submit_button("Save Entry")

    if submitted:
        if not df.empty:
            last_odo = df["Odometer"].max()
            if odo <= last_odo:
                st.error("Odometer must be greater than previous entry.")
                st.stop()

        new_row = {
            "Date":date,
            "Type":"Fuel",
            "Drive_Profile":drive,
            "AC_Usage":ac,
            "Liters":liters,
            "Cost_per_Liter":cost_per_liter,
            "Fuel_Cost":liters*cost_per_liter,
            "Full_Tank":full,
            "Odometer":odo,
            "FASTag_Trips":0,
            "State_Toll":0,
            "Private_Toll":0,
            "Service_Cost":0,
            "Service_Description":"",
            "Timestamp_Created":datetime.now(),
            "Timestamp_Edited":""
        }

        df = pd.concat([df,pd.DataFrame([new_row])],ignore_index=True)
        save_data(df)
        st.success("Fuel entry saved successfully.")

# ===================================
# TAB 2 — TOLL & SERVICE
# ===================================
with tab2:
    st.header("Transit & Maintenance")

    st.subheader("FASTag / Toll")

    with st.form("toll_form"):
        date2 = st.date_input("Date", key="toll_date")
        fastag = st.number_input("NHAI Trips Used", min_value=0, step=1)
        state = st.number_input("State Toll ₹", min_value=0.0, step=0.01)
        private = st.number_input("Private Toll ₹", min_value=0.0, step=0.01)
        submit2 = st.form_submit_button("Save Toll")

    if submit2:
        new_row = {
            "Date":date2,
            "Type":"Toll",
            "Drive_Profile":"",
            "AC_Usage":"",
            "Liters":0,
            "Cost_per_Liter":0,
            "Fuel_Cost":0,
            "Full_Tank":"",
            "Odometer":0,
            "FASTag_Trips":fastag,
            "State_Toll":state,
            "Private_Toll":private,
            "Service_Cost":0,
            "Service_Description":"",
            "Timestamp_Created":datetime.now(),
            "Timestamp_Edited":""
        }
        df = pd.concat([df,pd.DataFrame([new_row])],ignore_index=True)
        save_data(df)
        st.success("Toll entry saved.")

    st.subheader("Maintenance Entry")

    with st.form("service_form"):
        date3 = st.date_input("Date", key="service_date")
        desc = st.text_input("Service Description")
        cost = st.number_input("Service Cost ₹", min_value=0.01, step=0.01)
        submit3 = st.form_submit_button("Save Service")

    if submit3:
        new_row = {
            "Date":date3,
            "Type":"Service",
            "Drive_Profile":"",
            "AC_Usage":"",
            "Liters":0,
            "Cost_per_Liter":0,
            "Fuel_Cost":0,
            "Full_Tank":"",
            "Odometer":0,
            "FASTag_Trips":0,
            "State_Toll":0,
            "Private_Toll":0,
            "Service_Cost":cost,
            "Service_Description":desc,
            "Timestamp_Created":datetime.now(),
            "Timestamp_Edited":""
        }
        df = pd.concat([df,pd.DataFrame([new_row])],ignore_index=True)
        save_data(df)
        st.success("Service entry saved.")

# ===================================
# TAB 3 — DASHBOARD
# ===================================
with tab3:
    st.header("Dashboard & Analytics")

    if df.empty:
        st.warning("No data available.")
    else:
        distance, avg = calculate_distance_and_avg(df)
        cpk = lifetime_cpk(df)
        fuel_left = fuel_remaining(df)

        col1,col2,col3 = st.columns(3)
        col1.metric("Total Distance (KM)", distance)
        col2.metric("Average Economy (KM/L)", avg)
        col3.metric("Lifetime CPK (₹/KM)", cpk)

        st.subheader("Fuel Gauge")
        st.progress(min(fuel_left/TANK_CAPACITY,1.0))

        st.subheader("Database Records")
        st.dataframe(df.sort_values("Date",ascending=False), use_container_width=True)

        st.subheader("Date Range Report")
        start = st.date_input("Start Date", key="start")
        end = st.date_input("End Date", key="end")

        if start <= end:
            mask = (df["Date"]>=pd.to_datetime(start)) & (df["Date"]<=pd.to_datetime(end))
            report = df[mask]

            st.dataframe(report)

            total_cost = (
                report["Fuel_Cost"].sum() +
                report["Service_Cost"].sum() +
                report["State_Toll"].sum() +
                report["Private_Toll"].sum() +
                report["FASTag_Trips"].sum()*FASTAG_COST_PER_TRIP
            )

            st.metric("Total Cost (Selected Period)", round(total_cost,2))

# ===================================
# TAB 4 — DATABASE MANAGEMENT
# ===================================
with tab4:
    st.header("Database Management")

    uploaded = st.file_uploader("Replace Database with CSV", type=["csv"])
    if uploaded:
        new_df = pd.read_csv(uploaded)
        save_data(new_df)
        st.success("Database replaced successfully.")
        st.experimental_rerun()

    st.download_button(
        "Download Full Database Backup",
        df.to_csv(index=False),
        file_name="amaze_tech_log_backup.csv"
    )
