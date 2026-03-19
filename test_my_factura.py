import pytest
import requests
import random
from faker import Faker
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

fake = Faker()
load_dotenv()

# ─── Config ───
BASE_URL = "https://dev-cc.dev.gerniks.net"
API_KEY  = os.getenv("API_KEY")

HEADERS = {
    "API-key": API_KEY,
    "Content-Type": "application/json"
}

# ─── Helpers ───
def random_iban():
    digits = ''.join([str(random.randint(0, 9)) for _ in range(20)])
    return f"DE{digits}"

def future_date(days=30):
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


# ══════════════════════════════════════════
# TEST 1 — CREATE CONSUMER
# ══════════════════════════════════════════
class TestCreateConsumer:

    def test_create_person_consumer(self):
        """POST /consumer — kreira PERSON consumera"""
        first = fake.first_name()
        last  = fake.last_name()
        iban  = random_iban()

        payload = [{
            "idExternal": fake.uuid4(),
            "firstName": first,
            "lastName": last,
            "type": "PERSON",
            "flgDunningEnabled": "true",
            "gender": "MALE",
            "email": fake.email(),
            "bankInformation": {
                "iban": iban,
                "accountOwner": f"{first} {last}"
            }
        }]

        r = requests.post(f"{BASE_URL}/api/public/p2/v1/consumer", json=payload, headers=HEADERS)

        print(f"\nStatus: {r.status_code}")
        assert r.status_code == 201, f"Unexpected: {r.text}"
        data = r.json()
        assert data[0]["firstName"] == first
        assert data[0]["lastName"] == last
        assert data[0]["status"] == "ACTIVE"
        print(f"✅ Consumer kreiran: {first} {last}, ID: {data[0]['id']}")

    def test_create_consumer_missing_firstname(self):
        """POST /consumer — bez firstName treba vratiti grešku"""
        payload = [{
            "idExternal": fake.uuid4(),
            "lastName": "TestLast",
            "type": "PERSON",
            "email": fake.email()
        }]

        r = requests.post(f"{BASE_URL}/api/public/p2/v1/consumer", json=payload, headers=HEADERS)
        print(f"\nStatus: {r.status_code} — {r.text[:200]}")
        assert r.status_code in [400, 422], f"Trebalo bi failati: {r.text}"
        print(f"✅ Validacija radi — greška: {r.status_code}")

    def test_create_consumer_invalid_iban(self):
        """POST /consumer — nevažeći IBAN"""
        payload = [{
            "idExternal": fake.uuid4(),
            "firstName": fake.first_name(),
            "lastName": fake.last_name(),
            "type": "PERSON",
            "email": fake.email(),
            "bankInformation": {
                "iban": "INVALID_IBAN",
                "accountOwner": fake.name()
            }
        }]

        r = requests.post(f"{BASE_URL}/api/public/p2/v1/consumer", json=payload, headers=HEADERS)
        print(f"\nStatus: {r.status_code} — {r.text[:200]}")
        assert r.status_code == 201, f"Unexpected: {r.text}"
        assert r.json()[0]["bankAccounts"] == [], "⚠️ API prihvata invalid IBAN ali ne sprema bankAccount"
        print(f"✅ Consumer kreiran ali bankAccount prazan — očekivano ponašanje")


# ══════════════════════════════════════════
# TEST 2 — GET CONSUMER
# ══════════════════════════════════════════
class TestGetConsumer:

    def test_get_consumer_by_id(self):
        """POST /consumer → GET /consumer/{id}"""
        first = fake.first_name()
        last  = fake.last_name()
        email = fake.email()

        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{"idExternal": fake.uuid4(), "firstName": first, "lastName": last,
                   "type": "PERSON", "email": email,
                   "bankInformation": {"iban": random_iban(), "accountOwner": f"{first} {last}"}}],
            headers=HEADERS
        )
        assert r1.status_code == 201
        consumer_id = r1.json()[0]["id"]

        r2 = requests.get(f"{BASE_URL}/api/public/p2/v1/consumer/{consumer_id}", headers=HEADERS)
        assert r2.status_code == 200, f"GET failed: {r2.text}"
        data = r2.json()
        assert data["firstName"] == first
        assert data["lastName"] == last
        assert data["email"] == email
        print(f"✅ Consumer dohvaćen: {first} {last}, ID: {consumer_id}")

    def test_get_nonexistent_consumer(self):
        """GET /consumer/99999999 — consumer ne postoji"""
        r = requests.get(f"{BASE_URL}/api/public/p2/v1/consumer/99999999", headers=HEADERS)
        print(f"\nStatus: {r.status_code}")
        assert r.status_code in [403, 404]
        print(f"✅ Nepostojeći consumer odbijen: {r.status_code}")


# ══════════════════════════════════════════
# TEST 3 — UPDATE CONSUMER
# ══════════════════════════════════════════
class TestUpdateConsumer:

    def test_update_consumer(self):
        """POST /consumer → PUT /consumer/{id}"""
        first = fake.first_name()
        last  = fake.last_name()

        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{"idExternal": fake.uuid4(), "firstName": first, "lastName": last,
                   "type": "PERSON", "email": fake.email(),
                   "bankInformation": {"iban": random_iban(), "accountOwner": f"{first} {last}"}}],
            headers=HEADERS
        )
        assert r1.status_code == 201
        consumer_id = r1.json()[0]["id"]

        new_first = fake.first_name()
        new_last  = fake.last_name()

        r2 = requests.put(
            f"{BASE_URL}/api/public/p2/v1/consumer/{consumer_id}",
            json={"firstName": new_first, "lastName": new_last, "typeCd": "PERSON",
                  "email": fake.email(),
                  "bankAccounts": [{"iban": random_iban(), "owner": f"{new_first} {new_last}", "flgPrimary": True}]},
            headers=HEADERS
        )
        print(f"\nPUT Status: {r2.status_code}")
        assert r2.status_code == 200, f"Update failed: {r2.text}"
        assert r2.json()["firstName"] == new_first
        print(f"✅ Consumer updateovan: {first} → {new_first}")


# ══════════════════════════════════════════
# TEST 4 — DUPLICATE idExternal
# ══════════════════════════════════════════
class TestDuplicateIdExternal:

    def test_duplicate_id_external(self):
        """Isti idExternal dva puta → drugi treba failati"""
        external_id = fake.uuid4()

        payload = [{"idExternal": external_id, "firstName": fake.first_name(),
                    "lastName": fake.last_name(), "type": "PERSON", "email": fake.email()}]

        r1 = requests.post(f"{BASE_URL}/api/public/p2/v1/consumer", json=payload, headers=HEADERS)
        assert r1.status_code == 201
        print(f"\n✅ Prvi consumer kreiran")

        payload[0]["email"] = fake.email()
        r2 = requests.post(f"{BASE_URL}/api/public/p2/v1/consumer", json=payload, headers=HEADERS)
        print(f"Drugi pokušaj: {r2.status_code} — {r2.text[:200]}")
        assert r2.status_code in [400, 409]
        print(f"✅ Duplikat idExternal odbijen: {r2.status_code}")


# ══════════════════════════════════════════
# TEST 5 — DUPLICATE EMAIL
# ══════════════════════════════════════════
class TestDuplicateEmail:

    def test_duplicate_email(self):
        """Dva consumera sa istim emailom → drugi treba failati"""
        email = fake.email()

        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{"idExternal": fake.uuid4(), "firstName": fake.first_name(),
                   "lastName": fake.last_name(), "type": "PERSON", "email": email}],
            headers=HEADERS
        )
        assert r1.status_code == 201
        print(f"\n✅ Prvi consumer kreiran sa email: {email}")

        r2 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{"idExternal": fake.uuid4(), "firstName": fake.first_name(),
                   "lastName": fake.last_name(), "type": "PERSON", "email": email}],
            headers=HEADERS
        )
        print(f"Drugi pokušaj: {r2.status_code} — {r2.text[:200]}")
        assert r2.status_code in [400, 409]
        print(f"✅ Duplikat email odbijen: {r2.status_code}")


# ══════════════════════════════════════════
# TEST 6 — TRANSACTION STATUS
# ══════════════════════════════════════════
class TestTransactionStatus:

    def test_new_transaction_has_status_new(self):
        """Nova transakcija mora imati status NEW"""
        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{"idExternal": fake.uuid4(), "firstName": fake.first_name(),
                   "lastName": fake.last_name(), "type": "PERSON", "email": fake.email()}],
            headers=HEADERS
        )
        assert r1.status_code == 201
        consumer_id = r1.json()[0]["id"]

        r2 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 50.0, "description": "Status test", "dueDate": future_date(30),
                   "collectionType": "DO_NOT_COLLECT", "idConsumer": consumer_id, "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        assert r2.status_code == 201
        tx = r2.json()[0]
        assert tx["status"] == "NEW"
        assert tx["amount"] == 50.0
        print(f"✅ Status je NEW — ispravno!")


# ══════════════════════════════════════════
# TEST 7 — AMOUNT EDGE CASES
# ══════════════════════════════════════════
class TestTransactionAmountEdgeCases:

    def setup_method(self):
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{"idExternal": fake.uuid4(), "firstName": fake.first_name(),
                   "lastName": fake.last_name(), "type": "PERSON", "email": fake.email()}],
            headers=HEADERS
        )
        assert r.status_code == 201
        self.consumer_id = r.json()[0]["id"]

    def test_amount_zero(self):
        """⚠️ BUG: API prihvata iznos 0"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 0, "description": "Zero amount", "dueDate": future_date(30),
                   "collectionType": "DO_NOT_COLLECT", "idConsumer": self.consumer_id, "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        print(f"\nAmount 0 → Status: {r.status_code}")
        assert r.status_code == 201
        assert r.json()[0]["amount"] == 0.00
        print(f"⚠️ BUG: Iznos 0 prihvaćen!")

    def test_amount_very_large(self):
        """Veliki iznos 999999.99€ treba biti prihvaćen"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 999999.99, "description": "Large amount", "dueDate": future_date(30),
                   "collectionType": "DO_NOT_COLLECT", "idConsumer": self.consumer_id, "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        print(f"\nAmount 999999.99 → Status: {r.status_code}")
        assert r.status_code in [200, 201]
        print(f"✅ Veliki iznos prihvaćen!")


# ══════════════════════════════════════════
# TEST 8 — END-TO-END
# ══════════════════════════════════════════
class TestConsumerAndTransaction:

    def test_create_consumer_then_transaction(self):
        """POST /consumer → POST /transaction — end-to-end"""
        first = fake.first_name()
        last  = fake.last_name()
        iban  = random_iban()

        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{"idExternal": fake.uuid4(), "firstName": first, "lastName": last,
                   "type": "PERSON", "email": fake.email(),
                   "bankInformation": {"iban": iban, "accountOwner": f"{first} {last}"}}],
            headers=HEADERS
        )
        assert r1.status_code == 201
        consumer_id = r1.json()[0]["id"]
        print(f"\n✅ Consumer kreiran: {first} {last}, ID: {consumer_id}")

        r2 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 30.0, "description": f"Pytest transaction for {first} {last}",
                   "dueDate": future_date(30), "collectionType": "DO_NOT_COLLECT",
                   "idConsumer": consumer_id, "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        assert r2.status_code in [200, 201]
        print(f"✅ Transakcija kreirana za: {first} {last}")


# ══════════════════════════════════════════
# TEST 9 — CREATE TRANSACTION
# ══════════════════════════════════════════
class TestCreateTransaction:

    def test_create_transaction(self):
        """Kreiraj consumera pa transakciju"""
        first = fake.first_name()
        last  = fake.last_name()

        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{"idExternal": fake.uuid4(), "firstName": first, "lastName": last,
                   "type": "PERSON", "email": fake.email(),
                   "bankInformation": {"iban": random_iban(), "accountOwner": f"{first} {last}"}}],
            headers=HEADERS
        )
        assert r1.status_code == 201
        consumer_id = r1.json()[0]["id"]

        r2 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 30.0, "description": f"Pytest test transaction for {first} {last}",
                   "dueDate": future_date(30), "collectionType": "DO_NOT_COLLECT",
                   "idConsumer": consumer_id, "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        assert r2.status_code == 201
        print(f"✅ Transakcija kreirana za {first} {last}")

    def test_create_transaction_negative_amount(self):
        """Negativan iznos treba failati"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": -50.0, "description": "Negative amount", "dueDate": future_date(30),
                   "collectionType": "DO_NOT_COLLECT", "idConsumer": 974051,
                   "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        print(f"\nStatus: {r.status_code}")
        assert r.status_code in [400, 422]
        print(f"✅ Negativan iznos odbijen")

    def test_create_transaction_missing_consumer(self):
        """Nepostojeći consumer treba failati"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 30.0, "description": "Ghost consumer", "dueDate": future_date(30),
                   "collectionType": "DO_NOT_COLLECT", "idConsumer": 99999999,
                   "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        print(f"\nStatus: {r.status_code}")
        assert r.status_code in [400, 404]
        print(f"✅ Nepostojeći consumer odbijen")


# ══════════════════════════════════════════
# TEST 10 — GET TRANSACTIONS LIST
# ══════════════════════════════════════════
class TestGetTransactions:

    def test_get_transactions_list(self):
        """GET /transaction — dohvati listu transakcija"""
        r = requests.get(f"{BASE_URL}/api/public/p2/v1/transaction", headers=HEADERS)

        print(f"\nStatus: {r.status_code}")
        print(f"Response type: {type(r.json())}")
        print(f"Response: {r.text[:300]}")

        assert r.status_code == 200, f"GET failed: {r.text}"
        data = r.json()

        # API može vratiti listu ili objekat sa content/data ključem
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("content") or data.get("data") or data.get("transactions") or []
        else:
            items = []

        assert len(items) > 0, "Lista transakcija je prazna!"
        tx = items[0]
        assert "amount" in tx
        assert "status" in tx
        print(f"✅ Lista dohvaćena — ukupno: {len(items)}, prva: amount={tx['amount']}, status={tx['status']}")


# ══════════════════════════════════════════
# TEST 11 — DUE DATE U PROŠLOSTI
# ══════════════════════════════════════════
class TestTransactionDueDate:

    def test_due_date_in_past(self):
        """dueDate u prošlosti — dokumentujemo ponašanje"""
        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{"idExternal": fake.uuid4(), "firstName": fake.first_name(),
                   "lastName": fake.last_name(), "type": "PERSON", "email": fake.email()}],
            headers=HEADERS
        )
        assert r1.status_code == 201
        consumer_id = r1.json()[0]["id"]

        r2 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 30.0, "description": "Past due date", "dueDate": "2020-01-01",
                   "collectionType": "DO_NOT_COLLECT", "idConsumer": consumer_id, "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        print(f"\nPast dueDate → Status: {r2.status_code} — {r2.text[:200]}")
        if r2.status_code in [200, 201]:
            print(f"⚠️ Server prihvata dueDate u prošlosti!")
        else:
            assert r2.status_code in [400, 422]
            print(f"✅ Server odbija dueDate u prošlosti")

    def test_due_date_today(self):
        """dueDate danas treba proći"""
        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{"idExternal": fake.uuid4(), "firstName": fake.first_name(),
                   "lastName": fake.last_name(), "type": "PERSON", "email": fake.email()}],
            headers=HEADERS
        )
        assert r1.status_code == 201
        consumer_id = r1.json()[0]["id"]

        r2 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{"amount": 30.0, "description": "Today due date", "dueDate": datetime.now().strftime("%Y-%m-%d"),
                   "collectionType": "DO_NOT_COLLECT", "idConsumer": consumer_id, "idExternal": fake.uuid4()}],
            headers=HEADERS
        )
        print(f"\nToday dueDate → Status: {r2.status_code}")
        assert r2.status_code in [200, 201]
        print(f"✅ Današnji dueDate prihvaćen")


# ══════════════════════════════════════════
# TEST 12 — BULK CREATE
# ══════════════════════════════════════════
class TestBulkCreateConsumers:

    def test_bulk_create_5_consumers(self):
        """POST /consumer — 5 consumera u jednom pozivu"""
        payload = [
            {"idExternal": fake.uuid4(), "firstName": fake.first_name(),
             "lastName": fake.last_name(), "type": "PERSON", "email": fake.email()}
            for _ in range(5)
        ]

        r = requests.post(f"{BASE_URL}/api/public/p2/v1/consumer", json=payload, headers=HEADERS)

        print(f"\nBulk create → Status: {r.status_code}")
        assert r.status_code == 201, f"Bulk create failed: {r.text}"
        data = r.json()
        assert len(data) == 5, f"Očekivao 5, dobio: {len(data)}"
        for c in data:
            assert c["status"] == "ACTIVE"
            print(f"✅ {c['firstName']} {c['lastName']}, ID: {c['id']}")
        print(f"✅ Svih 5 consumera kreirano!")