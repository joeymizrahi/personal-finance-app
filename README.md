# Personal Finance Tracking System

A comprehensive personal finance tracking system that unifies quick data entry, a structured operational database, and automated analytics pipelines. The solution is anchored around Notion as the single source of truth while providing streamlined capture through a Python web app and live reporting in Google Looker Studio.

## Project Scope

The project orchestrates the following end-to-end flow:

1. **Python Web App (Input) & Notion UI (Input)** – Transactions, transfers, and investment activities can be recorded either through the native Notion interface or via the custom Flask web application hosted on PythonAnywhere.
2. **Notion (Single Source of Truth)** – All financial records live in a normalized Notion workspace that stores transactions, holdings, accounts, categories, and strategic pillars.
3. **Google Apps Script (Automation)** – A scheduled script runs every 15 minutes to extract data from Notion and completely refresh the mirrored Google Sheets tables.
4. **Google Sheets (Data Source)** – Clean, analysis-ready tables serve as the canonical data source for downstream reporting.
5. **Google Looker Studio (Output)** – Dashboards and visualizations consume the Google Sheets data for real-time monitoring of personal finances.

This architecture allows you to capture information once and have it propagate automatically to analytics, ensuring consistency across every interface.

## Component Overview

### Python Web Application (Hosted on PythonAnywhere)
- Provides a dedicated, mobile-friendly front-end for rapid data entry.
- Interacts with the Notion API to insert or update records in the linked databases.
- Eliminates the need to navigate the full Notion UI when logging transactions on the go.

### Notion Workspace
- Serves as the centralized operational database and system of record.
- Maintains relational structures for transactions, investment activity, holdings, accounts, categories, and financial pillars.
- Supports both manual entry and automated updates coming from the web app.

### Google Apps Script Automation
- Acts as the integration layer between Notion and Google Sheets.
- Executes on a fixed schedule to sync the latest data, overwriting Sheets so they remain an exact mirror of Notion.

### Google Sheets Data Warehouse
- Stores synchronized tables for analysis and aggregation.
- Feeds Google Looker Studio with live data for dashboards and performance tracking.

### Google Looker Studio Dashboards
- Visualizes spending, income, account balances, investment performance, and more using the up-to-date Google Sheets datasets.

## Notion Database Schema

The system relies on a set of interconnected Notion databases:

1. **Transactions** – Logs every expense, income, and transfer. Includes description, transaction date, amount, type, category, account, and pillar relations.
2. **Investment Transactions** – Tracks security purchases, sales, dividends, fees, and associated accounts. Stores quantities, pricing, and calculated trade costs.
3. **Holdings** – Aggregates current positions with rollups for quantity owned, average cost, total cost basis, and linked accounts.
4. **Accounts** – Lists every financial account, flags investment accounts, and rolls up balances from transactions.
5. **Categories** – Standardizes transaction categorization with optional parent categories, income/expense type, and rolled-up totals.

## Application Features

- **Transaction Logging**: Record expenses, income, and transfers with automated handling for double-entry transfers.
- **Dynamic Metadata**: Pulls categories, accounts, and pillars directly from Notion and adjusts dropdowns based on transaction type.
- **Investment Tracking**: Supports buy, sell, deposit, withdrawal, dividend, and fee actions while updating holdings and realized gains/losses.
- **Clean UI**: Provides a fast, single-page form optimized for desktop and mobile data entry.
- **Modular Backend**: Separates routing (Flask) from business logic (`notion_client.py`) for maintainability.

## How the Flask App Works

The application is composed of three primary layers:

- **Flask Backend (`app.py`)**
  - Serves the `index.html` page.
  - Exposes API endpoints (e.g., `/api/categories/...`) to populate dropdowns dynamically.
  - Accepts form submissions (`/log_transaction`, `/log_investment`) and returns success or failure feedback.

- **Notion Client (`notion_client.py`)**
  - Encapsulates all Notion API interactions.
  - Builds complex payloads for transactions, transfers, and investment updates.

- **Frontend (`templates/`, `static/`)**
  - `templates/index.html` contains the single-page form UI.
  - `static/style.css` delivers the design system.
  - `static/app.js` manages client-side logic such as toggling modes and fetching dropdown data.

## Setup & Installation

1. **Prerequisites**
   - Python 3.12+
   - A Notion account with the necessary databases (see `.env.example`).
   - A Notion Integration Token (Bot).

2. **Create your Notion Integration**
   - Visit <https://www.notion.so/my-integrations> and create a new integration (e.g., "Finance Logger Bot").
   - Copy the Internal Integration Token (`NOTION_API_KEY`).
   - Share each required Notion database with the integration.

3. **Local Development**
   ```bash
   git clone <your-repo-url>
   cd <your-repo-name>
   python -m venv venv
   source venv/bin/activate  # On Windows use venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Populate the following variables
   NOTION_API_KEY="secret_..."
   NOTION_TRANSACTIONS_DB_ID="..."
   NOTION_ACCOUNTS_DB_ID="..."
   NOTION_CATEGORIES_DB_ID="..."
   NOTION_PILLARS_DB_ID="..."
   NOTION_INVESTMENT_TRANSACTIONS_DB_ID="..."
   NOTION_HOLDINGS_DB_ID="..."
   SSL_VERIFY="true"  # Set to 'false' if corporate proxy breaks SSL
   ```

5. **Run the App**
   ```bash
   flask run
   ```
   Access the interface at <http://127.0.0.1:5000>.

## Deployment (Example: Google Cloud Run)

This app is container-ready. Use the provided `Dockerfile` to build and deploy.

```bash
docker build -t notion-finance-logger .
docker run -p 8080:8080 -e PORT=8080 --env-file .env notion-finance-logger
```

Deploy to Cloud Run (requires configured `gcloud` CLI):

```bash
gcloud run deploy notion-finance-logger \
  --image gcr.io/YOUR_PROJECT_ID/notion-finance-logger \
  --platform managed \
  --region YOUR_REGION \
  --set-env-vars="NOTION_API_KEY=secret_..." \
  --set-env-vars="NOTION_TRANSACTIONS_DB_ID=..." \
  # ... include all other env vars \
  --allow-unauthenticated
```

## Future Roadmap

- [ ] **Market Data Enrichment**: Build a scheduled `yfinance_updater.py` to pull market data for holdings and update Notion.
- [ ] **Caching Layer**: Implement caching (e.g., Flask-Caching) for slowly changing dropdown metadata.
- [ ] **AI Insights**: Feed enriched holdings data to an LLM for automated portfolio analysis and recommendations.


