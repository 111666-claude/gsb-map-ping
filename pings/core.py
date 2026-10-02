"""地图标记：每人上限、邻近去重、过期清理与稳定排序。

缺陷：每人上限不生效、去重半径不生效、过期不清理、结果不排序、
每次查询扫描全部标记。
"""

class Pings:
    """玩家地图标记台账。"""

    def __init__(self, per_player_max, ttl_ms, dedup_radius):
        self.per_player_max = per_player_max
        self.ttl_ms = ttl_ms
        self.dedup_radius = dedup_radius
        self.pings = []
        self.scanned = 0

    def add(self, player_id, x, y, now_ms):
        """加一个标记。"""
        self.scanned += len(self.pings)
        self.pings.append({"player": player_id, "x": x, "y": y, "at": now_ms})
        return True

    def purge(self, now_ms):
        """清理过期标记，返回清理数量。"""
        self.scanned += len(self.pings)
        return 0

    def active(self, now_ms):
        """当前有效的标记。"""
        self.scanned += len(self.pings)
        return [(ping["player"], ping["x"], ping["y"]) for ping in self.pings]

    def count(self):
        return len(self.pings)

    def scanned_count(self):
        return self.scanned
