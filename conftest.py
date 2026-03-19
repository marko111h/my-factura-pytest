import pytest
import requests
import os
from faker import Faker
from dotenv import load_dotenv

load_dotenv()
fake = Faker()

BASE_URL = "https://dev-cc.dev.gerniks.net"
API_KEY  = os.getenv("API_KEY")

HEADERS = {
    "API-key": API_KEY,
    "Content-Type": "application/json"
}


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def headers():
    return HEADERS


@pytest.fixture
def new_consumer(headers):
    """Kreira novog consumera i vraća njegov ID"""
    from faker import Faker
    f = Faker()
    r = requests.post(
        f"{BASE_URL}/api/public/p2/v1/consumer",
        json=[{
            "idExternal": f.uuid4(),
            "firstName": f.first_name(),
            "lastName": f.last_name(),
            "type": "PERSON",
            "email": f.email()
        }],
        headers=headers
    )
    assert r.status_code == 201
    return r.json()[0]