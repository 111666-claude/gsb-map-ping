"""地图标记：每人上限、邻近去重、过期清理与稳定排序。

数据结构：
- 每个玩家一个按 (时间, 序号) 有序的定长列表，去重与淘汰都是 O(per_player_max)。
- 全局过期最小堆，惰性清理：每条标记至多入堆一次、出堆一次，
  purge/active 只弹出堆顶已过期或已失效的条目，不遍历全部标记。
- 玩家顺序与 active 结果做缓存，仅在新增或清理发生变化时失效。
"""

import heapq


class Pings:
    """玩家地图标记台账。"""

    def __init__(self, per_player_max, ttl_ms, dedup_radius):
        self.per_player_max = per_player_max
        self.ttl_ms = ttl_ms
        self.dedup_radius = dedup_radius
        self.scanned = 0
        self._players = {}
        self._live = {}
        self._expiry = []
        self._seq = 0
        self._live_count = 0
        self._player_order = None
        self._active_cache = None

    def add(self, player_id, x, y, now_ms):
        """加一个标记；同一玩家半径内重复标记合并到最新一个。"""
        records = self._players.get(player_id)
        if records is not None:
            radius_sq = self.dedup_radius * self.dedup_radius
            match = None
            best_sq = None
            for record in records:
                self.scanned += 1
                dx = record["x"] - x
                dy = record["y"] - y
                dist_sq = dx * dx + dy * dy
                if dist_sq <= radius_sq and (best_sq is None or dist_sq < best_sq):
                    best_sq = dist_sq
                    match = record
            if match is not None:
                match["x"] = x
                match["y"] = y
                match["at"] = now_ms
                records.sort(key=lambda item: (item["at"], item["seq"]))
                heapq.heappush(self._expiry, (now_ms, match["seq"]))
                self._invalidate()
                return True

        record = {
            "player": player_id,
            "x": x,
            "y": y,
            "at": now_ms,
            "seq": self._seq,
        }
        self._seq += 1
        records = self._players.setdefault(player_id, [])
        records.append(record)
        records.sort(key=lambda item: (item["at"], item["seq"]))
        self._live[record["seq"]] = record
        heapq.heappush(self._expiry, (now_ms, record["seq"]))
        self._live_count += 1

        if len(records) > self.per_player_max:
            oldest = records.pop(0)
            self._live.pop(oldest["seq"], None)
            self._live_count -= 1

        self._invalidate()
        return True

    def purge(self, now_ms):
        """清理过期标记，返回清理数量。"""
        return self._expire(now_ms)

    def active(self, now_ms):
        """当前有效的标记：玩家 id 升序、同玩家按时间升序。"""
        self._expire(now_ms)
        if self._active_cache is None:
            result = []
            for player_id in self._ordered_players():
                for record in self._players[player_id]:
                    result.append((player_id, record["x"], record["y"]))
            self._active_cache = result
        return self._active_cache

    def count(self):
        return self._live_count

    def scanned_count(self):
        return self.scanned

    def _expire(self, now_ms):
        purged = 0
        changed = False
        heap = self._expiry
        deadline = now_ms - self.ttl_ms
        while heap and heap[0][0] <= deadline:
            at, seq = heapq.heappop(heap)
            self.scanned += 1
            record = self._live.get(seq)
            if record is None or record["at"] != at:
                continue
            records = self._players[record["player"]]
            records.remove(record)
            del self._live[seq]
            self._live_count -= 1
            purged += 1
            changed = True
            if not records:
                del self._players[record["player"]]
        if changed:
            self._invalidate()
        return purged

    def _ordered_players(self):
        if self._player_order is None:
            self._player_order = sorted(self._players)
        return self._player_order

    def _invalidate(self):
        self._player_order = None
        self._active_cache = None
