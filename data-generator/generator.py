import time
import psycopg2
from decimal import Decimal, ROUND_DOWN
from faker import Faker
import random
import argparse
import sys
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import hashlib

load_dotenv()

# -----------------------------
# Project configuration
# -----------------------------
NUM_CUSTOMERS = 100
ACCOUNTS_PER_CUSTOMER_MIN = 1
ACCOUNTS_PER_CUSTOMER_MAX = 4
NUM_TRANSACTIONS = 200
MAX_TXN_AMOUNT = 10000.00
CURRENCIES = ["USD", "EUR", "GBP", "INR", "CAD", "AUD"]

# Date range for realistic timestamps (2020-2024)
DATE_START = datetime(2020, 1, 1)
DATE_END = datetime(2024, 12, 31)

# Realistic balance ranges by account type
BALANCE_RANGES = {
    "SAVINGS": (Decimal("500.00"), Decimal("50000.00")),
    "CHECKING": (Decimal("100.00"), Decimal("15000.00")),
    "BUSINESS": (Decimal("5000.00"), Decimal("500000.00")),
    "INVESTMENT": (Decimal("10000.00"), Decimal("1000000.00")),
}

# Transaction amount ranges by type (more realistic)
TXN_AMOUNT_RANGES = {
    "DEPOSIT": (50.00, 5000.00),
    "WITHDRAWAL": (20.00, 2000.00),
    "TRANSFER": (100.00, 10000.00),
    "PAYMENT": (10.00, 500.00),
    "REFUND": (5.00, 200.00),
    "FEE": (1.00, 50.00),
    "INTEREST": (0.50, 500.00),
}

# Transaction statuses with realistic distribution
TXN_STATUSES = {
    "COMPLETED": 85,
    "PENDING": 8,
    "FAILED": 4,
    "CANCELLED": 3,
}

# Loop config
DEFAULT_LOOP = True
SLEEP_SECONDS = 2

# CLI override
parser = argparse.ArgumentParser(description="Run fake data generator")
parser.add_argument("--once", action="store_true", help="Run a single iteration and exit")
args = parser.parse_args()
LOOP = not args.once and DEFAULT_LOOP

# -----------------------------
# Initialize Faker with multiple locales for diversity
# -----------------------------
fake = Faker(['en_US', 'en_GB', 'en_IN', 'en_CA', 'en_AU'])
Faker.seed(None)  # Random seed for variety

# Track used emails to avoid duplicates
used_emails = set()

# -----------------------------
# Helpers
# -----------------------------
def random_money(min_val: Decimal, max_val: Decimal) -> Decimal:
    val = Decimal(str(random.uniform(float(min_val), float(max_val))))
    return val.quantize(Decimal("0.01"), rounding=ROUND_DOWN)

def generate_unique_email(first_name: str, last_name: str) -> str:
    """Generate a unique, realistic email address"""
    domains = [
        "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", 
        "icloud.com", "protonmail.com", "aol.com", "mail.com",
        "live.com", "msn.com", "ymail.com", "inbox.com"
    ]
    
    patterns = [
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()}",
        f"{first_name.lower()}_{last_name.lower()}",
        f"{first_name[0].lower()}{last_name.lower()}",
        f"{first_name.lower()}{last_name[0].lower()}",
        f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}",
        f"{first_name.lower()}{random.randint(1, 999)}",
        f"{last_name.lower()}.{first_name.lower()}",
    ]
    
    for _ in range(100):  # Try up to 100 times
        pattern = random.choice(patterns)
        domain = random.choice(domains)
        email = f"{pattern}@{domain}"
        
        if email not in used_emails:
            used_emails.add(email)
            return email
    
    # Fallback with UUID
    unique_id = hashlib.md5(f"{first_name}{last_name}{datetime.now()}".encode()).hexdigest()[:8]
    email = f"{first_name.lower()}.{unique_id}@{random.choice(domains)}"
    used_emails.add(email)
    return email

def generate_phone() -> str:
    """Generate realistic phone number"""
    formats = [
        f"+1-{random.randint(200,999)}-{random.randint(200,999)}-{random.randint(1000,9999)}",
        f"+44-{random.randint(20,79)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
        f"+91-{random.randint(70,99)}{random.randint(100,999)}-{random.randint(10000,99999)}",
    ]
    return random.choice(formats)

def generate_address() -> dict:
    """Generate a complete address"""
    return {
        "street": fake.street_address(),
        "city": fake.city(),
        "state": fake.state() if hasattr(fake, 'state') else fake.city(),
        "postal_code": fake.postcode(),
        "country": fake.current_country(),
    }

def weighted_choice(choices_dict: dict) -> str:
    """Select based on weighted probability"""
    choices = list(choices_dict.keys())
    weights = list(choices_dict.values())
    return random.choices(choices, weights=weights, k=1)[0]

def generate_random_timestamp(start_date: datetime = None, end_date: datetime = None) -> datetime:
    """Generate a random timestamp between 2020-2024 (or custom range)"""
    start = start_date or DATE_START
    end = end_date or DATE_END
    
    # Calculate total seconds between dates
    time_delta = end - start
    random_seconds = random.randint(0, int(time_delta.total_seconds()))
    
    # Generate random time during business hours (6 AM - 10 PM) for realism
    random_date = start + timedelta(seconds=random_seconds)
    
    # Adjust to realistic hours (weighted towards business hours)
    if random.random() < 0.7:  # 70% during business hours
        hour = random.randint(9, 18)
    else:
        hour = random.randint(6, 22)
    
    return random_date.replace(
        hour=hour,
        minute=random.randint(0, 59),
        second=random.randint(0, 59)
    )

# -----------------------------
# Connect to Postgres
# -----------------------------
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
)
conn.autocommit = True
cur = conn.cursor()

# -----------------------------
# Core generation logic
# -----------------------------
def run_iteration():
    customers = []
    
    # 1. Generate diverse customers
    for _ in range(NUM_CUSTOMERS):
        # Use different name styles for diversity
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        # Add middle name sometimes (30% chance)
        middle_name = fake.first_name() if random.random() < 0.3 else None
        
        email = generate_unique_email(first_name, last_name)
        phone = generate_phone()
        address = generate_address()
        
        # Realistic date of birth (18-80 years old)
        age = random.randint(18, 80)
        dob = datetime.now() - timedelta(days=age * 365 + random.randint(0, 365))
        
        # Customer created date (random between 2020-2024)
        created_at = generate_random_timestamp()
        
        cur.execute(
            """INSERT INTO customers (first_name, last_name, email, created_at) 
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (first_name, last_name, email, created_at),
        )
        customer_id = cur.fetchone()[0]
        customers.append({
            "id": customer_id,
            "created_at": created_at,
            "age": age,
        })

    # 2. Generate accounts with realistic variety
    accounts = []
    account_types = list(BALANCE_RANGES.keys())
    
    for customer in customers:
        customer_id = customer["id"]
        num_accounts = random.randint(ACCOUNTS_PER_CUSTOMER_MIN, ACCOUNTS_PER_CUSTOMER_MAX)
        
        # Ensure at least one checking account for most customers
        customer_account_types = ["CHECKING"] if random.random() < 0.9 else []
        
        # Add additional random account types
        remaining = num_accounts - len(customer_account_types)
        for _ in range(remaining):
            # Weighted selection - savings and checking more common
            weights = [0.35, 0.35, 0.15, 0.15]  # SAVINGS, CHECKING, BUSINESS, INVESTMENT
            account_type = random.choices(account_types, weights=weights, k=1)[0]
            customer_account_types.append(account_type)
        
        for account_type in customer_account_types:
            balance_range = BALANCE_RANGES[account_type]
            initial_balance = random_money(balance_range[0], balance_range[1])
            
            # Older customers tend to have higher balances
            if customer["age"] > 50:
                initial_balance = initial_balance * Decimal("1.5")
            
            # Select currency (USD most common)
            currency = random.choices(
                CURRENCIES, 
                weights=[0.6, 0.15, 0.1, 0.08, 0.04, 0.03], 
                k=1
            )[0]
            
            # Account created after customer (random date after customer creation)
            account_created_at = generate_random_timestamp(
                start_date=customer["created_at"],
                end_date=DATE_END
            )
            
            cur.execute(
                """INSERT INTO accounts (customer_id, account_type, balance, currency, created_at) 
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (customer_id, account_type, initial_balance, currency, account_created_at),
            )
            account_id = cur.fetchone()[0]
            accounts.append({
                "id": account_id,
                "customer_id": customer_id,
                "type": account_type,
                "balance": float(initial_balance),
                "created_at": account_created_at,
            })

    # 3. Generate realistic transactions
    txn_types = list(TXN_AMOUNT_RANGES.keys())
    
    for _ in range(NUM_TRANSACTIONS):
        account = random.choice(accounts)
        account_id = account["id"]
        
        # Weight transaction types realistically
        txn_weights = [0.25, 0.20, 0.25, 0.15, 0.05, 0.05, 0.05]
        txn_type = random.choices(txn_types, weights=txn_weights, k=1)[0]
        
        # Get realistic amount range for this transaction type
        amount_range = TXN_AMOUNT_RANGES[txn_type]
        amount = round(random.uniform(amount_range[0], amount_range[1]), 2)
        
        # Round amounts sometimes (people often transfer round numbers)
        if random.random() < 0.3:
            amount = round(amount / 10) * 10
        if random.random() < 0.1:
            amount = round(amount / 100) * 100
        
        # Ensure minimum amount
        amount = max(amount, 1.00)
        
        # Related account for transfers
        related_account = None
        if txn_type == "TRANSFER" and len(accounts) > 1:
            # Prefer transfers within same customer's accounts (40% chance)
            same_customer_accounts = [a for a in accounts if a["customer_id"] == account["customer_id"] and a["id"] != account_id]
            if same_customer_accounts and random.random() < 0.4:
                related_account = random.choice(same_customer_accounts)["id"]
            else:
                other_accounts = [a for a in accounts if a["id"] != account_id]
                if other_accounts:
                    related_account = random.choice(other_accounts)["id"]
        
        # Weighted status selection
        status = weighted_choice(TXN_STATUSES)
        
        # Transaction date (after account creation)
        txn_timestamp = generate_random_timestamp(
            start_date=account["created_at"],
            end_date=DATE_END
        )
        
        cur.execute(
            """INSERT INTO transactions (account_id, txn_type, amount, related_account_id, status, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (account_id, txn_type, amount, related_account, status, txn_timestamp),
        )

    print(f"✅ Generated {len(customers)} customers, {len(accounts)} accounts, {NUM_TRANSACTIONS} transactions.")
    print(f"   📊 Account types: {dict((t, sum(1 for a in accounts if a['type'] == t)) for t in set(a['type'] for a in accounts))}")

# -----------------------------
# Main loop
# -----------------------------
try:
    iteration = 0
    while True:
        iteration += 1
        print(f"\n{'='*50}")
        print(f"--- Iteration {iteration} started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        run_iteration()
        print(f"--- Iteration {iteration} finished ---")
        print(f"{'='*50}")
        if not LOOP:
            break
        time.sleep(SLEEP_SECONDS)

except KeyboardInterrupt:
    print("\n\n🛑 Interrupted by user. Exiting gracefully...")

finally:
    cur.close()
    conn.close()
    print("✅ Database connection closed.")
    sys.exit(0)