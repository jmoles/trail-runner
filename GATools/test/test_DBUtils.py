import os
import unittest

from DBUtils import DBUtils

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.pgdb = DBUtils(password=os.environ['PSYCOPG2_DB_PASS'])

    def testNetworkList(self):
        net_s, net_i, net_l = self.pgdb.fetchNetworksList()

        # Verify that the list of networks are equal.
        self.assertEqual(
            len(net_i), len(net_l),
            "Length of network list doesn't match number of integers.")

        # Verify that the net_s is a single string
        self.assertEqual(
            type(net_s), str,
            "Network string is not a single string.")

        net_s_2, net_i_2 = self.pgdb.fetchNetworkCmdPrettyPrint()

        # Verify that the values returned by these two functions
        # are identical.
        self.assertEqual(
            net_s, net_s_2,
            "Network strings for command prompt don't match!")

        self.assertEqual(
            net_i, net_i_2,
            "List of valid network integers don't match.")

if __name__ == '__main__':
    unittest.main()
