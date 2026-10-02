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
