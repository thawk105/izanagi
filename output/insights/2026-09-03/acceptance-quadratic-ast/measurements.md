# 親が取った実測値 (逐語)

すべて親が login node 上で直接実行した。pytest は hook が login node で拒否するため、
pytest を要する測定だけ計算ノードへ dispatch した。台帳由来の値と実測値は区別して書く。

## 1. 二乗の内訳 (cProfile、修正前)

`python3 -I -B` で `_load_static_modules()` を 1 回。

```
         255336801 function calls (254805670 primitive calls) in 59.142 seconds
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.001    0.001   59.146   59.146 p3_b4_wiring_probe.py:1005(_load_static_modules)
       45    0.008    0.000   57.585    1.280 p3_b4_wiring_probe.py:828(_analyze_source)
     3023    0.013    0.000   56.848    0.019 /usr/lib/python3.10/ast.py:343(get_source_segment)
     3023   46.151    0.015   56.834    0.019 /usr/lib/python3.10/ast.py:307(_splitlines_no_ff)
243665193/243665190   10.438    0.000   10.438    0.000 {built-in method builtins.len}
       45    0.000    0.000    0.299    0.007 /usr/lib/python3.10/ast.py:33(parse)
       45    0.299    0.007    0.299    0.007 {built-in method builtins.compile}
```

profiler を外した素の所要は 27.4 秒。

## 2. 修正前後の準備所要

```
修正前 (test と同じ呼び方: _load_runtime(guard) のあと _load_static_modules())
  import       0.07
  guard+audit  0.01
  load_runtime 29.65   <- 内部で _load_static_modules() が走る
  load_static  26.81   <- test 自身がもう一度呼ぶ
  build_inv    0.00
  seal         0.30
  TOTAL SETUP 56.84

修正前 (製品 main と同じ呼び方)
  load_static           27.40
  load_runtime(w/static) 2.08
  PRODUCTION-STYLE TOTAL 29.48

修正後 (製品 main と同じ呼び方)
  load_static AFTER fix: 0.89 s  (n=45)
  load_runtime(w/static): 0.85 s
  PRODUCTION-STYLE SETUP: 1.74 s
```

memoize だけの試作 (実装前の生死確認): `load_static WITH memoized splitlines: 1.07 s (n=45)`。

## 3. guard 文字列の同一性 (親の独立検算)

テストの実装を信用せず、親が別スクリプトで stdlib と直接比較した。

```
module 数: 45
比較した if node: 3282
  複数行にまたがるもの: 353
  stdlib が None を返すもの (fallback 経路): 0
  不一致: 0

_split_source_lines の呼び出し回数: 45 (module 数 45)
  module あたり: 1.0

結果: guard は完全一致、分割は module あたり 1 回。
```

## 4. 境界の baseline (レンズ D の must-fix を反証した測定)

C-2 の全ケースを pytest 抜きで再現した。

```
  OK 非ASCII前置                     'target'
  OK 非ASCII範囲内                    'α'
  OK 改行 '\n' / '\r\n' / '\r'       いずれも一致
  OK 非分割 '\x0c' '\x1c' '\x85' ' ' ' '  いずれも一致
  OK padded=False / padded=True     いずれも一致
  OK end_col_offset=0               'first\n'
  OK 空 source                       両者とも IndexError
  OK 行数超過                          両者とも IndexError
  OK location 欠落                    両者とも None

splitter の直接比較:
  OK ''             -> []
  OK 'a'            -> ['a']
  OK 'a\n'          -> ['a\n']
  OK 'a\nb\n'       -> ['a\n', 'b\n']
  OK 'a\n\n'        -> ['a\n', '\n']
  OK 'a\r\n'        -> ['a\r\n']
  OK 'a\rb'         -> ['a\r', 'b']
  OK 'a\x0cb'       -> ['a\x0cb']
  OK 'a b'     -> ['a b']

検査 25 件、失敗 0 件
```

CPython 3.10 の `ast._splitlines_no_ff` 本文は末尾で `if next_line:` のときだけ append する。
したがって終端空要素は作らない。実測:
`'' -> []`、`'a\n' -> ['a\n']`、`'a' -> ['a']`、`'a\n\n' -> ['a\n', '\n']`。

## 5. 変異の到達性 (事前登録の前提)

対象 45 module / `if` node 3282 個の走査。

```
if node 総数: 3282
非 ASCII を含む module: 36
M-A1 (guard の前に非 ASCII がある if): 0 件   -> 等価変異。合成 fixture が要る
M-A2 (form feed 等を含む module):     0 件   -> 等価変異。合成 fixture が要る
M-A3 (複数行にまたがる if.test):      353 件  -> 実データで殺せる
```

## 6. 直列化の鎖 (台帳由来。scheduling hint であり性能測定ではない)

```
台帳総 worker-time W = 11956.5 s (19519 node)
鎖 X (real-repo group)      = 303.7 s   96 node (厳密一致で 95/96 照合、1 件は台帳に不在)
  うち書き手                =   0.0 s    4 node
  うち読み手                = 303.7 s   92 node
鎖 Y (certified_evidence)   = 258.1 s   17 test (間接 fixture 依存の閉包込み)
最長単体 node               = 140.0 s
最大 xdist group            = 122.3 s   p3-b4-material-report / 42 node
```

`real-repo` group に入る node は、既存の `xdist_group` marker を持たないものだけである
(`conftest.py:2001` の条件を再現)。既存 marker を持つ node は 0 件だった。

鎖 X の上位 node (すべて `parent='read'`):

```
  94.0 s  test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment
  16.0 s  test_codex_reasoning_ab.py::test_cleaned_snapshot_records_absent_commit_graph...
  14.0 s  test_acceptance_schedule_order.py::test_g6_all_real_repo_items_stay_one_unit...
  13.0 s  test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official...
  12.0 s  test_codex_reasoning_ab.py::test_material_replay_rejects_task_manifest...
```

`lock 保持のまま yield する fixture` は repo 全体で `certified_evidence` の 1 件だけであり、
`DW-G03` の族一般化は成立しない (局所修復の型)。

## 7. 修正後の焦点走 (計算ノード)

```
48 workers [63 items]
63 passed in 10.49s      (request 974305.nqsv, Elapse 15S)
```

変異走の baseline (同 file、固定 commit ca8b14c61):

```
48 workers [63 items]
63 passed in 9.28s
```

## 8. 測定面についての注記

`tools/run_tests.py` の受入形は既定 K=2 shard、worker 上限 32 (`_NPROC_CAP = 32`)。
K=3 は `IZANAGI_ACCEPTANCE_SHARDS=3` の明示時だけ。
前 wave が記録した 297.5 秒と 388.3 秒がどの測定面の値かは本 wave では確定できていない。
「5 分」がどの量を指すかは未定義であり、裁定パッケージへ送った。
