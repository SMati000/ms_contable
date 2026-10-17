from collections.abc import Mapping
from itertools import tee

from sqlcipher3 import dbapi2 as Database

from django.db.backends.sqlite3.base import FORMAT_QMARK_REGEX


class SQLCipherCursorWrapper(Database.Cursor):
    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, names)
        return super().execute(query, params)

    def executemany(self, query, param_list):
        peekable, param_list = tee(iter(param_list))
        params = next(peekable, None)
        names = list(params) if params and isinstance(params, Mapping) else None
        query = self.convert_query(query, names)
        return super().executemany(query, param_list)

    @staticmethod
    def convert_query(query, param_names=None):
        if param_names is None:
            return FORMAT_QMARK_REGEX.sub("?", query).replace("%%", "%")
        return query % {name: f":{name}" for name in param_names}
