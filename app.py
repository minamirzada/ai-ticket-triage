import json

import anthropic
import pandas as pd
import streamlit as st

from triage import triage_ticket

st.set_page_config(page_title="AI Ticket Triage", layout="wide")

# ---------- Settings ----------
MAX_TICKETS = 25
MAX_TICKET_LENGTH = 2000
REQUIRED_COLUMNS = {"ticket_id", "name", "message"}
PRIORITY_ORDER = {"High": 0, "Needs review": 1, "Medium": 2, "Low": 3}


# ---------- Helper functions ----------
def load_tickets(file):
    """Read a CSV file and check that it's usable. Returns a table, or None if there's a problem."""
    try:
        df = pd.read_csv(file)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError):
        st.error("This file couldn't be read. Please check that it's a valid CSV file.")
        return None

    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        st.error(f"Your CSV is missing these columns: {', '.join(sorted(missing))}")
        return None

    df = df.dropna(subset=["message"])
    df = df[df["message"].astype(str).str.strip() != ""]

    if df.empty:
        st.error("No tickets with a message were found in this file.")
        return None

    if len(df) > MAX_TICKETS:
        st.warning(f"This demo analyzes up to {MAX_TICKETS} tickets at a time, so only the first {MAX_TICKETS} will be used.")
        df = df.head(MAX_TICKETS)

    return df.reset_index(drop=True)


def safe_triage(message):
    """Triage one ticket. If anything goes wrong, return a 'Needs review' result instead of crashing."""
    try:
        result = triage_ticket(str(message)[:MAX_TICKET_LENGTH])
        return {
            "priority": result["priority"],
            "category": result["category"],
            "summary": result["summary"],
            "suggested_reply": result["suggested_reply"],
        }
    except (anthropic.APIError, json.JSONDecodeError, KeyError, TypeError):
        return {
            "priority": "Needs review",
            "category": "Unknown",
            "summary": "The AI couldn't analyze this ticket. Please review it manually.",
            "suggested_reply": "",
        }


# ---------- Page header ----------
st.title("AI Help Desk Ticket Triage")
st.write("Get an AI first look at support tickets: category, priority, summary, and a suggested reply. A human always makes the final call.")

batch_tab, single_tab = st.tabs(["Upload CSV", "Single ticket"])

# ---------- Tab 1: a whole CSV file ----------
with batch_tab:
    st.write("Upload your own CSV file, or try the app with sample tickets.")
    uploaded_file = st.file_uploader("Upload a CSV with columns: ticket_id, name, message", type="csv")

    if st.button("Try with sample tickets"):
        st.session_state["use_sample"] = True

    tickets = None
    source = None
    if uploaded_file is not None:
        tickets = load_tickets(uploaded_file)
        source = uploaded_file.name
    elif st.session_state.get("use_sample"):
        tickets = load_tickets("tickets.csv")
        source = "sample"

    if tickets is not None:
        st.write(f"Loaded {len(tickets)} tickets:")
        st.dataframe(tickets, hide_index=True)

        if st.button("Analyze tickets"):
            results = []
            progress = st.progress(0)

            for index, row in tickets.iterrows():
                progress.progress((index + 1) / len(tickets), text=f"Analyzing ticket {index + 1} of {len(tickets)}...")
                triage = safe_triage(row["message"])
                results.append({
                    "ticket_id": row["ticket_id"],
                    "name": row["name"],
                    "priority": triage["priority"],
                    "category": triage["category"],
                    "summary": triage["summary"],
                    "suggested_reply": triage["suggested_reply"],
                })

            results_df = pd.DataFrame(results)
            results_df["priority_rank"] = results_df["priority"].map(PRIORITY_ORDER)
            results_df = results_df.sort_values("priority_rank").drop(columns="priority_rank")
            st.session_state["results"] = results_df
            st.session_state["results_source"] = source

        if st.session_state.get("results_source") == source:
            results_df = st.session_state["results"]

            failed = (results_df["priority"] == "Needs review").sum()
            if failed > 0:
                st.warning(f"{failed} ticket(s) couldn't be analyzed and are marked 'Needs review'.")

            st.subheader("Triaged tickets (most urgent first)")
            st.dataframe(results_df[["priority", "ticket_id", "name", "category", "summary"]], hide_index=True)

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Tickets by category**")
                st.bar_chart(results_df["category"].value_counts())
            with col2:
                st.write("**Tickets by priority**")
                st.bar_chart(results_df["priority"].value_counts())

            st.subheader("Suggested replies")
            selected_id = st.selectbox("Choose a ticket:", results_df["ticket_id"])
            ticket = results_df[results_df["ticket_id"] == selected_id].iloc[0]
            st.write(f"**{ticket['name']}** · {ticket['priority']} priority · {ticket['category']}")
            if ticket["suggested_reply"]:
                st.info(ticket["suggested_reply"])
            else:
                st.write("No suggested reply for this ticket. Please review it manually.")

            st.download_button(
                "Download results as CSV",
                results_df.to_csv(index=False),
                file_name="triaged_tickets.csv",
                mime="text/csv",
            )

# ---------- Tab 2: one ticket at a time ----------
with single_tab:
    ticket_text = st.text_area("Paste a support ticket:", height=150, max_chars=MAX_TICKET_LENGTH)

    if st.button("Triage ticket"):
        if ticket_text.strip() == "":
            st.warning("Please enter a ticket first.")
        else:
            with st.spinner("Analyzing..."):
                result = safe_triage(ticket_text)

            if result["priority"] == "Needs review":
                st.error("The AI couldn't analyze this ticket right now. Please try again in a moment.")
            else:
                st.subheader(f"Priority: {result['priority']}")
                st.write(f"**Category:** {result['category']}")
                st.write(f"**Summary:** {result['summary']}")
                st.write("**Suggested reply:**")
                st.info(result["suggested_reply"])