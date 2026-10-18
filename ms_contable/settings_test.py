import os

from .settings import *


TEST_DATA_DIR = BASE_DIR / "data"
TEST_DATA_DIR.mkdir(exist_ok=True)

DATABASES = {
    **DATABASES,
    "default": {
        **DATABASES["default"],
        "NAME": TEST_DATA_DIR / "db_test.sqlite3",
    },
}

ROOT_URLCONF = "ms_contable.urls_test"
SECRET_KEY = f"{SECRET_KEY}-test"
SESSION_COOKIE_NAME = "ms_contable_test_sessionid"
CSRF_COOKIE_NAME = "ms_contable_test_csrftoken"
TEST_ACCOUNT_USERNAME = os.environ.get("MS_CONTABLE_TEST_USERNAME", "test")
TEST_ACCOUNT_PASSWORD = os.environ.get("MS_CONTABLE_TEST_PASSWORD", "test")
TEST_SERVER_PORT = int(os.environ.get("MS_CONTABLE_TEST_PORT", "8001"))
AUTH_PASSWORD_VALIDATORS = []
LOGOUT_REDIRECT_URL = "/"
