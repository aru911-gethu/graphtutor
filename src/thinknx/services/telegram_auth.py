import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl
from typing import Dict, Any, Optional, Tuple
import structlog

from thinknx.config import settings

logger = structlog.get_logger(__name__)


def validate_telegram_init_data(
    init_data_raw: str,
    bot_token: Optional[str] = None,
    max_age_seconds: int = 86400 * 2
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Validates Telegram WebApp initData query string using HMAC-SHA256."""
    token = bot_token or settings.telegram_bot_token
    if not init_data_raw:
        return False, None, "Empty initData"

    try:
        parsed = dict(parse_qsl(init_data_raw, keep_blank_values=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return False, None, "Missing hash in initData"

        auth_date_str = parsed.get("auth_date")
        if auth_date_str:
            auth_date = int(auth_date_str)
            if time.time() - auth_date > max_age_seconds:
                return False, None, "initData has expired"

        if not token:
            if settings.environment == "development" or settings.debug:
                user_json = parsed.get("user")
                user_info = json.loads(user_json) if user_json else {}
                return True, user_info, "Development bypass (no bot token configured)"
            return False, None, "Bot token not configured on server"

        data_check_list = [f"{k}={v}" for k, v in sorted(parsed.items())]
        data_check_string = "\n".join(data_check_list)

        secret_key = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return False, None, "Invalid HMAC signature"

        user_json = parsed.get("user")
        user_info = json.loads(user_json) if user_json else {}
        return True, user_info, "OK"
    except Exception as e:
        logger.warning("Error parsing Telegram initData", error=str(e))
        return False, None, f"Parsing error: {e}"
