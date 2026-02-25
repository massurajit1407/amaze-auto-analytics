import streamlit as st
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Amaze Analytics Engine", layout="wide")

FILE_NAME = "amaze_tech_log.csv"
TANK_CAPACITY = 35

# -------------------------------------------------
# INITIALIZE CSV
# -------------------------------------------------
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
        "Entry_Type",
        "Description",
        "Amount",
        "Timestamp_Created"
    ])
    df_init.to_csv(FILE_NAME, index=False)

df = pd.read_csv(FILE_NAME)

# Convert date column properly
if not df.empty:
    # Safe Date Conversion
if "Date" in df.columns:
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.title("🚗 Amaze Analytics Engine v2.0")
menu = st.sidebar.radio("Select Module", [
    "Fuel Log",
    "Transit",
    "Maintenance",
    "Dashboard",
    "Reports"
])

# =====================================================
# FUEL LOG
# =====================================================
if menu == "Fuel Log":

    st.header("⛽ Fuel Entry")

    with st.form("fuel_form"):

        date = st.date_input("Date")
        drive_profile = st.selectbox("Drive Profile", ["City", "Highway"])
        ac_usage = st.selectbox("AC Usage", ["Mostly AC", "Mixed", "No AC"])
        liters = st.number_input("Liters Added", min_value=0.01, format="%.2f")
        cost_per_liter = st.number_input("Cost per Liter (₹)", min_value=0.01, format="%.2f")
        full_tank = st.selectbox("Full Tank (Autocut)?", ["No", "Yes"])
        odometer = st.number_input("Odometer Reading", min_value=0, step=1)

        submit = st.form_submit_button("Save")

        if submit:

            if not df[df["Entry_Type"] == "Fuel"].empty:
                last_odometer = df[df["Entry_Type"] == "Fuel"]["Odometer"].max()
                if odometer <= last_odometer:
                    st.error(f"Odometer must be greater than last entry ({last_odometer} km)")
                    st.stop()

            entry_id = len(df) + 1

            new_row = {
                "Entry_ID": entry_id,
                "Date": date,
                "Drive_Profile": drive_profile,
                "AC_Usage": ac_usage,
                "Liters": liters,
                "Cost_per_Liter": cost_per_liter,
                "Full_Tank": full_tank,
                "Odometer": odometer,
                "Entry_Type": "Fuel",
                "Description": "",
                "Amount": liters * cost_per_liter,
                "Timestamp_Created": datetime.now()
            }

            df = pd.concat([df, pd.DataFrame([new_row])])
            df.to_csv(FILE_NAME, index=False)
            st.success("Fuel Entry Saved Successfully!")

# =====================================================
# TRANSIT
# =====================================================
elif menu == "Transit":

    st.header("🛣 Transit Entry")

    with st.form("transit_form"):

        date = st.date_input("Date")
        state_toll = st.number_input("State Toll (₹)", min_value=0.0, format="%.2f")
        private_toll = st.number_input("Private Toll (₹)", min_value=0.0, format="%.2f")

        submit = st.form_submit_button("Save")

        if submit:

            entry_id = len(df) + 1
            total = state_toll + private_toll

            new_row = {
                "Entry_ID": entry_id,
                "Date": date,
                "Drive_Profile": "",
                "AC_Usage": "",
                "Liters": 0,
                "Cost_per_Liter": 0,
                "Full_Tank": "",
                "Odometer": "",
                "Entry_Type": "Transit",
                "Description": "Toll",
                "Amount": total,
                "Timestamp_Created": datetime.now()
            }

            df = pd.concat([df, pd.DataFrame([new_row])])
            df.to_csv(FILE_NAME, index=False)
            st.success("Transit Saved!")

# =====================================================
# MAINTENANCE
# =====================================================
elif menu == "Maintenance":

    st.header("🔧 Maintenance Entry")

    with st.form("maint_form"):

        date = st.date_input("Date")
        desc = st.text_input("Service Description")
        amount = st.number_input("Cost (₹)", min_value=0.01, format="%.2f")

        submit = st.form_submit_button("Save")

        if submit:

            entry_id = len(df) + 1

            new_row = {
                "Entry_ID": entry_id,
                "Date": date,
                "Drive_Profile": "",
                "AC_Usage": "",
                "Liters": 0,
                "Cost_per_Liter": 0,
                "Full_Tank": "",
                "Odometer": "",
                "Entry_Type": "Maintenance",
                "Description": desc,
                "Amount": amount,
                "Timestamp_Created": datetime.now()
            }

            df = pd.concat([df, pd.DataFrame([new_row])])
            df.to_csv(FILE_NAME, index=False)
            st.success("Maintenance Saved!")

# =====================================================
# DASHBOARD
# =====================================================
elif menu == "Dashboard":

    st.header("📊 All Entries")

    if not df.empty:
        df_display = df.sort_values(["Date", "Timestamp_Created"])
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No data available.")

# =====================================================
# REPORTS
# =====================================================
elif menu == "Reports":

    st.header("📈 Report Generator")

    if df.empty:
        st.info("No data available.")
    else:

        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")

        mask = (df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))
        period_df = df.loc[mask]

        fuel_df = period_df[period_df["Entry_Type"] == "Fuel"].sort_values("Odometer")

        if len(fuel_df) > 1:
            distance = fuel_df["Odometer"].iloc[-1] - fuel_df["Odometer"].iloc[0]
            total_liters = fuel_df["Liters"].sum()
            mileage = distance / total_liters if total_liters > 0 else 0

            fuel_cost = fuel_df["Amount"].sum()
            total_cost = period_df["Amount"].sum()

            fuel_cpk = fuel_cost / distance if distance > 0 else 0
            overall_cpk = total_cost / distance if distance > 0 else 0

            st.metric("Total Distance (KM)", round(distance,2))
            st.metric("Fuel Consumed (L)", round(total_liters,2))
            st.metric("Overall Mileage (KM/L)", round(mileage,2))
            st.metric("Fuel CPK (₹/KM)", round(fuel_cpk,2))
            st.metric("Overall CPK (₹/KM)", round(overall_cpk,2))

            # Trend graph
            fuel_df["Distance"] = fuel_df["Odometer"].diff()
            fuel_df["Mileage"] = fuel_df["Distance"] / fuel_df["Liters"]

            fig, ax = plt.subplots()
            ax.plot(fuel_df["Mileage"])
            ax.set_ylabel("KM/L")
            ax.set_title("Mileage Trend")
            st.pyplot(fig)

        else:
            st.warning("Not enough fuel entries in selected period.")
