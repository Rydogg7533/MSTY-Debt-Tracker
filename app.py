import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="MSTY Tool", layout="wide")

tab = st.sidebar.radio("Select Tool", ["Compounding Simulator", "Cost Basis Tools", "Return on Debt"])

if tab == "Compounding Simulator":
    st.title("Compounding Simulator")
    shares = st.number_input("Initial Share Count", min_value=0, value=10000)
    cost_basis = st.number_input("Initial Purchase Cost Basis ($)", min_value=0.0, value=25.0)
    holding_period = st.slider("Holding Period (Months)", 1, 120, 24)
    dividend = st.number_input("Average Monthly Dividend per Share ($)", value=2.0)
    reinvest_price = st.number_input("Average Reinvestment Cost Per Share ($)", value=25.0)
    account_type = st.selectbox("Account Type", ["Taxable", "Tax Deferred", "Non-Taxable"])
    defer_taxes = st.checkbox("Defer Taxes to Oct 15")
    fed_tax = st.number_input("Federal Tax Rate (%)", 0, 50, 20)
    state_tax = st.number_input("State Tax Rate (%)", 0, 15, 5)
    withdraw = st.number_input("Withdraw this Dollar Amount Monthly ($)", min_value=0, value=0)
    reinvest = withdraw == 0
    frequency = st.selectbox("View Output:", ["Monthly", "Yearly", "Total"])

    if st.button("Run Simulation"):
        data = []
        now = datetime.datetime.now()
        shares_owned = shares
        cum_taxes = 0
        cum_reinvested = 0
        cum_divs = 0
        tax_due = 0
        deferred = []

        for m in range(holding_period):
            date = now + pd.DateOffset(months=m)
            gross_div = shares_owned * dividend
            tax = 0 if account_type != "Taxable" else gross_div * (fed_tax + state_tax) / 100
            if defer_taxes and date.month != 10:
                deferred.append(tax)
                tax = 0
            elif defer_taxes and date.month == 10:
                tax = sum(deferred)
                deferred = []

            net_div = gross_div - tax
            reinvest_amt = 0 if not reinvest else max(0, net_div - withdraw)
            new_shares = reinvest_amt / reinvest_price
            shares_owned += new_shares

            cum_divs += net_div
            cum_taxes += tax
            cum_reinvested += reinvest_amt

            data.append({
                "Date": date.date(),
                "Shares": round(shares_owned, 2),
                "New Shares": round(new_shares, 2),
                "Net Dividends": round(net_div, 2),
                "Reinvested": round(reinvest_amt, 2),
                "Taxes Paid": round(tax, 2),
                "Total Taxes Owed": round(cum_taxes, 2)
            })

        df = pd.DataFrame(data)
        if frequency == "Monthly":
            st.dataframe(df)
        elif frequency == "Yearly":
            df["Year"] = df["Date"].apply(lambda x: x.year)
            st.dataframe(df.groupby("Year").agg({
                "Shares": "last",
                "Net Dividends": "sum",
                "Reinvested": "sum",
                "Taxes Paid": "sum",
                "Total Taxes Owed": "last"
            }).reset_index())
        else:
            st.dataframe(pd.DataFrame([{
                "Shares": df["Shares"].iloc[-1],
                "Total Dividends": df["Net Dividends"].sum(),
                "Total Reinvested": df["Reinvested"].sum(),
                "Total Taxes Paid": df["Taxes Paid"].sum(),
                "Total Taxes Owed": df["Total Taxes Owed"].iloc[-1]
            }]))

elif tab == "Cost Basis Tools":
    st.title("Cost Basis Calculator")
    if "entries" not in st.session_state:
        st.session_state.entries = []

    num_shares = st.number_input("Number of Shares", min_value=0, value=0, key="shares")
    price_per_share = st.number_input("Price per Share ($)", min_value=0.0, value=25.0, key="price")

    if st.button("Add Entry"):
        st.session_state.entries.append((num_shares, price_per_share))

    if st.session_state.entries:
        df = pd.DataFrame(st.session_state.entries, columns=["Shares", "Price"])
        df["Total"] = df["Shares"] * df["Price"]
        total_shares = df["Shares"].sum()
        total_cost = df["Total"].sum()
        avg_cost = total_cost / total_shares if total_shares else 0
        st.dataframe(df)
        st.success(f"Weighted Average Cost Basis: ${avg_cost:.2f}")

elif tab == "Return on Debt":
    st.title("Return on Debt")
    debt_amount = st.number_input("Total Debt Incurred ($)", value=100000.0)
    monthly_payment = st.number_input("Monthly Debt Payment ($)", value=2500.0)
    cost_basis = st.number_input("Cost Basis per Share ($)", value=25.0)
    loan_months = st.slider("Loan Duration (Months)", 1, 120, 48)
    compounding_months = st.slider("Compounding Duration (Months)", 1, 120, 48)
    reinvest_price = st.number_input("Average Reinvestment Share Price ($)", value=25.0)
    monthly_dividend = st.number_input("Average Monthly Dividend per Share ($)", value=2.0)
    interest_rate = st.number_input("Annual Interest Rate (%)", value=10.0)
    future_price = st.number_input("Projected Share Price After Loan Period ($)", value=40.0)

    if st.button("Calculate Return"):
        initial_shares = debt_amount / cost_basis
        shares = initial_shares

        for month in range(1, compounding_months + 1):
            monthly_divs = shares * monthly_dividend
            debt_remaining = max(0, loan_months - month)
            payment = monthly_payment if debt_remaining > 0 else 0
            reinvestment = max(0, monthly_divs - payment)
            new_shares = reinvestment / reinvest_price
            shares += new_shares

        total_interest = (monthly_payment * loan_months) - debt_amount
        portfolio_value = shares * future_price
        monthly_divs_post_loan = shares * monthly_dividend
        net_value = portfolio_value - debt_amount - total_interest

        st.subheader("Summary:")
        st.write(f"Initial Shares Purchased: {initial_shares:,.2f}")
        st.write(f"Final Share Count: {shares:,.2f}")
        st.write(f"Total Interest Paid: ${total_interest:,.2f}")
        st.write(f"Portfolio Value After Loan: ${portfolio_value:,.2f}")
        st.write(f"Monthly Dividends After Loan: ${monthly_divs_post_loan:,.2f}")
        st.write(f"Net Portfolio Value After Debt: ${net_value:,.2f}")
