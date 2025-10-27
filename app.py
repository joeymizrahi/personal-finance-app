# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
import logging
import sys
import os
from config import Config
import notion_client  # Import our new client

# Basic logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

app = Flask(__name__)


# --- Primary Routes ---

@app.route('/', methods=['GET'])
def index():
    try:
        # Per your request, we fetch fresh data every time
        all_accounts_pages = notion_client.fetch_notion_database_pages(Config.ACCOUNTS_DB_ID)
        all_pillars_pages = notion_client.fetch_notion_database_pages(Config.PILLARS_DB_ID)

        # ... (Your processing logic remains the same) ...
        accounts = [
            {'id': p['id'], 'name': p['properties']['Name']['title'][0]['plain_text'], 'properties': p['properties']}
            for p in all_accounts_pages]
        pillars = [{'id': p['id'], 'name': p['properties']['Name']['title'][0]['plain_text']} for p in
                   all_pillars_pages]
        pillars.reverse()
        investment_accounts = [acc for acc in accounts if
                               acc['properties'].get('Is Investment Account?', {}).get('checkbox') is True]
        non_investment_accounts = [acc for acc in accounts if
                                   acc['properties'].get('Is Investment Account?', {}).get('checkbox') is not True]

        # Use the new template file
        return render_template('index.html',
                               non_investment_accounts=non_investment_accounts,
                               pillars=pillars,
                               investment_accounts=investment_accounts)
    except Exception as e:
        log.error(f"Error loading index page: {e}")
        return render_template('failure.html', error_message=f"Failed to load page data from Notion: {e}")


@app.route('/log_transaction', methods=['POST'])
def log_transaction():
    try:
        form_data = request.form
        transaction_type = form_data.get('type')
        message = ""

        if transaction_type in ['expense', 'income']:
            # Call our new client function
            notion_client.create_expense_or_income(
                ttype=transaction_type,
                description=form_data.get('description', 'No description'),
                amount=float(form_data.get('amount', 0)),
                account_id=form_data.get('from_account_id'),
                category_id=form_data.get('category_id'),
                pillar_id=form_data.get('pillar_id'),
                currency=form_data.get('currency', 'ILS')
            )
            message = "✅ Successfully logged transaction."

        elif transaction_type == 'transfer':
            # This function now returns the success message
            message = notion_client.create_transfer_entries(
                from_account_id=form_data.get('from_account_id'),
                to_account_id=form_data.get('to_account_id'),
                amount=float(form_data.get('amount', 0)),
                currency=form_data.get('currency', 'ILS')
            )

        return redirect(url_for('success', message=message))

    except Exception as e:
        # This catches errors from notion_client and renders the failure page
        log.error(f"Error processing transaction form: {e}")
        return render_template('failure.html', error_message=str(e))


@app.route('/log_investment', methods=['POST'])
def log_investment():
    try:
        # All the complex logic is now in the client!
        message = notion_client.log_investment_transaction(request.form)
        return redirect(url_for('success', message=message))

    except Exception as e:
        log.error(f"An unexpected error occurred in log_investment: {e}")
        import traceback
        log.error(traceback.format_exc())
        return render_template('failure.html', error_message=str(e))


# --- API and Utility Routes ---

@app.route('/api/categories/<transaction_type>')
def get_categories_by_type(transaction_type):
    try:
        # This logic is fine to keep here, or move to notion_client
        parents, children_map = notion_client.fetch_and_process_categories(transaction_type)
        return jsonify({'parents': parents, 'children_map': children_map})
    except Exception as e:
        log.error(f"Error fetching categories: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/success')
def success():
    message = request.args.get('message', 'Your entry has been logged to Notion.')
    return render_template('success.html', message=message)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


# --- Main Run Block ---
if __name__ == '__main__':
    notion_client.enrich_holdings_with_more_info("INTC")
    # port = int(os.environ.get('PORT', 5000))
    # app.run(host='0.0.0.0', port=port, debug=False)