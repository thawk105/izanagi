# 段 4 裁定 + プラン v2 — login admission を回収不能メモリ判定へ

親が段 2 プランと段 3 敵対 2 レンズ (sol / luna) を裁定した結果である。**実装はこの文書に従う。**
段 2 の `plan-out.md` は参考であり、本文書と食い違う箇所は本文書が勝つ。

## 裁定 (real / refuted と採否)

| # | 所見 | 裁定 | 採否 |
|---|---|---|---|
| sol1 / luna4 | `required` を `{anon}` へ縮めるのは今日の DISPATCH を LOCAL に変える fail-open | **real** | 採用 (親の対案を確定) |
| sol2 | clean file 全体・`slab_reclaimable` 全体は「確実に回収可能」ではない (mlock/pin/unevictable) | **real** | 一部採用 (`unevictable` を減算側から除く。slab はユーザー指示どおり減算し残余risk を記録) |
| sol3 | `memory.current` と `memory.stat` の非原子読み取り、負値 clamp が最大の fail-open | **real** | 採用 (current 2 度読み + 不整合時は clamp せず degrade) |
| sol4 | 親 P1 (dirty/writeback を回収不能側) は正しい | **real** | 確定 (P1 採用) |
| sol5 | 最も危険な変異 (`required` 縮小) が変異集合から漏れている | **real** | 採用 (M5 として登録) |
| sol6 | `occupied_bytes` の意味を黙って変えると公開契約が壊れる | **real** | 採用 (`occupied_bytes` は raw のまま。admission は新 property を使う) |
| sol7 / luna1 | D209 決定 3・runbook §7.0 が「raw `memory.current`・file cache を差し引かない」のまま | **real** | 採用 (親が docs を同 wave で更新) |
| sol7 の AGENTS 部分 | `AGENTS.md:41-43` も要更新 | **refuted** | 不採用 — 当該記述は「1 コマンド自身の cgroup charged peak vs 天井」であり、slice 占有量の定義を述べていない。本 wave で意味は変わらない |
| sol8 / luna7 | 単一 snapshot から「local が通る」と一般化できない | **real** | 採用 (brief の主張を訂正。段 6 で実経路実測) |
| luna2 | 旧 peak (raw current peak) を新定義へ無標識で混ぜる | **real / scope 外** | 診断の metric 明記のみ採用。schema 版付けは裁定パッケージへ (旧 peak は raw current peak ≥ 回収不能 peak なので現状 fail-closed 側) |
| luna3 | force-dispatch・site OTHER・heavy-work refusal で admission が変わらない経路がある | **real** | 主張の scope 制限として採用 (「build が local 化する」とは書かない)。site 分類は裁定パッケージへ |
| luna5 | 診断が「何で落ちたか」を表さない | **real** | 採用 |
| luna6 | fixture が clean_file=0 に張り付き、変異帰属が弱い | **real** | 採用 (正の clean_file ベクトル + dirty 24 KiB 境界テスト) |
| luna8 | mutation fanout の scope が不明確 | **real / scope 外** | `_decision_locked` 共有経路として波及することだけ記録。fanout 固有の certified peak policy は別裁定 |

## 実装仕様 (v2)

### 1. 観測 — `login_headroom()` と `LoginHeadroom`

- `_parse_memory_stat()` の `required` は **現行 5 キーのまま変更しない**
  (`{anon, file, shmem, file_dirty, file_writeback}`)。欠落・破損・overflow は従来どおり
  `ValueError` → `login_headroom()` が `None` → 必ず DISPATCH。**この契約を弱めてはならない。**
- 新規に読むキーは `slab_reclaimable` と `unevictable` の 2 つで、**optional** とする
  (`stats.get(...)`)。どちらかが欠ければ回収不能量は unknown。
- `memory.current` を **2 回読む**。1 回目 (`c1`) は現行どおり `:409` の位置で読み、
  `memory_current_bytes` / `effective_ceiling_bytes` / `headroom_bytes` の算出に使う
  (**既存の意味を一切変えない**)。`memory.stat` を読んだ**後**に 2 回目 (`c2`) を読み、
  `unreclaimable_base_bytes = max(c1, c2)` として新規 field に保存する。
  理由: `current` と `stat` は同一 snapshot ではない。cache が増えた場合は `c2` が、
  減った場合は `c1` が大きくなるため、max を基準にすると両方向で保守側に倒れる。
- `LoginHeadroom` の新規 field (frozen dataclass、既存 field の型は変えない):
  - `unreclaimable_base_bytes: int`
  - `slab_reclaimable_bytes: int | None = None`
  - `unevictable_bytes: int | None = None`
  既存 `file_bytes` 等を `int | None` へ広げてはならない (required のままだから)。
- 新規 property `unreclaimable_bytes: int | None`:
  - `slab_reclaimable_bytes` か `unevictable_bytes` が `None` なら `None`。
  - `clean_file = max(0, file - shmem - file_dirty - file_writeback - unevictable)`
  - `reclaimable = clean_file + slab_reclaimable`
  - `reclaimable > unreclaimable_base_bytes` なら **`None`** を返す (snapshot 不整合。
    **0 へ clamp してはならない** — それは最も緩い値になる)。
  - それ以外は `unreclaimable_base_bytes - reclaimable`。
- 新規 property `admission_bytes: int`:
  `unreclaimable_bytes` が整数ならそれ、`None` なら `unreclaimable_base_bytes`。
- `occupied_bytes` / `current_bytes` / `headroom_bytes` は **意味も値も変えない**
  (`occupied_bytes` は raw `memory_current_bytes` のまま)。class docstring は
  「admission が使う判定量は `admission_bytes`」と書き替える。

### 2. degrade 経路

回収不能量が unknown になるのは次の 2 つだけであり、いずれも `admission_bytes` が
`unreclaimable_base_bytes` (= 従来の保守判定と同等以上) へ倒れる。

1. `slab_reclaimable` または `unevictable` が `memory.stat` に無い。
2. `reclaimable > unreclaimable_base_bytes` (snapshot 不整合)。

既存 5 キーの欠落・破損は **degrade ではなく `None` → DISPATCH** のまま。部分計算も 0 補完もしない。

### 3. admission 2 か所

- `_decision_locked` (`:829`):
  `required = observed.admission_bytes + reserved + estimate_bytes + RESERVE_BYTES`
- `grant_budget` (`:1034-1040`):
  `available = ceiling - observed.admission_bytes - reserved - RESERVE_BYTES`
- 比較演算子・4 定数・peak estimate・予約台帳の計算順は変えない。

### 4. 診断

両経路の理由文へ次を出す (既存の日本語表現と語順を保ち、その間に挿入する)。

- `現在使用量=<memory_current_bytes> bytes`
- 算出成功時: `回収不能量=<n> bytes`
- unknown 時: `回収不能量=不明 (<理由>)`。理由は `欠落キー=slab_reclaimable` のように
  **欠落キー名**、または `snapshot 不整合`。
- 判定に実際に使った量: `判定占有量=<admission_bytes> bytes`
- 前回ピークを使う経路では、その peak が **scope の raw memory.current peak** である旨を明記する
  (回収不能量とは別 metric であることを運用者が読み取れるようにする)。

### 5. テスト (3 面 + 変異帰属)

`orchestrator/tests/test_login_headroom.py` に以下を入れる。

- **算出面**: 正の clean_file を持つ実機に近いベクトル
  (`current=1000, file=500, shmem=100, dirty=60, writeback=40, unevictable=30, slab=50`)
  で `clean_file=270`、`reclaimable=320`、`unreclaimable=680`、`admission_bytes=680` を検証。
  `file < shmem+dirty+writeback+unevictable` で `clean_file=0` になる clamp も検証。
- **degrade 面**: `slab_reclaimable` 欠落 / `unevictable` 欠落 / snapshot 不整合の 3 case で
  `unreclaimable_bytes is None`、`admission_bytes == unreclaimable_base_bytes`、
  理由文に欠落キー名または `snapshot 不整合` が出ることを検証。
  **既存 5 キー欠落は従来どおり `None` / DISPATCH** であることを別 node で固定する
  (既存 `test_every_observation_failure_is_none_and_dispatch[stat_missing]` を**削除しない**)。
- **admission 面**: 新式なら exact boundary で `LOCAL`、旧 current 式なら `DISPATCH` になる値で
  `admit`/`reserve` と `grant_budget` をそれぞれ独立に検証する
  (片方だけ旧式へ戻す変異を殺し分けるため、2 経路を別 node にする)。
- **dirty 境界**: dirty を回収可能側へ入れると判定が反転する値
  (dirty の分だけ境界をまたぐ) を置き、`dirty=24576` と `dirty=0` で LOCAL/DISPATCH が
  変わることを検証する。**実機の差が小さいので、境界に置かないと M4 を殺せない。**
- `_observation()` helper は `file/shmem/dirty/writeback/unevictable/slab` を差し替え可能にする
  (既存 27 node を壊さないよう keyword 既定値付き)。既定値は既存 admission 期待値を変えない値にする。
- `_memory_stat()` fixture に `slab_reclaimable` と `unevictable` を足し、任意キーを
  除ける `omit` を足す。

### 6. 変異事前登録 (段 6 の matrix。実装前に確定)

| ID | 変異 | 位置 | 殺す node | 単一赤理由 |
|---|---|---|---|---|
| M1 | admission を `memory_current_bytes` へ戻す | `_decision_locked` の `required` | admission 面 (admit) | 判定が緩み LOCAL→DISPATCH が反転 |
| M2 | 同上 | `grant_budget` の `available` | admission 面 (grant) | 予算額が変わる |
| M3 | clean file の減算を落とす (`reclaimable = slab` のみ) | `unreclaimable_bytes` | 算出面 | 回収不能量が過大 |
| M4 | dirty/writeback を回収可能側へ入れる (memwatch 式) | `unreclaimable_bytes` の `clean_file` | dirty 境界 | 回収不能量が過小 |
| M5 | `required` を `{"anon"}` へ縮める | `_parse_memory_stat` | 既存 `[stat_missing]` | 観測失敗が DISPATCH でなくなる |
| M6 | snapshot 不整合を `None` でなく 0 clamp にする | `unreclaimable_bytes` | degrade 面 | 最も緩い値を返す |
| M7 | `unevictable` の減算を落とす | `unreclaimable_bytes` の `clean_file` | 算出面 | 回収不能量が過小 |
| P1 | (正例) 全キー健全・余裕十分な観測 | — | admission 面 | 過剰拒否していないこと |

### 7. 変えてはならないもの

`CEILING_BYTES` (14 GiB)、`RESERVE_BYTES` (2 GiB)、`MAX_LOCAL_BUDGET_BYTES` (4 GiB)、
`MIN_LOCAL_BUDGET_BYTES` (1 GiB)、`headroom_bytes` の意味、`occupied_bytes` の意味、
既存 5 キーの required 契約、observation 失敗時の `None` → DISPATCH。
