from __future__ import annotations

from datetime import datetime
from sys import version_info
from typing import TYPE_CHECKING, Any, get_origin

import orjson as json
from pydantic import BaseModel

from panther.db.connections import db
from panther.db.queries.base_queries import BaseQuery
from panther.exceptions import DatabaseError

if TYPE_CHECKING:
    from collections.abc import Iterable

if version_info >= (3, 11):
    from typing import Self
else:
    from typing import TypeVar

    Self = TypeVar('Self', bound='BaseSQLiteQuery')


class SQLiteCursor:
    def __init__(self, results: list):
        self._results = results
        self._index = 0

    def __aiter__(self):
        self._index = 0
        return self

    async def __anext__(self):
        try:
            result = self._results[self._index]
        except IndexError:
            raise StopAsyncIteration
        self._index += 1
        return result

    def __iter__(self):
        return iter(self._results)

    def __len__(self):
        return len(self._results)

    def __getitem__(self, index: int | slice):
        return self._results[index]

    def skip(self, count: int) -> Self:
        self._results = self._results[count:]
        return self

    def limit(self, count: int) -> Self:
        if count < 0:
            count = abs(count)
        self._results = self._results[:count]
        return self

    def sort(self, key_or_list, direction: int | None = None) -> Self:
        sort_fields = key_or_list if isinstance(key_or_list, list) else [(key_or_list, direction or 1)]
        for field_name, sort_direction in reversed(sort_fields):
            self._results.sort(key=lambda obj: getattr(obj, field_name), reverse=sort_direction == -1)
        return self


class BaseSQLiteQuery(BaseQuery):
    @classmethod
    def table_name(cls) -> str:
        return db.session.table_name(cls)

    @classmethod
    def _quote(cls, name: str) -> str:
        return f'"{name.replace(chr(34), chr(34) * 2)}"'

    @classmethod
    def _field_type(cls, field_name: str) -> Any:
        field = cls.model_fields[field_name]
        return db.session._unwrap_annotation(field.annotation)  # noqa: SLF001

    @classmethod
    def _column_name(cls, field_name: str) -> str:
        if field_name == 'id':
            return 'id'
        if field_name in cls.model_fields and db.session._is_model(cls._field_type(field_name)):  # noqa: SLF001
            return f'{field_name}_id'
        return field_name

    @classmethod
    def _where(cls, _filter: dict | None = None, /, **kwargs) -> tuple[str, tuple]:
        filters = cls._merge(_filter, kwargs)
        if not filters:
            return '', ()

        conditions = []
        params = []
        for field_name, value in filters.items():
            if field_name.startswith('$'):
                raise DatabaseError(f'{field_name} is not supported in SQLite filters.')
            if field_name == '_id':
                field_name = 'id'
            column_name = cls._column_name(field_name)
            conditions.append(f'{cls._quote(column_name)} = ?')
            params.append(cls._serialize_value(value))
        return f' WHERE {" AND ".join(conditions)}', tuple(params)

    @classmethod
    def _serialize_value(cls, value):
        from panther.db import Model

        if isinstance(value, Model):
            return value.id
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, BaseModel):
            return json.dumps(value.model_dump()).decode()
        if isinstance(value, (dict, list)):
            return json.dumps(value).decode()
        if isinstance(value, bool):
            return int(value)
        return value

    @classmethod
    def _deserialize_value(cls, field_name: str, value):
        if value is None:
            return None

        field_type = cls._field_type(field_name)
        origin = get_origin(field_type)
        if origin in (list, dict) or (isinstance(field_type, type) and issubclass(field_type, BaseModel)):
            if not isinstance(value, (str, bytes, bytearray, memoryview)):
                return value
            return json.loads(value)
        if field_type is bool:
            return bool(value)
        return value

    @classmethod
    async def _create_model_instance(cls, document: dict, is_updating: bool = False) -> Self:  # noqa: FBT001, FBT002
        final_document = {}
        for field_name in cls.model_fields:
            if field_name == 'id':
                final_document['id'] = document.get('id')
                continue

            field_type = cls._field_type(field_name)
            if db.session._is_model(field_type):  # noqa: SLF001
                related_id = document.get(f'{field_name}_id', document.get(field_name))
                if related_id is None and not cls.model_fields[field_name].is_required():
                    continue
                final_document[field_name] = related_id
            elif field_name in document:
                if document[field_name] is None and not cls.model_fields[field_name].is_required():
                    continue
                final_document[field_name] = cls._deserialize_value(field_name, document[field_name])

        return await super()._create_model_instance(document=final_document, is_updating=is_updating)

    @classmethod
    async def _row_to_model(cls, row) -> Self:
        return await cls._create_model_instance(document=dict(row))

    @classmethod
    def _document_to_columns(cls, document: dict) -> tuple[list[str], list]:
        columns = []
        values = []
        for field_name, value in document.items():
            if field_name in ('id', '_id'):
                columns.append('id')
                values.append(value)
                continue

            columns.append(cls._column_name(field_name))
            values.append(cls._serialize_value(value))
        return columns, values

    @classmethod
    async def find_one(cls, _filter: dict | None = None, /, **kwargs) -> Self | None:
        where, params = cls._where(_filter, **kwargs)
        row = await db.session.fetchone(f'SELECT * FROM {cls._quote(cls.table_name())}{where} LIMIT 1', params)
        return await cls._row_to_model(row) if row else None

    @classmethod
    async def find(cls, _filter: dict | None = None, /, **kwargs) -> SQLiteCursor:
        where, params = cls._where(_filter, **kwargs)
        rows = await db.session.fetchall(f'SELECT * FROM {cls._quote(cls.table_name())}{where}', params)
        return SQLiteCursor([await cls._row_to_model(row) for row in rows])

    @classmethod
    async def first(cls, _filter: dict | None = None, /, **kwargs) -> Self | None:
        return await cls.find_one(_filter, **kwargs)

    @classmethod
    async def last(cls, _filter: dict | None = None, /, **kwargs) -> Self | None:
        where, params = cls._where(_filter, **kwargs)
        query = f'SELECT * FROM {cls._quote(cls.table_name())}{where} ORDER BY rowid DESC LIMIT 1'
        row = await db.session.fetchone(query, params)
        return await cls._row_to_model(row) if row else None

    @classmethod
    async def aggregate(cls, *args, **kwargs):
        msg = 'aggregate() is not supported in `SQLite`.'
        raise DatabaseError(msg) from None

    @classmethod
    async def count(cls, _filter: dict | None = None, /, **kwargs) -> int:
        where, params = cls._where(_filter, **kwargs)
        row = await db.session.fetchone(f'SELECT COUNT(*) AS count FROM {cls._quote(cls.table_name())}{where}', params)
        return row['count']

    @classmethod
    async def insert_one(cls, document: dict) -> str:
        document = {'id': db.session.generate_id(), **document}
        columns, values = cls._document_to_columns(document)
        placeholders = ', '.join('?' for _ in columns)
        quoted_columns = ', '.join(cls._quote(column) for column in columns)
        query = f'INSERT INTO {cls._quote(cls.table_name())} ({quoted_columns}) VALUES ({placeholders})'
        await db.session.execute(query, tuple(values))
        return document['id']

    @classmethod
    async def insert_many(cls, documents: Iterable[dict]) -> list[Self]:
        results = []
        for document in documents:
            final_document = await cls._process_document(document)
            result = await cls._create_model_instance(document=final_document)
            result.id = await cls.insert_one(final_document)
            results.append(result)
        return results

    @classmethod
    async def delete_one(cls, _filter: dict | None = None, /, **kwargs) -> bool:
        obj = await cls.find_one(_filter, **kwargs)
        if obj is None:
            return False
        cursor = await db.session.execute(f'DELETE FROM {cls._quote(cls.table_name())} WHERE "id" = ?', (obj.id,))
        return bool(cursor.rowcount)

    @classmethod
    async def delete_many(cls, _filter: dict | None = None, /, **kwargs) -> int:
        where, params = cls._where(_filter, **kwargs)
        cursor = await db.session.execute(f'DELETE FROM {cls._quote(cls.table_name())}{where}', params)
        return cursor.rowcount

    @classmethod
    async def update_one(cls, _filter: dict, _update: dict | None = None, /, **kwargs) -> bool:
        obj = await cls.find_one(_filter)
        if obj is None:
            return False
        return bool(await cls._update({'id': obj.id}, _update, **kwargs))

    @classmethod
    async def update_many(cls, _filter: dict, _update: dict | None = None, /, **kwargs) -> int:
        return await cls._update(_filter, _update, **kwargs)

    @classmethod
    async def _update(cls, _filter: dict, _update: dict | None = None, /, **kwargs) -> int:
        document = cls._merge(_update, kwargs)
        if any(field.startswith('$') for field in document):
            raise DatabaseError('SQLite updates do not support Mongo-style operators.')

        final_document = await cls._process_document(document)
        await cls._create_model_instance(document=final_document, is_updating=True)
        columns, values = cls._document_to_columns(final_document)
        assignments = ', '.join(f'{cls._quote(column)} = ?' for column in columns)
        where, params = cls._where(_filter)
        query = f'UPDATE {cls._quote(cls.table_name())} SET {assignments}{where}'
        cursor = await db.session.execute(query, (*values, *params))
        return cursor.rowcount
