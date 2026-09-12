import unittest

import httpx2
from petstore_cli.client import PetstoreClient

PET = {
    'id': 1,
    'name': 'Rex',
    'category': 'dog',
    'photo_urls': [],
    'tags': [],
    'status': 'available',
    'created_at': '2024-01-01T00:00:00',
}


class TestPetstoreClient(unittest.TestCase):
    def _client(self, handler) -> PetstoreClient:
        return PetstoreClient(
            'http://testserver', transport=httpx2.MockTransport(handler)
        )

    def test_list_pets(self):
        def handler(request):
            assert request.url.path == '/pets'
            return httpx2.Response(200, json=[PET])

        with self._client(handler) as client:
            self.assertEqual(client.list_pets(), [PET])

    def test_get_pet(self):
        def handler(request):
            assert request.url.path == '/pets/1'
            return httpx2.Response(200, json=PET)

        with self._client(handler) as client:
            self.assertEqual(client.get_pet(1), PET)

    def test_create_pet_sends_form_data(self):
        def handler(request):
            assert request.url.path == '/pets'
            assert request.method == 'POST'
            return httpx2.Response(201, json=PET)

        with self._client(handler) as client:
            self.assertEqual(client.create_pet(name='Rex'), PET)

    def test_delete_pet_raises_on_404(self):
        def handler(request):
            return httpx2.Response(404, json={'detail': 'not found'})

        with self._client(handler) as client, self.assertRaises(httpx2.HTTPStatusError):
            client.delete_pet(999)


if __name__ == '__main__':
    unittest.main()
