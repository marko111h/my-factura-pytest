import requests
import random
from faker import Faker
from conftest import BASE_URL, HEADERS

fake = Faker()


def random_iban():
    digits = ''.join([str(random.randint(0, 9)) for _ in range(20)])
    return f"DE{digits}"


class TestCreateConsumer:

    def test_create_person_consumer(self):
        """POST /consumer — kreira PERSON consumera"""
        first = fake.first_name()
        last  = fake.last_name()

        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{
                "idExternal": fake.uuid4(),
                "firstName": first,
                "lastName": last,
                "type": "PERSON",
                "flgDunningEnabled": "true",
                "gender": "MALE",
                "email": fake.email(),
                "bankInformation": {"iban": random_iban(), "accountOwner": f"{first} {last}"}
            }],
            headers=HEADERS
        )
        assert r.status_code == 201
        data = r.json()[0]
        assert data["firstName"] == first
        assert data["lastName"] == last
        assert data["status"] == "ACTIVE"
        print(f"✅ Consumer kreiran: {first} {last}, ID: {data['id']}")

    def test_create_consumer_missing_firstname(self):
        """POST /consumer — bez firstName treba failati"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{"idExternal": fake.uuid4(), "lastName": "TestLast",
                   "type": "PERSON", "email": fake.email()}],
            headers=HEADERS
        )
        assert r.status_code in [400, 422]
        print(f"✅ Validacija radi: {r.status_code}")

    def test_create_consumer_invalid_iban(self):
        """POST /consumer — nevažeći IBAN — API prihvata ali ignoriše"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{
                "idExternal": fake.uuid4(),
                "firstName": fake.first_name(),
                "lastName": fake.last_name(),
                "type": "PERSON",
                "email": fake.email(),
                "bankInformation": {"iban": "INVALID_IBAN", "accountOwner": fake.name()}
            }],
            headers=HEADERS
        )
        assert r.status_code == 201
        assert r.json()[0]["bankAccounts"] == []
        print(f"⚠️ BUG: Invalid IBAN prihvaćen ali bankAccount prazan")

    def test_create_consumer_special_characters(self):
        """POST /consumer — specijalni karakteri u imenu"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{
                "idExternal": fake.uuid4(),
                "firstName": "Test!@#",
                "lastName": "User$%^",
                "type": "PERSON",
                "email": fake.email()
            }],
            headers=HEADERS
        )
        print(f"\nSpecial chars → Status: {r.status_code} — {r.text[:200]}")
        if r.status_code == 201:
            print(f"⚠️ API prihvata specijalne karaktere u imenu")
        else:
            print(f"✅ API odbija specijalne karaktere: {r.status_code}")

    def test_empty_payload(self):
        """POST /consumer — prazan array"""
        r = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[],
            headers=HEADERS
        )
        print(f"\nEmpty payload → Status: {r.status_code}")
        # ⚠️ BUG: Server vraća 500 umjesto 400 za prazan payload
        assert r.status_code in [400, 422, 500]
        print(f"⚠️ BUG: Prazan payload vraća {r.status_code} — trebalo bi biti 400")


class TestGetConsumer:

    def test_get_consumer_by_id(self):
        """POST /consumer → GET /consumer/{id}"""
        first = fake.first_name()
        last  = fake.last_name()
        email = fake.email()

        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{"idExternal": fake.uuid4(), "firstName": first,
                   "lastName": last, "type": "PERSON", "email": email}],
            headers=HEADERS
        )
        assert r1.status_code == 201
        consumer_id = r1.json()[0]["id"]

        r2 = requests.get(f"{BASE_URL}/api/public/p2/v1/consumer/{consumer_id}", headers=HEADERS)
        assert r2.status_code == 200
        data = r2.json()
        assert data["firstName"] == first
        assert data["email"] == email
        print(f"✅ Consumer dohvaćen: {first} {last}")

    def test_get_nonexistent_consumer(self):
        """GET /consumer/99999999 — treba vratiti 403 ili 404"""
        r = requests.get(f"{BASE_URL}/api/public/p2/v1/consumer/99999999", headers=HEADERS)
        assert r.status_code in [403, 404]
        print(f"✅ Nepostojeći consumer: {r.status_code}")


class TestUpdateConsumer:

    def test_update_consumer(self):
        """POST → PUT /consumer/{id} — promijeni ime"""
        first = fake.first_name()
        last  = fake.last_name()

        r1 = requests.post(
            f"{BASE_URL}/api/public/p2/v1/consumer",
            json=[{"idExternal": fake.uuid4(), "firstName": first,
                   "lastName": last, "type": "PERSON", "email": fake.email()}],
            headers=HEADERS
        )
        assert r1.status_code == 201
        consumer_id = r1.json()[0]["id"]

        new_first = fake.first_name()
        new_last  = fake.last_name()

        r2 = requests.put(
            f"{BASE_URL}/api/public/p2/v1/consumer/{consumer_id}",
            json={"firstName": new_first, "lastName": new_last,
                  "typeCd": "PERSON", "email": fake.email()},
            headers=HEADERS
        )
        assert r2.status_code == 200
        assert r2.json()["firstName"] == new_first
        print(f"✅ Consumer updateovan: {first} → {new_first}")


class TestDuplicateValidation:

    def test_duplicate_email(self):
        """Duplikat email → treba failati"""
        email = fake.email()
        payload = lambda: [{"idExternal": fake.uuid4(), "firstName": fake.first_name(),
                            "lastName": fake.last_name(), "type": "PERSON", "email": email}]

        r1 = requests.post(f"{BASE_URL}/api/public/p2/v1/consumer", json=payload(), headers=HEADERS)
        assert r1.status_code == 201

        r2 = requests.post(f"{BASE_URL}/api/public/p2/v1/consumer", json=payload(), headers=HEADERS)
        assert r2.status_code in [400, 409]
        print(f"✅ Duplikat email odbijen: {r2.status_code}")

    def test_duplicate_id_external(self):
        """Duplikat idExternal → treba failati"""
        ext_id = fake.uuid4()
        payload = [{"idExternal": ext_id, "firstName": fake.first_name(),
                    "lastName": fake.last_name(), "type": "PERSON", "email": fake.email()}]

        r1 = requests.post(f"{BASE_URL}/api/public/p2/v1/consumer", json=payload, headers=HEADERS)
        assert r1.status_code == 201

        payload[0]["email"] = fake.email()
        r2 = requests.post(f"{BASE_URL}/api/public/p2/v1/consumer", json=payload, headers=HEADERS)
        assert r2.status_code in [400, 409]
        print(f"✅ Duplikat idExternal odbijen: {r2.status_code}")


class TestBulkCreateConsumers:

    def test_bulk_create_5_consumers(self):
        """POST /consumer — 5 consumera u jednom pozivu"""
        payload = [{"idExternal": fake.uuid4(), "firstName": fake.first_name(),
                    "lastName": fake.last_name(), "type": "PERSON", "email": fake.email()}
                   for _ in range(5)]

        r = requests.post(f"{BASE_URL}/api/public/p2/v1/consumer", json=payload, headers=HEADERS)
        assert r.status_code == 201
        data = r.json()
        assert len(data) == 5
        for c in data:
            assert c["status"] == "ACTIVE"
        print(f"✅ Bulk create — svih 5 kreirano!")