# ynab_api.py

# HTTP requests library to communicate with YNAB API
import requests

# Streamlit is used to read secrets and optionally show errors
import streamlit as st

# Standard date utilities (not strictly required here but useful)
from datetime import date


# ------------------------------------------
# API CONFIGURATION
# ------------------------------------------

# Personal access token stored in Streamlit secrets
TOKEN = st.secrets["YNAB_TOKEN"]

# YNAB budget ID stored in secrets
BUDGET = st.secrets["BUDGET_ID"]


# ------------------------------------------
# FETCH ALL CATEGORIES FROM YNAB
# ------------------------------------------

def traer_categorias():
    """
    Retrieves all active categories from the YNAB budget.
    Returns a simplified list with category name and ID.
    """

    # Endpoint for retrieving categories
    url = f"https://api.ynab.com/v1/budgets/{BUDGET}/categories"

    # Authorization header using Bearer token
    headers = {"Authorization": f"Bearer {TOKEN}"}

    # Send GET request
    r = requests.get(url, headers=headers)

    # Convert JSON response
    data = r.json()

    categorias = []

    # YNAB organizes categories in groups (Needs, Wants, etc.)
    for group in data["data"]["category_groups"]:

        # Iterate through each category inside the group
        for cat in group["categories"]:

            # Ignore deleted categories
            if not cat["deleted"]:

                categorias.append({
                    # Friendly name shown in the UI
                    "nombre": f"{group['name']} → {cat['name']}",

                    # Category ID required when creating transactions
                    "id": cat["id"]
                })

    return categorias


# ------------------------------------------
# CREATE TRANSACTION IN YNAB
# ------------------------------------------

def crear_transaccion(account_id, categoria_id, payee, amount, fecha, memo):
    """
    Creates a transaction inside the specified YNAB account.

    Parameters
    ----------
    account_id : str
        The YNAB account where the transaction will be recorded

    categoria_id : str
        Category assigned to the transaction

    payee : str
        Store / merchant name

    amount : float
        Amount in normal currency units (e.g., 6800 COP)

    fecha : str
        Transaction date (YYYY-MM-DD)

    memo : str
        Additional detail (in this case the product name)
    """

    # Endpoint for creating transactions
    url = f"https://api.ynab.com/v1/budgets/{BUDGET}/transactions"

    # Payload structure required by YNAB API
    payload = {
        "transaction": {

            # Account receiving the transaction
            "account_id": account_id,

            # Date of the transaction
            "date": fecha,

            # YNAB uses milliunits (amount * 1000)
            # Negative number = spending
            "amount": -int(amount * 1000),

            # Merchant / store name
            "payee_name": payee,

            # Product description
            "memo": memo,

            # Category assignment
            "category_id": categoria_id,

            # Mark transaction as already cleared
            # This prevents it from appearing as "uncleared" in YNAB
            "cleared": "cleared"
        }
    }

    # Authorization header
    headers = {"Authorization": f"Bearer {TOKEN}"}

    # Send transaction to YNAB
    requests.post(url, json=payload, headers=headers)