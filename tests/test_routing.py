from unittest import TestCase

from panther.routings import flatten_urls, finalize_urls


class TestRoutingFunctions(TestCase):

    def test_check_and_load_urls(self):
        # TODO: ...
        pass

    def test_collect_ellipsis_urls(self):
        urls = {
            'user/': {
                '<user_id>/': ...,
                'profile/': ...,
                'list/': ...,
            },
        }

        with self.assertLogs() as captured:
            collected_urls = flatten_urls(urls)

        self.assertEqual(len(captured.records), 3)
        self.assertEqual(captured.records[0].getMessage(), "URL Can't Point To Ellipsis. ('user/<user_id>/' -> ...)")
        self.assertEqual(captured.records[1].getMessage(), "URL Can't Point To Ellipsis. ('user/profile/' -> ...)")
        self.assertEqual(captured.records[2].getMessage(), "URL Can't Point To Ellipsis. ('user/list/' -> ...)")

        self.assertDictEqual(collected_urls, {})

    def test_collect_None_urls(self):
        urls = {
            'user/': {
                '<user_id>/': None,
                'profile/': None,
                'list/': None,
            },
        }

        with self.assertLogs() as captured:
            collected_urls = flatten_urls(urls)

        self.assertEqual(len(captured.records), 3)
        self.assertEqual(captured.records[0].getMessage(), "URL Can't Point To None. ('user/<user_id>/' -> None)")
        self.assertEqual(captured.records[1].getMessage(), "URL Can't Point To None. ('user/profile/' -> None)")
        self.assertEqual(captured.records[2].getMessage(), "URL Can't Point To None. ('user/list/' -> None)")

        self.assertDictEqual(collected_urls, {})

    def test_collect_invalid_urls(self):
        def temp_func():
            pass

        urls = {
            'user/': {
                '?': temp_func,
                '%^': temp_func,
                'لیست': temp_func,
            },
        }

        with self.assertLogs() as captured:
            collected_urls = flatten_urls(urls)

        self.assertEqual(len(captured.records), 3)
        self.assertEqual(captured.records[0].getMessage(), "URL Is Not Valid. --> 'user/?/'")
        self.assertEqual(captured.records[1].getMessage(), "URL Is Not Valid. --> 'user/%^/'")
        self.assertEqual(captured.records[2].getMessage(), "URL Is Not Valid. --> 'user/لیست/'")

        self.assertDictEqual(collected_urls, {})

    def test_collect_simple_urls(self):
        def temp_func():
            pass

        urls = {
            '<user_id>/': temp_func,
            'profile/': temp_func,
            'list/': temp_func,
        }

        collected_urls = flatten_urls(urls)

        expected_result = {
            '<user_id>/': temp_func,
            'profile/': temp_func,
            'list/': temp_func
        }
        self.assertEqual(collected_urls, expected_result)

    def test_collect_simple_nested_urls(self):
        def temp_func():
            pass

        urls = {
            'user/': {
                '<user_id>/': temp_func,
                'profile/': temp_func,
                'list/': temp_func,
            }
        }

        collected_urls = flatten_urls(urls)

        expected_result = {
            'user/<user_id>/': temp_func,
            'user/profile/': temp_func,
            'user/list/': temp_func
        }
        self.assertEqual(collected_urls, expected_result)

    def test_collect_simple_nested_urls_without_slash_at_end(self):
        def temp_func():
            pass

        urls = {
            'user': {
                '<user_id>': temp_func,
                'profile': temp_func,
                'list': temp_func,
            }
        }

        collected_urls = flatten_urls(urls)

        expected_result = {
            'user/<user_id>/': temp_func,
            'user/profile/': temp_func,
            'user/list/': temp_func
        }
        self.assertEqual(collected_urls, expected_result)

    def test_collect_complex_nested_urls(self):
        def temp_func():
            pass

        urls = {
            'user/': {
                '<user_id>/profile/<id>': temp_func,
                'profile/': temp_func,
                'list/': temp_func,
            },
            '': {
                'payments': temp_func,
                'notifications': temp_func,
            },
            'admin/v1': {
                'profile/avatar': temp_func,
                '<user_id>': temp_func,
                'users/': {
                    'list': {
                        'registered': temp_func,
                        'not-registered': temp_func,
                    },
                    'detail': {
                        'registered': temp_func,
                        'not-registered': temp_func,
                    },
                }
            },
            'admin/v2': {

            }
        }

        collected_urls = flatten_urls(urls)
        expected_result = {
            'user/<user_id>/profile/<id>/': temp_func,
            'user/profile/': temp_func,
            'user/list/': temp_func,
            'payments/': temp_func,
            'notifications/': temp_func,
            'admin/v1/profile/avatar/': temp_func,
            'admin/v1/<user_id>/': temp_func,
            'admin/v1/users/list/registered/': temp_func,
            'admin/v1/users/list/not-registered/': temp_func,
            'admin/v1/users/detail/registered/': temp_func,
            'admin/v1/users/detail/not-registered/': temp_func
        }
        self.assertEqual(collected_urls, expected_result)

    def test_finalize_urls(self):
        def temp_func():
            pass

        urls = {
            'user/': {
                '<user_id>/profile/<id>': temp_func,
                'profile/': temp_func,
                'list/': temp_func,
            },
            '': {
                'payments': temp_func,
                'notifications': temp_func,
            },
            'admin/v1': {
                'profile/avatar': temp_func,
                '<user_id>': temp_func,
                'users/': {
                    'list': {
                        'registered': temp_func,
                        'not-registered': temp_func,
                    },
                    'detail': {
                        'registered': temp_func,
                        'not-registered': temp_func,
                    },
                }
            },
            'admin/v2': {

            }
        }

        collected_urls = flatten_urls(urls)
        finalized_urls = finalize_urls(collected_urls)

        expected_result = {
            'user': {
                '<user_id>': {
                    'profile': {
                        '<id>': temp_func
                    }
                },
                'profile': temp_func,
                'list': temp_func
            },
            'payments': temp_func,
            'notifications': temp_func,
            'admin': {
                'v1': {
                    'profile': {
                        'avatar': temp_func
                    },
                    '<user_id>': temp_func,
                    'users': {
                        'list': {
                            'registered': temp_func,
                            'not-registered': temp_func
                        },
                        'detail': {
                            'registered': temp_func,
                            'not-registered': temp_func
                        }
                    }
                }
            }
        }
        self.assertEqual(finalized_urls, expected_result)

    def test_find_endpoint(self):
        # TODO: ...
        pass
