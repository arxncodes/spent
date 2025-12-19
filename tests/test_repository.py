import os

import db.repository as repo


def test_add_transaction_and_list():
    repo.init_db()
    before = len(repo.list_transactions())

    repo.add_transaction({
        "date": "2025-01-01",
        "amount": 12.34,
        "type": "expense",
        "category": "TestCat",
        "payment_method": "Cash",
        "tags": "test",
        "note": "pytest entry",
    })

    after = len(repo.list_transactions())
    assert after == before + 1


def test_export_import_csv(tmp_path):
    repo.init_db()
    out = tmp_path / "out.csv"
    repo.export_transactions_csv(str(out))
    assert out.exists()

    # importing back should return an int (number of rows imported)
    imported = repo.import_transactions_csv(str(out))
    assert isinstance(imported, int)
