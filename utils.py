# utils.py
from schwifty import IBAN
import random
from datetime import datetime

def generate_valid_german_iban() -> str:
    bank_codes = ["37040044", "20030000", "10010010"]
    bank_code = random.choice(bank_codes)
    account = str(random.randint(1000000000, 9999999999))
    return str(IBAN.generate("DE", bank_code=bank_code, account_code=account))

def valid_bank_information(owner_name: str) -> list:
    return [{
        "iban": generate_valid_german_iban(),
        "bic": "COBADEFFXXX",
        "owner": owner_name,
        "bankName": "Commerzbank AG",
        "flgPrimaty": True,          # ← typo je namjeran, tako API očekuje
        "flgConsumer360": True,
        "flgVerify": True,
        "sepaMandateDate": datetime.now().strftime("%Y-%m-%d"),
        "sepaMandateId": str(random.randint(10000000000, 99999999999))
    }]