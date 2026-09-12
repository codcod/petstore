import re
import unittest
import uuid

from petstore_api.db import engine
from petstore_web.main import app
from starlette.testclient import TestClient


def _extract_selected_id(url: str) -> int:
    match = re.search(r'[?&]selected=(\d+)', str(url))
    assert match is not None, f'no ?selected= id in redirected url {url!r}'
    return int(match.group(1))


class PetstoreWebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app=app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.portal.call(engine.dispose)
        cls.client.__exit__(None, None, None)

    def _create_pet(self, **overrides) -> tuple[str, int, 'object']:
        name = f'Test Pet {uuid.uuid4()}'
        payload = {
            'name': name,
            'category': 'Dogs',
            'tags': 'friendly, trained',
            'photo_urls': 'https://example.com/a.jpg, https://example.com/b.jpg',
            'status': 'available',
        }
        payload.update(overrides)
        response = self.client.post('/pets/new', data=payload)
        pet_id = _extract_selected_id(response.url)
        return name, pet_id, response

    def test_list_pets_returns_html_fragment(self) -> None:
        response = self.client.get('/pets')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'text/html; charset=utf-8')
        self.assertIn('<ul id="pet-list">', response.text)

    def test_add_pet_page_renders_full_screen_form(self) -> None:
        response = self.client.get('/pets/new')
        self.assertEqual(response.status_code, 200)
        self.assertIn('action="/pets/new"', response.text)
        self.assertIn('name="name"', response.text)

    def test_create_pet_redirects_to_index_with_selection(self) -> None:
        name, pet_id, response = self._create_pet()
        self.assertEqual(response.status_code, 200)  # TestClient follows the 303
        self.assertIn(name, response.text)
        self.assertIn(f'hx-get="/pets/{pet_id}/detail/edit"', response.text)

        follow_up = self.client.get('/pets')
        self.assertIn(name, follow_up.text)

    def test_create_pet_escapes_html_in_output(self) -> None:
        _name, _pet_id, response = self._create_pet(
            name=f'<script>evil-{uuid.uuid4()}</script>'
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('<script>evil', response.text)
        self.assertIn('&lt;script&gt;evil', response.text)

    def test_edit_pet_via_html_form(self) -> None:
        name, pet_id, _response = self._create_pet()

        form = self.client.get(f'/pets/{pet_id}/detail/edit')
        self.assertEqual(form.status_code, 200)
        self.assertIn(f'hx-put="/pets/{pet_id}/detail/edit"', form.text)
        self.assertIn(name, form.text)

        updated = self.client.put(
            f'/pets/{pet_id}/detail/edit',
            data={
                'name': name,
                'category': 'Cats',
                'tags': 'calm',
                'photo_urls': '',
                'status': 'sold',
            },
        )
        self.assertEqual(updated.status_code, 200)
        self.assertIn('Cats', updated.text)
        self.assertIn('status-sold', updated.text)
        # the saved detail response also carries an out-of-band refresh of the list
        self.assertIn('hx-swap-oob="true"', updated.text)

        detail = self.client.get(f'/pets/{pet_id}/detail')
        self.assertEqual(detail.status_code, 200)
        self.assertIn('Cats', detail.text)

    def test_delete_pet_clears_detail_and_updates_list(self) -> None:
        name, pet_id, _response = self._create_pet()

        delete = self.client.delete(f'/pets/{pet_id}')
        self.assertEqual(delete.status_code, 200)
        self.assertNotIn(name, delete.text)
        self.assertIn('Select a pet', delete.text)

        detail = self.client.get(f'/pets/{pet_id}/detail')
        self.assertEqual(detail.status_code, 404)

    def test_index_page_has_sidebar_and_add_pet_link(self) -> None:
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('href="/pets/new"', response.text)
        self.assertIn('<ul id="pet-list">', response.text)
        self.assertIn('Select a pet to view details', response.text)

    def test_index_page_preselects_pet_from_query_param(self) -> None:
        name, pet_id, _response = self._create_pet()

        response = self.client.get(f'/?selected={pet_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(name, response.text)
        self.assertIn(f'hx-get="/pets/{pet_id}/detail/edit"', response.text)


if __name__ == '__main__':
    unittest.main()
