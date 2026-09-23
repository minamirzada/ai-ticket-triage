import pandas as pd
from triage import triage_ticket

tickets = pd.read_csv("tickets.csv")

results = []

for index, row in tickets.iterrows():
    print(f"Analyzing ticket {index + 1} of {len(tickets)}...")
    triage = triage_ticket(row["message"])
    results.append({
        "ticket_id": row["ticket_id"],
        "name": row["name"],
        "priority": triage["priority"],
        "category": triage["category"],
        "summary": triage["summary"],
        "suggested_reply": triage["suggested_reply"],
    })

results_df = pd.DataFrame(results)

priority_order = {"High": 0, "Medium": 1, "Low": 2}
results_df["priority_rank"] = results_df["priority"].map(priority_order)
results_df = results_df.sort_values("priority_rank").drop(columns="priority_rank")

print()
print(results_df[["ticket_id", "name", "priority", "category", "summary"]].to_string(index=False))

results_df.to_csv("triaged_tickets.csv", index=False)
print("\nSaved results to triaged_tickets.csv")