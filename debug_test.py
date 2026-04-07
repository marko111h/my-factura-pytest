import requests, os, json
from dotenv import load_dotenv
from schwifty import IBAN
import random
load_dotenv()

BASE_URL = "https://dev-cc.dev.gerniks.net"
HEADERS = {"API-key": os.getenv("API_KEY"), "Content-Type": "application/json"}

# Korak 1: Kreiraj consumera
r1 = requests.post(
    f"{BASE_URL}/api/public/p2/v1/consumer",
    json=[{
        "idExternal": "test-put-bank-001",
        "firstName": "Test",
        "lastName": "BankUser",
        "type": "PERSON",
        "email": "test-put-bank001@test.com"
    }],
    headers=HEADERS
)
consumer = r1.json()[0]
consumer_id = consumer["id"]
version = consumer["version"]
print(f"Consumer kreiran: ID={consumer_id}, version={version}")

# Korak 2: PUT sa bankAccounts
iban_obj = IBAN.generate("DE", bank_code="37040044", account_code=str(random.randint(1000000000, 9999999999)))

r2 = requests.put(
    f"{BASE_URL}/api/public/p2/v1/consumer/{consumer_id}",
    json={
        "firstName": "Test",
        "lastName": "BankUser",
        "typeCd": "PERSON",
        "email": "test-put-bank001@test.com",
        "version": version,
        "bankAccounts": [{
            "iban": str(iban_obj),
            "bic": "COBADEFFXXX",
            "owner": "Test BankUser",
            "bankName": "Commerzbank AG",
            "flgPrimary": True
        }]
    },
    headers=HEADERS
)
print(f"PUT status: {r2.status_code}")
print(f"Response: {json.dumps(r2.json(), indent=2)}")