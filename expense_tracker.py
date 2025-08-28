# Expense Tracker App with Budget Limit & Login System (Streamlit + SQLite)
# Author: Hamsika

import streamlit as st
import sqlite3
import pandas as pd
import hashlib

# ------------------ DATABASE SETUP ------------------
conn = sqlite3.connect('expenses.db')
c = conn.cursor()

# Users table for login system
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT)''')

# Expenses table
c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                category TEXT,
                note TEXT,
                date TEXT)''')

# Budget table
c.execute('''CREATE TABLE IF NOT EXISTS budget (
                user_id INTEGER UNIQUE,
                budget_limit REAL)''')

conn.commit()

# ------------------ HELPERS ------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------ SESSION STATE ------------------
if "user" not in st.session_state:
    st.session_state["user"] = None

# ------------------ LOGIN & REGISTER ------------------
st.set_page_config(page_title="Expense Tracker", page_icon="💰", layout="centered")

if st.session_state["user"] is None:
    st.title("🔐 Login or Register")
    option = st.radio("Select Option", ["Login", "Register"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Register":
        if st.button("Register"):
            try:
                hashed_pw = hash_password(password)
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
                conn.commit()
                st.success("✅ Registered successfully! Please login.")
            except:
                st.error("⚠️ Username already exists.")

    elif option == "Login":
        if st.button("Login"):
            hashed_pw = hash_password(password)
            c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, hashed_pw))
            user = c.fetchone()
            if user:
                st.session_state["user"] = user[0]
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

# ------------------ MAIN APP ------------------
else:
    st.title("💰 Expense Tracker")
    menu = ["Add Expense", "View Expenses", "Analytics", "Set Budget", "Logout"]
    choice = st.sidebar.selectbox("Menu", menu)

    user_id = st.session_state["user"]

    # ADD EXPENSE
    if choice == "Add Expense":
        st.subheader("➕ Add a New Expense")
        amount = st.number_input("Enter Amount (₹)", min_value=0.0, step=1.0, format="%.2f")
        category = st.selectbox("Category", ["Food", "Travel", "Shopping", "Bills", "Other"])
        note = st.text_area("Note")
        date = st.date_input("Date")

        if st.button("Save Expense"):
            c.execute('INSERT INTO expenses (user_id, amount, category, note, date) VALUES (?, ?, ?, ?, ?)',
                      (user_id, amount, category, note, str(date)))
            conn.commit()
            st.success("✅ Expense added successfully!")

    # VIEW EXPENSES
    elif choice == "View Expenses":
        st.subheader("📋 All Expenses")
        df = pd.read_sql(f"SELECT * FROM expenses WHERE user_id={user_id}", conn)

        if df.empty:
            st.warning("No expenses recorded yet.")
        else:
            st.dataframe(df)
            st.write("### 💵 Total Spent: ₹", round(df["amount"].sum(), 2))

            delete_id = st.number_input("Enter Expense ID to Delete", min_value=0, step=1)
            if st.button("Delete Expense"):
                c.execute("DELETE FROM expenses WHERE id=? AND user_id=?", (delete_id, user_id))
                conn.commit()
                st.success(f"🗑 Expense ID {delete_id} deleted!")

    # ANALYTICS
    elif choice == "Analytics":
        st.subheader("📊 Expense Analytics")
        df = pd.read_sql(f"SELECT * FROM expenses WHERE user_id={user_id}", conn)

        if df.empty:
            st.warning("No data for analytics.")
        else:
            # Total by category
            cat_summary = df.groupby("category")["amount"].sum().reset_index()
            st.bar_chart(cat_summary.set_index("category"))

            # Monthly summary
            df["date"] = pd.to_datetime(df["date"])
            monthly_summary = df.groupby(df["date"].dt.to_period("M"))["amount"].sum()
            st.line_chart(monthly_summary)

            # Budget check
            c.execute("SELECT budget_limit FROM budget WHERE user_id=?", (user_id,))
            row = c.fetchone()
            if row:
                budget_limit = row[0]
                monthly_total = df[df["date"].dt.to_period("M") == pd.Timestamp.today().to_period("M")]["amount"].sum()
                if monthly_total > budget_limit:
                    st.error(f"⚠️ Budget exceeded! Limit: ₹{budget_limit}, Spent: ₹{monthly_total}")
                else:
                    st.success(f"✅ Within Budget. Limit: ₹{budget_limit}, Spent: ₹{monthly_total}")

    # SET BUDGET
    elif choice == "Set Budget":
        st.subheader("💡 Set Monthly Budget")
        new_budget = st.number_input("Enter Budget Limit (₹)", min_value=0.0, format="%0.2f")
        if st.button("Save Budget"):
            c.execute("INSERT OR REPLACE INTO budget (user_id, budget_limit) VALUES (?, ?)", (user_id, new_budget))
            conn.commit()
            st.success("✅ Budget set successfully!")

    # LOGOUT
    elif choice == "Logout":
        st.session_state["user"] = None
        st.rerun()

# ------------------ FOOTER ------------------
st.markdown("---")
st.caption("Built in Python using Streamlit + SQLite | By Hamsika")