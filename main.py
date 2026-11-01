
import mysql.connector
import urllib.request
import json
from datetime import datetime
import time

# Set your MySQL credentials and database here.
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "crypto_market"
}

# admin password
ADMIN_PASS = "root123"

# Supported cryptos (CoinGecko IDs).
CRYPTO_LIST = ["bitcoin", "ethereum", "solana", "cardano", "dogecoin"]
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=inr"


# ---------------- API / PRICING ----------------
def fetch_prices():
    """
    Fetch live prices (INR) for CRYPTO_LIST from CoinGecko.
    Returns dict: { 'bitcoin': 1234567.0, ... }
    On failure returns None.
    """
    ids = ",".join(CRYPTO_LIST)
    url = COINGECKO_URL.format(ids=ids)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            raw = resp.read().decode()
            data = json.loads(raw)
            prices = {}
            for c in CRYPTO_LIST:
                # defensive: check key presence
                if c in data and 'inr' in data[c]:
                    prices[c] = float(data[c]['inr'])
                else:
                    print(f"Warning: price for {c} missing in API response.")
                    prices[c] = None
            return prices
    except Exception as e:
        print("Error fetching live prices:", e)
        return None


# ---------------- BALANCE & HOLDINGS ----------------
def get_balance():

    # Return current INR balance.
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT balance FROM user_balance LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return float(row[0]) if row else 0.0


def set_balance(value):

    # Set INR balance to a specific value (admin only). This will overwrite whatever was there.
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("UPDATE user_balance SET balance = %s", (float(value),))
    conn.commit()
    cur.close()
    conn.close()


def get_holdings():

    # Return a dict of current crypto holdings,
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT crypto_name, amount FROM crypto_holdings")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {r[0]: float(r[1]) for r in rows}


def update_holding(crypto_name, delta_qty):

    # Add delta_qty to the holding for crypto_name.
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("UPDATE crypto_holdings SET amount = amount + %s WHERE crypto_name = %s",
                (float(delta_qty), crypto_name))
    conn.commit()
    cur.close()
    conn.close()


# ---------------- CRYPTO TRANSACTIONS ----------------
def log_crypto_tx(crypto_name, action, price_in_inr, quantity):
    
    # Insert a crypto transaction log row.
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO crypto_transactions (crypto_name, action, price_in_inr, quantity, timestamp) VALUES (%s, %s, %s, %s, %s)",
        (crypto_name, action, float(price_in_inr), float(quantity), datetime.now())
    )
    conn.commit()
    cur.close()
    conn.close()


# ---------------- ITEM MANAGEMENT & PURCHASES ----------------
def admin_add_item():

    # Add a new item to marketplace (persisted in items table).
    name = input("Item name: ").strip()
    description = input("Short description: ").strip()
    print("Choose crypto to price item in. Supported:", ", ".join(CRYPTO_LIST))
    crypto = input("Price crypto (use exact id, e.g., 'bitcoin'): ").strip().lower()
    if crypto not in CRYPTO_LIST:
        print("Invalid crypto. Aborting add.")
        return
    try:
        amount = float(input("Amount of crypto required (e.g., 0.001): ").strip())
    except:
        print("Invalid amount. Aborting add.")
        return

    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("INSERT INTO items (name, description, price_crypto, amount) VALUES (%s, %s, %s, %s)",
                (name, description, crypto, amount))
    conn.commit()
    cur.close()
    conn.close()
    print("Item added successfully.")


def admin_delete_item():

    # Delete an item by ID.
    view_items(show_header=True)
    try:
        item_id = int(input("Enter item_id to delete: ").strip())
    except:
        print("Invalid id.")
        return
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE item_id = %s", (item_id,))
    if cur.rowcount == 0:
        print("No item with that ID.")
    else:
        print("Item deleted.")
    conn.commit()
    cur.close()
    conn.close()


def view_items(show_header=False):
    # List all items with IDs, description, crypto price and amount.
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT item_id, name, description, price_crypto, amount FROM items")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if show_header:
        print("\n--- ITEMS (marketplace) ---")
    if not rows:
        print("No items in marketplace.")
        return
    for r in rows:
        print(f"ID:{r[0]} | {r[1]} | {r[2]} | Price: {r[4]} {r[3]}")
    print("")  # blank line


def buy_item(prices):
    
    # User buys an item using a specific crypto.
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT item_id, name, description, price_crypto, amount FROM items")
    rows = cur.fetchall()
    if not rows:
        print("No items available.")
        cur.close()
        conn.close()
        return

    print("\n--- Items ---")
    for r in rows:
        # Also show approximate INR price using live prices (if available)
        price_crypto = r[3]
        crypto_amount = float(r[4])
        inr_text = ""
        if prices and prices.get(price_crypto):
            inr_text = f" (~INR {crypto_amount * prices[price_crypto]:.2f})"
        print(f"ID:{r[0]} | {r[1]} | {r[2]} | Price: {crypto_amount} {price_crypto}{inr_text}")

    try:
        item_id = int(input("Enter item ID to buy: ").strip())
    except:
        print("Invalid item id.")
        cur.close()
        conn.close()
        return

    # fetch item
    cur.execute("SELECT item_id, name, price_crypto, amount FROM items WHERE item_id = %s", (item_id,))
    item = cur.fetchone()
    if not item:
        print("Item not found.")
        cur.close()
        conn.close()
        return

    _, item_name, price_crypto, crypto_amount = item
    # check holdings
    cur.execute("SELECT amount FROM crypto_holdings WHERE crypto_name = %s", (price_crypto,))
    hold_row = cur.fetchone()
    if not hold_row:
        print("Error: crypto holding missing in DB.")
        cur.close()
        conn.close()
        return
    holding_qty = float(hold_row[0])

    if holding_qty < crypto_amount:
        print(f"Insufficient {price_crypto}. You have {holding_qty}, need {crypto_amount}.")
        cur.close()
        conn.close()
        return

    # Deduct crypto holding
    cur.execute("UPDATE crypto_holdings SET amount = amount - %s WHERE crypto_name = %s",
                (crypto_amount, price_crypto))

    # Log purchase in marketplace_purchases
    cur.execute("INSERT INTO marketplace_purchases (item_id, crypto_used, amount, timestamp) VALUES (%s, %s, %s, %s)",
                (item_id, price_crypto, crypto_amount, datetime.now()))

    conn.commit()
    cur.close()
    conn.close()
    print(f"Purchased '{item_name}' for {crypto_amount} {price_crypto}.")


# ---------------- CRYPTO BUY / SELL (USER) ----------------
def buy_crypto(prices):
    
    # User buys crypto using INR balance.
    if not prices:
        print("Cannot fetch live prices. Try again later.")
        return

    print("\n--- Available cryptos (live INR) ---")
    for i, c in enumerate(CRYPTO_LIST, start=1):
        print(f"{i}. {c} @ INR {prices[c]:.2f}")
    try:
        choice = int(input("Select crypto number to buy: ").strip()) - 1
        if choice < 0 or choice >= len(CRYPTO_LIST):
            print("Invalid selection.")
            return
    except:
        print("Invalid input.")
        return
    crypto = CRYPTO_LIST[choice]

    try:
        qty = float(input("Enter quantity to buy (e.g., 0.01): ").strip())
    except:
        print("Invalid quantity.")
        return
    if qty <= 0:
        print("Quantity must be positive.")
        return

    price = prices[crypto]
    total_cost = qty * price
    balance = get_balance()
    if total_cost > balance:
        print(f"Insufficient balance. Needed INR {total_cost:.2f}, you have INR {balance:.2f}.")
        return

    # Deduct INR and add crypto, then log
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        # Deduct INR
        cur.execute("UPDATE user_balance SET balance = balance - %s", (total_cost,))
        # Update holding
        cur.execute("UPDATE crypto_holdings SET amount = amount + %s WHERE crypto_name = %s",
                    (qty, crypto))
        # Log tx
        cur.execute("INSERT INTO crypto_transactions (crypto_name, action, price_in_inr, quantity, timestamp) VALUES (%s, %s, %s, %s, %s)",
                    (crypto, "BUY", price, qty, datetime.now()))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Transaction failed:", e)
    finally:
        cur.close()
        conn.close()
    print(f"Bought {qty} {crypto} for INR {total_cost:.2f}.")


def sell_crypto(prices):
    
    # User sells crypto for INR.
    holdings = get_holdings()
    print("\n--- Your crypto holdings ---")
    for i, c in enumerate(CRYPTO_LIST, start=1):
        print(f"{i}. {c} : {holdings.get(c, 0.0)}")
    try:
        choice = int(input("Select crypto number to sell: ").strip()) - 1
        if choice < 0 or choice >= len(CRYPTO_LIST):
            print("Invalid selection.")
            return
    except:
        print("Invalid input.")
        return
    crypto = CRYPTO_LIST[choice]
    available = holdings.get(crypto, 0.0)
    try:
        qty = float(input(f"Enter quantity to sell (available {available}): ").strip())
    except:
        print("Invalid quantity.")
        return
    if qty <= 0:
        print("Quantity must be positive.")
        return
    if qty > available:
        print("You do not have that much to sell.")
        return

    if not prices or prices.get(crypto) is None:
        print("Cannot fetch live prices. Try again later.")
        return

    price = prices[crypto]
    revenue = qty * price

    # Deduct crypto, add INR, and log
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        # Deduct holding
        cur.execute("UPDATE crypto_holdings SET amount = amount - %s WHERE crypto_name = %s", (qty, crypto))
        # Credit INR
        cur.execute("UPDATE user_balance SET balance = balance + %s", (revenue,))
        # Log tx
        cur.execute("INSERT INTO crypto_transactions (crypto_name, action, price_in_inr, quantity, timestamp) VALUES (%s, %s, %s, %s, %s)",
                    (crypto, "SELL", price, qty, datetime.now()))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Sell failed:", e)
    finally:
        cur.close()
        conn.close()
    print(f"Sold {qty} {crypto} for INR {revenue:.2f}.")


# ---------------- ADMIN LOG VIEWS ----------------
def admin_view_crypto_logs():
    # Print crypto_transactions table.
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT id, crypto_name, action, price_in_inr, quantity, timestamp FROM crypto_transactions ORDER BY timestamp DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        print("No crypto transactions yet.")
        return
    print("\n--- CRYPTO TRANSACTIONS ---")
    for r in rows:
        print(f"ID:{r[0]} | {r[1]} | {r[2]} | qty:{r[4]} | price(INR):{r[3]:.2f} | time:{r[5]}")
    print("")


def admin_view_item_logs():
    # Print marketplace_purchases table with item names.
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        "SELECT mp.order_id, mp.item_id, it.name, mp.crypto_used, mp.amount, mp.timestamp "
        "FROM marketplace_purchases mp LEFT JOIN items it ON mp.item_id = it.item_id ORDER BY mp.timestamp DESC"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        print("No marketplace purchases yet.")
        return
    print("\n--- MARKETPLACE PURCHASES ---")
    for r in rows:
        print(f"Order:{r[0]} | ItemID:{r[1]} | Item:{r[2]} | Crypto:{r[3]} | Amount:{r[4]} | Time:{r[5]}")
    print("")


# ---------------- USER VIEWS ----------------
def view_holdings_and_balance(prices=None):
    # Show current INR balance and crypto holdings, with optional INR equivalents.
    balance = get_balance()
    holdings = get_holdings()
    print("\n--- YOUR ACCOUNT ---")
    print(f"INR Balance: INR {balance:.2f}")
    print("Crypto Holdings:")
    for c in CRYPTO_LIST:
        qty = holdings.get(c, 0.0)
        inr_equiv = ""
        if prices and prices.get(c):
            inr_equiv = f" (~INR {qty * prices[c]:.2f})"
        print(f"  - {c}: {qty}{inr_equiv}")
    print("")


# ---------------- MENUS ----------------
def user_menu_text():
    return """
===== USER MENU =====
1. View Crypto Prices (live)
2. Buy Crypto (uses INR)
3. Sell Crypto (receive INR)
4. View My Crypto Holdings and INR Balance
5. View Marketplace Items
6. Buy Item (crypto only)
7. Enter Admin Mode (password required)
0. Exit
"""


def admin_menu_text():
    return """
===== ADMIN MENU =====
1. Add Item
2. Delete Item
3. View All Items
4. View Crypto Transactions Log
5. View Marketplace Purchases Log
6. Set INR Balance (overwrite)
7. Exit Admin Mode
"""


# ---------------- MAIN LOOP ----------------
def main():

    is_admin = False
    while True:
        if is_admin:
            print(admin_menu_text())
            opt = input("Choose: ").strip()
            if opt == "1":
                admin_add_item()
            elif opt == "2":
                admin_delete_item()
            elif opt == "3":
                view_items(show_header=True)
            elif opt == "4":
                admin_view_crypto_logs()
            elif opt == "5":
                admin_view_item_logs()
            elif opt == "6":
                try:
                    val = float(input("Enter new INR balance : ").strip())
                except:
                    print("Invalid value.")
                else:
                    set_balance(val)
                    print("Balance set.")
            elif opt == "7":
                is_admin = False
                print("Exited admin mode.")
            else:
                print("Invalid option.")
        else:
            print(user_menu_text())
            opt = input("Choose: ").strip()
            if opt == "1":
                prices = fetch_prices()
                if prices:
                    print("\n--- Live Prices (INR) ---")
                    for c in CRYPTO_LIST:
                        p = prices.get(c)
                        if p:
                            print(f"{c}: INR {p:.2f}")
                        else:
                            print(f"{c}: price unavailable")
                    print("")
                else:
                    print("Failed to fetch prices.")

            elif opt == "2":
                prices = fetch_prices()
                buy_crypto(prices)

            elif opt == "3":
                prices = fetch_prices()
                sell_crypto(prices)

            elif opt == "4":
                # optionally fetch prices to display INR equivalents
                ask = input("Fetch live prices to show INR equivalents? (y/n): ").strip().lower()
                prices = fetch_prices() if ask == 'y' else None
                view_holdings_and_balance(prices)

            elif opt == "5":
                # show items with live-inr approximate price
                prices = fetch_prices()
                view_items(show_header=True)
                if prices:
                    print("Approx INR price shown per item when available (calculated from live crypto prices).")

            elif opt == "6":
                prices = fetch_prices()
                buy_item(prices)

            elif opt == "7":
                pwd = input("Enter admin password: ").strip()
                if pwd == ADMIN_PASS:
                    is_admin = True
                    print("Admin mode enabled.")
                else:
                    print("Wrong password.")

            elif opt == "0":
                print("Exiting. Goodbye.")
                break
            else:
                print("Invalid option. Choose a valid menu number.")

        # slight pause to avoid spamming
        time.sleep(0.2)


if __name__ == "__main__":
    main()
