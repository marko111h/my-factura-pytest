import requests
from faker import Faker
from datetime import datetime, timedelta
from conftest import BASE_URL, HEADERS

fake = Faker()


def future_date(days=30):
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


def create_consumer():
    """Helper — kreira consumera i vraća ID"""
    r = requests.post(
        f"{BASE_URL}/api/public/p2/v1/consumer",
        json=[{"idExternal": fake.uuid4(), "firstName": fake.first_name(),
               "lastName": fake.last_name(), "type": "PERSON", "email": fake.email()}],
        headers=HEADERS
    )
    assert r.status_code == 201
    return r.json()[0]["id"]


class TestCreateTransaction:

    def test_create_transaction(self):
        """Kreiraj consumera → kreiraj transakciju"""
        first = fake.first_name()
        last  = fake.last_name()
        consumer_id = create_consumer()

        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 30.0, "description": f"Pytest transaction for {first} {last}",
                   "dueDate": future_date(30), "collectionType": "DO_NOT_COLLECT",
                   "idConsumer": consumer_id, "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        assert r.status_code == 201
        print(f"✅ Transakcija kreirana za consumer ID: {consumer_id}")

    def test_new_transaction_has_status_new(self):
        """Nova transakcija mora imati status NEW"""
        consumer_id = create_consumer()

        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 50.0, "description": "Status test",
                   "dueDate": future_date(30), "collectionType": "DO_NOT_COLLECT",
                   "idConsumer": consumer_id, "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        assert r.status_code == 201
        tx = r.json()[0]
        assert tx["status"] == "NEW"
        assert tx["amount"] == 50.0
        print(f"✅ Status je NEW!")

    def test_create_transaction_negative_amount(self):
        """Negativan iznos treba failati"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": -50.0, "description": "Negative amount",
                   "dueDate": future_date(30), "collectionType": "DO_NOT_COLLECT",
                   "idConsumer": 974051, "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        assert r.status_code in [400, 422]
        print(f"✅ Negativan iznos odbijen")

    def test_create_transaction_missing_consumer(self):
        """Nepostojeći consumer treba failati"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 30.0, "description": "Ghost consumer",
                   "dueDate": future_date(30), "collectionType": "DO_NOT_COLLECT",
                   "idConsumer": 99999999, "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        assert r.status_code in [400, 404]
        print(f"✅ Nepostojeći consumer odbijen")


class TestTransactionAmountEdgeCases:

    def setup_method(self):
        self.consumer_id = create_consumer()

    def test_amount_zero(self):
        """⚠️ BUG: API prihvata iznos 0"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 0, "description": "Zero amount", "dueDate": future_date(30),
                   "collectionType": "DO_NOT_COLLECT", "idConsumer": self.consumer_id,
                   "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        assert r.status_code == 201
        assert r.json()[0]["amount"] == 0.00
        print(f"⚠️ BUG: Iznos 0 prihvaćen!")

    def test_amount_very_large(self):
        """Veliki iznos 999999.99€ treba biti prihvaćen"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 999999.99, "description": "Large amount", "dueDate": future_date(30),
                   "collectionType": "DO_NOT_COLLECT", "idConsumer": self.consumer_id,
                   "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        assert r.status_code in [200, 201]
        print(f"✅ Veliki iznos prihvaćen!")

    def test_very_long_description(self):
        """Opis od 1000+ karaktera"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 30.0, "description": "A" * 1000, "dueDate": future_date(30),
                   "collectionType": "DO_NOT_COLLECT", "idConsumer": self.consumer_id,
                   "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        print(f"\nLong description → Status: {r.status_code}")
        if r.status_code in [200, 201]:
            print(f"⚠️ API prihvata 1000+ karaktera u opisu")
        else:
            print(f"✅ API odbija predugačak opis: {r.status_code}")


class TestTransactionDueDate:

    def test_due_date_in_past(self):
        """dueDate u prošlosti — dokumentujemo ponašanje"""
        consumer_id = create_consumer()

        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 30.0, "description": "Past due date", "dueDate": "2020-01-01",
                   "collectionType": "DO_NOT_COLLECT", "idConsumer": consumer_id,
                   "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        print(f"\nPast dueDate → Status: {r.status_code}")
        if r.status_code in [200, 201]:
            print(f"⚠️ Server prihvata dueDate u prošlosti!")
        else:
            print(f"✅ Server odbija dueDate u prošlosti")

    def test_due_date_today(self):
        """dueDate danas treba proći"""
        consumer_id = create_consumer()

        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 30.0, "description": "Today due date",
                   "dueDate": datetime.now().strftime("%Y-%m-%d"),
                   "collectionType": "DO_NOT_COLLECT", "idConsumer": consumer_id,
                   "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        assert r.status_code in [200, 201]
        print(f"✅ Današnji dueDate prihvaćen")


class TestGetTransactions:

    def test_get_transactions_list(self):
        """GET /transaction — dohvati listu"""
        r = requests.get(f"{BASE_URL}/api/public/p2/v1/transaction", headers=HEADERS)
        assert r.status_code == 200

        data = r.json()
        items = data if isinstance(data, list) else (
            data.get("content") or data.get("data") or data.get("transactions") or []
        )
        assert len(items) > 0
        tx = items[0]
        assert "amount" in tx
        assert "status" in tx
        print(f"✅ Lista dohvaćena — ukupno: {len(items)}")