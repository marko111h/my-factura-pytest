import pytest
import requests
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

# ─── Config ───
BASE_URL = "https://dev-cc.dev.gerniks.net"
API_KEY  = "icFTh8Nx.34b7e7cce387539140adcd5726e08b2f46b00502bc90f2724e76774d7604e010"

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

        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=payload,
            headers=HEADERS
        )

        print(f"\nStatus: {r.status_code}")
        print(f"Response: {r.text[:300]}")

        assert r.status_code == 201, f"Unexpected: {r.text}"
        data = r.json()
        assert len(data) > 0
        assert data[0]["firstName"] == first
        assert data[0]["lastName"] == last
        assert data[0]["status"] == "ACTIVE"
        print(f"✅ Consumer kreiran: {first} {last}, ID: {data[0]['id']}")

    def test_create_consumer_missing_firstname(self):
        """POST /consumer — bez firstName treba vratiti grešku"""
        payload = [{
            "idExternal": f"pytest-{random.randint(100000, 999999)}",
            "lastName": "TestLast",
            "type": "PERSON",
            "email": "test@noemail.com"
        }]

        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=payload,
            headers=HEADERS
        )

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

        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=payload,
            headers=HEADERS
        )

        print(f"\nStatus: {r.status_code} — {r.text[:200]}")
        # API prihvata consumera ali ignoriše invalid IBAN — dokumentujemo ponašanje
        assert r.status_code == 201, f"Unexpected: {r.text}"
        data = r.json()
        # IBAN nije sačuvan jer je invalid
        assert data[0]["bankAccounts"] == [], "⚠️ API prihvata invalid IBAN ali ne sprema bankAccount"
        print(f"✅ Consumer kreiran ali bankAccount prazan zbog invalid IBAN — očekivano ponašanje")


# ══════════════════════════════════════════
# TEST 6 — TRANSACTION STATUS NEW
# ══════════════════════════════════════════
class TestTransactionStatus:

    def test_new_transaction_has_status_new(self):
        """Kreiraj consumera + transakciju → provjeri da je status NEW"""

        # Kreiraj consumera
        first = fake.first_name()
        last  = fake.last_name()

        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{
                "idExternal": fake.uuid4(),
                "firstName": first,
                "lastName": last,
                "type": "PERSON",
                "email": fake.email()
            }],
            headers=HEADERS
        )
        assert r1.status_code == 201
        consumer_id = r1.json()[0]["id"]

        # Kreiraj transakciju
        r2 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{
                "amount": 50.0,
                "description": f"Status test for {first} {last}",
                "dueDate": future_date(30),
                "collectionType": "DO_NOT_COLLECT",
                "idConsumer": consumer_id,
                "idExternal": fake.uuid4()
            }],
            headers=HEADERS
        )
        assert r2.status_code == 201
        tx = r2.json()[0]

        print(f"\n✅ Transakcija kreirana, status: {tx['status']}")
        assert tx["status"] == "NEW", f"Očekivao NEW, dobio: {tx['status']}"
        assert tx["amount"] == 50.0
        assert tx["idConsumer"] == consumer_id
        print(f"✅ Status je NEW — ispravno!")


# ══════════════════════════════════════════
# TEST 7 — DUPLICATE EMAIL
# ══════════════════════════════════════════
class TestDuplicateEmail:

    def test_duplicate_email(self):
        """Dva consumera sa istim emailom → drugi treba failati"""
        email = fake.email()

        payload1 = [{
            "idExternal": fake.uuid4(),
            "firstName": fake.first_name(),
            "lastName": fake.last_name(),
            "type": "PERSON",
            "email": email
        }]

        # Prvi consumer
        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=payload1,
            headers=HEADERS
        )
        assert r1.status_code == 201, f"Prvi create failed: {r1.text}"
        print(f"\n✅ Prvi consumer kreiran sa email: {email}")

        # Drugi consumer sa istim emailom
        payload2 = [{
            "idExternal": fake.uuid4(),
            "firstName": fake.first_name(),
            "lastName": fake.last_name(),
            "type": "PERSON",
            "email": email
        }]

        r2 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=payload2,
            headers=HEADERS
        )
        print(f"Drugi pokušaj status: {r2.status_code} — {r2.text[:200]}")
        assert r2.status_code in [400, 409], f"Trebalo bi failati sa duplikat emailom: {r2.text}"
        print(f"✅ Duplikat email odbijen: {r2.status_code}")


# ══════════════════════════════════════════
# TEST 8 — EDGE CASES: AMOUNT
# ══════════════════════════════════════════
class TestTransactionAmountEdgeCases:

    def setup_method(self):
        """Kreiraj consumera koji se koristi u svim amount testovima"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{
                "idExternal": fake.uuid4(),
                "firstName": fake.first_name(),
                "lastName": fake.last_name(),
                "type": "PERSON",
                "email": fake.email()
            }],
            headers=HEADERS
        )
        assert r.status_code == 201
        self.consumer_id = r.json()[0]["id"]

    def test_amount_zero(self):
        """Transakcija sa iznosom 0 — šta server vraća?"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{
                "amount": 0,
                "description": "Zero amount test",
                "dueDate": future_date(30),
                "collectionType": "DO_NOT_COLLECT",
                "idConsumer": self.consumer_id,
                "idExternal": fake.uuid4()
            }],
            headers=HEADERS
        )
        print(f"\nAmount 0 → Status: {r.status_code} — {r.text[:200]}")
        # ⚠️ BUG: API prihvata transakciju sa iznosom 0 — trebalo bi odbiti!
        assert r.status_code == 201, f"API prihvata iznos 0"
        tx = r.json()[0]
        assert tx["amount"] == 0.00
        print(f"⚠️ BUG: Iznos 0 prihvaćen — status: {r.status_code}, amount: {tx['amount']}")

    def test_amount_very_large(self):
        """Transakcija sa vrlo velikim iznosom 999999.99€"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=[{
                "amount": 999999.99,
                "description": "Very large amount test",
                "dueDate": future_date(30),
                "collectionType": "DO_NOT_COLLECT",
                "idConsumer": self.consumer_id,
                "idExternal": fake.uuid4()
            }],
            headers=HEADERS
        )
        print(f"\nAmount 999999.99 → Status: {r.status_code} — {r.text[:200]}")
        assert r.status_code in [200, 201], f"Veliki iznos trebalo bi prihvatiti: {r.text}"
        print(f"✅ Veliki iznos prihvaćen: {r.status_code}")



class TestGetConsumer:

    def test_get_consumer_by_id(self):
        """POST /consumer → GET /consumer/{id} — provjeri da su podaci isti"""

        first = fake.first_name()
        last  = fake.last_name()
        email = fake.email()

        # Kreiraj consumera
        payload = [{
            "idExternal": fake.uuid4(),
            "firstName": first,
            "lastName": last,
            "type": "PERSON",
            "email": email,
            "bankInformation": {
                "iban": random_iban(),
                "accountOwner": f"{first} {last}"
            }
        }]

        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=payload,
            headers=HEADERS
        )
        assert r1.status_code == 201, f"Create failed: {r1.text}"
        consumer_id = r1.json()[0]["id"]
        print(f"\n✅ Consumer kreiran: {first} {last}, ID: {consumer_id}")

        # Dohvati consumera po ID-u
        r2 = requests.get(
            f"{BASE_URL}/api/public/p2/v1/consumer/{consumer_id}",
            headers=HEADERS
        )

        print(f"GET Status: {r2.status_code}")
        print(f"GET Response: {r2.text[:300]}")

        assert r2.status_code == 200, f"GET failed: {r2.text}"
        data = r2.json()
        assert data["firstName"] == first
        assert data["lastName"] == last
        assert data["email"] == email
        assert data["id"] == consumer_id
        print(f"✅ Consumer dohvaćen i podaci se podudaraju!")

    def test_get_nonexistent_consumer(self):
        """GET /consumer/99999999 — consumer ne postoji → 404"""
        r = requests.get(
            f"{BASE_URL}/api/public/p2/v1/consumer/99999999",
            headers=HEADERS
        )
        print(f"\nStatus: {r.status_code} — {r.text[:200]}")
        assert r.status_code in [403, 404], f"Trebalo bi biti 403 ili 404: {r.text}"
        print(f"✅ Nepostojeći consumer odbijen: {r.status_code}")


# ══════════════════════════════════════════
# TEST 3 — DUPLICATE idExternal
# ══════════════════════════════════════════
class TestDuplicateIdExternal:

    def test_duplicate_id_external(self):
        """Isti idExternal dva puta → drugi treba failati"""
        external_id = fake.uuid4()

        payload = [{
            "idExternal": external_id,
            "firstName": fake.first_name(),
            "lastName": fake.last_name(),
            "type": "PERSON",
            "email": fake.email(),
        }]

        # Prvi put — treba proći
        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=payload,
            headers=HEADERS
        )
        assert r1.status_code == 201, f"Prvi create failed: {r1.text}"
        print(f"\n✅ Prvi consumer kreiran sa idExternal: {external_id}")

        # Drugi put sa istim idExternal — treba failati
        payload[0]["email"] = fake.email()  # drugačiji email
        r2 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=payload,
            headers=HEADERS
        )
        print(f"Drugi pokušaj status: {r2.status_code} — {r2.text[:200]}")
        assert r2.status_code in [400, 409], f"Trebalo bi failati sa duplikatom: {r2.text}"
        print(f"✅ Duplikat idExternal odbijen: {r2.status_code}")


# ══════════════════════════════════════════
# TEST 4 — UPDATE CONSUMER
# ══════════════════════════════════════════
class TestUpdateConsumer:

    def test_update_consumer(self):
        """POST /consumer → PUT /consumer/{id} — promijeni ime i provjeri"""

        # Kreiraj consumera
        first = fake.first_name()
        last  = fake.last_name()

        payload = [{
            "idExternal": fake.uuid4(),
            "firstName": first,
            "lastName": last,
            "type": "PERSON",
            "email": fake.email(),
            "bankInformation": {
                "iban": random_iban(),
                "accountOwner": f"{first} {last}"
            }
        }]

        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=payload,
            headers=HEADERS
        )
        assert r1.status_code == 201, f"Create failed: {r1.text}"
        consumer_id = r1.json()[0]["id"]
        print(f"\n✅ Consumer kreiran: {first} {last}, ID: {consumer_id}")

        # Update — novo ime
        new_first = fake.first_name()
        new_last  = fake.last_name()

        update_payload = {
            "firstName": new_first,
            "lastName": new_last,
            "typeCd": "PERSON",
            "email": fake.email(),
            "bankAccounts": [{
                "iban": random_iban(),
                "owner": f"{new_first} {new_last}",
                "flgPrimary": True
            }]
        }

        r2 = requests.put(
            f"{BASE_URL}/api/public/p2/v1/consumer/{consumer_id}",
            json=update_payload,
            headers=HEADERS
        )

        print(f"PUT Status: {r2.status_code}")
        print(f"PUT Response: {r2.text[:300]}")

        assert r2.status_code == 200, f"Update failed: {r2.text}"
        data = r2.json()
        assert data["firstName"] == new_first
        assert data["lastName"] == new_last
        print(f"✅ Consumer updateovan: {first} {last} → {new_first} {new_last}")


# ══════════════════════════════════════════
# TEST 5 — END-TO-END: CREATE CONSUMER + TRANSACTION
# ══════════════════════════════════════════
class TestConsumerAndTransaction:

    def test_create_consumer_then_transaction(self):
        """POST /consumer → uzmi ID → POST /transaction za tog consumera"""

        # ─── Korak 1: Kreiraj consumera ───
        first = fake.first_name()
        last  = fake.last_name()
        iban  = random_iban()

        consumer_payload = [{
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

        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=consumer_payload,
            headers=HEADERS
        )

        assert r1.status_code == 201, f"Consumer failed: {r1.text}"
        consumer_id = r1.json()[0]["id"]
        print(f"\n✅ Consumer kreiran: {first} {last}, ID: {consumer_id}")

        # ─── Korak 2: Kreiraj transakciju za tog consumera ───
        tx_payload = [{
            "amount": 30.0,
            "amountNet": 25.50,
            "vatRate": 5,
            "vatAmount": 1.5,
            "description": f"Pytest transaction for {first} {last}",
            "dueDate": future_date(30),
            "flgTermination": False,
            "collectionType": "DO_NOT_COLLECT",
            "idConsumer": consumer_id,
            "idExternal": f"pytest-tx-{random.randint(100000, 999999)}"
        }]

        r2 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=tx_payload,
            headers=HEADERS
        )

        print(f"Status: {r2.status_code}")
        print(f"Response: {r2.text[:300]}")

        assert r2.status_code in [200, 201], f"Transaction failed: {r2.text}"
        tx_data = r2.json()
        assert len(tx_data) > 0
        print(f"✅ Transakcija kreirana za consumera ID: {consumer_id}")


# ══════════════════════════════════════════
# TEST 3 — CREATE TRANSACTION
# ══════════════════════════════════════════
class TestCreateTransaction:

    def test_create_transaction(self):
        """POST /consumer → POST /transaction — kreira consumera pa transakciju"""

        # ─── Kreiraj consumera ───
        first = fake.first_name()
        last  = fake.last_name()
        iban  = random_iban()

        consumer_payload = [{
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

        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=consumer_payload,
            headers=HEADERS
        )
        assert r1.status_code == 201, f"Consumer failed: {r1.text}"
        consumer_id = r1.json()[0]["id"]
        print(f"\n✅ Consumer kreiran: {first} {last}, ID: {consumer_id}")

        # ─── Kreiraj transakciju ───
        payload = [{
            "amount": 30.0,
            "amountNet": 25.50,
            "vatRate": 5,
            "vatAmount": 1.5,
            "description": f"Pytest test transaction for {first} {last}",
            "dueDate": future_date(30),
            "flgTermination": False,
            "collectionType": "DO_NOT_COLLECT",
            "idConsumer": consumer_id,
            "idExternal": fake.uuid4()
        }]

        r2 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=payload,
            headers=HEADERS
        )

        print(f"Status: {r2.status_code}")
        print(f"Response: {r2.text[:300]}")

        assert r2.status_code == 201, f"Transaction failed: {r2.text}"
        assert len(r2.json()) > 0
        print(f"✅ Transakcija kreirana za {first} {last}")

    def test_create_transaction_negative_amount(self):
        """POST /transaction — negativan iznos treba failati"""
        payload = [{
            "amount": -50.0,
            "description": "Negative amount test",
            "dueDate": future_date(30),
            "collectionType": "DO_NOT_COLLECT",
            "idConsumer": 974051,
            "idExternal": f"pytest-neg-{random.randint(100000, 999999)}"
        }]

        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=payload,
            headers=HEADERS
        )

        print(f"\nStatus: {r.status_code} — {r.text[:200]}")
        assert r.status_code in [400, 422], f"Trebalo bi failati: {r.text}"
        print(f"✅ Negativan iznos odbijen")

    def test_create_transaction_missing_consumer(self):
        """POST /transaction — consumer ne postoji"""
        payload = [{
            "amount": 30.0,
            "description": "Ghost consumer test",
            "dueDate": future_date(30),
            "collectionType": "DO_NOT_COLLECT",
            "idConsumer": 99999999,
            "idExternal": f"pytest-ghost-{random.randint(100000, 999999)}"
        }]

        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/transaction",
            json=payload,
            headers=HEADERS
        )

        print(f"\nStatus: {r.status_code} — {r.text[:200]}")
        assert r.status_code in [400, 404], f"Trebalo bi failati: {r.text}"
        print(f"✅ Nepostojeći consumer odbijen")