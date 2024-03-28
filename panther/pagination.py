from panther.db.cursor import Cursor
from pantherdb import Cursor as PantherDBCursor


class Pagination:
    """
    Request URL:
        example.com/users?limit=10&skip=0
    Response Data:
        {
            'count': 10,
            'next': '?limit=10&skip=10',
            'previous': None,
            results: [...]
        }
    """
    DEFAULT_LIMIT = 20
    DEFAULT_SKIP = 0

    def __init__(self, query_params: dict, cursor: Cursor | PantherDBCursor):
        self.limit = self.get_limit(query_params=query_params)
        self.skip = self.get_skip(query_params=query_params)
        self.cursor = cursor

    def get_limit(self, query_params: dict) -> int:
        return int(query_params.get('limit', self.DEFAULT_LIMIT))

    def get_skip(self, query_params: dict) -> int:
        return int(query_params.get('skip', self.DEFAULT_SKIP))

    def build_next_params(self):
        next_skip = self.skip + self.limit
        return f'?limit={self.limit}&skip={next_skip}'

    def build_previous_params(self):
        previous_skip = max(self.skip - self.limit, 0)
        return f'?limit={self.limit}&skip={previous_skip}'

    def paginate(self):
        return self.cursor.skip(skip=self.skip).limit(limit=self.limit)

    async def template(self, response: list):
        count = await self.cursor.cls.count(self.cursor.filter)
        has_next = not bool(self.limit + self.skip >= count)

        return {
            'count': count,
            'next': self.build_next_params() if has_next else None,
            'previous': self.build_previous_params() if self.skip else None,
            'results': response
        }
