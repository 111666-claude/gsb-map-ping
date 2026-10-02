"""地图标记：每人上限、邻近去重、过期清理与稳定排序。

实现口径：
- 过期用最小堆按时间弹出，purge/active 只触碰到期的标记；
- 去重与上限只查该玩家自己的标记列表；
- scanned 只统计内部维护时真正检查的标记数，不随标记总数线性增长。
"""

import heapq
import itertools


class Pings:
    """玩家地图标记台账。"""

    def __init__(self, per_player_max, ttl_ms, dedup_radius):
        self.per_player_max = per_player_max
        self.ttl_ms = ttl_ms
        self.dedup_radius = dedup_radius
        self.scanned = 0
        self._ids = itertools.count()
        self._live = {}
        self._by_player = {}
        self._expiry = []
        self._player_order = None

    def _drop(self, entry):
        del self._live[entry["id"]]
        entries = self._by_player[entry["player"]]
        entries.remove(entry)
        if not entries:
            del self._by_player[entry["player"]]
            self._player_order = None

    def _expire(self, now_ms):
        removed = 0
        heap = self._expiry
        while heap and heap[0][0] + self.ttl_ms <= now_ms:
            _, _, entry = heapq.heappop(heap)
            self.scanned += 1
            if entry["id"] in self._live:
                self._drop(entry)
                removed += 1
        return removed

    def add(self, player_id, x, y, now_ms):
        """加一个标记。"""
        self._expire(now_ms)
        entries = self._by_player.get(player_id)
        if entries:
            self.scanned += len(entries)
            radius_sq = self.dedup_radius * self.dedup_radius
            for old in list(entries):
                dx = old["x"] - x
                dy = old["y"] - y
                if dx * dx + dy * dy <= radius_sq:
                    self._drop(old)
        entry = {"id": next(self._ids), "player": player_id,
                 "x": x, "y": y, "at": now_ms}
        self._live[entry["id"]] = entry
        if player_id not in self._by_player:
            self._by_player[player_id] = []
            self._player_order = None
        entries = self._by_player[player_id]
        entries.append(entry)
        entries.sort(key=lambda item: (item["at"], item["id"]))
        heapq.heappush(self._expiry, (now_ms, entry["id"], entry))
        while len(entries) > self.per_player_max:
            self.scanned += 1
            self._drop(entries[0])
        return True

    def purge(self, now_ms):
        """清理过期标记，返回清理数量。"""
        return self._expire(now_ms)

    def active(self, now_ms):
        """当前有效的标记，按玩家 id 升序、同玩家按时间升序。"""
        self._expire(now_ms)
        if self._player_order is None:
            self._player_order = sorted(self._by_player)
        result = []
        for player in self._player_order:
            for entry in self._by_player[player]:
                result.append((player, entry["x"], entry["y"]))
        return result

    def count(self):
        return len(self._live)

    def scanned_count(self):
        return self.scanned
