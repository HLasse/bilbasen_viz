"""Streamlit app to compare the total cost of ownership of multiple cars"""

# Import libraries
import json

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
with st.sidebar:
    with st.expander("ℹ️ About the app", expanded=False):
        st.write(
            "This app lets you estimate the total cost of ownership of "
            + "a car over time. Input the price of the car, yearly cost of ownership, "
            + "and estimated km per liter of gasoline and press 'Add car' "
            + "to add a car to the comparison. You can add as many cars as you want. "
            + "Shared values for estimated kms driven per year and price of gasoline "
            + "can be set in the 'Shared parameters' section and will be used for all cars."
            + " Hover over the graph to see a head-by-head comparison of the cars."
        )

# set global inputs
st.subheader("Shared parameters")
col1, col2 = st.columns([1, 1])
with col1:
    km_per_year = st.number_input("Estimated kilometers driven per year", value=10000)
with col2:
    gas_price = st.number_input("Price of gasoline", value=14.0)

update_global_values = st.button("Update shared parameters", use_container_width=True)

# create form to add a car
with st.form(key="add_car_form"):
    with st.sidebar:
        # Set sidebar inputs
        name_of_car = st.sidebar.text_input("Name of car", value="Tesla Model 3")
        price = st.sidebar.number_input("Price of car", value=50_000)
        yearly_cost = st.sidebar.number_input(
            "Yearly cost of ownership",
            value=3000,
        )
        # km per liter of gasoline
        km_per_liter = st.sidebar.number_input(
            "Estimated kilometers per liter of gasoline", value=15.0
        )

        # add submit button that saves the sidebar inputs to a pandas dataframe
        submitted = st.form_submit_button("Add car", use_container_width=True)

# create button to download session state dict as json
if st.session_state["cars"] != {}:
    json_string = json.dumps(st.session_state["cars"])
    st.sidebar.download_button(
        label="Download car data",
        data=json_string,
        file_name="car_cost_calculator.json",
        mime="application/json",
    )
# create button to import session state dict from json
uploaded_file = st.sidebar.file_uploader(
    "Import car data", type=["json"], key="import_data"
)

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        st.session_state["cars"].update(data)
        st.write("Successfully imported data")
    except Exception as e:
        st.sidebar.error(f"Invalid file: {e}")

# create form to remove a car
if st.session_state["cars"] != {}:
    # add toggle to remove cars from the dataframe
    remove_car = st.sidebar.selectbox(
        "Remove car",
        options=list(st.session_state["cars"].keys()) + [""],
        index=len(st.session_state["cars"]),
    )
    with st.form(key="remove_car_form"):
        with st.sidebar:
            remove_car_form = st.form_submit_button(
                "Remove car", use_container_width=True
            )

            if remove_car_form and remove_car != "":
                st.session_state["cars"].pop(remove_car)

# if a car has been submitted, add it to the dataframe
# if the update button has been pressed, update the global values
if submitted or update_global_values:
    # add the parameters from the sidebar to a stateful dictionary
    if submitted:
        st.session_state["cars"][name_of_car] = {
            "Price": price,
            "Yearly cost": yearly_cost,
            "Km per liter": km_per_liter,
        }

    meta_df = pd.DataFrame(st.session_state["cars"]).T
    meta_df.index.name = "Car model"
    # Calculate total cost of ownership without the price of the car
    meta_df["Gas/month"] = km_per_year / meta_df["Km per liter"] * gas_price / 12
    meta_df["Operational cost/month"] = (
        meta_df["Yearly cost"] / 12
        + km_per_year / meta_df["Km per liter"] * gas_price / 12
    )
    meta_df["Operational cost/year"] = (
        meta_df["Yearly cost"] + km_per_year / meta_df["Km per liter"] * gas_price
    )

    # print car comparison dataframe
    st.subheader("Car comparison")
    st.text("Operational cost = Yearly cost + gas")
    st.dataframe(
        meta_df.sort_values(by="Operational cost/year").round(
            {
                "Km per liter": 1,
                "Price": 0,
                "Yearly cost": 0,
                "Gas/month": 0,
                "Operational cost/month": 0,
                "Operational cost/year": 0,
            }
        )
    )

    # prepare data for plotting price over time
    dates = pd.date_range(start=pd.Timestamp.today(), periods=120, freq="M")

    # Calculate the total cost of ownership per month by car over 10 years
    operational_costs = {}
    for car, cost in meta_df["Operational cost/month"].items():
        total_cost_by_month = cost * np.arange(1, 121) + meta_df["Price"][car]
        operational_costs[car] = total_cost_by_month
    # create dataframe
    df = pd.DataFrame(operational_costs, index=dates)

    # convert dataframe from wide to long format
    df_long = df.reset_index().melt(id_vars="index", var_name="Car", value_name="Cumulative cost")
    df_long = df_long.rename(columns={"index": "Date"}).round(0)

    base = (
        alt.Chart(df_long).encode(x=alt.X('Date:T', axis=alt.Axis(title='Date')))
    ).properties(width=800, height=500)
    columns = sorted(df_long["Car"].unique())
    selection = alt.selection_single(
        fields=['Date'], nearest=True, on='mouseover', empty='none', clear='mouseout'
    )
    lines = base.mark_line().encode(
        y=alt.Y('Cumulative cost:Q', axis=alt.Axis(title='Cumulative cost')),
        color=alt.Color('Car:N', legend=alt.Legend(title='Car model')),
    )
    points = lines.mark_point().transform_filter(selection)

    rule = base.transform_pivot(
        'Car', value='Cumulative cost', groupby=['Date']
    ).mark_rule().encode(
        opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
        tooltip=["Date"] + [alt.Tooltip(c, type='quantitative', format=",") for c in columns]
    ).add_selection(selection)

    lines + points + rule


    # add larger line for tooltip
    # tt = chart.mark_line(strokeWidth=30, opacity=0.01)
    # chart + tt
    # # change x and y axis labels
    # chart.encoding.x.title = "Date"
    # chart.encoding.y.title = "Cumulative cost"
    #st.altair_chart(base)
    #st.altair_chart(base)
    #st.altair_chart(base)
    #st.altair_chart(base)
