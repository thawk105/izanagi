# login admission の判定量を回収不能メモリへ変える (2026-08-13)

wave = `dev-wave-login-unreclaimable` / branch `worktree-dev-wave-login-unreclaimable`。
2026-08-12 rulings 第 6 束の追加指示 (authority: user) の執行。
設計判断は decisions fragment `login-headroom-unreclaimable` (D 番号は land 時の fold が付ける)。

## 1. 変更前の実測 — local 実行は恒常的に閉じていた

観測 = Pegasus login (`pegasus02`)、`user-31609.slice`、2026-08-12 23:03 JST。

| 量 | 値 |
|---|---|
| `memory.max` | 16.00 GiB |
| `memory.current` | **12.32 GiB** |
| `file` | 3.47 GiB |
| `shmem` | 452 KiB |
| `file_dirty` | 24 KiB |
| `file_writeback` | 0 |
| `slab_reclaimable` | 1.70 GiB |
| `unevictable` | 4.4 MiB |
| 回収不能量 (本 wave の式) | **7.15 GiB** |

天井 14 GiB − 予備 2 GiB = 12 GiB を **合計が超えている**ため、変更前は要求サイズに関わらず
必ず dispatch していた。判定量を回収不能量にすると同じ天井のまま local が成立する。

**値は揮発する。** 段 3 レンズ A の独立読み取りでは合計 12.51 GiB / 回収不能 7.69 GiB、
段 6 の実走時は合計 12.66 GiB / 回収不能 7.54 GiB。単一 snapshot から「実装すれば local が
通る」と一般化してはならない (親 brief の当初主張は段 4 で訂正した)。

## 2. 実装後の実経路実測

`tools/run_tests.py` 自身の admission ログ (2026-08-13 00:32 JST):

```
bounded local に与えた予算: 4294967296 bytes。ログインノードで 4294967296 bytes の予算を
予約しました（予約控除後の観測余裕=4792749304 bytes、算出予算=4294967296 bytes、
現在使用量=13592727552 bytes、回収不能量=8092152584 bytes、判定占有量=8092152584 bytes、
実効天井=15032385536 bytes、生存中の予約=0 bytes）。
```

旧判定量 (12.66 GiB) なら余裕が負になり必ず dispatch だった走行が、local で実走した。

## 3. 差だけに頼る算出が持つ原理的な穴 (段 6 レンズ A、blocker)

親は非原子読み取り対策として `memory.current` を `memory.stat` の前後で 2 回読み、
`max(c1,c2)` を基準にした。**これは ABA schedule を検出できない。**

```
c1 = 1000        (全量が回収不能)
  → memory.stat 読取中だけ clean file cache 900 が現れる
c2 = 1000        (cache は既に消えている)
base = max(1000,1000) = 1000、reclaimable = 900 → 判定占有量 100 (真値は 1000)
reclaimable <= base なので snapshot 不整合としても弾かれない
```

**是正 = 直接の下限を併用する。** swap 無し環境では `anon` と `shmem` はいずれも回収不能なので、
`anon + shmem` は回収不能量の妥当な下限になる。矛盾のない snapshot では
`base − reclaimable` の内訳に anon・shmem・dirty・writeback・unevictable・回収不能 slab・
kernel 構造体が残るため、差は必ずこの下限以上になる。したがって
**通常運用では発火せず、競合時だけ効く**。

一般化: **差で求めた安全量には、独立に構成した下限を併せる。** 差の両項が別時点の観測なら、
差だけでは競合を検出できない。

## 4. 変異 9/9 一致 — 単層変異が実効 gate を外した記録

`mutation-ledger.json` が本走 (round2)、`mutation-ledger-probe.json` が probe。
runner = `python3 tools/run_tests.py --force-dispatch -rf orchestrator/tests/test_login_headroom.py
-p no:cacheprovider`、`--runner-mode dispatch`、repo HEAD = `0738f7e9`。

| ID | 変異 | 結果 | 期待 node 数 |
|---|---|---|---|
| M1 | admission (`admit`) を raw current へ戻す | KILLED | 3 |
| M2 | admission (`grant_budget`) を raw current へ戻す | KILLED | 1 |
| M3 | clean file の減算を落とす | KILLED | 6 |
| M4 | dirty/writeback を回収可能側へ戻す (memwatch 式) | KILLED | 2 |
| M5 | `required` を `{anon}` へ縮小 (単層) | **SURVIVED (等価)** | 0 |
| M5b | 同上 + 直接参照の `.get(..., 0)` 化 (両層) | KILLED | 1 |
| M6 | snapshot 不整合を 0 clamp にする | KILLED | 1 |
| M7 | `unevictable` の減算を落とす | KILLED | 1 |
| M8 | `anon + shmem` 下限を落とす | KILLED | 1 |

**M5 の SURVIVED は検出漏れではなく等価変異である。** `required` から外しても観測組み立てが
`stats["file_writeback"]` を直接参照するため KeyError → 観測失敗 → dispatch となり、受理集合が
変わらない。**この防壁は required 集合と直接参照の二重で効いていた。**

`DW-M02` に従い実効 gate へ再照準した M5b (段 2 プランの提案そのもの = required 縮小と
`.get()` 化の同時注入) は KILLED になり、**却下した案が実際に fail-open だったことを実証した**。
単層 M5 は消さず `expected_status=SURVIVED` で登録に残した。

probe では M1 / M3 / M4 が MISMATCH だった (期待 node が不完全)。実測を完全集合として
再登録した。**予測で完全集合を書けると考えてはならない。**

## 5. 副作用 — F155 への露出が構造的に増える

本変更は local 採択を増やすため、**login からの短時間 targeted 走行が cgroup scope の
1 秒 race に入る F155 の発火頻度が上がる**。従来は判定量が天井を超えて必ず dispatch されて
いた走行が local を選ぶようになるためで、本 wave でも再走 1 回が rc=16 になった。
恒久対応は F155 既載の `--force-dispatch` のままとし、新しい機構は作らない。

## 6. 工程の記録

`verbatim/` に段 2 プラン、段 3 敵対 2 レンズ、段 4 裁定 (plan v2)、段 6 敵対 2 レンズを置く。

**段 3 の初回 2 本は Web 検索で全損した。** 検索イベント行の重複 key (`['id','type','id',
'query','action']` × 20 行) が `stdout_invalid` を立て `evidence_status=invalid` になり、
`codex_exit_code=0` / 13,969 bytes の成果物があったのに `-o` はゼロだった。
一次原因は親の prompt 設計で、「この環境は存在するか」型の外部事実を問うと検索を誘発する。
再走では検索禁止を明記し、外部事実の設問を「この機械の `/sys/fs/cgroup` を読んで確認せよ」へ
書き換えた。**`docs/dev-wave/` にはこの禁止義務が無い** (`web` / `検索` / `search` で grep して
不在を確認済み)。
