import unittest

from pings.core import Pings


class BasicTest(unittest.TestCase):
    def test_empty_active(self):
        self.assertEqual(Pings(3, 1000, 10).active(0), [])

    def test_add_then_active(self):
        pings = Pings(3, 1000, 10)
        pings.add("p1", 1, 2, 0)
        self.assertEqual(pings.active(0), [("p1", 1, 2)])

    def test_purge_empty_is_zero(self):
        self.assertEqual(Pings(3, 1000, 10).purge(0), 0)

    def test_limits_are_stored(self):
        pings = Pings(2, 1000, 5)
        self.assertEqual((pings.per_player_max, pings.ttl_ms, pings.dedup_radius), (2, 1000, 5))

    def test_scanned_starts_at_zero(self):
        self.assertEqual(Pings(3, 1000, 10).scanned_count(), 0)


class CapTest(unittest.TestCase):
    def test_cap_evicts_oldest(self):
        pings = Pings(2, 100000, 1)
        pings.add("p1", 0, 0, 0)
        pings.add("p1", 100, 0, 1)
        pings.add("p1", 200, 0, 2)
        self.assertEqual(pings.active(10), [("p1", 100, 0), ("p1", 200, 0)])

    def test_cap_is_per_player(self):
        pings = Pings(1, 100000, 1)
        pings.add("p1", 0, 0, 0)
        pings.add("p2", 50, 0, 1)
        pings.add("p1", 200, 0, 2)
        self.assertEqual(pings.active(10), [("p1", 200, 0), ("p2", 50, 0)])

    def test_active_never_exceeds_cap(self):
        pings = Pings(2, 100000, 1)
        for index in range(10):
            pings.add("p1", index * 100, 0, index)
        self.assertLessEqual(len(pings.active(20)), 2)


class DedupTest(unittest.TestCase):
    def test_within_radius_keeps_latest(self):
        pings = Pings(5, 100000, 10)
        pings.add("p1", 0, 0, 0)
        pings.add("p1", 5, 0, 10)
        self.assertEqual(pings.active(10), [("p1", 5, 0)])

    def test_exactly_radius_is_duplicate(self):
        pings = Pings(5, 100000, 10)
        pings.add("p1", 0, 0, 0)
        pings.add("p1", 6, 8, 10)
        self.assertEqual(pings.active(10), [("p1", 6, 8)])

    def test_beyond_radius_keeps_both(self):
        pings = Pings(5, 100000, 10)
        pings.add("p1", 0, 0, 0)
        pings.add("p1", 11, 0, 10)
        self.assertEqual(len(pings.active(10)), 2)

    def test_dedup_only_same_player(self):
        pings = Pings(5, 100000, 10)
        pings.add("p1", 0, 0, 0)
        pings.add("p2", 1, 0, 10)
        self.assertEqual(len(pings.active(10)), 2)


class TtlTest(unittest.TestCase):
    def test_reaching_ttl_expires(self):
        pings = Pings(5, 1000, 1)
        pings.add("p1", 0, 0, 0)
        self.assertEqual(pings.active(1000), [])

    def test_just_below_ttl_survives(self):
        pings = Pings(5, 1000, 1)
        pings.add("p1", 0, 0, 0)
        self.assertEqual(len(pings.active(999)), 1)

    def test_purge_returns_count(self):
        pings = Pings(5, 1000, 1)
        pings.add("p1", 0, 0, 0)
        pings.add("p2", 100, 0, 500)
        self.assertEqual(pings.purge(1001), 1)
        self.assertEqual(pings.active(1001), [("p2", 100, 0)])


class OrderTest(unittest.TestCase):
    def test_sorted_by_player_then_time(self):
        pings = Pings(5, 100000, 1)
        pings.add("b", 0, 0, 1)
        pings.add("a", 0, 0, 2)
        pings.add("b", 100, 0, 0)
        self.assertEqual(pings.active(10),
                         [("a", 0, 0), ("b", 100, 0), ("b", 0, 0)])

    def test_replay_is_deterministic(self):
        script = [("p1", 0, 0, 0), ("p2", 3, 4, 1), ("p1", 1, 1, 2),
                  ("p1", 100, 0, 3), ("p2", 3, 4, 4), ("p1", 200, 0, 5)]

        def run():
            pings = Pings(2, 1000, 10)
            for args in script:
                pings.add(*args)
            return pings.active(6)

        self.assertEqual(run(), run())


class ScanCostTest(unittest.TestCase):
    def test_scanned_not_linear_in_total(self):
        pings = Pings(5, 100000, 1)
        for index in range(3000):
            pings.add("p-%d" % index, index, 0, index)
        for _ in range(3000):
            pings.active(100000)
        self.assertLessEqual(pings.scanned_count(), 6000)


if __name__ == "__main__":
    unittest.main()
