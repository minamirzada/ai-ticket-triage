import json

import altair as alt
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
PRIORITY_COLORS = {"High": "#d62728", "Needs review": "#7f7f7f", "Medium": "#f28e2b", "Low": "#2ca02c"}
GITHUB_URL = "https://github.com/minamirzada/ai-ticket-triage"
PRIVACY_NOTE = "Please don't enter real personal or confidential information. Tickets are sent to an AI service for analysis."

TEMPLATE_CSV = """ticket_id,name,message
1001,Jane Doe,"My laptop won't turn on after last night's update."
1002,John Smith,"I need access to the shared Finance folder."
"""


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

    df["ticket_id"] = df["ticket_id"].astype(str)

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


def plural(count, word):
    """Return '1 ticket' or '3 tickets' depending on the count."""
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def color_priority(value):
    """Style a priority cell with its color."""
    color = PRIORITY_COLORS.get(value)
    if color:
        return f"background-color: {color}; color: white; font-weight: bold"
    return ""


# ---------- Page header ----------
st.title("AI Help Desk Ticket Triage")
st.write("Get an AI first look at support tickets: category, priority, summary, and a suggested reply. A human always makes the final call.")

batch_tab, single_tab = st.tabs(["Upload CSV", "Single ticket"])

# ---------- Tab 1: a whole CSV file ----------
with batch_tab:
    st.write("Upload your own CSV file, or try the app with sample tickets.")

    with st.expander("What should my CSV look like?"):
        st.write("Your file needs three columns: **ticket_id**, **name**, and **message**. Other columns are ignored. For example:")
        st.dataframe(
            pd.DataFrame({
                "ticket_id": ["1001", "1002"],
                "name": ["Jane Doe", "John Smith"],
                "message": ["My laptop won't turn on after last night's update.", "I need access to the shared Finance folder."],
            }),
            hide_index=True,
        )
        st.download_button(
            "Download a CSV template",
            TEMPLATE_CSV,
            file_name="ticket_template.csv",
            mime="text/csv",
        )

    uploaded_file = st.file_uploader("Upload a CSV with columns: ticket_id, name, message", type="csv")
    st.caption(PRIVACY_NOTE)

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
        st.write(f"Loaded {plural(len(tickets), 'ticket')}:")
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

            progress.empty()
            st.success(f"Done! Analyzed {plural(len(tickets), 'ticket')}.")

            results_df = pd.DataFrame(results)
            results_df["priority_rank"] = results_df["priority"].map(PRIORITY_ORDER)
            results_df = results_df.sort_values("priority_rank").drop(columns="priority_rank")
            st.session_state["results"] = results_df
            st.session_state["results_source"] = source

        if st.session_state.get("results_source") == source:
            results_df = st.session_state["results"]

            # --- Summary numbers ---
            total = len(results_df)
            high_count = (results_df["priority"] == "High").sum()
            top_category = results_df["category"].value_counts().idxmax()
            failed = (results_df["priority"] == "Needs review").sum()

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total tickets", total)
            m2.metric("High priority", high_count)
            m3.metric("Most common category", top_category)
            m4.metric("Needs review", failed)

            if failed > 0:
                st.warning(f"{plural(failed, 'ticket')} couldn't be analyzed and need manual review.")

            # --- Results table with colored priorities ---
            st.subheader("Triaged tickets (most urgent first)")
            table = results_df[["priority", "ticket_id", "name", "category", "summary"]]
            st.dataframe(table.style.map(color_priority, subset=["priority"]), hide_index=True)

            # --- Charts ---
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Tickets by category**")
                category_counts = results_df["category"].value_counts().reset_index()
                category_chart = alt.Chart(category_counts).mark_bar(color="#4e79a7").encode(
                    x=alt.X("category", sort="-y", title=None),
                    y=alt.Y("count", title="Tickets", axis=alt.Axis(tickMinStep=1)),
                )
                st.altair_chart(category_chart)

            with col2:
                st.write("**Tickets by priority**")
                priority_counts = results_df["priority"].value_counts().reset_index()
                priority_chart = alt.Chart(priority_counts).mark_bar().encode(
                    x=alt.X("priority", sort=list(PRIORITY_ORDER), title=None),
                    y=alt.Y("count", title="Tickets", axis=alt.Axis(tickMinStep=1)),
                    color=alt.Color(
                        "priority",
                        scale=alt.Scale(domain=list(PRIORITY_COLORS), range=list(PRIORITY_COLORS.values())),
                        legend=None,
                    ),
                )
                st.altair_chart(priority_chart)

            # --- Suggested replies ---
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
    st.caption(PRIVACY_NOTE)

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

# ---------- Footer ----------
st.divider()
st.caption(f"Built by Mina Mirzada · [View the code on GitHub]({GITHUB_URL})")