Personal Notion Finance Logger

A lightweight web application built with Flask and the Notion API to quickly log financial transactions (expenses, income, transfers) and investment activities directly into your Notion workspace.

This app provides a simple, mobile-friendly interface to bypass the complexity of the Notion app for on-the-go logging, ensuring your financial databases are always up-to-date.

Features

Transaction Logging: Log expenses, income, and transfers.

Automatically pulls categories and pillars from your Notion DBs.

Dynamically updates category dropdowns based on transaction type (Expense vs. Income).

Handles transfer logic by creating both a debit and a credit entry.

Investment Tracking: Log detailed investment activities.

Supports Buy, Sell, Deposit, Withdrawal, Dividend, and Fee actions.

Automatically updates your Holdings database when you buy or sell assets.

Calculates realized gains/losses on 'Sell' transactions.

Clean UI: A simple, fast, single-page form for quick data entry.

Modular Backend: The Flask application is separated into a "thin" route layer and a robust notion_client service for maintainability.

How It Works

The application is composed of three main parts:

Flask Backend (app.py): A lightweight web server that handles:

Serving the main index.html page.

Providing API endpoints (e.g., /api/categories/...) to dynamically populate form dropdowns.

Receiving form submissions (/log_transaction, /log_investment).

Displaying success or failure messages.

Notion Client (notion_client.py):

Acts as a dedicated "service" that contains all business logic.

Handles all API requests to Notion (fetching pages, creating pages, updating pages).

Contains functions for building complex Notion payloads (e.g., create_transfer_entries, log_investment_transaction).

Frontend (templates/ & static/):

A single index.html file provides the form interface.

static/style.css contains all styling for the app.

static/app.js handles all client-side logic, such as:

Switching between Expense, Income, and Transfer modes.

Showing/hiding form fields based on the investment action selected.

Fetching category lists from the backend API.

Setup & Installation

1. Prerequisites

Python 3.12+

A Notion account with a set of databases (see .env.example).

A Notion Integration Token (Bot).

2. Create your Notion Integration

Go to https://www.notion.so/my-integrations.

Click "New integration" and give it a name (e.g., "Finance Logger Bot").

Copy the "Internal Integration Token" - this is your NOTION_API_KEY.

Go to each of your Notion databases (Transactions, Accounts, etc.) and click the ... menu.

Click "Add connections" and select your new "Finance Logger Bot" integration. You must do this for every database the app needs to access.

3. Local Development

Clone the repository:

git clone <your-repo-url>
cd <your-repo-name>


Create a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install dependencies:

pip install -r requirements.txt


Create your environment file:

Copy the .env.example file to a new file named .env.

Open .env and fill in all the required values:

# .env
NOTION_API_KEY="secret_..."
NOTION_TRANSACTIONS_DB_ID="your_transactions_db_id"
NOTION_ACCOUNTS_DB_ID="your_accounts_db_id"
NOTION_CATEGORIES_DB_ID="your_categories_db_id"
NOTION_PILLARS_DB_ID="your_pillars_db_id"
NOTION_INVESTMENT_TRANSACTIONS_DB_ID="your_investment_tx_db_id"
NOTION_HOLDINGS_DB_ID="your_holdings_db_id"

# Set to 'false' if you are behind a corporate proxy that breaks SSL
SSL_VERIFY="true"


Run the app:

flask run


The app will be available at http://127.0.0.1:5000.

Deployment (e.g., Google Cloud Run)

This app is container-ready. A Dockerfile is included to deploy as a serverless container.

Build the container:

docker build -t notion-finance-logger .


Run the container locally (to test):

docker run -p 8080:8080 -e PORT=8080 --env-file .env notion-finance-logger


Deploy to Cloud Run:
(Assuming you have gcloud CLI configured)

gcloud run deploy notion-finance-logger \
  --image gcr.io/YOUR_PROJECT_ID/notion-finance-logger \
  --platform managed \
  --region YOUR_REGION \
  --set-env-vars="NOTION_API_KEY=secret_..." \
  --set-env-vars="NOTION_TRANSACTIONS_DB_ID=..." \
  # ... (add all your other env vars here) \
  --allow-unauthenticated


Future Roadmap

This app provides the data entry foundation. The next logical step is to build a data enrichment and analysis service.

[ ] Create yfinance_updater.py: A separate, cron-job-style script that:

Fetches all pages from the HoldEings database.

Uses yfinance to get current market data (price, P/E, sector, country, etc.).

Updates the Notion pages with this enriched data.

[ ] Add Caching: Implement caching (e.g., Flask-Caching) for dropdown data (Accounts, Pillars, Categories) that doesn't change often, improving page load speed.

[ ] AI Integration: Use the enriched Holdings data as a prompt context for an LLM to get portfolio analysis and recommendations.