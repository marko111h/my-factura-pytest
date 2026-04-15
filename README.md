# My-Factura API Test Suite

Automated API tests for the **My-Factura** application using **pytest** and **requests**.

---

## 🐛 Bugs Found

| # | Bug | Endpoint | Status Code |
|---|-----|----------|-------------|
| 1 | Invalid IBAN accepted — consumer created but bankAccounts empty | POST /consumer | 201 |
| 2 | Amount 0 accepted — transaction created with 0.00€ | POST /transaction | 201 |
| 3 | Empty payload returns 500 instead of 400 | POST /consumer | 500 |
| 4 | Very long description (1000+ chars) accepted without validation | POST /transaction | 201 |
| 5 | `bankInformation` field silently ignored — correct field is `bankAccounts` | POST /consumer | 201 |
| 6 | `flgPrimary` typo in API — correct field name is `flgPrimaty` | POST /consumer | - |
| 7 | Duplicate transaction returns `UNKNOWN_ERROR_CODE` instead of specific error code | POST /transaction | 400 |
| 8 | Transaction response missing `id` field — only `idExternal` returned | POST /transaction | 201 |
| 9 | Long description (1000+ chars) accepted — test commented out, no validation on description length | POST /transaction | 201 |

---

## 🧪 Test Coverage

### Consumers — `tests/test_consumers.py`

| Test | Description |
|------|-------------|
| `test_create_person_consumer` | Creates PERSON consumer with valid bank account |
| `test_create_consumer_missing_firstname` | Validates that firstName is required |
| `test_create_consumer_invalid_iban` | ⚠️ BUG: API accepts invalid IBAN silently |
| `test_create_consumer_special_characters` | Tests special characters in name fields |
| `test_empty_payload` | ⚠️ BUG: Empty array returns 500 instead of 400 |
| `test_get_consumer_by_id` | Creates consumer then fetches by ID |
| `test_get_nonexistent_consumer` | Returns 403/404 for unknown ID |
| `test_update_consumer` | Updates consumer first/last name via PUT |
| `test_duplicate_email` | Rejects duplicate email address |
| `test_duplicate_id_external` | Rejects duplicate idExternal |
| `test_bulk_create_5_consumers` | Creates 5 consumers in one request |

### Transactions — `tests/test_transactions.py`

| Test | Description |
|------|-------------|
| `test_create_transaction` | Creates consumer then transaction |
| `test_new_transaction_has_status_new` | Verifies new transaction status is NEW |
| `test_create_transaction_negative_amount` | Rejects negative amount |
| `test_create_transaction_missing_consumer` | Rejects nonexistent consumer ID |
| `test_amount_zero` | ⚠️ BUG: API accepts amount 0.00€ |
| `test_amount_very_large` | Accepts large amount 999999.99€ |
| `test_very_long_description` | Tests 1000+ character description |
| `test_due_date_in_past` | Documents behavior for past due date |
| `test_due_date_today` | Accepts today as due date |
| `test_get_transactions_list` | Fetches transaction list and validates structure |
| `test_duplicate_id_external_transaction` | ✅ FN retry scenario — duplicate idExternal rejected with 400 |
| `test_bulk_transactions_same_consumer` | 10 transactions at once for same consumer — all NEW |

**Total: 23 tests**

---

## 🔍 Key Discoveries

- `POST /consumer` accepts `bankAccounts` array (not `bankInformation`)
- Bank account requires `flgPrimaty: true` (typo in API — intentional)
- Bank account requires `sepaMandateDate` and `sepaMandateId` fields
- `POST /transaction` response does not return `id` — use `idExternal` for tracking
- Duplicate `idExternal` on transaction correctly returns 400 (idempotency works)
- Bulk create supports up to 10 transactions per request for same consumer

---

## 🚀 Setup

### 1. Clone the repository
```bash
git clone https://github.com/marko111h/my-factura-pytest.git
cd my-factura-pytest
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create `.env` file
```
API_KEY=your_api_key_here
```

### 5. Run all tests
```bash
pytest tests/ -v
```

### Run specific file
```bash
pytest tests/test_consumers.py -v
pytest tests/test_transactions.py -v
```

### Run specific test
```bash
pytest tests/test_transactions.py::TestDuplicateTransaction -v -s
```

---

## 📁 Project Structure
```
my-factura-pytest/
├── tests/
│   ├── __init__.py
│   ├── test_consumers.py      # 11 consumer tests
│   └── test_transactions.py   # 12 transaction tests
├── conftest.py                # Shared config and fixtures
├── utils.py                   # IBAN generator + bank info helper
├── requirements.txt           # Dependencies
├── .env                       # API key (not committed)
├── .gitignore
└── README.md
```

---

## 🛠️ Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.13 | Language |
| pytest | 9.0.2 | Test framework |
| requests | 2.32.5 | HTTP client |
| Faker | 40.11.0 | Realistic test data |
| python-dotenv | 1.1.1 | Environment variables |
| schwifty | latest | Valid IBAN generation |