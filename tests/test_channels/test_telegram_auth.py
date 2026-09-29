import hmac
import hashlib
import json
import time
from urllib.parse import urlencode
from graphtutor.services.telegram_auth import validate_telegram_init_data


def generate_test_init_data(bot_token: str, user_dict: dict, auth_date: int = None) -> str:
    auth_date = auth_date or int(time.time())
    data = {
        "auth_date": str(auth_date),
        "query_id": "AAHdF6IQAAAAAN0XohDhrPzC",
        "user": json.dumps(user_dict, separators=(",", ":")),
    }

    data_check_list = [f"{k}={v}" for k, v in sorted(data.items())]
    data_check_string = "\n".join(data_check_list)

    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    data["hash"] = calc_hash
    return urlencode(data)


def test_valid_telegram_init_data():
    token = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
    user_payload = {"id": 987654321, "first_name": "Arun", "last_name": "Dev", "username": "arundev"}

    raw_init_data = generate_test_init_data(token, user_payload)
    is_valid, user_data, msg = validate_telegram_init_data(raw_init_data, bot_token=token)

    assert is_valid is True
    assert msg == "OK"
    assert user_data is not None
    assert user_data["id"] == 987654321
    assert user_data["first_name"] == "Arun"


def test_tampered_telegram_init_data():
    token = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
    user_payload = {"id": 987654321, "first_name": "Arun"}

    raw_init_data = generate_test_init_data(token, user_payload)
    tampered_data = raw_init_data.replace("987654321", "999999999")

    is_valid, user_data, msg = validate_telegram_init_data(tampered_data, bot_token=token)
    assert is_valid is False
    assert "Invalid HMAC signature" in msg


def test_expired_telegram_init_data():
    token = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
    user_payload = {"id": 987654321, "first_name": "Arun"}

    expired_date = int(time.time()) - (86400 * 5)
    raw_init_data = generate_test_init_data(token, user_payload, auth_date=expired_date)

    is_valid, user_data, msg = validate_telegram_init_data(raw_init_data, bot_token=token, max_age_seconds=86400 * 2)
    assert is_valid is False
    assert "expired" in msg


def test_missing_hash():
    raw = "user=%7B%22id%22%3A123%7D&auth_date=1600000000"
    is_valid, _, msg = validate_telegram_init_data(raw, bot_token="token")
    assert is_valid is False
    assert "Missing hash" in msg
