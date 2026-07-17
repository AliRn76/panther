from unittest import TestCase

from panther.db.queries.base_queries import BaseQuery
from panther.db.queries.document_queries import BaseDocumentQuery
from panther.db.queries.mongodb_queries import BaseMongoDBQuery
from panther.db.queries.pantherdb_queries import BasePantherDBQuery


class TestQuerySeparation(TestCase):
    def test_document_query_behavior_is_not_part_of_the_generic_contract(self):
        assert not hasattr(BaseQuery, '_process_document')
        assert not hasattr(BaseQuery, '_create_model_instance')
        assert not hasattr(BaseQuery, '_merge')

    def test_document_backends_keep_document_query_behavior(self):
        assert issubclass(BaseDocumentQuery, BaseQuery)
        assert issubclass(BaseMongoDBQuery, BaseDocumentQuery)
        assert issubclass(BasePantherDBQuery, BaseDocumentQuery)
        assert hasattr(BaseMongoDBQuery, '_process_document')
        assert hasattr(BasePantherDBQuery, '_create_model_instance')
