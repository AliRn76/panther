from unittest import TestCase
from panther import status


class TestStatus(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.statuses = {
            'HTTP_100_CONTINUE': 100,
            'HTTP_101_SWITCHING_PROTOCOLS': 101,
            'HTTP_102_PROCESSING': 102,
            'HTTP_103_EARLY_HINTS': 103,
            'HTTP_200_OK': 200,
            'HTTP_201_CREATED': 201,
            'HTTP_202_ACCEPTED': 202,
            'HTTP_203_NON_AUTHORITATIVE_INFORMATION': 203,
            'HTTP_204_NO_CONTENT': 204,
            'HTTP_205_RESET_CONTENT': 205,
            'HTTP_206_PARTIAL_CONTENT': 206,
            'HTTP_207_MULTI_STATUS': 207,
            'HTTP_208_ALREADY_REPORTED': 208,
            'HTTP_226_IM_USED': 226,
            'HTTP_300_MULTIPLE_CHOICES': 300,
            'HTTP_301_MOVED_PERMANENTLY': 301,
            'HTTP_302_FOUND': 302,
            'HTTP_303_SEE_OTHER': 303,
            'HTTP_304_NOT_MODIFIED': 304,
            'HTTP_305_USE_PROXY': 305,
            'HTTP_306_RESERVED': 306,
            'HTTP_307_TEMPORARY_REDIRECT': 307,
            'HTTP_308_PERMANENT_REDIRECT': 308,
            'HTTP_400_BAD_REQUEST': 400,
            'HTTP_401_UNAUTHORIZED': 401,
            'HTTP_402_PAYMENT_REQUIRED': 402,
            'HTTP_403_FORBIDDEN': 403,
            'HTTP_404_NOT_FOUND': 404,
            'HTTP_405_METHOD_NOT_ALLOWED': 405,
            'HTTP_406_NOT_ACCEPTABLE': 406,
            'HTTP_407_PROXY_AUTHENTICATION_REQUIRED': 407,
            'HTTP_408_REQUEST_TIMEOUT': 408,
            'HTTP_409_CONFLICT': 409,
            'HTTP_410_GONE': 410,
            'HTTP_411_LENGTH_REQUIRED': 411,
            'HTTP_412_PRECONDITION_FAILED': 412,
            'HTTP_413_REQUEST_ENTITY_TOO_LARGE': 413,
            'HTTP_414_REQUEST_URI_TOO_LONG': 414,
            'HTTP_415_UNSUPPORTED_MEDIA_TYPE': 415,
            'HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE': 416,
            'HTTP_417_EXPECTATION_FAILED': 417,
            'HTTP_418_IM_A_TEAPOT': 418,
            'HTTP_421_MISDIRECTED_REQUEST': 421,
            'HTTP_422_UNPROCESSABLE_ENTITY': 422,
            'HTTP_423_LOCKED': 423,
            'HTTP_424_FAILED_DEPENDENCY': 424,
            'HTTP_425_TOO_EARLY': 425,
            'HTTP_426_UPGRADE_REQUIRED': 426,
            'HTTP_428_PRECONDITION_REQUIRED': 428,
            'HTTP_429_TOO_MANY_REQUESTS': 429,
            'HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE': 431,
            'HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS': 451,
            'HTTP_500_INTERNAL_SERVER_ERROR': 500,
            'HTTP_501_NOT_IMPLEMENTED': 501,
            'HTTP_502_BAD_GATEWAY': 502,
            'HTTP_503_SERVICE_UNAVAILABLE': 503,
            'HTTP_504_GATEWAY_TIMEOUT': 504,
            'HTTP_505_HTTP_VERSION_NOT_SUPPORTED': 505,
            'HTTP_506_VARIANT_ALSO_NEGOTIATES': 506,
            'HTTP_507_INSUFFICIENT_STORAGE': 507,
            'HTTP_508_LOOP_DETECTED': 508,
            'HTTP_510_NOT_EXTENDED': 510,
            'HTTP_511_NETWORK_AUTHENTICATION_REQUIRED': 511,

            'WS_1000_NORMAL_CLOSURE': 1000,
            'WS_1001_GOING_AWAY': 1001,
            'WS_1002_PROTOCOL_ERROR': 1002,
            'WS_1003_UNSUPPORTED_DATA': 1003,
            'WS_1007_INVALID_FRAME_PAYLOAD_DATA': 1007,
            'WS_1008_POLICY_VIOLATION': 1008,
            'WS_1009_MESSAGE_TOO_BIG': 1009,
            'WS_1010_MANDATORY_EXT': 1010,
            'WS_1011_INTERNAL_ERROR': 1011,
            'WS_1012_SERVICE_RESTART': 1012,
            'WS_1013_TRY_AGAIN_LATER': 1013,
            'WS_1014_BAD_GATEWAY': 1014,
        }

    def test_status_numbers(self):
        for _status, number in self.statuses.items():
            assert getattr(status, _status) == number

    def test_status_is_informational(self):
        for number in range(100, 600):
            if 100 <= number < 200:
                assert status.is_informational(number) is True
            else:
                assert status.is_informational(number) is False

    def test_status_is_success(self):
        for number in range(100, 600):
            if 200 <= number < 300:
                assert status.is_success(number) is True
            else:
                assert status.is_success(number) is False

    def test_status_is_redirect(self):
        for number in range(100, 600):
            if 300 <= number < 400:
                assert status.is_redirect(number) is True
            else:
                assert status.is_redirect(number) is False

    def test_status_is_client_error(self):
        for number in range(100, 600):
            if 400 <= number < 500:
                assert status.is_client_error(number) is True
            else:
                assert status.is_client_error(number) is False

    def test_status_is_server_error(self):
        for number in range(100, 600):
            if 500 <= number < 600:
                assert status.is_server_error(number) is True
            else:
                assert status.is_server_error(number) is False

    def test_statuses_text(self):
        for _status, number in self.statuses.items():
            if _status.startswith('HTTP'):
                assert status.status_text[number] == _status[9:].replace('_', ' ').title()
            else:  # WS
                assert status.status_text[number] == _status[8:].replace('_', ' ').title()
