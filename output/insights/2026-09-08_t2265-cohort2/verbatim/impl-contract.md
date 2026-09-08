# cohort 2 実装契約 (3 unit 共通。親が段 4 で確定した。逸脱しない)

## 凍結済みの事実

- 事前登録: `docs/backoff-counterfactual-cohort2-preregistration.md`
  - 凍結 commit `f3daa80db` (docs のみ)
  - **bytes の sha256 = `8b4127f4be895da0d25da88b0837f679ecf06d43ab656b16d2944146b9f7a9e9`**
  - **この文書の bytes を変えてはならない。** 誤りを見つけたら直さず親へ報告する。
- cohort 1 の事前登録 `docs/backoff-counterfactual-preregistration.md`
  (sha256 `526d9384d8a8c62f82b132c41672aa2eff32722788ad06858c09f80185ca495a`) も**変えてはならない**。
- cohort 1 の解析器 `orchestrator/campaign/backoff_counterfactual_analysis.py` と
  その test `orchestrator/tests/test_backoff_counterfactual_analysis.py` も**変えてはならない**。
  受理集合・定数・挙動を 1 つも変えない。

## cohort 2 の exact な cell 文字列 (12 field)

```text
cw-as-dyn-c2-p0:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:0
cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1
cw-as-dyn-c2-p2:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:2
```

- comma 区切り (driver の `--cells`): 上の 3 本を `,` で連結した逐語。
- plus 区切り (`.pbs` の raw literal): 同じ 3 本を `+` で連結した逐語。
- **既存 cohort 1 の cell 集合・観測長 3 秒の受理を 1 つも壊さない。**

## 観測長と terminal

- cohort 2 の `--extime` は **6** 秒。既存 2 literal は **3** 秒のまま。
  **cell literal ごとに exact な extime を引く閉じた表**にする。任意の正の整数を受理しない。
- CMake option `CCBENCH_BACKOFF_TRACE_TERMINAL_US` (define `BACKOFF_TRACE_TERMINAL_US`)、
  cohort 2 の値は **5000000** (µs)。既定は **0** = terminal 無効。

## trace schema v4 の逐語契約 (3 unit が同じものを実装する)

- schema version 文字列: **`izanagi-dynamic-backoff-trace/v4`**。既存の
  `izanagi-dynamic-backoff-trace/v3` は**そのまま受理し続ける**。
- event の追加 field: **`terminal_flush`** (整数、通常 event は `0`、terminal は `1`)。
- terminal event の値:
  - `terminal_flush = 1`
  - `trigger = "terminal"` (既存の受理集合は `"time"` / `"count"` / `"cap"`。v4 でのみ `"terminal"` を足す)
  - `assigned_invert = -1` (非適用の sentinel)
  - `recommended_delta_sign = 0`、`inversion_realized = 0`、`both_actions_feasible = 0` (いずれも非適用)
- **`seq` は terminal を含めて 0 から連続**する。terminal の `seq` は通常 event 数に等しい。
- **terminal は run につきちょうど 1 件、必ず列の末尾**。中間位置の terminal は schema 違反。
- `trace_summary` は v4 で次の exact な 4 key を持つ。
  - `updates` = **通常 event の件数** (terminal を含めない)
  - `retained` = `updates` と同値
  - `dropped` = `0`
  - `flushes` = `1`
  - すなわち `len(events) == updates + flushes` が成り立つ。
  - **`flushes` を `updates` へ足し込んではならない** (`updates` は controller の更新回数の意味を保つ)。
- v3 以前の event に `terminal_flush` が付く形、v4 で field が欠ける形、terminal が末尾以外にある形、
  terminal が 2 件以上ある形は、いずれも**拒否**する。

## 時間 cap の比較 (絶対規律 1 の扱いを含む)

- cap は `9223372036854775807`。**乗算のままでは `clocks_per_us_ * cap_us` が 64 bit を溢れ、
  cap が即座に発火する。** 比較を `elapsed / clocks_per_us_ >= cap_us` へ変える。
  正整数では `floor(e/c) >= cap` と `e >= c * cap` は厳密に同値なので、既存 cell の挙動は変わらない。
- **この cap と比較は計装ではなく CC 本来の機構である。** `#if BACKOFF_TRACE` の外にあり、
  trace 無効 build にも効く。trace on / off で同じ値を使う。「計装」と書かない。
- 一方 **terminal の記録・trace state・trace 出力は計装であり、`#if BACKOFF_TRACE` の内側に
  完全に収める** (絶対規律 1: 性能計測用ビルドからコンパイル時に完全除去)。
  ランタイム分岐 `if (tracing)` にしない。

## 絶対に触ってはならない path

- `common/runner.hh` を patch 対象へ足してはならない。
  `orchestrator/campaign/source_digest.py` の `ALLOWLIST` は
  `cmake/Options.cmake` / `include/backoff.hh` / `cc/silo/transaction.cc` / `cc/mocc/transaction.cc`
  の 4 つだけで、driver は patch 適用後に allowlist 外の tracked 改変を拒否する。
  **runner を触る設計は build 前に必ず止まり、成果物が 1 件も出ない。**
- `orchestrator/campaign/source_digest.py` の `ALLOWLIST` を広げてはならない (親 scope 外)。
- `patches/cicada-adaptive-dynamic.patch` (patch B) と `patches/cicada-adaptive-params.patch`
  (patch A) を変えてはならない。B は B-10 の全 campaign と認証が使う。
  cap 比較の行は B が `+` で入れたものだが、**patch C が同じ `include/backoff.hh` を触るので
  C 側で `-`/`+` にする。**

## 解析側の規則 (cohort 2 専用 module)

- `seq = 0` の位置除外を **cohort 1 v2 と同じ順序**で実装する。
  生の `events` から `analysis_events = events[1:]` を作り、対・index・件数をすべて残存集合基準にする。
- `window_commits = 0` の走査は、位置除外の後に残る event (**terminal を含む**) 全体に対して行う。
  1 件でも 0 があれば主判定全体を `inconclusive` (`reasons` に `window_commits_zero`) にする。
  **terminal の 0 だけを除外してはならない。**
- terminal は **`following` 専用**。`Z[r,f]` を定義しない。割当数、割当率、
  `recommended_delta_sign` / `both_actions_feasible` の層、時間 block の current event に入れない。
  terminal を current として扱う実装は schema 違反にする。
- **terminal 非閉鎖** (terminal event が無い run) は、その run を除外も置換もせず
  主判定全体を `inconclusive` にする。
- 割当整合性検査 (assignment-integrity check): 初期 `state = step_policy_seed` から通常 event ごとに
  `state = (state * 6364136223846793005 + 1442695040888963407) % 2**64` を進め、
  `(state >> 63) & 1` を `assigned_invert` と exact 比較する。terminal では state を進めず
  `assigned_invert == -1` を要求する。**不一致は `ValueError` (入力不適格) で、判定を返さない。**
  **これを「無作為化の検証」と呼ばない。** 名前は assignment-integrity check とする。
- `EQUIVALENCE_MARGIN`、t 値、12 cluster 等重み、判定境界、主層 (policy 2 / write-heavy / 48) は
  cohort 1 と同一にする。

## テストの規律 (F42 / F27 / F649)

- **緑には実走した nodeid と範囲を併記する。** 子の実走は親の全走を代替しない。
  実走できない場合は `closed` と申告せず「実装済み・未実走」と書く。
- test の新設・改名では、親の名指しを網羅と見なさず、**制約 meta-test を自ら洗い出して走らせる**。
- **fixture へ現行 hash を差し込むなど、テストを甘くして緑にしない。**
- **機構の正例・負例は実体を名指しし、依存先を stub しない。** 性質だけの検査は両層 stub で
  機構を通らない緑になる。
- 期待値へ揮発 payload (working tree hash 等) を焼き込まない。
- **指示外の受理集合変更をしない。** scope の前に現行の受理・拒否挙動を明記する。
- 親・他 unit の成果物が入るまで意図的に赤になる test を xfail 化しない。既存 test の期待値も変えない。
  赤の内訳を完了報告に明記する。
- 完了報告に、所有外の caller・共有 fixture・consumer test への波及可能性を静的に列挙する。

## 実行環境

- `tools/run_tests.py` は計算ノード dispatch を要求し、`rc=16` になることがある。
  その場合は**自走 harness** (`PYTHONPATH=. python3 <test file>` 形式が使えるなら) か、
  `python3 -m pytest` が guard に拒否されるならその旨を報告する。
  **走れないことを緑と記録しない。**
- commit・`git add`・branch 操作・push を行わない。**編集だけ**を行う。docs も編集しない。
- 出力へ結合文字 U+0300〜U+036F を使わない。
