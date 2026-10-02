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


if __name__ == "__main__":
    unittest.main()


class CapTest(unittest.TestCase):
    def test_cap_evicts_oldest(self):
        pings = Pings(2, 100000, 1)
        for index in range(3):
            pings.add("p1", index * 100, 0, index)
        self.assertEqual(pings.active(10), [("p1", 100, 0), ("p1", 200, 0)])

    def test_cap_is_per_player(self):
        pings = Pings(1, 100000, 1)
        pings.add("a", 0, 0, 0)
        pings.add("b", 100, 0, 0)
        pings.add("a", 1000, 0, 1)
        self.assertEqual(pings.active(10), [("a", 1000, 0), ("b", 100, 0)])


class DedupTest(unittest.TestCase):
    def test_within_radius_merges_to_latest(self):
        pings = Pings(5, 100000, 10)
        pings.add("p1", 0, 0, 0)
        pings.add("p1", 5, 0, 10)
        self.assertEqual(pings.active(10), [("p1", 5, 0)])

    def test_exact_radius_counts_as_duplicate(self):
        pings = Pings(5, 100000, 10)
        pings.add("p1", 0, 0, 0)
        pings.add("p1", 10, 0, 5)
        self.assertEqual(pings.active(10), [("p1", 10, 0)])

    def test_just_outside_radius_stays(self):
        pings = Pings(5, 100000, 10)
        pings.add("p1", 0, 0, 0)
        pings.add("p1", 11, 0, 5)
        self.assertEqual(pings.active(10), [("p1", 0, 0), ("p1", 11, 0)])

    def test_dedup_updates_timestamp_for_ttl(self):
        pings = Pings(5, 100, 10)
        pings.add("p1", 0, 0, 0)
        pings.add("p1", 5, 0, 90)
        self.assertEqual(pings.active(150), [("p1", 5, 0)])
        self.assertEqual(pings.active(190), [])


class TtlTest(unittest.TestCase):
    def test_reaching_ttl_expires(self):
        pings = Pings(5, 1000, 1)
        pings.add("p1", 0, 0, 0)
        self.assertEqual(pings.active(999), [("p1", 0, 0)])
        self.assertEqual(pings.active(1000), [])

    def test_purge_returns_count_and_clears(self):
        pings = Pings(5, 1000, 1)
        pings.add("p1", 0, 0, 0)
        pings.add("p2", 100, 0, 500)
        self.assertEqual(pings.purge(1001), 1)
        self.assertEqual(pings.active(1001), [("p2", 100, 0)])
        self.assertEqual(pings.purge(1001), 0)


class OrderTest(unittest.TestCase):
    def test_sorted_by_player_then_time(self):
        pings = Pings(5, 100000, 1)
        pings.add("b", 0, 0, 0)
        pings.add("a", 100, 0, 1)
        pings.add("a", 200, 0, 0)
        self.assertEqual(pings.active(10), [("a", 200, 0), ("a", 100, 0), ("b", 0, 0)])

    def test_replay_same_sequence_is_stable(self):
        def run():
            pings = Pings(2, 1000, 10)
            pings.add("b", 0, 0, 0)
            pings.add("a", 100, 0, 1)
            pings.add("b", 5, 0, 2)
            pings.add("a", 200, 0, 3)
            pings.add("a", 300, 0, 4)
            return pings.active(10)

        self.assertEqual(run(), run())


class ScanTest(unittest.TestCase):
    def test_scanned_does_not_scale_with_total(self):
        pings = Pings(5, 100000, 1)
        for index in range(3000):
            pings.add("p-%d" % index, index, 0, index)
        for _ in range(3000):
            pings.active(100000)
        self.assertLessEqual(pings.scanned_count(), 6000)

    def test_repeated_active_does_not_rescan(self):
        pings = Pings(5, 100000, 1)
        for index in range(100):
            pings.add("p-%d" % index, index, 0, index)
        pings.active(100)
        scanned = pings.scanned_count()
        for _ in range(100):
            pings.active(100)
        self.assertEqual(pings.scanned_count(), scanned)
