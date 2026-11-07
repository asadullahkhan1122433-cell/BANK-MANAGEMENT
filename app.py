import streamlit as st
import pandas as pd
from bank import Bank

st.set_page_config(page_title="ABC Bank", page_icon="🏦", layout="wide")

@st.cache_resource
def get_bank():
    return Bank()

try:
    bank = get_bank()
except RuntimeError as error:
    st.error(str(error))
    st.stop()

st.title("🏦 ABC Bank Limited")
st.caption("A learning project built with Python, OOP, JSON and Streamlit.")
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choose an option",
    ["Home", "Create account", "Deposit", "Withdraw", "Account details",
     "Update account", "Delete account"]
)

def show_error(action):
    try:
        action()
    except ValueError as error:
        st.error(str(error))
    except OSError as error:
        st.error(f"Could not save your data: {error}")

if page == "Home":
    st.subheader("Welcome to ABC Bank")
    col1, col2 = st.columns(2)
    col1.metric("Total accounts", len(bank.data))
    col2.metric("Total deposits held", f"Rs. {sum(a['balance'] for a in bank.data):,.2f}")
    st.info("Choose an operation from the navigation menu on the left.")
    st.warning(
        "Educational demonstration only. JSON storage and this login approach "
        "are not suitable for real banking or real customer information."
    )

elif page == "Create account":
    st.subheader("Create a new account")
    with st.form("create_account_form"):
        name = st.text_input("Full name")
        age = st.number_input("Age", min_value=1, max_value=120, value=18)
        email = st.text_input("Email address")
        pin = st.text_input("Choose a 4-digit PIN", type="password", max_chars=4)
        submitted = st.form_submit_button("Create account")
    if submitted:
        def create():
            number = bank.create_account(name, int(age), email, pin)
            st.success("Account created successfully!")
            st.code(number)
            st.write("Save your account number. It will be needed for future operations.")
        show_error(create)

elif page in ("Deposit", "Withdraw", "Account details", "Update account", "Delete account"):
    st.subheader(page)
    with st.form(f"{page}_form"):
        account_number = st.text_input("Account number")
        pin = st.text_input("4-digit PIN", type="password", max_chars=4)

        amount = None
        name = age = email = new_pin = None
        if page in ("Deposit", "Withdraw"):
            amount = st.number_input("Amount (Rs.)", min_value=0.0, step=100.0)
        elif page == "Update account":
            st.caption("Leave fields unchanged if you do not want to update them.")
            name = st.text_input("New name (optional)")
            age_enabled = st.checkbox("Update age")
            age = st.number_input("New age", min_value=18, max_value=120, value=18) if age_enabled else None
            email = st.text_input("New email (optional)")
            new_pin = st.text_input("New 4-digit PIN (optional)", type="password", max_chars=4)
        elif page == "Delete account":
            st.warning("You can delete an account only when its balance is zero.")
            confirm = st.checkbox("I understand and want to delete this account.")
        submitted = st.form_submit_button(page)

    if submitted:
        def operation():
            if page == "Deposit":
                balance = bank.deposit(account_number, pin, amount)
                st.success(f"Deposit successful. New balance: Rs. {balance:,.2f}")
            elif page == "Withdraw":
                balance = bank.withdraw(account_number, pin, amount)
                st.success(f"Withdrawal successful. New balance: Rs. {balance:,.2f}")
            elif page == "Account details":
                details = bank.get_account_details(account_number, pin)
                st.success("Account verified.")
                st.write("### Account information")
                st.write({k: v for k, v in details.items() if k != "transactions"})
                st.write("### Transaction history")
                transactions = details.get("transactions", [])
                if transactions:
                    st.dataframe(pd.DataFrame(transactions), use_container_width=True)
            elif page == "Update account":
                bank.update_account(
                    account_number, pin,
                    name=name or None, age=age, email=email or None,
                    new_pin=new_pin or None
                )
                st.success("Account details updated.")
            elif page == "Delete account":
                if not confirm:
                    st.error("Please confirm before deleting.")
                    return
                bank.delete_account(account_number, pin)
                st.success("Account deleted successfully.")
        show_error(operation)

st.divider()
st.caption("ABC Bank learning project • Do not enter real financial or personal information.")
