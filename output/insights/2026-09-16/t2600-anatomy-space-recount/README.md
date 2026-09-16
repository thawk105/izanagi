# [T-2600] anatomy の tictoc・cicada 探索空間サイズを現物で数え直した — どちらも 5 軸・生 32・制約後 24、合計は ≈234

- 日付: 2026-09-16
- wave: dev-wave-t2600-anatomy-space-recount (branch `worktree-dev-wave-t2600-anatomy-space-recount`)
- 起票: archive `docs/archive/worklog-phase3-0914-1482.md` の [T-2600] (T-758 wave が 2026-09-14 に起票)。
  起票の経緯は `output/insights/2026-09-14/t758-docs-corrections.md` の「本 wave では直さなかった食い違い」
- 正本: D1418 (tictoc の no-wait 制約は両 1 だけを除き有効 24)、D1419 (cicada は SINGLE_EXEC を軸にしない)
- 基準: local main e667c8c139004221723ee223b7d8f09fba5f9be1、CCBench submodule はその pin
- 実装 commit: 410e21751 (docs は親、genome.py docstring は Codex author)

## 1. 数え方 — 軸数ではなく、各軸の候補数と軸間の制約から出した

依頼は「軸数だけから要素数を推測しない」ことを求めた。次の 3 段で数を出し、2 経路が一致することを確かめた。

1. **候補数。** CMake 側の option はすべて `CACHE STRING` であり BOOL ではない
   (`external/ccbench/cmake/Options.cmake`)。そこで各フラグのソース上の使われ方を全件列挙した。
   tictoc・cicada の探索軸はどれも `#if FLAG` か C++ の真偽式 (`rmw || WRITE_LATEST_ONLY` など) でしか
   使われず、0 以外の値は 1 と同じ挙動になる。したがって各軸の候補は実質 0/1 の 2 値である。
2. **軸間の制約。** 前処理分岐の入れ子を `#if` / `#elif` / `#else` / `#endif` の行一覧で読み、
   「ある軸が別の軸の分岐の内側にしか作用点を持たない」組を探した。
3. **現行コードの列挙。** `orchestrator/campaign/genome.py` の `SPACES` を実際に `enumerate()` した。

## 2. tictoc — 2 × 2 × 2 × 3 = 24 (生 32)

| 軸 | 作用点 (`external/ccbench/cc/tictoc/transaction.cc`) | 入れ子 |
|---|---|---|
| `BACK_OFF` | 486, 708 | 最上位 |
| `PREEMPTIVE_ABORTS` | 134 | 最上位 |
| `TIMESTAMP_HISTORY` | 381, 508 (最上位)、587 (`#elif NO_WAIT_OF_TICTOC` の内側) | 最上位の作用点があるので常に効く |
| `NO_WAIT_LOCKING_IN_VALIDATION` | 340 (最上位)、564 (`#if`) | 常に効く |
| `NO_WAIT_OF_TICTOC` | 574 (`#elif`) だけ | `NO_WAIT_LOCKING_IN_VALIDATION=1` のとき dead code |

- no-wait の対は 3 通りの挙動になる。(1,0) = 即 abort、(0,1) = 自ロック解放・事前検証・1 µs 待って retry、
  (0,0) = 分岐が空になり、`#endif` の後で lock word を再読込して解放を待つ blocking spin。
  (1,1) は `#elif` が dead code になり (1,0) と同じ挙動なので除く。
- (0,0) を残す根拠は D1418 のとおり。silo の両 0 livelock とは機構が違う。競合下の完走性は未実測。

## 3. cicada — 2 × 2 × 2 × 3 = 24 (生 32)

| 軸 | 作用点 (`external/ccbench/cc/cicada/`) | 入れ子 |
|---|---|---|
| `BACK_OFF` | `transaction.cc` 770, 964 | どちらも `SINGLE_EXEC` の `#endif` の後で最上位 |
| `INLINE_VERSION_OPT` | `include/tuple.hh` 27, 54, 81, 101、`include/transaction.hh` 178, 199, 219, 351、`transaction.cc` 128、`util.cc` 226 | 最上位 |
| `INLINE_VERSION_PROMOTION` | `transaction.cc` 129、`include/transaction.hh` 200 | **2 箇所とも `#if INLINE_VERSION_OPT` の内側** |
| `REUSE_VERSION` | `include/transaction.hh` 185, 229, 358 | 最上位 |
| `WRITE_LATEST_ONLY` | `transaction.cc` 242 (`#if SINGLE_EXEC` の `#else` 側)、491, 512 (最上位) | `SINGLE_EXEC=0` で常に効く |

- (OPT, PROMOTION) = (0,1) は (0,0) と CC / data path の挙動が同じなので除く。
  起動時表示 (`util.cc:330`) だけは違う (genome.py の notes に既記載)。
- `SINGLE_EXEC` は D1419 で軸にしない。`Options.cmake` の既定は 0 で、`SINGLE_EXEC=0` 側を前提に数えた。
- `INLINE_VERSION_OPT` の CMake 変数は `CCBENCH_INLINE_VERSION_OPT_CICADA` という別名である。
  izanagi のビルド側は `orchestrator/campaign/model.py` の写像表でこの別名へ渡しているので、軸は生きている。

## 4. 列挙の実測

`SPACES` を `raw_size()` / `len(enumerate())` で数えた値 (親と Codex 実装子が独立に実走し一致):

| protocol | 生 | 制約後 |
|---|---:|---:|
| silo | 16 | 8 |
| mocc | 8 | 8 |
| tictoc | 32 | 24 |
| cicada | 32 | 24 |

§2・§3 の分岐読解と一致した。

## 5. 直したもの

- `docs/ccbench-anatomy.md` §3
  - 探索空間サイズ: tictoc 2^4=16 → 2^5=32、cicada 2^6=64 → 2^5=32、単純和 ≈250 → ≈234。
    両者の軸・候補数・制約・有効数 24 と根拠 (D1418 / D1419) を書き、「未検証のまま残す」を外した。
  - 死にフラグ一覧から `NO_WAIT_OF_TICTOC` を外した。同じ節の表は silo・tictoc の `#elif` 分岐として
    載せていたのに、一覧は「挙動 `#if` 無し」と書いており、旧 tictoc 2^4 はこの誤認から来ていた。
  - 相互排他の行を silo (XOR) と tictoc (両 1 だけ除く) に分けた。XOR のままだと tictoc は 16 になる。
  - §8 の Phase 1 申し送り (死にフラグとして `NO_WAIT_OF_TICTOC` を挙げる行) は歴史記録なので触っていない。
- `orchestrator/campaign/genome.py` module docstring: `cicada 2^6` → `cicada 2^5`、`≈ 258 binaries` → `≈ 234 binaries`。
  `SPACES`・軸・候補値・制約・notes は 1 byte も変えていない。

## 6. 触っていないもの・限界

- 凍結物 (`output/s1-freeze/*.json`、`output/s8b-freeze/holdout_freeze.json`) は genome.py の旧 sha256 を
  中に持つが、再凍結していない。genome.py は S1 凍結検証で歴史的容認の対象 (`_HISTORICAL_CODE_PATHS`) であり、
  3 本とも全体 sha を `orchestrator/tests/test_frozen_artifacts.py` が pin している。docstring だけの前例
  8e06a37c8 でも無改修だった。pin 閉包は独立の調査子 (read-only) で引き、anatomy の数値を逐語 pin する検査は 0 件だった。
- anatomy §3 の表の行番号 (例: silo の `NO_WAIT_OF_TICTOC` を `cc/silo/transaction.cc:157` とするが、現物の
  `#elif` は 165 行) は submodule pin の前進でずれている。本件の数とは無関係なので直していない。
- 変異 matrix は事前登録ゼロ。docstring と docs の数字を守る実効 gate が repo に無く、DW-M01 の単一理由性を
  満たす変異を登録できない。gate の新設は依頼の scope 外。免除ではなく「登録可能な変異が存在しない」記録である
  (同日の先例 [T-1642])。

## 7. 検査の実測

- 焦点走: tip 410e21751 で、genome.py を参照する test 7 本 (`test_campaign.py`、`test_artifact_admission.py`、
  `test_check_trace0_preprocess_identity.py`、`test_guided.py`、`test_pegasus_calibration_workload.py`、
  `test_s1_known_axes_freeze.py`、`test_t671_source_binding.py`) と、genome.py の bytes を束縛する凍結検証系 4 本
  (`test_frozen_artifacts.py`、`test_s1_measurement_freeze.py`、`test_s8b_holdout_freeze.py`、
  `test_campaign_lock_codec.py`) と `test_check_docs.py` を計算ノード (Pegasus request 1592.nqsv) で走らせ、
  1956 passed / 28 skipped、失敗 0 (rc=0)。
- `tools/check_docs.py` rc=0 (違反なし)、`tools/check_ai_provenance.py` の全史監査 rc=0 (実装 commit 後と main 取り込み後の 2 回)。
