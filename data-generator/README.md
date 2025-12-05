# Data Generator

A realistic fake data generator for the banking database. Creates customers, accounts, and transactions with real-world patterns and distributions.

## 🚀 Quick Start

```bash
# Activate virtual environment
source .venv/bin/activate

# Run continuously (default - generates data every 2 seconds)
python data-generator/generator.py

# Run once and exit
python data-generator/generator.py --once
```

## 📊 What It Generates

### Customers
- **100 customers** per iteration
- Diverse names from multiple locales (US, UK, India, Canada, Australia)
- Unique realistic email addresses (john.smith@gmail.com, jsmith42@outlook.com)
- Age range: 18-80 years

### Accounts
- **1-4 accounts** per customer (variable)
- **Account Types** (weighted distribution):
  | Type | Probability | Balance Range |
  |------|-------------|---------------|
  | SAVINGS | 35% | $500 - $50,000 |
  | CHECKING | 35% | $100 - $15,000 |
  | BUSINESS | 15% | $5,000 - $500,000 |
  | INVESTMENT | 15% | $10,000 - $1,000,000 |

- **Currencies**: USD (60%), EUR (15%), GBP (10%), INR (8%), CAD (4%), AUD (3%)
- Older customers (50+) have 1.5x higher balances

### Transactions
- **200 transactions** per iteration
- **Transaction Types** (weighted):
  | Type | Amount Range |
  |------|--------------|
  | DEPOSIT | $50 - $5,000 |
  | WITHDRAWAL | $20 - $2,000 |
  | TRANSFER | $100 - $10,000 |
  | PAYMENT | $10 - $500 |
  | REFUND | $5 - $200 |
  | FEE | $1 - $50 |
  | INTEREST | $0.50 - $500 |

- **Status Distribution**: COMPLETED (85%), PENDING (8%), FAILED (4%), CANCELLED (3%)
- Round number bias (people often transfer $500 instead of $487.32)
- 40% of transfers stay within same customer's accounts

## ⚙️ Configuration

Edit these variables in `generator.py`:

```python
NUM_CUSTOMERS = 100              # Customers per iteration
ACCOUNTS_PER_CUSTOMER_MIN = 1    # Min accounts per customer
ACCOUNTS_PER_CUSTOMER_MAX = 4    # Max accounts per customer
NUM_TRANSACTIONS = 200           # Transactions per iteration
SLEEP_SECONDS = 2                # Delay between iterations
DEFAULT_LOOP = True              # Run continuously by default
```

## 🔧 Environment Variables

Required in `.env` file (project root):

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=banking
```

## 📦 Dependencies

```bash
pip install psycopg2-binary faker python-dotenv
```

## 🗄️ Database Schema

The generator expects these tables to exist:

```sql
-- customers table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE
);

-- accounts table
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    account_type VARCHAR(50),
    balance DECIMAL(15,2),
    currency VARCHAR(3)
);

-- transactions table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id),
    txn_type VARCHAR(50),
    amount DECIMAL(15,2),
    related_account_id INTEGER REFERENCES accounts(id),
    status VARCHAR(50)
);
```

## 🛑 Stopping the Generator

Press `Ctrl+C` to gracefully stop the generator. It will close the database connection properly.

## 🧹 Clear Generated Data

```bash
docker compose exec postgres psql -U postgres -d banking -c \
  "TRUNCATE TABLE transactions, accounts, customers RESTART IDENTITY CASCADE;"
```
