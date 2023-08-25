import random
from unittest import TestCase

from panther.routings import collect_path_variables, finalize_urls, find_endpoint, flatten_urls


class TestRoutingFunctions(TestCase):

    def tearDown(self) -> None:
        from panther.configs import config
        config['urls'] = {}

    # Collecting
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

    def test_collect_None_urls(self):  # noqa: N802
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
        def temp_func(): pass

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

    def test_collect_empty_url(self):
        def temp_func(): pass

        urls = {
            '': temp_func,
        }

        collected_urls = flatten_urls(urls)

        expected_result = {
            '': temp_func,
        }
        self.assertEqual(collected_urls, expected_result)

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
        self.assertEqual(collected_urls, expected_result)

    def test_collect_root_url(self):
        def temp_func(): pass

        urls = {
            '/': temp_func,
        }

        collected_urls = flatten_urls(urls)

        expected_result = {
            '/': temp_func,
        }
        self.assertEqual(collected_urls, expected_result)

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
        self.assertEqual(collected_urls, expected_result)

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
        self.assertEqual(collected_urls, expected_result)

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
        self.assertEqual(collected_urls, expected_result)

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
        self.assertEqual(collected_urls, expected_result)

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
            'admin/v2': {

            },
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
        self.assertEqual(collected_urls, expected_result)

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
        self.assertEqual(finalized_urls, expected_result)

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
        self.assertEqual(finalized_urls, expected_result)

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
        self.assertEqual(finalized_urls, expected_result)

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
        self.assertEqual(finalized_urls, expected_result)

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
        self.assertEqual(finalized_urls, expected_result)

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
        self.assertEqual(finalized_urls, expected_result)

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
            'admin/v2': {

            },
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
        self.assertEqual(finalized_urls, expected_result)

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
        self.assertEqual(finalized_urls, expected_result)

    # Find Endpoint
    def test_find_endpoint_root_url(self):
        def temp_func(): pass

        from panther.configs import config

        config['urls'] = {
            '': temp_func,
        }
        _func, _ = find_endpoint('')

        self.assertIsNotNone(_func)
        self.assertEqual(_func, temp_func)

    def test_find_endpoint_success(self):
        def user_id_profile_id(): pass

        def user_profile(): pass

        def payment(): pass

        def admin_v1_profile_avatar(): pass

        def admin_v1_id(): pass

        def admin_v2_users_list_registered(): pass

        def admin_v2_users_detail_not_registered(): pass

        from panther.configs import config

        config['urls'] = {
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

        self.assertEqual(user_id_profile_id_func, user_id_profile_id)
        self.assertEqual(user_profile_func, user_profile)
        self.assertEqual(payment_func, payment)
        self.assertEqual(admin_v1_profile_avatar_func, admin_v1_profile_avatar)
        self.assertEqual(admin_v1_id_func, admin_v1_id)
        self.assertEqual(admin_v2_users_list_registered_func, admin_v2_users_list_registered)
        self.assertEqual(admin_v2_users_detail_not_registered_func, admin_v2_users_detail_not_registered)

    def test_find_endpoint_success_path(self):
        def user_id_profile_id(): pass

        def user_profile(): pass

        def payment(): pass

        def admin_v1_profile_avatar(): pass

        def admin_v1_id(): pass

        def admin_v2_users_list_registered(): pass

        def admin_v2_users_detail_not_registered(): pass

        from panther.configs import config

        config['urls'] = {
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
        _, user_id_profile_id_path = find_endpoint(f'user/{random.randint(0, 100)}/profile/{random.randint(2, 100)}')
        _, user_profile_path = find_endpoint('user/profile/')
        _, payment_path = find_endpoint('payments/')
        _, admin_v1_profile_avatar_path = find_endpoint('admin/v1/profile/avatar')
        _, admin_v1_id_path = find_endpoint(f'admin/v1/{random.randint(0, 100)}')
        _, admin_v2_users_list_registered_path = find_endpoint('admin/v1/users/list/registered/')
        _, admin_v2_users_detail_not_registered_path = find_endpoint('admin/v1/users/detail/not-registered')

        self.assertEqual(user_id_profile_id_path, 'user/<user_id>/profile/<id>/')
        self.assertEqual(user_profile_path, 'user/profile/')
        self.assertEqual(payment_path, 'payments/')
        self.assertEqual(admin_v1_profile_avatar_path, 'admin/v1/profile/avatar/')
        self.assertEqual(admin_v1_id_path, 'admin/v1/<user_id>/')
        self.assertEqual(admin_v2_users_list_registered_path, 'admin/v1/users/list/registered/')
        self.assertEqual(admin_v2_users_detail_not_registered_path, 'admin/v1/users/detail/not-registered/')

    def test_find_endpoint_not_found(self):
        def temp_func(): pass

        from panther.configs import config

        config['urls'] = {
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

        self.assertIsNone(user_id_profile_id_func)
        self.assertIsNone(user_profile_func)
        self.assertIsNone(payment_func)
        self.assertIsNone(admin_v1_profile_avatar_func)
        self.assertIsNone(admin_v1_id_func)
        self.assertIsNone(admin_v2_users_list_registered_func)
        self.assertIsNone(admin_v2_users_detail_not_registered_func)

    def test_find_endpoint_not_found_path(self):
        def temp_func(): pass

        from panther.configs import config

        config['urls'] = {
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

        self.assertEqual(user_id_profile_id_path, '')
        self.assertEqual(user_profile_path, '')
        self.assertEqual(payment_path, '')
        self.assertEqual(admin_v1_profile_avatar_path, '')
        self.assertEqual(admin_v1_id_path, '')
        self.assertEqual(admin_v2_users_list_registered_path, '')
        self.assertEqual(admin_v2_users_detail_not_registered_path, '')

    def test_find_endpoint_same_pre_path_variable(self):
        def temp_1(): pass

        def temp_2(): pass

        def temp_3(): pass

        from panther.configs import config

        config['urls'] = {
            '': temp_1,
            '<index>': {
                '': temp_2,
                '<id>': temp_3,
            },
        }
        temp_1_func, _ = find_endpoint('')
        temp_2_func, _ = find_endpoint(f'{random.randint(2, 100)}')
        temp_3_func, _ = find_endpoint(f'{random.randint(2, 100)}/{random.randint(2, 100)}')

        self.assertEqual(temp_1_func, temp_1)
        self.assertEqual(temp_2_func, temp_2)
        self.assertEqual(temp_3_func, temp_3)


    def test_find_endpoint_same_pre_path_variable_path(self):
        def temp_1(): pass

        def temp_2(): pass

        def temp_3(): pass

        from panther.configs import config

        config['urls'] = {
            '': temp_1,
            '<index>': {
                '': temp_2,
                '<id>': temp_3,
            },
        }
        _, temp_1_path = find_endpoint('')
        _, temp_2_path = find_endpoint(f'{random.randint(2, 100)}')
        _, temp_3_path = find_endpoint(f'{random.randint(2, 100)}/{random.randint(2, 100)}')

        self.assertEqual(temp_1_path, '/')
        self.assertEqual(temp_2_path, '<index>/')
        self.assertEqual(temp_3_path, '<index>/<id>/')

    def test_find_endpoint_same_pre_key(self):
        def temp_1(): pass

        def temp_2(): pass

        def temp_3(): pass

        from panther.configs import config

        config['urls'] = {
            '': temp_1,
            'hello': {
                '': temp_2,
                '<id>': temp_3,
            },
        }
        temp_1_func, _ = find_endpoint('')

        temp_2_func, _ = find_endpoint('hello')
        temp_3_func, _ = find_endpoint(f'hello/{random.randint(2, 100)}')

        self.assertEqual(temp_1_func, temp_1)
        self.assertEqual(temp_2_func, temp_2)
        self.assertEqual(temp_3_func, temp_3)

    def test_find_endpoint_same_pre_key_path(self):
        def temp_1(): pass

        def temp_2(): pass

        def temp_3(): pass

        from panther.configs import config

        config['urls'] = {
            '': temp_1,
            'hello': {
                '': temp_2,
                '<id>': temp_3,
            },
        }
        _, temp_1_path = find_endpoint('')

        _, temp_2_path = find_endpoint('hello')
        _, temp_3_path = find_endpoint(f'hello/{random.randint(2, 100)}')

        self.assertEqual(temp_1_path, '/')
        self.assertEqual(temp_2_path, 'hello/')
        self.assertEqual(temp_3_path, 'hello/<id>/')

    # Collect PathVariables
    def test_collect_path_variables(self):
        def temp_func(): pass

        from panther.configs import config

        config['urls'] = {
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
        path_variables = collect_path_variables(request_path=request_path, found_path=found_path)

        self.assertIsInstance(path_variables, dict)

        self.assertTrue('user_id' in path_variables)
        self.assertTrue('id' in path_variables)

        self.assertEqual(path_variables['user_id'], str(_user_id))
        self.assertEqual(path_variables['id'], str(_id))
