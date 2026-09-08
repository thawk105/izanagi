# 段 1 probe — `_reasons()` の WW 順が `PYTHONHASHSEED` で変わることの end-to-end 実測

probe script は repo 外 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/probe_ww_order.py`)。
repo は変更していない。

## 入力

2 transaction が 6 個の共通 key を lost-update する trace。
key は `0000000000000001`〜`0000000000000006`。

```
C 0 0 1 1 6 6 / R 0 <k> 1 0 ×6 / W 0 <k> U 1 1 ×6 / E 0
C 1 1 1 2 6 6 / R 1 <k> 1 0 ×6 / W 1 <k> U 1 2 ×6 / E 1
```

`verify_trace_dir(d, workers=1)` → `result_to_dict` を
`json.dumps(sort_keys=True, separators=(",",":"))` して sha256。

## 出力 (2026-09-08、worktree `dev-wave-t2436-ww-reason-order`、CPython 3.10.12)

```
{"seed": "0",   "anomaly_count": 1, "ww_orders": [[0, 1, ["...06","...01","...04","...03","...02","...05"]]], "digest": "bf6262789f373a7f9d5c9dfbbdb9fc6fbbfd084ac40d17a5093e2d9595c2d266"}
{"seed": "1",   "anomaly_count": 1, "ww_orders": [[0, 1, ["...05","...02","...04","...01","...03","...06"]]], "digest": "99dc7a97e51f5f575b19e3f74b22b7ae77e1d83f54417161598870a066c2303f"}
{"seed": "2",   "anomaly_count": 1, "ww_orders": [[0, 1, ["...04","...01","...05","...03","...06","...02"]]], "digest": "b0aeda2370f044b31b9da598baff151f1cad1cf41d843e3ae5af64709b155e8a"}
{"seed": "3",   "anomaly_count": 1, "ww_orders": [[0, 1, ["...05","...02","...06","...03","...04","...01"]]], "digest": "1b15d361d3b927f99ef378a18d26780df6c2cc0e95c0e1a88799bc99d2d90211"}
{"seed": "4",   "anomaly_count": 1, "ww_orders": [[0, 1, ["...01","...06","...03","...05","...02","...04"]]], "digest": "b3f5fd64ef87844d8f657ee3a4f5c75a662c316a3c715ca15c2810bb023ced33"}
{"seed": "777", "anomaly_count": 1, "ww_orders": [[0, 1, ["...02","...01","...03","...04","...05","...06"]]], "digest": "e5a5085e9daf5ae7b5f8d4042b93dfaf7af33ff32626fc75cb6cbed95d1f74cb"}
```

(`...0N` は `000000000000000N` の末尾。)

## 読み

1. **欠陥は実在し、end-to-end で digest に届く。** 6 seed が 6 通りの ww key 順と 6 通りの digest。
2. **受理集合は seed に依らない。** `anomaly_count` は全 seed で 1。順序だけの問題であり、
   整列を入れても判定は変わらない (規律 2 の面には触れない)。
3. **変動するのは ww だけ。** 同じ probe を全 reason 型で取り直したところ、rw 枝の理由順は
   6 seed すべて `123456` で安定していた。

```
seed 0   ww='614325'  rw='123456'
seed 1   ww='524136'  rw='123456'
seed 2   ww='415362'  rw='123456'
seed 3   ww='526341'  rw='123456'
seed 4   ww='163524'  rw='123456'
seed 777 ww='213456'  rw='123456'
```

wr 枝は rw 枝と同じ `Txn.reads` list を走査するので、同じ理由で安定する。
→ D1817 の scope (WW 交差だけ整列する) は十分である。

## 起点との一致

`output/insights/2026-09-07_8c-rejected-witness-closure/verbatim/codex/s6-reviewB.md:52` が
「二つの共通 WW key の順が `PYTHONHASHSEED` により変わり anomaly digest が
`4a0f6a...` と `b9fb0f...` になった」と報告した現象の、key 数を 6 へ増やした再現である。
同 file の再照準 (「consumer で正規化せず producer の集合走査を `sorted(...)` にせよ」) は D1817 と一致する。

## 追測 — 段 2 プランが指定した trace 配置での確認 (20:12 JST)

段 2 プランは probe と違い **1 file に 2 transaction** を置く配置を選んだ。親がその配置で測り直した。
script は `probe_plan_layout.py` (job dir)。

```
{"seed": "1",   "total_cycles": 1, "anomaly_count": 1, "edge_0_1_reasons": ww[05,02,04,01,03,06], "sha256": "4cff345784b7c7a119c4991d9642903d56ed913e73b217ccdefb3e2c1dfc2369"}
{"seed": "777", "total_cycles": 1, "anomaly_count": 1, "edge_0_1_reasons": ww[02,01,03,04,05,06], "sha256": "0d6e6f8da1c01b1605f6f6f718011f440d0e5e4b617d0fd79c713411a51c46ca"}
```

- 未修正実装で seed 1 と 777 の bytes は**異なる**。プランのテストは修正前に確実に赤になる。
- `total_cycles` と `anomaly_count` はどちらも 1 で seed に依らない。
- 2 subprocess の実所要は **0.224 秒** (`time` の real)。台帳の同型テスト 0.33 秒と同水準。
- **注意 (段 4 で扱う):** seed 777 の順序 `2,1,3,4,5,6` は昇順から transposition 1 個しか離れていない。
  seed 1 (`5,2,4,1,3,6`) との bytes 比較は強いが、seed を 2 本に絞る設計は
  「両方が偶然昇順になる」余地を将来の Python 実装変更に対して残す。
