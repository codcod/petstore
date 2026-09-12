import unittest

from petstore_api.main import app
from starlette.testclient import TestClient


class RequestLoggingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app=app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)

    def test_response_gets_a_request_id_header(self) -> None:
        response = self.client.get('/health')
        self.assertIn('x-request-id', response.headers)

    def test_incoming_request_id_is_echoed_back(self) -> None:
        response = self.client.get('/health', headers={'X-Request-ID': 'trace-123'})
        self.assertEqual(response.headers['x-request-id'], 'trace-123')

    def test_request_is_logged_with_its_request_id(self) -> None:
        with self.assertLogs('petstore', level='INFO') as captured:
            self.client.get('/health', headers={'X-Request-ID': 'trace-abc'})
        [record] = captured.records
        self.assertEqual(record.request_id, 'trace-abc')
        self.assertIn('GET /health 200', record.getMessage())


if __name__ == '__main__':
    unittest.main()
