# Helpers for testing.
import numpy as np
import os
import unittest

# Parts of design under test.
from ..DBUtils import DBUtils
from ..trail.trail import trail
from ..trail.trail import GridVals


TEST_TRAIL = np.matrix(
[[0,0,0,0,0],
 [1,1,7,1,0],
 [0,0,0,1,0],
 [0,0,0,1,0],
 [0,0,0,2,0]])

TEST_TRAIL_DB_ID     = 1

TEST_TRAIL_FOOD_CNT  = 5
TEST_TRAIL_GAP_CNT   = 1
TEST_TRAIL_START_CNT = 2
TEST_TRAIL_X         = 5
TEST_TRAIL_Y         = 5

AGENT_INIT_ROT  = 0
AGENT_VAL     = 2
AGENT_START_X = 4
AGENT_START_Y = 4


class TestTrailFunctions(unittest.TestCase):

    def setUp(self):
        # This class requires accessing the database.
        self.pgdb  = DBUtils(password=os.environ['PSYCOPG2_DB_PASS'])
        self.trail_i = trail()
        self.trail_i.readTrail(TEST_TRAIL_DB_ID)

    def test_GridVals(self):
        # Verify that all of the grid values are unique.
        self.assertEqual(
            len(GridVals.FULL_LIST), len(set(GridVals.FULL_LIST)),
            "There are duplicate values in GridVals!")

    def test_getMatrix(self):
        self.assertTrue(
            (self.trail_i.getMatrix()==TEST_TRAIL).all(),
            "Input trail does not match test trail!")

    def test_getTrailDim(self):
        trailx, traily = self.trail_i.getTrailDim()

        self.assertEqual(trailx, TEST_TRAIL_X)
        self.assertEqual(traily, TEST_TRAIL_Y)

    def test_readTrail(self):
        trail_temp = trail()
        trail_temp.readTrail(TEST_TRAIL_DB_ID)

        self.assertTrue(
            (trail_temp.getMatrix()==TEST_TRAIL).all(),
            "Input trail does not match test trail!")

    def test_readTrailInstant(self):
        trail_temp = trail()
        trail_temp.readTrailInstant(TEST_TRAIL, "Stuff", 0)

        self.assertTrue(
            (trail_temp.getMatrix()==TEST_TRAIL).all(),
            "Input trail does not match test trail!")

    def test_getTrailDim(self):
        trail_x, trail_y = self.trail_i.getTrailDim()

        self.assertEqual(
            trail_x, TEST_TRAIL_X,
            "Max X dimension of trail does not match test trail!")

        self.assertEqual(
            trail_y, TEST_TRAIL_Y,
            "Max Y dimension of trail does not match test trail!")

    def test_turnLeft(self):
        tt_wc = TEST_TRAIL.copy()

        test_angle = 360

        for idx in range(0, 200):
            self.trail_i.turnLeft()

            test_angle -= 90

            if test_angle == 90:
                tt_wc.itemset((4, 3), GridVals.ANT90)
            elif test_angle == 180:
                tt_wc.itemset((4, 3), GridVals.ANT180)
            elif test_angle == 270:
                tt_wc.itemset((4, 3), GridVals.ANT270)
            elif test_angle == 0:
                tt_wc.itemset((4, 3), GridVals.ANT0)
                test_angle = 360

            self.assertTrue(
                (self.trail_i.getMatrix()==tt_wc).all(), (
                    "Test trail does not match on iteration {0}!\n" +
                    "Expected:\n{1}\nActual:\n{2}").format(
                        idx, tt_wc, self.trail_i.getMatrix()))

    def test_turnRight(self):
        tt_wc = TEST_TRAIL.copy()

        test_angle = 0

        for idx in range(0, 200):
            self.trail_i.turnRight()

            test_angle += 90

            if test_angle == 90:
                tt_wc.itemset((4, 3), GridVals.ANT90)
            elif test_angle == 180:
                tt_wc.itemset((4, 3), GridVals.ANT180)
            elif test_angle == 270:
                tt_wc.itemset((4, 3), GridVals.ANT270)
            elif test_angle == 360:
                tt_wc.itemset((4, 3), GridVals.ANT0)
                test_angle = 0

            self.assertTrue(
                (self.trail_i.getMatrix()==tt_wc).all(), (
                    "Test trail does not match on iteration {0}!\n" +
                    "Expected:\n{1}\nActual:\n{2}").format(
                        idx, tt_wc, self.trail_i.getMatrix()))

    def test_noMove(self):
        for idx in range(0, 200):
            self.trail_i.noMove()

            self.assertTrue(
                (self.trail_i.getMatrix()==TEST_TRAIL).all(), (
                    "Test trail does not match on iteration {0}!\n" +
                    "Expected:\n{1}\nActual:\n{2}").format(
                        idx, TEST_TRAIL, self.trail_i.getMatrix()))

    def test_moveFoward(self):
        tt_wc = TEST_TRAIL.copy()

        # Move the agent forward 5 times to verify it also wraps around top.
        for idx in range(0, 5):
            self.trail_i.moveForward()
            tt_wc.itemset((4 - idx, 3), GridVals.HIST)
            tt_wc.itemset((3 - idx, 3), GridVals.ANT0)

            self.assertTrue(
                (self.trail_i.getMatrix()==tt_wc).all(), (
                    "Test trail does not match on iteration {0}!\n" +
                    "Expected:\n{1}\nActual:\n{2}").format(
                        idx, tt_wc, self.trail_i.getMatrix()))


    def test_getFoodConsumed(self):
        expect_food = 0

        for idx in range(0, 11):
            if idx == 0:
                pass
            elif idx == 1:
                self.trail_i.moveForward()
                expect_food += 1
            elif idx == 2:
                self.trail_i.moveForward()
                expect_food += 1
            elif idx == 3:
                self.trail_i.turnRight()
            elif idx == 4:
                self.trail_i.turnLeft()
            elif idx == 5:
                self.trail_i.noMove()
            elif idx == 6:
                self.trail_i.moveForward()
                expect_food += 1
            elif idx == 7:
                self.trail_i.turnLeft()
            elif idx == 8:
                self.trail_i.moveForward()
            elif idx == 9:
                self.trail_i.moveForward()
                expect_food += 1
            elif idx == 10:
                self.trail_i.moveForward()
                expect_food += 1

            self.assertEqual(
                self.trail_i.getFoodConsumed(), expect_food,
                ("Agent is reporting {0} food consumed " +
                "when it should have {1} on iteration {2}.").format(
                    self.trail_i.getFoodConsumed(), expect_food, idx))

    def test_isFoodAhead(self):
        for idx in range(0, 11):
            if idx == 0:
                expect_ahead = True
            elif idx == 1:
                self.trail_i.moveForward()
                expect_ahead = True
            elif idx == 2:
                self.trail_i.moveForward()
                expect_ahead = True
            elif idx == 3:
                self.trail_i.turnRight()
                expect_ahead = False
            elif idx == 4:
                self.trail_i.turnLeft()
                expect_ahead = True
            elif idx == 5:
                self.trail_i.noMove()
                expect_ahead = True
            elif idx == 6:
                self.trail_i.moveForward()
                expect_ahead = False
            elif idx == 7:
                self.trail_i.turnLeft()
                expect_ahead = False
            elif idx == 8:
                self.trail_i.moveForward()
                expect_ahead = True
            elif idx == 9:
                self.trail_i.moveForward()
                expect_ahead = True
            elif idx == 10:
                self.trail_i.moveForward()
                expect_ahead = False

            self.assertEqual(
                self.trail_i.isFoodAhead(), expect_ahead,
                ("Agent is reporting {0} food ahead " +
                "when it should have {1} on iteration {2}.").format(
                    self.trail_i.isFoodAhead(), expect_ahead, idx))

    def test_getNumMoves(self):
        expect_moves = 0

        for idx in range(0, 11):
            if idx == 0:
                pass
            elif idx == 1:
                self.trail_i.moveForward()
            elif idx == 2:
                self.trail_i.moveForward()
            elif idx == 3:
                self.trail_i.turnRight()
            elif idx == 4:
                self.trail_i.turnLeft()
            elif idx == 5:
                self.trail_i.noMove()
            elif idx == 6:
                self.trail_i.moveForward()
            elif idx == 7:
                self.trail_i.turnLeft()
            elif idx == 8:
                self.trail_i.moveForward()
            elif idx == 9:
                self.trail_i.moveForward()
            elif idx == 10:
                self.trail_i.moveForward()

            if (idx != 0):
                expect_moves += 1

            self.assertEqual(
                self.trail_i.getNumMoves(), expect_moves,
                ("Agent is reporting {0} moves " +
                "when it should have {1} on iteration {2}.").format(
                    self.trail_i.getNumMoves(), expect_moves, idx))

    def test_getFoodConsumed(self):
        expect_food   = 0
        expect_remain = TEST_TRAIL_FOOD_CNT

        for idx in range(0, 11):
            if idx == 0:
                pass
            elif idx == 1:
                self.trail_i.moveForward()
                expect_food += 1
                expect_remain -= 1
            elif idx == 2:
                self.trail_i.moveForward()
                expect_food += 1
                expect_remain -= 1
            elif idx == 3:
                self.trail_i.turnRight()
            elif idx == 4:
                self.trail_i.turnLeft()
            elif idx == 5:
                self.trail_i.noMove()
            elif idx == 6:
                self.trail_i.moveForward()
                expect_food += 1
                expect_remain -= 1
            elif idx == 7:
                self.trail_i.turnLeft()
            elif idx == 8:
                self.trail_i.moveForward()
            elif idx == 9:
                self.trail_i.moveForward()
                expect_food += 1
                expect_remain -= 1
            elif idx == 10:
                self.trail_i.moveForward()
                expect_food += 1
                expect_remain -= 1

            act_food, act_remain = self.trail_i.getFoodStats()

            self.assertEqual(
                act_food, expect_food,
                ("Agent is reporting {0} food consumed " +
                "when it should have {1} on iteration {2}.").format(
                    act_food, expect_food, idx))

            self.assertEqual(
                act_remain, expect_remain,
                ("Agent is reporting {0} food remaining " +
                "when it should have {1} on iteration {2}.").format(
                    act_remain, expect_remain, idx))


if __name__ == '__main__':
    unittest.main()
