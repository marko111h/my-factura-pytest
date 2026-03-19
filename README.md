# My-Factura API Test Suite

Automated API tests for My-Factura application using **pytest** and **requests**.

## 🧪 Test Coverage

| Test Class | Tests | Description |
|------------|-------|-------------|
| `TestCreateConsumer` | 3 | Create consumer — positive, missing firstName, invalid IBAN |
| `TestTransactionStatus` | 1 | New transaction has status NEW |
| `TestDuplicateEmail` | 1 | Duplicate email validation |
| `TestTransactionAmountEdgeCases` | 2 | Amount = 0 (bug), very large amount |
| `TestGetConsumer` | 2 | Get by ID, nonexistent consumer |
| `TestDuplicateIdExternal` | 1 | Duplicate idExternal validation |
| `TestUpdateConsumer` | 1 | Update consumer fields |
| `TestConsumerAndTransaction` | 1 | End-to-end: create consumer + transaction |
| `TestCreateTransaction` | 3 | Create, negative amount, missing consumer |

**Total: 15 tests**

## 🐛 Bugs Found

| Bug | Description | Status |
|-----|-------------|--------|
| Invalid IBAN accepted | API accepts consumer with invalid IBAN without error | Open |
| Amount = 0 accepted | API creates transaction with amount 0.00€ | Open |

## 🚀 Setup

### 1. Clone the repository
```bash
git clone https://github.com/marko111h/my-factura-pytest.git
cd my-factura-pytest
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

### 3. Install dependencies
```bash
pip install pytest requests faker python-dotenv
```

### 4. Create .env file
```bash
# Create .env file and add your API key
API_KEY=your_api_key_here
```

### 5. Run tests
```bash
pytest test_my_factura.py -v
```

## 📁 Project Structure

```
my-factura-pytest/
├── test_my_factura.py   # All API tests
├── .env                 # API key (not committed)
├── .gitignore
└── README.md
```

## 🛠️ Tech Stack

- **Python** 3.13
- **pytest** 9.0.2
- **requests** 2.32.5
- **Faker** 40.11.0
- **python-dotenv** 1.1.1