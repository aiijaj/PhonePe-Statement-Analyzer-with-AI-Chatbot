# 📊 PhonePe Statement Analyzer with AI Chatbot

A Streamlit web app that analyzes your PhonePe transaction statements (PDF/CSV), auto-categorizes expenses, visualizes spending, and lets you ask questions about your transactions using an AI-powered chatbot.

---
#Working Website -- https://github.com/aiijaj/PhonePe-Statement-Analyzer-with-AI-Chatbot.git 
## 🚀 Features

- **Upload PhonePe statements** (PDF or CSV)
- **Automatic parsing** of transactions
- **Expense categorization** (with learning from your edits)
- **Interactive editing** of categories
- **Visual insights** (pie/bar charts)
- **Download categorized CSV**
- **AI Chatbot**: Ask natural language questions like  
  _"How much did I spend on food?"_ or _"Show all transactions above ₹1000"_

---

## 🖥️ Demo

![Screenshot 2025-05-26 112402](https://github.com/user-attachments/assets/f4da6e2e-b106-445e-a7fd-14c304db2b34)
![Screenshot 2025-05-26 112416](https://github.com/user-attachments/assets/1d7a1283-0c20-41c7-ba63-e6bef7f27928)
![Screenshot 2025-05-26 112428](https://github.com/user-attachments/assets/72729e24-eb5b-4f1f-9417-0450986d91b5)





---

## 🛠️ How It Works

1. **Upload** your PhonePe statement (PDF or CSV).
2. The app **extracts and parses** your transactions.
3. Transactions are **auto-categorized** based on merchant name and keywords.
4. **Edit categories** directly in the table to improve accuracy.
5. **Visualize** your expenses by category.
6. **Ask questions** in plain English using the built-in AI chatbot.

---

## 🧑‍💻 Tech Stack

- [Streamlit](https://streamlit.io/) (UI)
- [pandas](https://pandas.pydata.org/) (data processing)
- [pdfplumber](https://github.com/jsvine/pdfplumber) & [pikepdf](https://github.com/pikepdf/pikepdf) (PDF parsing)
- [plotly](https://plotly.com/python/) (visualizations)
- [transformers](https://huggingface.co/transformers/) (AI chatbot, Q&A)
- [sqlite3](https://docs.python.org/3/library/sqlite3.html) (category learning)

---

## 📦 Installation

1. **Clone this repo:**
   ```bash
    https://github.com/aiijaj/PhonePe-Statement-Analyzer-with-AI-Chatbot.git
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   Or, install manually:
   ```bash
   pip install streamlit pandas pikepdf pdfplumber plotly transformers torch
   ```

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

---

## ☁️ Free Deployment

You can deploy this app for free using [Streamlit Community Cloud](https://streamlit.io/cloud):

- Push your code to a public GitHub repo.
- Go to [Streamlit Cloud](https://streamlit.io/cloud) and connect your repo.
- Click **"Deploy"** and get a public link!

---

## 💬 Example Questions for Chatbot

- `How much did I spend on food?`
- `What was my highest expense category last month?`
- `Show all transactions above 2000 INR`
- `How many transactions did I make in March?`

---

## 📝 Customization

- **Add/Edit Categories:** The app learns new categories as you edit them.
- **Keyword Tuning:** Edit the `default_keywords` dictionary in the code to improve auto-categorization.
- **Model Choice:** Uses Hugging Face’s `distilbert-base-cased-distilled-squad` for Q&A.

---

## 🛡️ Privacy

- All processing is done locally or on your chosen cloud instance.
- Your data is not stored or shared.

---

## 📄 License

MIT License

---

## 👤 Author

- [Your Name](https://github.com/aiijaj)

---

## 🙏 Acknowledgements

- [Streamlit](https://streamlit.io/)
- [Hugging Face Transformers](https://huggingface.co/transformers/)
- [pdfplumber](https://github.com/jsvine/pdfplumber)
- [pikepdf](https://github.com/pikepdf/pikepdf)
- [Plotly](https://plotly.com/python/)

---

*Feel free to fork, contribute, or open issues!*
