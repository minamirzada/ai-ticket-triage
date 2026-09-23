# AI Help Desk Ticket Triage

An AI-powered web app that helps IT help desk teams triage support tickets. It reads each ticket, assigns a category and priority, writes a short summary, and drafts a suggested first reply, then sorts everything so the most urgent issues are handled first.

**Live demo:** [ai-ticket-triage-mm.streamlit.app](https://ai-ticket-triage-mm.streamlit.app/)

## About

Help desk staff often spend a lot of time just reading and sorting tickets before any real troubleshooting starts. This app automates that first pass. It is designed to support people, not replace them: the AI suggests, and a human always makes the final call.

I built this project to learn how to develop real applications with AI APIs, from prompt design and structured output to error handling and deployment. My background in AV technical support at DePaul University shaped the focus on practical, day-to-day help desk work.

## Features

- **Batch triage:** upload a CSV of up to 25 tickets and analyze them all at once, with a progress bar
- **Single-ticket mode:** paste one ticket for a quick analysis
- **Priority sorting:** results are ordered High, Medium, Low, with color-coded priorities
- **Summary dashboard:** total tickets, high-priority count, most common category, and tickets needing review
- **Charts:** ticket breakdowns by category and priority
- **Suggested replies:** a draft first response for every ticket
- **CSV export:** download the triaged results
- **Sample data:** try the app instantly without your own file
- **Reliable error handling:** tickets the AI can't process are flagged "Needs review" instead of crashing the app
- **Flexible input:** accepts different column name formats, such as `Ticket ID` or `ticket_id`

## Tech Stack

- **Python**
- **Claude API** (Anthropic), using Claude Haiku 4.5
- **Streamlit** for the web interface
- **pandas** for data processing
- **Altair** for data visualization
- **Streamlit Community Cloud** for deployment

## How It Works

1. Tickets are loaded from a CSV file or entered directly.
2. Each ticket is sent to Claude with a system prompt that defines a fixed set of categories and priorities.
3. Claude returns structured JSON, which the app validates and parses.
4. Results are sorted by urgency and displayed in a table, dashboard, and charts.

## Getting Started

### Prerequisites

- Python 3.10 or newer
- An [Anthropic API key](https://console.anthropic.com)

### Installation

```bash
git clone https://github.com/minamirzada/ai-ticket-triage.git
cd ai-ticket-triage
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project folder:

```
ANTHROPIC_API_KEY=your-api-key-here
```

Run the app:

```bash
streamlit run app.py
```

## CSV Format

The file must include three columns: `ticket_id`, `name`, and `message`. Any other columns are ignored.

```csv
ticket_id,name,message
1001,Jane Doe,"My laptop won't turn on after last night's update."
1002,John Smith,"I need access to the shared Finance folder."
```

A sample file is included: `tickets.csv`.

## Project Structure

```
ai-ticket-triage/
├── app.py            # Streamlit web app
├── triage.py         # Core triage function using the Claude API
├── batch.py          # Command-line batch triage script
├── first_call.py     # Initial API connection test
├── tickets.csv       # Sample tickets
└── requirements.txt  # Python dependencies
```

## Future Improvements

- Support optional fields such as subject, department, and created time for more accurate triage
- Allow users to correct AI-assigned categories and priorities
- Rebuild the front end in Next.js with a FastAPI back end
- Containerize the app with Docker
- Integrate with ticketing systems to triage new tickets automatically

## Privacy

This is a demo application. Please don't submit real personal or confidential information, as tickets are processed by an external AI service.

## Author

**Mina Mirzada**
[GitHub](https://github.com/minamirzada)