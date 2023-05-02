"""Streamlit app to compare the total cost of ownership of multiple cars"""

# Import libraries
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# Set page title
st.set_page_config(page_title="Car Cost Calculator", page_icon="🚗")

# initialize session state
if "cars" not in st.session_state:
    st.session_state["cars"] = {}

# Make input fields in sidebar
st.sidebar.title("Car Cost Calculator")
st.sidebar.markdown("This app lets you calculate the total cost of ownership of a car over time.")

# set global inputs
col1, col2 = st.columns([1,1])
with col1:
    km_per_year = st.number_input("Estimated kilometers driven per year", min_value=1000, max_value=50000, value=10000)
with col2:
    gas_price = st.number_input("Price of gasoline", min_value=None, max_value=None, value=14.0)

update_global_values = st.button("Update global values", use_container_width=True)

with st.form(key="add_car_form"):
    with st.sidebar:
        # Set sidebar inputs
        name_of_car = st.sidebar.text_input("Name of car", value="Tesla Model 3")
        price = st.sidebar.number_input("Price of car", value=50_000)
        yearly_cost = st.sidebar.number_input("Yearly cost of ownership", value=3000, )
        # km per liter of gasoline
        km_per_liter = st.sidebar.number_input("Estimated kilometers per liter of gasoline", value=15.0)

        # add submit button that saves the sidebar inputs to a pandas dataframe
        submitted = st.form_submit_button("Add car", use_container_width=True)

if st.session_state["cars"] != {}:
    # add toggle to remove cars from the dataframe
    remove_car = st.sidebar.selectbox("Remove car", options=list(st.session_state["cars"].keys()) + [""], index=len(st.session_state["cars"]) )
    with st.form(key="remove_car_form"):
        with st.sidebar:
            remove_car_form = st.form_submit_button("Remove car", use_container_width=True)

            if remove_car_form and remove_car != "":
                st.session_state["cars"].pop(remove_car)


if submitted or update_global_values:
    # add the parameters from the sidebar to a dictionary
    st.session_state["cars"][name_of_car] = {
        "Price": price,
        "Yearly cost": yearly_cost,
        "Km per liter": km_per_liter,
    }

    meta_df = pd.DataFrame(st.session_state["cars"]).T
    meta_df.index.name = "Car model"


    # # Calculate total cost of ownership per month without the price of the car
    operational_cost_per_month = meta_df["Yearly cost"] / 12 + km_per_year / meta_df["Km per liter"] * gas_price / 12
    operational_cost_per_month.name = "Operational costs per month"
    operational_cost_per_month.index.name = "Car model"
    
    col1, col2 = st.columns([1,1])
    with col1:
        st.write("Current comparisons")
        st.write(meta_df)
    with col2:
        st.write("Operational costs per month")
        st.write(operational_cost_per_month.round(0))
    # Calculate 10 years ahead in the future from todays date
    dates = pd.date_range(start=pd.Timestamp.today(), periods=120, freq="M")

    # Calculate the total cost of ownership per month by car 
    operational_costs = {}
    for car, cost in operational_cost_per_month.items():
        total_cost_per_month = cost * np.arange(1,121) + meta_df["Price"][car]
        operational_costs[car] = total_cost_per_month
    # create dataframe
    df = pd.DataFrame(operational_costs, index=dates)

    # plot a line for each car
    chart = alt.Chart(df.reset_index()).transform_fold(
        list(df.columns),
        as_=["Car", "Operational costs per month"]
    ).mark_line().encode(
        x="index:T",
        y="Operational costs per month:Q",
        color="Car:N"
    ).properties(
        width=800,
        height=500
    )
    st.altair_chart(chart)

