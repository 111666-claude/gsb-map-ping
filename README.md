# map-ping

地图标记：每人上限、邻近去重、过期清理与稳定排序，只用 Python 标准库。

```
python3 -m pings.cli --sample cap
python3 -m pings.cli --sample dedup
python3 -m pings.cli --sample ttl
python3 -m pings.cli --sample order
python3 -m pings.cli --sample scan
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **每人上限**：同一个玩家最多保留 `per_player_max` 个标记，超出时移除该玩家
  最早的标记。
- **去重**：同一个玩家在 `dedup_radius` 内重复标记时只保留最新一个，
  坐标与时间都更新；距离正好等于半径算重复。
- **过期**：标记存在时间达到 `ttl_ms` 就算过期，`purge` 清理并返回数量，
  `active` 只返回未过期的。
- **顺序**：`active` 按玩家 id 升序、同一玩家按时间升序排列。
- **不变量**：`active` 里每个玩家的标记数不超过 `per_player_max`；
  同一串标记序列重复执行结果相同。
- **查询代价**：`purge` 与 `active` 不许遍历全部标记，`scanned_count`
  不随标记总数线性增长。
- **规模**：10 万标记、每秒 10 万次查询，单次摊还 O(新增标记数)。

## 输出契约（不改格式）

```
active=..
purged=.. active=..
order=..
scanned=..
```

## 目录

```
pings/core.py   上限、去重、过期与排序
pings/cli.py    命令行入口
tests/          unittest 用例
```
