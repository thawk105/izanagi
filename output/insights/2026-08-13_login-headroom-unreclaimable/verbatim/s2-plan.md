# 段 2 実装プラン

指定された brief、実装、テスト、`memwatch.sh:127-130` はすべて読了した。以下は現行 HEAD `2310ea67` に対する行番号である。pytest・build は未実走であり、緑とは判定しない。

## 1. 回収不能量の観測

### `LoginHeadroom`

[orchestrator/campaign/login_headroom.py:209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-login-unreclaimable/orchestrator/campaign/login_headroom.py:209) の frozen dataclass を次のように変更する。

- `file_bytes`、`shmem_bytes`、`file_dirty_bytes`、`file_writeback_bytes` を `int | None` にする。キー欠落を偽の `0` として表現しないため。
- 既存の式に足りない生観測値として、全 non-default field の後へ `slab_reclaimable_bytes: int | None = None` を追加する。末尾に置くのは dataclass の default/non-default 順序制約を守り、既存の外部コンストラクタを fail-closed な既定値で互換にするため。
- 重複した計算済み field は保持せず、`unreclaimable_bytes: int | None` を読み取り専用 property として `occupied_bytes` の直前に追加する。frozen instance を構築後に書き換えない。

`unreclaimable_bytes` は、5 値のいずれかが `None` なら `None` を返す。全値がある場合は次を計算する。

- `clean_file = max(0, file - shmem - file_dirty - file_writeback)`
- `reclaimable = clean_file + slab_reclaimable`
- `unreclaimable = min(memory_current, max(0, memory_current - reclaimable))`

内側の `max(0, ...)` は回収可能量が `memory.current` を超える観測でも負値を防ぐ。外側の `min(memory_current, ...)` は判定量が生の current を超えない不変条件をコード上にも固定する。`file < shmem + dirty + writeback` は現行 fixture でも実在するため、`clean_file` 側の clamp も省けない。

[参照式 `memwatch.sh:127-130`](/work/1/SFC/tanab/scripts/memwatch.sh:127) との差は、(P1) に従って dirty/writeback を clean cache から除き、回収不能側へ残す点である。

`occupied_bytes`（現行 `login_headroom.py:232-234`）は次の意味へ変える。

- `unreclaimable_bytes` が整数ならそれを返す。
- `None` なら `memory_current_bytes` を返す。

### `login_headroom()`

[orchestrator/campaign/login_headroom.py:425-437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-login-unreclaimable/orchestrator/campaign/login_headroom.py:425) では、`memory.stat` から次を読む。

- `file`
- `shmem`
- `file_dirty`
- `file_writeback`
- `slab_reclaimable`

コンストラクタでは `anon` だけを `stats["anon"]` で取得し、上記 5 値は `stats.get(...)` で渡す。これによりキー欠落は例外ではなく `None` として dataclass へ保存される。

`headroom_bytes=max(0, effective_ceiling-current)`（現行 `:431`）は変更しない。

## 2. degrade 経路

[orchestrator/campaign/login_headroom.py:338-354](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-login-unreclaimable/orchestrator/campaign/login_headroom.py:338) の `_parse_memory_stat()` は、`required` を `{"anon"}` に縮める。

- admission 計算用 5 キーは optional とし、いずれかの欠落は `unreclaimable_bytes is None`、続いて `occupied_bytes == memory_current_bytes` となる。
- `anon` 欠落は既存観測契約を緩めず、引き続き `ValueError` とする。
- optional キーでも、存在するのに非数値、重複、uint64 超過なら従来どおり例外にする。欠落だけを current degrade とし、破損値を local 許可へ流さない。

経路の区別は次のとおり。

- 回収不能量用キー欠落: `login_headroom.py:425-437` から `LoginHeadroom` を返す。admission は current を使って継続する。
- cgroup/path/interface 不明、`memory.current`／`memory.max`／`memory.stat` 自体の欠落、必須 `anon` 欠落、構文破損: `login_headroom.py:438-439` で `None`。
- 後者は `_decision_locked()` の `:820-826` と `grant_budget()` の `:1025-1032` で、従来どおり即 `DISPATCH`。

したがって missing-key degrade は「観測不能」ではなく「回収不能量だけ不明」であり、部分計算や `0` 補完は行わない。

## 3. admission 判定 2 か所

### `_decision_locked`

[orchestrator/campaign/login_headroom.py:828-836](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-login-unreclaimable/orchestrator/campaign/login_headroom.py:828) の式を次へ置換する。

`required = observed.occupied_bytes + reserved + estimate_bytes + RESERVE_BYTES`

比較演算子 `>`、`effective_ceiling_bytes`、4 定数の値は変更しない。

### `grant_budget`

[orchestrator/campaign/login_headroom.py:1034-1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-login-unreclaimable/orchestrator/campaign/login_headroom.py:1034) の `available` は次へ置換する。

`effective_ceiling - occupied_bytes - reserved - RESERVE_BYTES`

`max_bytes`、`min_bytes`、peak estimate、予約台帳の計算順は変更しない。

### 診断

`_issues_suffix()` の直後（現行 `:806-809`）へ共通の診断 fragment helper を追加し、`_decision_locked` の各理由と `grant_budget()` の `detail`（`:1055-1060`）で使う。

- 算出成功時: `現在使用量=<current> bytes、回収不能量=<unreclaimable> bytes`
- degrade 時: `現在使用量=<current> bytes、回収不能量=不明（現在使用量で保守判定）`

既存の `予約控除後の観測余裕`、`算出予算`、`実効天井`、`生存中の予約` という日本語表現と順序を維持し、その間へ上記 fragment を挿入する。

## 4. テスト実装

### fixture/helper

[orchestrator/tests/test_login_headroom.py:34-44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-login-unreclaimable/orchestrator/tests/test_login_headroom.py:34) の `_memory_stat()` は次を変更する。

- 通常 fixture に `slab_reclaimable: 50` を追加する。通常観測が偶然 degrade になるのを防ぐ。
- optional の `omit: str | None = None` を追加し、`fields.update()` 後に指定キーを除けるようにする。
- 既存呼び出しは keyword-only の optional 追加なので壊れない。

[orchestrator/tests/test_login_headroom.py:86-98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-login-unreclaimable/orchestrator/tests/test_login_headroom.py:86) の `_observation()` には `slab_reclaimable: int | None = 0` を追加し、`slab_reclaimable_bytes` へ渡す。既存の `file=2, shmem=3, dirty=4, writeback=5` では clean file が 0 になるため、既定値 0 は既存 admission の判定量を current と同値に保つ。

静的に数えると `_observation()` は 26 呼び出し箇所あり、`test_ledger_directory_wrong_owner_or_mode_dispatches` が 2 parameter node なので合計 27 既存 node で使われている。新引数を必須にすれば 27 node が壊れるが、上記 optional 署名なら 0 node。`LoginHeadroom` の新 field も default 付きなので、現行 `:176` の直接構築は引数不足では壊れない。ただし実観測との equality 期待値には明示的に `slab_reclaimable_bytes=50` を追加する。

### 新規テスト: 算出面

1. `test_calculates_unreclaimable_from_clean_file_and_reclaimable_slab`

   `current=1000, file=500, shmem=100, dirty=60, writeback=40, slab=50` を与え、`clean_file=300`、`unreclaimable=650`、`occupied_bytes=650` を検証する。dirty/writeback を回収可能側へ戻す変異を検出できる値にする。

2. `test_unreclaimable_clamps_inconsistent_memory_stat_to_current_interval`

   parameterize し、少なくとも以下を検証する。

   - `file < shmem + dirty + writeback`: clean file は 0。
   - 回収可能量が current を超える: unreclaimable は 0。
   - 全 case で `0 <= unreclaimable_bytes <= memory_current_bytes`。
   - `headroom_bytes` は引き続き `ceiling-current`。

### 新規テスト: degrade 面

`test_missing_any_unreclaimable_stat_key_degrades_to_memory_current`

5 キーを parameterize して 5 node にする。各 case で次を検証する。

- `login_headroom()` は `None` ではない。
- `unreclaimable_bytes is None`。
- `occupied_bytes == memory_current_bytes`。
- current 判定なら境界を 1 byte 超える値で `admit()` と `grant_budget()` がともに `DISPATCH`。
- reason に `回収不能量=不明` が含まれる。

現行 `_stat_missing`（`test_login_headroom.py:397-399`）は file-writeback 欠落なので、`test_every_observation_failure_is_none_and_dispatch[stat_missing]` から外す。代わりに `_stat_anon_missing` を置き、`anon` 欠落が引き続き `None`／`DISPATCH` になる既存経路を保持する。`memory.stat` ファイル自体の欠落や malformed case は変更しない。

### 新規テスト: admission 面

1. `test_admit_uses_unreclaimable_bytes_in_required_total`

   `current=900, occupied=100, ceiling=RESERVE_BYTES+200, estimate=100` とし、新式では exact boundary で `LOCAL`、旧 current 式なら `DISPATCH` となることを検証する。

2. `test_grant_budget_uses_unreclaimable_bytes_for_available`

   `current=900, occupied=100, ceiling=RESERVE_BYTES+1000` とし、`available` と grant が 900 bytes になることを検証する。旧式なら 100 bytes なので参照取り残しを検出できる。reason に `現在使用量=900 bytes` と `回収不能量=100 bytes` の両方を要求する。

## 5. 既存 assertion への影響

grep で該当した既存 node は 2 本だけである。

- `test_reads_exact_user_slice_and_returns_every_observation_field`（`test_login_headroom.py:168-190`）

  - `memory_current_bytes=500`、`current_bytes` alias、`headroom_bytes` は変更なし。
  - 通常 fixture に slab 50 が入るため、`occupied_bytes` は 500 から 450 へ変更。
  - expected dataclass に `slab_reclaimable_bytes=50` を追加。

- `test_uses_raw_memory_current_not_anon_for_occupancy_and_admission`（`:215-239`）

  - `memory_current_bytes=900`、`anon_bytes=100`、`headroom_bytes=1100` は変更なし。
  - `occupied_bytes` は 900 から 850 へ変更。
  - 現行名は新しい意味と矛盾するため、`test_preserves_raw_memory_current_but_uses_unreclaimable_for_occupancy` へ改名し、admission 部分は上記の専用テストへ分離する。

`test_login_headroom.py:91` は helper 内の代入で assertion ではない。これ以外に両 identifier を assert する既存 node はない。

## 6. リスクと consumer

- optional 化した stat field を `0` と同一視すると fail-open になる。5 キー全数の欠落テストで `None → current` を固定する。
- (P1) は memwatch より保守的だが、dirty と writeback の包含関係や非同期 snapshot により clean file が負になり得る。内側 clamp が必要で、親が段 4 で式を確定すべきである。
- `memory.current` と `memory.stat` は同時 snapshot ではない。外側 clamp は範囲破壊を防ぐが、観測レース自体は解消しない。
- `LoginHeadroom` は `__all__` で公開されているため、新しい stored field は default `None` とし、旧コンストラクタを保守判定へ倒す。
- `headroom_bytes` の意味は変えない。repo 内で読む production consumer はなく、既存参照はテスト `:212, :231, :274` のみである。`tools/mutation_fanout.py:1539-1552` は観測から `memory_max_bytes` だけを読む。`run_tests.py` と `check_ai_provenance.py` は `BudgetGrant` を消費し、dataclass field を直接読まない。
- `headroom_bytes` を `ceiling-occupied` に変えると、物理的な current headroom と admission 用の回収後余裕を混同し、cgroup 上限直前でも大きな headroom を表示する。admission の 2 式だけを `occupied_bytes` へ切り替える。

`CEILING_BYTES`、`RESERVE_BYTES`、`MAX_LOCAL_BUDGET_BYTES`、`MIN_LOCAL_BUDGET_BYTES` は一切変更しない。

## 総括

- stored field は optional な `slab_reclaimable_bytes`、回収不能量は derived property、`occupied_bytes` は欠落時だけ current へ戻す。  
- admission の `required` と `available` を `occupied_bytes` に統一し、診断へ current と回収不能量を併記する。  
- 算出・5 キー degrade・admission 2 seam を独立テスト化する。pytest は未実走で、緑判定はない。  
- 段 4 では (P1) dirty/writeback を clean cache から除く保守式を最終裁定する必要がある。  
- 段 4 では (P2) 5 キー欠落だけを current degrade、破損値と `anon` 欠落を `None`／DISPATCH に残す粒度を裁定する。