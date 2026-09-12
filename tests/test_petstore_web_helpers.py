import unittest

from petstore_web.pets.routes import _detail_edit_html, _row_html, _status_options

PET = {
    'id': 1,
    'name': 'Rex',
    'category': 'Dogs',
    'photo_urls': ['https://example.com/rex.jpg'],
    'tags': ['friendly', 'trained'],
    'status': 'available',
}


class StatusOptionsTests(unittest.TestCase):
    def test_marks_current_status_selected(self) -> None:
        html = _status_options('pending')
        self.assertIn('<option value="pending" selected>', html)
        self.assertIn('<option value="available">', html)
        self.assertIn('<option value="sold">', html)


class RowHtmlTests(unittest.TestCase):
    def test_escapes_and_renders_row(self) -> None:
        html = _row_html(PET)
        self.assertIn('Rex', html)
        self.assertIn('status-available', html)
        self.assertIn('hx-get="/pets/1/detail"', html)

    def test_missing_category_and_tags_show_placeholder(self) -> None:
        pet = {**PET, 'category': None, 'tags': []}
        html = _row_html(pet)
        self.assertIn('—', html)

    def test_marks_selected_row(self) -> None:
        html = _row_html(PET, selected_id=1)
        self.assertIn('class="pet-row selected"', html)

        html = _row_html(PET, selected_id=2)
        self.assertIn('class="pet-row "', html)


class DetailEditHtmlTests(unittest.TestCase):
    def test_marks_current_status(self) -> None:
        html = _detail_edit_html(PET)
        self.assertIn('value="Rex"', html)
        self.assertIn('<option value="available" selected>', html)
        self.assertIn('hx-put="/pets/1/detail/edit"', html)


if __name__ == '__main__':
    unittest.main()
