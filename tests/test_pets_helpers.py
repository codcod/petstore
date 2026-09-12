import unittest

from petstore_api.pets.routes import _pet_values, _split_csv
from petstore_api.pets.schemas import PetCreate


class SplitCsvTests(unittest.TestCase):
    def test_splits_and_strips(self) -> None:
        self.assertEqual(_split_csv('a, b ,c'), ['a', 'b', 'c'])

    def test_drops_empty_items(self) -> None:
        self.assertEqual(_split_csv('a,,b,'), ['a', 'b'])

    def test_none_and_empty_string(self) -> None:
        self.assertEqual(_split_csv(None), [])
        self.assertEqual(_split_csv(''), [])


class PetValuesTests(unittest.TestCase):
    def test_splits_csv_fields(self) -> None:
        data = PetCreate(name='Rex', category='Dogs', tags='a, b', photo_urls='x, y')
        values = _pet_values(data)
        self.assertEqual(values['tags'], ['a', 'b'])
        self.assertEqual(values['photo_urls'], ['x', 'y'])
        self.assertEqual(values['name'], 'Rex')


if __name__ == '__main__':
    unittest.main()
