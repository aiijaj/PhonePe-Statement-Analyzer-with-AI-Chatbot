import streamlit as st
import pandas as pd
import pikepdf
import pdfplumber
import os
import tempfile
import re
import sqlite3
from datetime import datetime

import plotly.express as px
from transformers import pipeline

# ---------------------------
# SQLite DB Setup
# ---------------------------

DB_FILE = "phonepe_finance.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS name_category_map (
            name TEXT PRIMARY KEY,
            category TEXT
        )
    ''')
    conn.commit()
    conn.close()

def load_name_category_map():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT name, category FROM name_category_map')
    rows = c.fetchall()
    conn.close()
    return {name: category for name, category in rows}

def save_name_category_map(name_category_dict):
    conn = get_db_connection()
    c = conn.cursor()
    for name, category in name_category_dict.items():
        c.execute('''
            INSERT INTO name_category_map (name, category) 
            VALUES (?, ?) 
            ON CONFLICT(name) DO UPDATE SET category=excluded.category
        ''', (name, category))
    conn.commit()
    conn.close()

# ---------------------------
# PDF Utility
# ---------------------------
def remove_pdf_password(input_path, output_path, password):
    try:
        with pikepdf.open(input_path, password=password) as pdf:
            pdf.save(output_path)
        return output_path
    except Exception:
        st.error("❌ Failed to remove PDF password. Try again.")
        return None

# ---------------------------
# PhonePe Parser
# ---------------------------
def parse_phonepe_pdf(pdf_path):
    transactions = []

    def is_transaction_line(line):
        return re.match(r'^[A-Za-z]{3} \d{2}, \d{4} .* (Debit|Credit) INR \d', line)

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split("\n")
            for line in lines:
                if is_transaction_line(line):
                    transactions.append(line)

    parsed_rows = []
    for line in transactions:
        try:
            # Extract date
            date_match = re.search(r'^([A-Za-z]{3} \d{2}, \d{4})', line)
            date_str = date_match.group(1)
            date = datetime.strptime(date_str, "%b %d, %Y").date()

            # Extract name
            if "Paid to" in line:
                name = line.split("Paid to")[1].split("Debit")[0].strip()
            elif "Received from" in line:
                name = line.split("Received from")[1].split("Credit")[0].strip()
            else:
                name = "Unknown"

            # Extract type
            txn_type = "Debit" if "Debit" in line else "Credit"

            # Extract amount
            amount_match = re.search(r'INR ([\d,]+\.\d{2})', line)
            amount = float(amount_match.group(1).replace(",", "")) if amount_match else 0.0

            parsed_rows.append({
                "Date": date,
                "Name": name,
                "Debit/Credit": txn_type,
                "Amount": amount
            })

        except Exception as e:
            print("Error parsing line:", line)
            continue

    return pd.DataFrame(parsed_rows)

# ---------------------------
# Category Defaults
# ---------------------------
default_keywords = {
    'Food': ['zomato', 'swiggy', 'restaurant', 'pizza'],
    'Groceries': ['d-mart', 'big bazaar', 'grocery'],
    'Recharge/Bill': ['recharge', 'electricity', 'mobile', 'water'],
    'Shopping': ['amazon', 'flipkart', 'myntra'],
    'Entertainment': ['netflix', 'hotstar', 'spotify'],
    'Transport': ['uber', 'ola', 'fuel', 'metro'],
    'Education': ['institute', 'college', 'fees'],
    'Health': ['pharmacy', 'hospital', 'clinic'],
    'Other': []
}

# ---------------------------
# Categorization
# ---------------------------
def categorize_transactions(df, keyword_dict, name_map):
    categories = []
    for name in df["Name"]:
        name_lower = name.lower().strip()
        if name_lower in name_map:
            categories.append(name_map[name_lower])
            continue

        matched = False
        for category, keywords in keyword_dict.items():
            if any(keyword.lower() in name_lower for keyword in keywords):
                categories.append(category)
                matched = True
                break
        if not matched:
            categories.append("Other")
    df["Category"] = categories
    return df

# ---------------------------
# Hugging Face Chatbot Functions
# ---------------------------

@st.cache_resource
def load_hf_pipelines():
    qa = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
    return qa

def answer_nlp_question(df, question):
    # Rule-based for common finance questions
    question_lower = question.lower()
    if ("total" in question_lower or "how much" in question_lower) and "spend" in question_lower:
        for cat in df["Category"].unique():
            if cat.lower() in question_lower:
                total = df[df["Category"] == cat]["Amount"].sum()
                return f"Total spent on {cat}: INR {total:.2f}"
        # Try for all expenses
        if "total" in question_lower and ("expense" in question_lower or "spend" in question_lower):
            total = df["Amount"].sum()
            return f"Total spent: INR {total:.2f}"
    # Fallback to QA model
    context = ""
    for _, row in df.iterrows():
        context += f"On {row['Date']}, paid {row['Amount']} INR to {row['Name']} in category {row['Category']}.\n"
    if len(context) > 1800:
        context = context[:1800]
    qa = load_hf_pipelines()
    result = qa(question=question, context=context)
    return result['answer']

# ---------------------------
# Main Streamlit App
# ---------------------------
def main():
    st.set_page_config(page_title="📄 PhonePe Finance Analyzer", layout="wide")
    st.title("📊 PhonePe Statement Analyzer with AI Chatbot")

    # Initialize DB (if first run)
    init_db()

    uploaded_file = st.file_uploader("Upload PhonePe Statement (PDF or CSV)", type=["pdf", "csv"])

    if uploaded_file:
        # Load category learning map from DB
        if "name_to_category" not in st.session_state:
            st.session_state.name_to_category = load_name_category_map()

        if "keyword_dict" not in st.session_state:
            st.session_state.keyword_dict = default_keywords.copy()

        file_ext = uploaded_file.name.split(".")[-1].lower()
        df = None

        if file_ext == "pdf":
            password = st.text_input("Enter PDF Password (if any)", type="password")
            if password or st.button("Load PDF without password"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_input:
                    temp_input.write(uploaded_file.read())
                    temp_input_path = temp_input.name

                temp_output_path = temp_input_path.replace(".pdf", "_unlocked.pdf")
                if password:
                    unlocked_path = remove_pdf_password(temp_input_path, temp_output_path, password)
                    if unlocked_path:
                        df = parse_phonepe_pdf(unlocked_path)
                else:
                    df = parse_phonepe_pdf(temp_input_path)

        elif file_ext == "csv":
            df = pd.read_csv(uploaded_file)
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"])

        if df is not None and not df.empty:
            st.success("✅ Transactions Loaded")
            debits_df = df[df["Debit/Credit"] == "Debit"].copy()

            # Initial categorization
            df = categorize_transactions(debits_df, st.session_state.keyword_dict, st.session_state.name_to_category)
            edited_df = df.copy()

            st.markdown("### ✏️ Categorize & Edit Transactions")
            edited_df = st.data_editor(edited_df, num_rows="dynamic", use_container_width=True)

            # Learn from user edits
            changed = False
            for i in range(len(edited_df)):
                old_cat = df.iloc[i]["Category"]
                new_cat = edited_df.iloc[i]["Category"]
                name = edited_df.iloc[i]["Name"]

                if new_cat != old_cat and new_cat.strip():
                    changed = True

                    # Add new category to keyword dict if missing
                    if new_cat not in st.session_state.keyword_dict:
                        st.session_state.keyword_dict[new_cat] = []

                    # Learn from full name
                    st.session_state.name_to_category[name.lower()] = new_cat

                    # Add name tokens to keyword dict
                    words = name.lower().split()
                    for word in words:
                        if word not in st.session_state.keyword_dict[new_cat]:
                            st.session_state.keyword_dict[new_cat].append(word)

            # If any changes, save mapping and re-categorize all rows
            if changed:
                save_name_category_map(st.session_state.name_to_category)
                df = categorize_transactions(debits_df, st.session_state.keyword_dict, st.session_state.name_to_category)
                edited_df = df.copy()

            # Expense Summary Table
            st.markdown("### 📌 Expense Summary")
            summary = edited_df.groupby("Category")["Amount"].sum().reset_index().sort_values(by="Amount", ascending=False)
            st.dataframe(summary, use_container_width=True)

            # Visual Insights
            st.markdown("### 📊 Visual Insights")

            # Pie Chart
            fig_pie = px.pie(
                summary,
                names="Category",
                values="Amount",
                title="Expense Distribution by Category",
                hole=0.4
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            # Bar Chart
            fig_bar = px.bar(
                summary,
                x="Category",
                y="Amount",
                title="Total Expenses per Category",
                text_auto=".2s",
                color="Category"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # CSV Download
            st.download_button(
                "⬇️ Download Categorized CSV",
                data=edited_df.to_csv(index=False),
                file_name="categorized_phonepe.csv",
                mime="text/csv"
            )
            
            # --- AI Chatbot Section ---
            st.markdown("## 🤖 AI Chatbot: Ask About Your Transactions")
            user_query = st.text_input("Ask a question about your expenses (e.g., 'How much did I spend on food?')", key="chatbot_query")
            if st.button("Ask", key="ask_btn") and user_query.strip():
                with st.spinner("Thinking..."):
                    try:
                        answer = answer_nlp_question(edited_df, user_query)
                        st.success(answer)
                    except Exception as e:
                        st.error(f"Sorry, couldn't answer your question. Try rephrasing or ask something else. Error: {str(e)}")

        else:
            st.warning("⚠️ Unable to extract any transactions. Check the file or password.")

if __name__ == "__main__":
    main()
