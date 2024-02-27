import random
from unittest import TestCase

from panther.base_request import BaseRequest
from panther.exceptions import PantherError
from panther.routings import (
    finalize_urls,
    find_endpoint,
    flatten_urls,
)


class TestRoutingFunctions(TestCase):
    def tearDown(self) -> None:
        from panther.configs import config

        config.URLS = {}

    # Collecting
    def test_collect_ellipsis_urls(self):
        urls1 = {
            'user/': {
                '<user_id>/': ...,
            },
        }
        urls2 = {
            'user/': {
                'list/': ...,
            },
        }

        try:
            flatten_urls(urls1)
        except PantherError as exc:
            assert exc.args[0] == "URL Can't Point To Ellipsis. ('user/<user_id>/' -> ...)"
        else:
            assert False

        try:
            flatten_urls(urls2)
        except PantherError as exc:
            assert exc.args[0] == "URL Can't Point To Ellipsis. ('user/list/' -> ...)"
        else:
            assert False

    def test_collect_None_urls(self):
        urls1 = {
            'user/': {
                'list/': None,
            },
        }
        urls2 = {
            'user/': {
                '<user_id>/': None,
            },
        }

        try:
            flatten_urls(urls1)
        except PantherError as exc:
            assert exc.args[0] == "URL Can't Point To None. ('user/list/' -> None)"
        else:
            assert False

        try:
            flatten_urls(urls2)
        except PantherError as exc:
            assert exc.args[0] == "URL Can't Point To None. ('user/<user_id>/' -> None)"
        else:
            assert False

    def test_collect_invalid_urls(self):
        def temp_func(): pass

        urls1 = {
            'user/': {
                '?': temp_func,
            },
        }
        urls2 = {
            'user/': {
                'لیست': temp_func,
            },
        }

        try:
            flatten_urls(urls1)
        except PantherError as exc:
            assert exc.args[0] == "URL Is Not Valid. --> 'user/?/'"
        else:
            assert False

        try:
            flatten_urls(urls2)
        except PantherError as exc:
            assert exc.args[0] == "URL Is Not Valid. --> 'user/لیست/'"
        else:
            assert False

    def test_collect_empty_url(self):
        def temp_func(): pass

        urls = {
            '': temp_func,
        }

        collected_urls = flatten_urls(urls)

        expected_result = {
            '': temp_func,
        }
        assert collected_urls == expected_result

    def test_collect_empty_url_nested(self):
        def temp_func(): pass

        urls = {
            '': {
                '': {
                    'nested/<user_id>/': temp_func,
                    'nested/profile/': temp_func,
                    'nested/list/': temp_func,
                },
                '<user_id>/': temp_func,
                'profile/': temp_func,
                'list/': temp_func,
            },
        }

        collected_urls = flatten_urls(urls)

        expected_result = {
            '<user_id>/': temp_func,
            'profile/': temp_func,
            'list/': temp_func,
            'nested/<user_id>/': temp_func,
            'nested/profile/': temp_func,
            'nested/list/': temp_func,
        }
        assert collected_urls == expected_result

    def test_collect_root_url(self):
        def temp_func(): pass

        urls = {
            '/': temp_func,
        }

        collected_urls = flatten_urls(urls)

        expected_result = {
            '/': temp_func,
        }
        assert collected_urls == expected_result

    def test_collect_root_url_nested(self):
        def temp_func(): pass

        urls = {
            '/': {
                '/': {
                    'nested/<user_id>/': temp_func,
                    'nested/profile/': temp_func,
                    'nested/list/': temp_func,
                },
                '<user_id>/': temp_func,
                'profile/': temp_func,
                'list/': temp_func,
            },
        }

        collected_urls = flatten_urls(urls)

        expected_result = {
            '/<user_id>/': temp_func,
            '/profile/': temp_func,
            '/list/': temp_func,
            '//nested/<user_id>/': temp_func,
            '//nested/profile/': temp_func,
            '//nested/list/': temp_func,
        }
        assert collected_urls == expected_result

    def test_collect_simple_urls(self):
        def temp_func(): pass

        urls = {
            '<user_id>/': temp_func,
            'profile/': temp_func,
            'list/': temp_func,
        }

        collected_urls = flatten_urls(urls)

        expected_result = {
            '<user_id>/': temp_func,
            'profile/': temp_func,
            'list/': temp_func,
        }
        assert collected_urls == expected_result

    def test_collect_simple_nested_urls(self):
        def temp_func(): pass

        urls = {
            'user/': {
                '<user_id>/': temp_func,
                'profile/': temp_func,
                'list/': temp_func,
            },
        }

        collected_urls = flatten_urls(urls)

        expected_result = {
            'user/<user_id>/': temp_func,
            'user/profile/': temp_func,
            'user/list/': temp_func,
        }
        assert collected_urls == expected_result

    def test_collect_simple_nested_urls_without_slash_at_end(self):
        def temp_func(): pass

        urls = {
            'user': {
                '<user_id>': temp_func,
                'profile': temp_func,
                'list': temp_func,
            },
        }

        collected_urls = flatten_urls(urls)

        expected_result = {
            'user/<user_id>/': temp_func,
            'user/profile/': temp_func,
            'user/list/': temp_func,
        }
        assert collected_urls == expected_result

    def test_collect_complex_nested_urls(self):
        def temp_func(): pass

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
                },
            },
            'admin/v2': {},
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
            'admin/v1/users/detail/not-registered/': temp_func,
        }
        assert collected_urls == expected_result

    # Finalize
    def test_finalize_empty_url(self):
        def temp_func(): pass

        urls = {
            '': temp_func,
        }

        collected_urls = flatten_urls(urls)
        finalized_urls = finalize_urls(collected_urls)

        expected_result = {
            '': temp_func,
        }
        assert finalized_urls == expected_result

    def test_finalize_empty_url_nested(self):
        def temp_func(): pass

        urls = {
            '': {
                '': {
                    'nested/<user_id>/': temp_func,
                    'nested/profile/': temp_func,
                    'nested/list/': temp_func,
                },
                '<user_id>/': temp_func,
                'profile/': temp_func,
                'list/': temp_func,
            },
        }

        collected_urls = flatten_urls(urls)
        finalized_urls = finalize_urls(collected_urls)

        expected_result = {
            'nested': {
                '<user_id>': temp_func,
                'profile': temp_func,
                'list': temp_func,
            },
            '<user_id>': temp_func,
            'profile': temp_func,
            'list': temp_func,
        }
        assert finalized_urls == expected_result

    def test_finalize_root_url(self):
        def temp_func(): pass

        urls = {
            '/': temp_func,
        }

        collected_urls = flatten_urls(urls)
        finalized_urls = finalize_urls(collected_urls)

        expected_result = {
            '': temp_func,
        }
        assert finalized_urls == expected_result

    def test_finalize_root_url_nested(self):
        def temp_func(): pass

        urls = {
            '/': {
                '/': {
                    'nested/<user_id>/': temp_func,
                    'nested/profile/': temp_func,
                    'nested/list/': temp_func,
                },
                '<user_id>/': temp_func,
                'profile/': temp_func,
                'list/': temp_func,
            },
        }

        collected_urls = flatten_urls(urls)
        finalized_urls = finalize_urls(collected_urls)

        expected_result = {
            'nested': {
                '<user_id>': temp_func,
                'profile': temp_func,
                'list': temp_func,
            },
            '<user_id>': temp_func,
            'profile': temp_func,
            'list': temp_func,
        }
        assert finalized_urls == expected_result

    def test_finalize_root_and_empty_url_nested(self):
        def temp_func(): pass

        urls = {
            '/': {
                '': {
                    'nested/<user_id>/': temp_func,
                    'nested/profile/': temp_func,
                    'nested/list/': temp_func,
                },
                '/': temp_func,
                'profile/': temp_func,
                'list/': temp_func,
            },
        }

        collected_urls = flatten_urls(urls)
        finalized_urls = finalize_urls(collected_urls)

        expected_result = {
            'nested': {
                '<user_id>': temp_func,
                'profile': temp_func,
                'list': temp_func,
            },
            '': temp_func,
            'profile': temp_func,
            'list': temp_func,
        }
        assert finalized_urls == expected_result

    def test_finalize_empty_and_root_url_nested(self):
        def temp_func(): pass

        urls = {
            '': {
                '/': {
                    'nested/<user_id>/': temp_func,
                    'nested/profile/': temp_func,
                    'nested/list/': temp_func,
                },
                '': temp_func,
                'profile/': temp_func,
                'list/': temp_func,
            },
        }

        collected_urls = flatten_urls(urls)
        finalized_urls = finalize_urls(collected_urls)

        expected_result = {
            'nested': {
                '<user_id>': temp_func,
                'profile': temp_func,
                'list': temp_func,
            },
            '': temp_func,
            'profile': temp_func,
            'list': temp_func,
        }
        assert finalized_urls == expected_result

    def test_finalize_urls(self):
        def temp_func(): pass

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
                },
            },
            'admin/v2': {},
        }

        collected_urls = flatten_urls(urls)
        finalized_urls = finalize_urls(collected_urls)

        expected_result = {
            'user': {
                '<user_id>': {
                    'profile': {
                        '<id>': temp_func,
                    },
                },
                'profile': temp_func,
                'list': temp_func,
            },
            'payments': temp_func,
            'notifications': temp_func,
            'admin': {
                'v1': {
                    'profile': {
                        'avatar': temp_func,
                    },
                    '<user_id>': temp_func,
                    'users': {
                        'list': {
                            'registered': temp_func,
                            'not-registered': temp_func,
                        },
                        'detail': {
                            'registered': temp_func,
                            'not-registered': temp_func,
                        },
                    },
                },
            },
        }
        assert finalized_urls == expected_result

    def test_finalize_urls_same_pre_path_variable(self):
        def temp_func(): pass

        urls = {
            '': temp_func,
            '<index>/': temp_func,
            '<index>/<id>/': temp_func,
        }

        collected_urls = flatten_urls(urls)
        finalized_urls = finalize_urls(collected_urls)
        expected_result = {
            '': temp_func,
            '<index>': {
                '': temp_func,
                '<id>': temp_func,
            },
        }
        assert finalized_urls == expected_result

    def test_finalize_urls_with_same_level_path_variables(self):
        def temp_func(): pass

        urls1 = {
            'user': {
                '<index1>/': temp_func,
                '<index2>/': temp_func,
            }
        }
        urls2 = {
            'user': {
                '<index1>/': {'detail': temp_func},
                '<index2>/': temp_func,
                '<index3>/': {'detail': temp_func},
                '<index4>/': {'detail': temp_func},
            }
        }

        try:
            finalize_urls(flatten_urls(urls1))
        except PantherError as exc:
            assert exc.args[0] == (
                "URLs can't have same-level path variables that point to an endpoint: "
                "\n\t- /user/<index1>"
                "\n\t- /user/<index2>"
            )
        else:
            assert False

        try:
            finalize_urls(flatten_urls(urls2))
        except PantherError as exc:
            assert exc.args[0] == (
                "URLs can't have same-level path variables that point to a dict: "
                "\n\t- /user/<index1>"
                "\n\t- /user/<index3>"
                "\n\t- /user/<index4>"
            )
        else:
            assert False

    # Find Endpoint
    def test_find_endpoint_root_url(self):
        def temp_func(): pass

        from panther.configs import config

        config.URLS = {
            '': temp_func,
        }
        _func, _ = find_endpoint('')

        assert _func == temp_func

    def test_find_endpoint_success(self):
        def user_id_profile_id(): pass

        def user_profile(): pass

        def payment(): pass

        def admin_v1_profile_avatar(): pass

        def admin_v1_id(): pass

        def admin_v2_users_list_registered(): pass

        def admin_v2_users_detail_not_registered(): pass

        from panther.configs import config

        config.URLS = {
            'user': {
                '<user_id>': {
                    'profile': {
                        '<id>': user_id_profile_id,
                    },
                },
                'profile': user_profile,
                'list': ...,
            },
            'payments': payment,
            'notifications': ...,
            'admin': {
                'v1': {
                    'profile': {
                        'avatar': admin_v1_profile_avatar,
                    },
                    '<user_id>': admin_v1_id,
                    'users': {
                        'list': {
                            'registered': admin_v2_users_list_registered,
                            'not-registered': ...,
                        },
                        'detail': {
                            'registered': ...,
                            'not-registered': admin_v2_users_detail_not_registered,
                        },
                    },
                },
            },
        }
        user_id_profile_id_func, _ = find_endpoint(f'user/{random.randint(0, 100)}/profile/{random.randint(2, 100)}')
        user_profile_func, _ = find_endpoint('user/profile/')
        payment_func, _ = find_endpoint('payments/')
        admin_v1_profile_avatar_func, _ = find_endpoint('admin/v1/profile/avatar')
        admin_v1_id_func, _ = find_endpoint(f'admin/v1/{random.randint(0, 100)}')
        admin_v2_users_list_registered_func, _ = find_endpoint('admin/v1/users/list/registered/')
        admin_v2_users_detail_not_registered_func, _ = find_endpoint('admin/v1/users/detail/not-registered')

        assert user_id_profile_id_func == user_id_profile_id
        assert user_profile_func == user_profile
        assert payment_func == payment
        assert admin_v1_profile_avatar_func == admin_v1_profile_avatar
        assert admin_v1_id_func == admin_v1_id
        assert admin_v2_users_list_registered_func == admin_v2_users_list_registered
        assert admin_v2_users_detail_not_registered_func == admin_v2_users_detail_not_registered

    def test_find_endpoint_success_path(self):
        def user_id_profile_id(): pass

        def user_profile(): pass

        def payment(): pass

        def admin_v1_profile_avatar(): pass

        def admin_v1_id(): pass

        def admin_v2_users_list_registered(): pass

        def admin_v2_users_detail_not_registered(): pass

        from panther.configs import config

        config.URLS = {
            'user': {
                '<user_id>': {
                    'profile': {
                        '<id>': user_id_profile_id,
                    },
                },
                'profile': user_profile,
                'list': ...,
            },
            'payments': payment,
            'notifications': ...,
            'admin': {
                'v1': {
                    'profile': {
                        'avatar': admin_v1_profile_avatar,
                    },
                    '<user_id>': admin_v1_id,
                    '<user_id2>': {
                        'list': {
                            '<registered2>': {},
                            '<registered1>': admin_v2_users_list_registered,
                            'registered': admin_v2_users_list_registered,
                        },
                    },
                    'users': {
                        'list': {
                            'registered': admin_v2_users_list_registered,
                            'not-registered': ...,
                        },
                        'detail': {
                            'registered': ...,
                            'not-registered': admin_v2_users_detail_not_registered,
                        },
                    },
                },
            },
        }
        _, user_id_profile_id_path = find_endpoint(f'user/{random.randint(0, 100)}/profile/{random.randint(2, 100)}')
        _, user_profile_path = find_endpoint('user/profile/')
        _, payment_path = find_endpoint('payments/')
        _, admin_v1_profile_avatar_path = find_endpoint('admin/v1/profile/avatar')
        _, admin_v1_id_path = find_endpoint(f'admin/v1/{random.randint(0, 100)}')
        _, admin_v1_id_registered_path = find_endpoint(f'admin/v1/{random.randint(0, 100)}/list/registered')
        _, admin_v1_id_registered1_path = find_endpoint(f'admin/v1/{random.randint(0, 100)}/list/1/')
        _, admin_v2_users_list_registered_path = find_endpoint('admin/v1/users/list/registered/')
        _, admin_v2_users_detail_not_registered_path = find_endpoint('admin/v1/users/detail/not-registered')

        assert user_id_profile_id_path == 'user/<user_id>/profile/<id>'
        assert user_profile_path == 'user/profile'
        assert payment_path == 'payments'
        assert admin_v1_profile_avatar_path == 'admin/v1/profile/avatar'
        assert admin_v1_id_path == 'admin/v1/<user_id>'
        assert admin_v1_id_registered_path == 'admin/v1/<user_id2>/list/registered'
        assert admin_v1_id_registered1_path == 'admin/v1/<user_id2>/list/<registered1>'
        assert admin_v2_users_list_registered_path == 'admin/v1/users/list/registered'
        assert admin_v2_users_detail_not_registered_path == 'admin/v1/users/detail/not-registered'

    def test_find_endpoint_not_found(self):
        def temp_func(): pass

        from panther.configs import config

        config.URLS = {
            'user': {
                'list': temp_func,
            },
        }
        user_id_profile_id_func, _ = find_endpoint(f'user/{random.randint(0, 100)}/profile/{random.randint(2, 100)}')
        user_profile_func, _ = find_endpoint('user/profile/')
        payment_func, _ = find_endpoint('payments/')
        admin_v1_profile_avatar_func, _ = find_endpoint('admin/v1/profile/avatar')
        admin_v1_id_func, _ = find_endpoint(f'admin/v1/{random.randint(0, 100)}')
        admin_v2_users_list_registered_func, _ = find_endpoint('admin/v1/users/list/registered/')
        admin_v2_users_detail_not_registered_func, _ = find_endpoint('admin/v1/users/detail/not-registered')

        assert user_id_profile_id_func is None
        assert user_profile_func is None
        assert payment_func is None
        assert admin_v1_profile_avatar_func is None
        assert admin_v1_id_func is None
        assert admin_v2_users_list_registered_func is None
        assert admin_v2_users_detail_not_registered_func is None

    def test_find_endpoint_not_found_path(self):
        def temp_func(): pass

        from panther.configs import config

        config.URLS = {
            'user': {
                'list': temp_func,
            },
        }
        _, user_id_profile_id_path = find_endpoint(f'user/{random.randint(0, 100)}/profile/{random.randint(2, 100)}')
        _, user_profile_path = find_endpoint('user/profile/')
        _, payment_path = find_endpoint('payments/')
        _, admin_v1_profile_avatar_path = find_endpoint('admin/v1/profile/avatar')
        _, admin_v1_id_path = find_endpoint(f'admin/v1/{random.randint(0, 100)}')
        _, admin_v2_users_list_registered_path = find_endpoint('admin/v1/users/list/registered/')
        _, admin_v2_users_detail_not_registered_path = find_endpoint('admin/v1/users/detail/not-registered')

        assert user_id_profile_id_path == ''
        assert user_profile_path == ''
        assert payment_path == ''
        assert admin_v1_profile_avatar_path == ''
        assert admin_v1_id_path == ''
        assert admin_v2_users_list_registered_path == ''
        assert admin_v2_users_detail_not_registered_path == ''

    def test_find_endpoint_not_found_last_is_path_variable(self):
        def temp_func(): pass

        from panther.configs import config

        config.URLS = {
            'user': {
                '<name>': temp_func,
            },
        }
        user_id_profile_id_func, _ = find_endpoint(f'user/{random.randint(0, 100)}/profile/{random.randint(2, 100)}')
        user_profile_func, _ = find_endpoint('user/ali/')
        payment_func, _ = find_endpoint('payments/')
        admin_v1_profile_avatar_func, _ = find_endpoint('admin/v1/profile/avatar')
        admin_v1_id_func, _ = find_endpoint(f'admin/v1/{random.randint(0, 100)}')
        admin_v2_users_list_registered_func, _ = find_endpoint('admin/v1/users/list/registered/')
        admin_v2_users_detail_not_registered_func, _ = find_endpoint('admin/v1/users/detail/not-registered')

        assert user_id_profile_id_func is None
        assert user_profile_func is not None
        assert payment_func is None
        assert admin_v1_profile_avatar_func is None
        assert admin_v1_id_func is None
        assert admin_v2_users_list_registered_func is None
        assert admin_v2_users_detail_not_registered_func is None

    def test_find_endpoint_not_found_path_last_is_path_variable(self):
        def temp_func(): pass

        from panther.configs import config

        config.URLS = {
            'user': {
                '<name>': temp_func,
            },
        }
        _, user_id_profile_id_path = find_endpoint(f'user/{random.randint(0, 100)}/profile/{random.randint(2, 100)}')
        _, user_profile_path = find_endpoint('user/ali/')
        _, payment_path = find_endpoint('payments/')
        _, admin_v1_profile_avatar_path = find_endpoint('admin/v1/profile/avatar')
        _, admin_v1_id_path = find_endpoint(f'admin/v1/{random.randint(0, 100)}')
        _, admin_v2_users_list_registered_path = find_endpoint('admin/v1/users/list/registered/')
        _, admin_v2_users_detail_not_registered_path = find_endpoint('admin/v1/users/detail/not-registered')

        assert user_id_profile_id_path == ''
        assert user_profile_path != ''
        assert payment_path == ''
        assert admin_v1_profile_avatar_path == ''
        assert admin_v1_id_path == ''
        assert admin_v2_users_list_registered_path == ''
        assert admin_v2_users_detail_not_registered_path == ''

    def test_find_endpoint_not_found_too_many(self):
        def temp_func(): pass

        from panther.configs import config

        config.URLS = {
            'user/name': temp_func,
        }
        func, path = find_endpoint('user/name/troublemaker')

        assert path == ''
        assert func is None

    def test_find_endpoint_not_found_not_enough(self):
        def temp_func(): pass

        from panther.configs import config

        config.URLS = {
            'user/name': temp_func,
        }
        func, path = find_endpoint('user/')

        assert path == ''
        assert func is None

    def test_find_endpoint_same_pre_path_variable(self):
        def temp_1(): pass

        def temp_2(): pass

        def temp_3(): pass

        from panther.configs import config

        config.URLS = {
            '': temp_1,
            '<index>': {
                '': temp_2,
                '<id>': temp_3,
            },
        }
        temp_1_func, _ = find_endpoint('')
        temp_2_func, _ = find_endpoint(f'{random.randint(2, 100)}')
        temp_3_func, _ = find_endpoint(f'{random.randint(2, 100)}/{random.randint(2, 100)}')

        assert temp_1_func == temp_1
        assert temp_2_func == temp_2
        assert temp_3_func == temp_3

    def test_find_endpoint_same_pre_path_variable_path(self):
        def temp_1(): pass

        def temp_2(): pass

        def temp_3(): pass

        from panther.configs import config

        config.URLS = {
            '': temp_1,
            '<index>': {
                '': temp_2,
                '<id>': temp_3,
            },
        }
        _, temp_1_path = find_endpoint('')
        _, temp_2_path = find_endpoint(f'{random.randint(2, 100)}')
        _, temp_3_path = find_endpoint(f'{random.randint(2, 100)}/{random.randint(2, 100)}')

        assert temp_1_path == ''
        assert temp_2_path == '<index>'
        assert temp_3_path == '<index>/<id>'

    def test_find_endpoint_same_pre_key(self):
        def temp_1(): pass

        def temp_2(): pass

        def temp_3(): pass

        from panther.configs import config

        config.URLS = {
            '': temp_1,
            'hello': {
                '': temp_2,
                '<id>': temp_3,
            },
        }
        temp_1_func, _ = find_endpoint('')

        temp_2_func, _ = find_endpoint('hello')
        temp_3_func, _ = find_endpoint(f'hello/{random.randint(2, 100)}')

        assert temp_1_func == temp_1
        assert temp_2_func == temp_2
        assert temp_3_func == temp_3

    def test_find_endpoint_same_pre_key_path(self):
        def temp_1(): pass

        def temp_2(): pass

        def temp_3(): pass

        from panther.configs import config

        config.URLS = {
            '': temp_1,
            'hello': {
                '': temp_2,
                '<id>': temp_3,
            },
        }
        _, temp_1_path = find_endpoint('')

        _, temp_2_path = find_endpoint('hello')
        _, temp_3_path = find_endpoint(f'hello/{random.randint(2, 100)}')

        assert temp_1_path == ''
        assert temp_2_path == 'hello'
        assert temp_3_path == 'hello/<id>'

    def test_find_endpoint_with_params(self):
        def user_id_profile_id(): pass
        from panther.configs import config

        config.URLS = {
            'user': {
                '<user_id>': {
                    'profile': user_id_profile_id,
                },
            },
        }
        user_id_profile_id_func, _ = find_endpoint(f'user/{random.randint(0, 100)}/profile?name=ali')

        assert user_id_profile_id_func == user_id_profile_id

    # Collect PathVariables
    def test_collect_path_variables(self):
        def temp_func(): pass

        from panther.configs import config

        config.URLS = {
            'user': {
                '<user_id>': {
                    'profile': {
                        '<id>': temp_func,
                    },
                },
            },
        }

        _user_id = random.randint(0, 100)
        _id = random.randint(0, 100)
        request_path = f'user/{_user_id}/profile/{_id}'

        _, found_path = find_endpoint(request_path)
        request = BaseRequest(scope={'path': request_path}, receive=lambda x: x, send=lambda x: x)
        request.collect_path_variables(found_path=found_path)
        path_variables = request.path_variables

        assert isinstance(path_variables, dict)

        assert 'user_id' in path_variables
        assert 'id' in path_variables

        assert path_variables['user_id'] == str(_user_id)
        assert path_variables['id'] == str(_id)
