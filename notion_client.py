# notion_client.py
import requests
import time
from datetime import datetime
from collections import defaultdict
import logging

from flask import render_template

from config import Config

log = logging.getLogger(__name__)

def notion_api_request(method, url, headers, payload=None):
    """A single, reusable function to make Notion API calls."""
    try:
        if payload is None: payload = {}

        # Use the SSL_VERIFY config variable
        verify_ssl = Config.SSL_VERIFY

        if method.lower() == 'post':
            response = requests.post(url, headers=headers, json=payload, timeout=30, verify=verify_ssl)
        elif method.lower() == 'patch':
            response = requests.patch(url, headers=headers, json=payload, timeout=30, verify=verify_ssl)
        else:
            response = requests.get(url, headers=headers, timeout=30, verify=verify_ssl)

        response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx, 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        error_text = e.response.text if getattr(e, 'response', None) else str(e)
        log.error(f"Error making Notion API request to {url}: {e}")
        log.error(f"Response body: {error_text}")
        # Re-raise the exception so the route can catch it and show the user
        raise Exception(f"Notion API Error: {error_text}")


def _get_auth_headers():
    """Helper to get standard auth headers."""
    return {
        'Authorization': f"Bearer {Config.NOTION_API_KEY}",
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28'
    }


def fetch_notion_database_pages(database_id, filters=None, sorts=None):
    """Fetches all pages from a database."""
    if not database_id:
        log.warning("fetch_notion_database_pages called but database_id is missing.")
        return []
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    headers = _get_auth_headers()
    payload = {}
    if filters: payload['filter'] = filters
    if sorts: payload['sorts'] = sorts

    # We let the exception bubble up if it fails
    response_data = notion_api_request('post', url, headers, payload=payload)
    return response_data.get('results', [])


def fetch_and_process_categories(transaction_type=None):
    all_category_pages = fetch_notion_database_pages(Config.CATEGORIES_DB_ID)
    if not all_category_pages: return [], {}
    all_categories = []
    for page in all_category_pages:
        try:
            page_type = page['properties'].get('Type', {}).get('select', {}).get('name')
            if transaction_type and page_type and page_type.lower() != transaction_type.lower():
                continue
            name = page['properties']['Name']['title'][0]['plain_text']
            page_id = page['id']
            parent_relation = page['properties'].get('Parent Category', {}).get('relation', [])
            parent_id = parent_relation[0]['id'] if parent_relation else None
            all_categories.append({'id': page_id, 'name': name, 'parent_id': parent_id})
        except (KeyError, IndexError): continue
    parents = [cat for cat in all_categories if not cat['parent_id']]
    children_map = defaultdict(list)
    for cat in all_categories:
        if cat['parent_id']:
            children_map[cat['parent_id']].append({'id': cat['id'], 'name': cat['name']})
    def sort_key_other_last(category):
        is_other = 1 if 'other' in category['name'].lower() else 0
        return (is_other, category['name'])
    parents.sort(key=sort_key_other_last)
    for parent_id in children_map:
        children_map[parent_id].sort(key=sort_key_other_last)
    return parents, dict(children_map)



# --- HIGH-LEVEL BUSINESS LOGIC ---

def create_expense_or_income(ttype, description, amount, account_id, category_id, pillar_id, currency):
    """Logs a single expense or income transaction."""
    is_expense = ttype == 'expense'
    final_amount = -abs(amount) if is_expense else abs(amount)

    properties = {
        "Description": {"title": [{"text": {"content": description}}]},
        "Amount": {"number": final_amount},
        "Transaction Date": {"date": {"start": datetime.now().strftime('%Y-%m-%d')}},
        "Type": {"select": {"name": "Expense" if is_expense else "Income"}},
        "Account": {"relation": [{"id": account_id}]},
        "Category": {"relation": [{"id": category_id}]},
        "Pillar": {"relation": [{"id": pillar_id}]},
        "Currency": {"select": {"name": currency}}
    }

    url = "https://api.notion.com/v1/pages"
    headers = _get_auth_headers()
    payload = {"parent": {"database_id": Config.TRANSACTIONS_DB_ID}, "properties": properties}

    return notion_api_request('post', url, headers, payload)


def create_transfer_entries(from_account_id, to_account_id, amount, currency):
    """Logs a transfer (debit and credit) between two accounts."""
    if from_account_id == to_account_id:
        raise ValueError("Source and destination accounts cannot be the same.")

    transfer_id = f"TXF-{int(time.time())}"
    url = "https://api.notion.com/v1/pages"
    headers = _get_auth_headers()

    # To get account names, we must fetch them.
    # This is inefficient, but per your request, we are not caching.
    all_accounts = fetch_notion_database_pages(Config.ACCOUNTS_DB_ID)
    from_account_name = next(
        (p['properties']['Name']['title'][0]['plain_text'] for p in all_accounts if p['id'] == from_account_id),
        'Unknown')
    to_account_name = next(
        (p['properties']['Name']['title'][0]['plain_text'] for p in all_accounts if p['id'] == to_account_id),
        'Unknown')

    # 1. Debit
    debit_payload = {"parent": {"database_id": Config.TRANSACTIONS_DB_ID},
                     "properties": {"Description": {"title": [{"text": {"content": f"Transfer to {to_account_name}"}}]},
                                    "Amount": {"number": -abs(amount)},
                                    "Transaction Date": {"date": {"start": datetime.now().strftime('%Y-%m-%d')}},
                                    "Type": {"select": {"name": "Money Transfer (one account to another)"}},
                                    "Account": {"relation": [{"id": from_account_id}]},
                                    "Currency": {"select": {"name": currency}},
                                    "Transfer ID": {"rich_text": [{"text": {"content": transfer_id}}]}}}

    try:
        notion_api_request('post', url, headers, debit_payload)
    except Exception as e:
        raise Exception(f"Failed to log debit side of transfer. Error: {e}")

    # 2. Credit
    credit_payload = {"parent": {"database_id": Config.TRANSACTIONS_DB_ID}, "properties": {
        "Description": {"title": [{"text": {"content": f"Transfer from {from_account_name}"}}]},
        "Amount": {"number": abs(amount)}, "Transaction Date": {"date": {"start": datetime.now().strftime('%Y-%m-%d')}},
        "Type": {"select": {"name": "Money Transfer (one account to another)"}},
        "Account": {"relation": [{"id": to_account_id}]}, "Currency": {"select": {"name": currency}},
        "Transfer ID": {"rich_text": [{"text": {"content": transfer_id}}]}}}

    try:
        notion_api_request('post', url, headers, credit_payload)
    except Exception as e:
        # This is your "critical" error. We raise a specific message for it.
        raise Exception(f"CRITICAL: Debit logged, but CREDIT FAILED. FIX MANUALLY. Error: {e}")

    return f"✅ Successfully logged transfer of {amount} {currency} from {from_account_name} to {to_account_name}."


def find_holding(ticker, account_id):
    filters = {"and": [{"property": "Ticker", "rich_text": {"equals": ticker}},
                       {"property": "Account", "relation": {"contains": account_id}}]}
    holdings_pages = fetch_notion_database_pages(Config.HOLDINGS_DB_ID, filters=filters)
    return holdings_pages[0] if holdings_pages else None

def get_all_holdings():
    return fetch_notion_database_pages(Config.HOLDINGS_DB_ID)

def update_holding(page_id, properties_to_update):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = _get_auth_headers()
    payload = {"properties": properties_to_update}
    return notion_api_request('patch', url, headers, payload)


def create_holding(ticker, account_id, quantity, cost_basis):
    url = "https://api.notion.com/v1/pages"
    headers = _get_auth_headers()
    all_accounts = fetch_notion_database_pages(Config.ACCOUNTS_DB_ID)
    account_name = next(
        (p['properties']['Name']['title'][0]['plain_text'] for p in all_accounts if p['id'] == account_id), 'Unknown')
    holding_id_title = f"{ticker} ({account_name})"

    properties = {
        "Holding ID": {"title": [{"text": {"content": holding_id_title}}]},
        "Ticker": {"rich_text": [{"text": {"content": ticker}}]},
        "Account": {"relation": [{"id": account_id}]},
        "Quantity": {"number": quantity},
        "Total Cost Basis USD": {"number": cost_basis}
    }
    payload = {
        "parent": {"database_id": Config.HOLDINGS_DB_ID},
        "properties": properties
    }
    return notion_api_request('post', url, headers, payload)


def log_investment_transaction(form_data):
    """
    Handles all investment logic (Buy, Sell, Conversion, etc.)
    This is a complex function, so it's good it's isolated here.
    """
    action = form_data.get('action')
    account_id = form_data.get('account_id')
    url = "https://api.notion.com/v1/pages"
    headers = _get_auth_headers()
    success_messages = []

    if action == 'Money Conversion':
        # ... (This logic remains unchanged from previous version) ...
        from_amount = float(form_data.get('from_amount', 0))
        from_currency = form_data.get('from_currency')
        to_amount = float(form_data.get('to_amount', 0))
        to_currency = form_data.get('to_currency')
        rate = float(form_data.get('conversion_rate', 0))
        fee = float(form_data.get('conversion_fee', 0))

        debit_payload = {"parent": {"database_id": Config['investment_transactions_db_id']}, "properties": {
            "Transaction Name": {"title": [{"text": {"content": f"Convert: Sell {from_amount:,.2f} {from_currency}"}}]},
            "Date": {"date": {"start": datetime.now().strftime('%Y-%m-%d')}},
            "Action": {"select": {"name": "Withdrawal"}}, "Account": {"relation": [{"id": account_id}]},
            "Price Per Share USD": {"number": from_amount}, "Currency": {"select": {"name": from_currency}}}}
        debit_response = notion_api_request('post', url, headers, debit_payload)
        if debit_response.get("error"): return render_template("failure.html",
                                                                      error_message=f"Failed to log debit side of conversion. Notion said: {debit_response['message']}")
        success_messages.append("✅ Logged ILS withdrawal.")

        credit_payload = {"parent": {"database_id": Config['investment_transactions_db_id']}, "properties": {
            "Transaction Name": {"title": [{"text": {"content": f"Convert: Buy {to_amount:,.2f} {to_currency}"}}]},
            "Date": {"date": {"start": datetime.now().strftime('%Y-%m-%d')}}, "Action": {"select": {"name": "Deposit"}},
            "Account": {"relation": [{"id": account_id}]}, "Price Per Share USD": {"number": to_amount},
            "Currency": {"select": {"name": to_currency}}, "Conversion Rate": {"number": rate}}}
        credit_response = notion_api_request('post', url, headers, credit_payload)
        if credit_response.get("error"): return render_template("failure.html",
                                                                       error_message=f"CRITICAL: Logged withdrawal but failed to log deposit. FIX MANUALLY. Notion said: {credit_response['message']}")
        success_messages.append("<br>✅ Logged USD deposit.")

        if fee > 0:
            fee_payload = {"parent": {"database_id": Config['investment_transactions_db_id']}, "properties": {
                "Transaction Name": {"title": [{"text": {"content": "Currency Conversion Fee"}}]},
                "Date": {"date": {"start": datetime.now().strftime('%Y-%m-%d')}},
                "Action": {"select": {"name": "Fee/Expense"}}, "Account": {"relation": [{"id": account_id}]},
                "Price Per Share USD": {"number": -fee}, "Currency": {"select": {"name": "USD"}},
                "Conversion Fee USD": {"number": fee}}}
            fee_response = notion_api_request('post', url, headers, fee_payload)
            if fee_response.get("error"): return render_template("failure.html",
                                                                        error_message=f"CRITICAL: Conversion logged, but fee failed. ADD MANUALLY. Notion said: {fee_response['message']}")
            success_messages.append("<br>✅ Logged conversion fee.")
        success_messages.append("✅ Conversion logged." )

    else:  # Buy, Sell, Dividend, etc.
        ticker = form_data.get('ticker', '').upper()
        quantity = float(form_data.get('quantity') or 0)
        price_per_share = float(form_data.get('price_per_share') or 0)
        fees = float(form_data.get('fees') or 0)
        transaction_name = f"{action} {ticker}" if ticker else f"{action} Cash"

        log_payload = {"parent": {"database_id": Config.INVESTMENT_TRANSACTIONS_DB_ID},
                       "properties": { "Transaction Name": {"title": [{"text": {"content": transaction_name}}]}, "Date": {"date": {"start": datetime.now().strftime('%Y-%m-%d')}}, "Action": {"select": {"name": action}}, "Account": {"relation": [{"id": account_id}]}, "Ticker": {"rich_text": [{"text": {"content": ticker if action not in ['Deposit', 'Withdrawal'] else ''}}]}, "Quantity": {"number": quantity if action in ['Buy', 'Sell'] else None}, "Price Per Share USD": {"number": price_per_share}, "Fees USD": {"number": fees if fees > 0 else None}, "Currency": {"select": {"name": "USD"}} } }  # Build payload
        gain_from_this_sale = 0
        proceeds_from_sale = 0
        cost_of_sold_shares = 0

        if action == 'Sell':
            # This is the calculation logic we are moving from the route
            existing_holding_for_gain = find_holding(ticker, account_id)
            if not existing_holding_for_gain:
                raise ValueError(f"Cannot log sale: No existing holding found for {ticker}.")

            current_qty_for_gain = existing_holding_for_gain['properties']['Quantity']['number'] or 0
            if current_qty_for_gain < quantity:
                raise ValueError(f"Cannot sell {quantity} shares of {ticker}, you only own {current_qty_for_gain}.")

            current_cost_basis_for_gain = existing_holding_for_gain['properties']['Total Cost Basis USD']['number'] or 0
            avg_cost = current_cost_basis_for_gain / current_qty_for_gain if current_qty_for_gain > 0 else 0
            cost_of_sold_shares = quantity * avg_cost
            proceeds_from_sale = (quantity * price_per_share) - fees
            gain_from_this_sale = proceeds_from_sale - cost_of_sold_shares
            log_payload["properties"]["Realized Gain/Loss USD"] = {"number": gain_from_this_sale}

        # Log the actual transaction
        notion_api_request('post', url, headers, log_payload)
        success_messages = ["✅ Logged investment transaction."]

        # Update holdings
        if action == 'Buy':
            existing_holding = find_holding(ticker, account_id)
            trade_cost = (quantity * price_per_share) + fees
            if existing_holding:
                current_qty = existing_holding['properties']['Quantity']['number'] or 0
                current_cost_basis = existing_holding['properties']['Total Cost Basis USD']['number'] or 0
                properties_to_update = {"Quantity": {"number": current_qty + quantity},
                                        "Total Cost Basis USD": {"number": current_cost_basis + trade_cost}}
                update_holding(existing_holding['id'], properties_to_update)
                success_messages.append("<br>✅ Updated existing holding.")
            else:
                # ... (logic to create holding, *without* yfinance) ...
                create_holding(ticker, account_id, quantity, trade_cost)
                success_messages.append("<br>✅ Created new holding.")

        elif action == 'Sell':
            existing_holding = find_holding(ticker, account_id)
            # Ensure holding exists (already checked earlier, but good practice)
            if not existing_holding: return render_template("failure.html",
                                                                   error_message="Holding not found for update after sale.")

            current_qty = existing_holding['properties']['Quantity']['number'] or 0
            current_cost_basis = existing_holding['properties']['Total Cost Basis USD']['number'] or 0
            current_realized_gain = existing_holding['properties'].get('Total Realized Gain/Loss USD', {}).get('number',
                                                                                                               0)
            current_proceeds = existing_holding['properties'].get('Total Proceeds from Sales USD', {}).get('number', 0)
            new_realized_gain = current_realized_gain + gain_from_this_sale
            new_proceeds = current_proceeds + proceeds_from_sale
            properties_to_update = {
                "Quantity": {"number": current_qty - quantity},
                "Total Cost Basis USD": {"number": current_cost_basis - cost_of_sold_shares},
                "Total Realized Gain/Loss USD": {"number": new_realized_gain},
                "Total Proceeds from Sales USD": {"number": new_proceeds}
            }
            update_response = update_holding(existing_holding['id'], properties_to_update)
            if update_response.get("error"): return render_template("failure.html",
                                                                           error_message=f"LOGGED TXN but FAILED to update holding: {update_response['message']}")
            success_messages.append("<br>✅ Updated holding with realized gain.")
            success_messages.append("<br>✅ Updated holding with realized gain.")

    return " ".join(success_messages)

def enrich_holdings_with_more_info(ticker=None):
    if ticker is None:
        # enrich all tickers
        holdings_pages = fetch_notion_database_pages(Config.HOLDINGS_DB_ID)
    else:
        # enrich a specific ticker
        holdings_pages = fetch_notion_database_pages(Config.HOLDINGS_DB_ID, filters={"property": "Ticker", "rich_text": {"equals": ticker}})

    update_holding(holdings_pages[0]["id"], properties_to_update = {
                                                "Country": {"select": {"name":  "USA"}},
                                                "Sector": {"select": {"name": "temp_sector"}}})



