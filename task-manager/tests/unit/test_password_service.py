import pytest
from app.infrastructure.security.password_service import PasswordService

@pytest.fixture
def svc():
    return PasswordService(rounds=4)

def test_hash_not_plaintext(svc):
    assert svc.hash("secret") != "secret"

def test_different_hashes(svc):
    assert svc.hash("pw") != svc.hash("pw")

def test_bcrypt_format(svc):
    assert svc.hash("pw").startswith("$2")

def test_correct_verifies(svc):
    assert svc.verify("correct", svc.hash("correct")) is True

def test_wrong_fails(svc):
    assert svc.verify("wrong", svc.hash("correct")) is False

def test_case_sensitive(svc):
    h = svc.hash("Password")
    assert svc.verify("password", h) is False
    assert svc.verify("Password", h) is True

def test_unicode(svc):
    pw = "p4ss!öüä"
    assert svc.verify(pw, svc.hash(pw)) is True

def test_no_rehash_needed_fresh(svc):
    assert svc.needs_rehash(svc.hash("pw")) is False
