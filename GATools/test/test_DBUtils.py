import os
import unittest

from ..DBUtils import DBUtils

class TestDatabaseUtils(unittest.TestCase):

    def setUp(self):
        # Test Fixture
        self.pgdb = DBUtils(config_file='config/config.json')

    def test_getIDs(self):
        # Checks that
        results = self.pgdb.getIDs()

        # Verify each list is a list of ints.
        for key, curr_list in results.items():
            self.assertTrue(all(isinstance(x, int) for x in curr_list))

    def test_getNetworkByID(self):
        pass

    def test_getTrailData(self):
        pass


if __name__ == '__main__':
    unittest.main()
