"""命令行入口：跑地图标记样例。"""

import argparse

from .core import Pings


def build_parser():
    parser = argparse.ArgumentParser(prog="map-ping", description="地图标记")
    parser.add_argument("--sample", default="cap",
                        help="cap / dedup / ttl / order / scan")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "cap":
        pings = Pings(per_player_max=2, ttl_ms=100000, dedup_radius=1)
        for index in range(3):
            pings.add("p1", index * 100, 0, index)
        print("active=%d" % len(pings.active(10)))
    elif args.sample == "dedup":
        pings = Pings(per_player_max=5, ttl_ms=100000, dedup_radius=10)
        pings.add("p1", 0, 0, 0)
        pings.add("p1", 5, 0, 10)
        print("active=%d" % len(pings.active(10)))
    elif args.sample == "ttl":
        pings = Pings(per_player_max=5, ttl_ms=1000, dedup_radius=1)
        pings.add("p1", 0, 0, 0)
        purged = pings.purge(1001)
        print("purged=%d active=%d" % (purged, len(pings.active(1001))))
    elif args.sample == "order":
        pings = Pings(per_player_max=5, ttl_ms=100000, dedup_radius=1)
        pings.add("b", 0, 0, 0)
        pings.add("a", 100, 0, 1)
        print("order=%s" % ",".join(player for player, _, _ in pings.active(10)))
    elif args.sample == "scan":
        pings = Pings(per_player_max=5, ttl_ms=100000, dedup_radius=1)
        for index in range(3000):
            pings.add("p-%d" % index, index, 0, index)
        for _ in range(3000):
            pings.active(100000)
        print("scanned=%d" % pings.scanned_count())
    else:
        raise SystemExit("需要 --sample cap|dedup|ttl|order|scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
