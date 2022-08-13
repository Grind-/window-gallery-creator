'''
Created on 24.06.2022

@author: jhirte
'''
import binascii
import os

import requests

URL = 'https://demo.cashlink.de/api/external'

CLIENT_ID = 'a6KWuDAf4DFChjbCGaddQ5685mAxhPcy1qfpu7AE'
CLIENT_SECRET = 'wMhi3PRwJnRMdPuoW0NVG3uZr28DoilzGgTscNsugv5ph8hyDhEq9YeBgtbULfAYsrMAQZaRZCEbVBdXfFMHdnl7HxjVqjPHnu47GMRVEcNWs1tWHcxPS91GZFkK5aVN'

WALLET_ADDRESS = '<wallet address of the investor>'


def authenticate():
    r = requests.post(f'{URL}/oauth/token', data={
        'grant_type': 'client_credentials',
        'scope': 'investors:write investors:read investments:write investments:read documents:write',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    })
    assert r.status_code == 200, r.content
    return r.json()['access_token']


def make_key():
    return binascii.hexlify(os.urandom(8)).decode()


if __name__ == '__main__':
    headers = {
        'Authorization': f'Bearer {authenticate()}',
    }

    # Note: in normal usage, you would use an idempotency key that correlates
    # to the internal object on the customer side.

    # create investor
    r = requests.post(
        f'{URL}/v2/investors/',
        json={
            "natural_person": {
                "salutation": "MR",
                "forename": "Peter",
                "surname": "Parker",
                "birth_date": "2020-08-10",
                "birth_place": "New York",
                "citizenship": "DEU",
                "street": "Hauptstr. 37",
                "city": "Frankfurt",
                "zip": "60316",
                "country": "DEU",
                "phone": "+49 123 456 789"
            },
            "bank_account": {
                "account_holder": "Peter Parker",
                "iban": 'DE53500105173569146251',
                "bic": "GENODEF1ERG",
                "bank": "Commerzbank Frankfurt",
                "country": "DEU",
                "currency": "EUR"
            },
            "tax_information": {
                "tax_identification_number": "12345678",
                "non_assessment_certificate": True
            },
            "is_beneficiary": True,
            "pep_status": False,
            "account_setup_accepted_at": "2021-05-06T07:14:13.630308+00:00"
        },

        headers={**headers, 'X-Idempotency-Key': make_key()}
    )
    assert r.status_code < 300, r.content
    investor_id = r.json()['id']

    # add an identification to created investor
    # 1. upload the legitimation protocol document to reference it later
    r = requests.post(
        f'{URL}/v2/documents/',
        files={'file': ('protocol.pdf', b'ASD', 'application/pdf')},
        headers={**headers, 'X-Idempotency-Key': make_key()}
    )
    assert r.status_code < 300, r.content
    doc_id = r.json()['id']
    # 2. create the identification for investor
    r = requests.post(
        f'{URL}/v2/investors/{investor_id}/identifications/',
        json={
            "document_type": "IDCARD",
            "document_id": "ID123456",
            "document_issuer": "Buergeramt Frankfurt",
            "document_valid_from": "2020-08-10",
            "document_valid_to": "2025-08-10",
            "identity_provider": "POSTIDENT",
            "legitimation_process_id": "string",
            "legitimation_protocol_id": doc_id,
            "verified_at": "2020-08-10T14:06:22.134Z"
        },
        headers={**headers, 'X-Idempotency-Key': make_key()}
    )
    assert r.status_code < 300, r.content
    identification_id = r.json()['id']

    # create a wallet for investor ...
    r = requests.post(
        f'{URL}/v2/investors/{investor_id}/wallets/eth-generic/',
        json={"address": "{WALLET_ADDRESS}"},
        headers={**headers, 'X-Idempotency-Key': make_key()}
    )
    assert r.status_code < 300, r.content
    wallet_id = r.json()['id']

    # Retrieve information about the investor
    r = requests.get(
        f'{URL}/v2/investors/{investor_id}/',
        headers={**headers}
    )
    assert r.status_code < 300, r.content
    print(r.json())
