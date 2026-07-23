# [T-066] 継続 wave — 逐語凍結・変異台帳 (2026-07-23)

正本: D82 (docs/decisions.md)、worklog 2026-07-23 (4)。wave branch = worktree-dev-wave-ruling-ac、
commit 系列 = d50f714 (golden 台帳 v1) → 4c01a05 (実装 3 単位統合) → 6982579 (golden 台帳 v2) →
e2217c4 (fix 3 単位統合)。基準 = 1a41090。受入全走 (repo root) = 2832 passed / 18 skipped / 0 failed。

本ファイルは wave 中の一次資料 (brief / プラン / 敵対相談 2 / 裁定 / 実装・fix 報告 / 敵対レビュー 2 /
焦点再レビュー / 変異 matrix) の逐語凍結である。コマンドログ・生ログは凍結対象外
(セッション tmp、生存保証なし — F20 の範囲で本文へ吸収済み)。

## 変異台帳 (最終 commit e2217c4 基準の本走。全 11 変異)

判定基準: kill = 「受理集合または fail-closed 挙動が期待方向へ変わった」こと。診断文字列のみの
変化は kill に数えない (本 wave では該当なし — diagnostic sensitivity pin 枠は空)。テスト強化
wave の規律に従い、全変異を「新テスト (e2217c4)」と「HEAD テスト (1a41090)」の両方に適用し、
新テストのみが検出することを差分で示した。MU-CTRL (K.py への comment 1 行のみ) は意味変異では
なく対照 — HEAD の `test_verify_rejects_tampered_source_copy` が K.py の任意 bytes 変更で赤に
なる (canonical generator sha 経由の false-reason 赤) ことを分離し、MU-A/B/C/J/K の HEAD 側の
同一赤を「意味検出」と誤計上しない根拠にした。ハーネスは flock 単一走行 guard・anchor 一意性
assert・subprocess timeout・内容比較による復元検証 (`read_text == 元ソース`) を備える
(F32/F33 対応)。

| 変異 | 対象 | 内容 | new 側の赤 (期待どおり) | head 側の赤 |
|---|---|---|---|---|
| MU-CTRL | K.py | comment 1 行 (対照) | なし (全緑) | test_verify_rejects_tampered_source_copy |
| MU-A | K.py _sort_entry | comparator へ空白付加 | test_generate_selects_registered_expected_points ほか計 11 node (measurement fixture 伝播含む) | test_verify_rejects_tampered_source_copy |
| MU-B | K.py _trigger_entries | gate_predicate へ空白付加 | test_generate_selects_registered_expected_points ほか計 11 node (measurement fixture 伝播含む) | test_verify_rejects_tampered_source_copy |
| MU-C | K.py _source | 余分 key 'extra' 追加 | test_generate_selects_registered_expected_points ほか計 11 node (measurement fixture 伝播含む) | test_verify_rejects_tampered_source_copy |
| MU-D | backoff_sweep.py | SWEEP_US から 100 を削除 | test_backoff_sweep_grid_matches_registered_golden | なし (全緑) |
| MU-E | M.py _build_cells | cells 射影から comparator 脱落 | test_generate_builds_registered_cells_comparisons_and_schedule | なし (全緑) |
| MU-F | M.py _verify_known_axes | K.verify_document 呼出し除去 | test_build_document_rejects_tampered_known_axes_semantics | なし (全緑) |
| MU-H | K.py verify_document | generator sha 検査除去 | test_verify_rejects_generator_sha_tamper | なし (全緑) |
| MU-I | s1_direct_comparison.py | comparator を strip して受け渡し | test_prepare_sort_best_passes_comparator_verbatim_to_quarantine[canonical-balanced-sp-dd]<br>test_prepare_sort_best_passes_comparator_verbatim_to_quarantine[canonical-write-heavy-sk-ad]<br>test_prepare_sort_best_passes_comparator_verbatim_to_quarantine[synthetic-whitespace-sentinel] | なし (全緑) |
| MU-J | K.py _trigger_entries | ident predicate へ空白付加 | test_generate_selects_registered_expected_points ほか計 11 node (measurement fixture 伝播含む) | test_verify_rejects_tampered_source_copy |
| MU-K | K.py _sort_entry | sources 2 要素の順序入替え | test_generate_selects_registered_expected_points ほか計 11 node (measurement fixture 伝播含む) | test_verify_rejects_tampered_source_copy |

補足: MU-A/B/C/J/K の new 側は known-axes golden テスト 1 failed + measurement module fixture の
10 errors (同一の golden assert が fixture で発火する伝播であり、理由は単一)。head 側の赤は
MU-CTRL と同一集合 (bytes 感度) のみ。baseline (無変異) は両側全緑 (new 57 / head 41)。
MU-D/E/F/H/I は new 側で期待した単一 node のみ赤・head 側全緑の最も明瞭な差分。
MU-I は fix 後の canonical parameterize 2 node も同時に検出した (synthetic sentinel + canonical
sp_dd/sk_ad の 3 failed)。

事前登録 (段4) の 9 件 (MU-CTRL/A/B/C/D/E/F/H/I) は 4c01a05 基準の 1 巡目でも同結果、
段6 レビュー所見 RC9 を受けて MU-J/MU-K を追加登録し、最終 commit 基準で全 11 変異を再走した
(anchor は最終 commit で一意性を再検証 — production は wave を通じ無変更のため stale 化なし)。

---

## 段1 brief (親、逐語)

# brief: [T-066] 継続 wave — comparator/predicate/source golden 化 + measurement 恒真 fixture 除去

## scope (D81 (6) 持ち越し + T-066 元裁定 2026-07-21 の核心)

- **(A) known-axes test-local golden の拡張** (`orchestrator/tests/test_s1_known_axes_freeze.py`):
  comparator 逐語 (sp_dd/sk_ad)・gate predicate 逐語 (g_rl/g_rt/ident_all)・p2_2/backoff_fixed/sort の
  flags・source record 構造。sort comparator 差替え攻撃 (名前保持・実装差替え) の検出が受入基準
- **(B) measurement 恒真 fixture 本体の除去** (`orchestrator/tests/test_s1_measurement_freeze.py`):
  D68 (7) 型隠蔽 = 「production generator の現行 hash を動的注入 (fixture 行 95-100) +
  `K.build_document` を fixture の echo へ置換 (行 117-118)」を外部固定の期待値へ置き換える
- **(C) known-axes 側 `test_verify_rejects_one_byte_freeze_tamper` (行 113-121) の false-green 修正**
- production コード・凍結成果物は 1 byte も変更しない (テスト強化のみの wave)

## 確定済みユーザー裁定

- T-066 (裁定 2026-07-21、承認済み実装 wave): 「`test_s1_measurement_freeze.py` の D68 (7) 型の
  隠蔽を、外部固定の期待値へ置き換える」— これが本体。前 wave (D81) は known-axes 側 flags を部分消化
- D81 (6): scope-out は取り消さず次 wave 要件 = comparator/predicate/source record への外部固定
  golden 拡張 + sort comparator 差替え攻撃への対処

## brief 前実測 (本 wave で実施)

- **E1 (新規実測、模擬なし・実ファイルコピーで実走)**: canonical `known_axes_freeze.json` の
  無改竄コピーへの `M.verify()` は `source sha256 不一致: orchestrator/campaign/s8a_trigger_sweep.py`
  で FreezeError。**sp_dd→xp_dd 改竄版も全く同じエラー**。つまり現行 tamper test は改竄検出を
  一切検査していない false-green (D81 (7) 疑義の確定)
- D81 (4) 記録 (前 wave 実測、同一 HEAD): `K.build_document()` (実材料) は `K.verify_document` に
  self-consistent で通る。改竄 1 フィールドで FreezeError。→ (B)(C) の設計基盤
- D81 (5) 記録 (前 wave レビュー実測): sort comparator 差替え・predicate 差替え・source record 偽装・
  P2/backoff flags 破壊は現行全 assertion を通過する (in-memory 模擬。実差分 = 防護ツリーの
  provenance は編集不可のため、上流 drift を doc 偽造で模擬)

## 不変条件

- production (`orchestrator/campaign/**`) と凍結成果物は 1 byte も変更しない。
  `FROZEN_MANIFEST` (orchestrator/tests/test_frozen_artifacts.py:33) の 8 pin 不変
  (s1 2 + v1 1 + 資料 5)。理由: D81 (2) self-hash blocker (K.py 編集は canonical の
  generator.sha256 pin を外す)
- 受入全走は repo root cwd から `python3 tools/run_tests.py`。baseline = 2816 passed / 18 skipped
  (本 wave 開始時に再実測中)
- 期待して赤くなる finding: **なし** (新テストは現行実装で緑になるべき。検出力だけを足す)
- テスト強化 wave の変異規律: 変異を「新テスト」と「HEAD 版テスト」の両方に走らせ、
  新テストのみが検出する差分を示す

## 親の provisional 裁定 (攻撃対象 — 一件ずつ否認/採用を返せ)

- **(P1)** scope は (A)(B)(C) の 3 点で、いずれもテストファイル (+テスト用共有 helper 新設可) のみ。
  canonical freeze の drift 解消・再凍結 (T-005 系) は scope 外のまま
- **(P2)** source record golden の sha256 は **output/campaigns 配下 (防護ツリー・不変) のみ** pin し、
  編集可能ファイル (orchestrator/campaign/*.py・docs/*・output/insights/*) は path/key/(lines 構造)
  のみ pin する — 揮発値の焼き込み禁止 (正当編集で false red になるため)。external/ccbench 配下も
  sha256 は pin しない (ccbench_pin 検査が別途あり、pin bump で変わる)
- **(P3)** (B) の設計: hermetic echo fixture を「`K.build_document()` が実材料から生成した
  self-consistent known doc を tmp へ書き出し、`M.build_document(known_axes_path=<tmp>)` に食わせる」
  形へ置換する。`K.verify_document` は live generator hash・ancestry・ccbench pin・実再構成で通る
  (D81 (4))。s1_stats.py は引き続き tmp dummy でよい (M 層の hash 照合検査の対象は照合機構そのもの)。
  module スコープ fixture で生成は 1 回に抑える
- **(P4)** (C) の修正: canonical file 対象をやめ、「`K.build_document()` 生成 doc を tmp へ書き →
  1 byte 改竄 (sp_dd→xp_dd) → `K.verify()` が『機械再構成と不一致』の単一理由で落ちる」形へ
  差し替える。canonical の drift 状態を green/red で固定する新テストは追加しない (T-005 裁定待ち)
- **(P5)** comparator/predicate/flags の golden 定数はテスト用共有 helper
  (`orchestrator/tests/s1_expected_goldens.py` 等、production から import しない) に置き、
  known-axes テストと measurement テストの両方から参照する
- **(P6)** 実装単位: 単位1 = test_s1_known_axes_freeze.py + 共有 helper 新設 (A/C)。
  単位2 = test_s1_measurement_freeze.py (B)。素集合だが単位2が helper を import するため、
  単位1完了 → 所有ファイル限定 patch 展開 → 単位2 の順 (直列 2 段) か、helper 仕様を親が先に
  固定して並列にするかは codex プランの提案を待って裁定する

## 成果物の形

- テスト差分 (上記 2 ファイル + helper) の統合 commit (親が実施、AI-Agent trailer)
- 変異 matrix (新/旧テスト差分実測つき) + 逐語の insights 凍結、D82 (decisions)、worklog 吸収

## 計画 gate 5 述語の適用

- G1: 生死実験 = E1 実施済み (false-green 確定)。新規大型機構なし
- G2: 本 wave は correctness 判定の検出力 (freeze 抽出の regression 検出) を実際に変える — blocker 適格
- G3: 族一般化なし (既存 2 テストファイルの強化のみ)
- G4: 発火条件付き機能なし
- G5: レビュー must-fix には影響 1 行を要求する

---

## 段2 プラン起草 (codex gpt-5.6-sol max、逐語)

# [T-066] 実装プラン

## 1. provisional 裁定の補正

- **P1 は補正が必要。** production・凍結成果物を変更しない方針は維持するが、対象は 2 テスト本体と helper だけでは完結しない。measurement fixture が実 `K.build_document()` を読むようになるため、xdist の共有 repo reader 登録として `orchestrator/tests/conftest.py` と、その独立 golden である `orchestrator/tests/test_real_repo_serialization.py` も同時更新する。
- **P1/P4 の追加補正:** [test_s1_known_axes_freeze.py:124](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:124) の `test_verify_rejects_tampered_source_copy` も canonical の既存 source drift で先に落ちる false-green である。指定された一 byte テストと同様、fresh `K.build_document()` を対象に直す。
- **P2 は採用する。** `output/campaigns/**` だけ exact SHA-256 を pin する。それ以外は source の順序・path・key・`lines` の有無と構造、および SHA が 64 桁小文字 hex であることだけを pin する。
- **P3 は二層 fixture に補正する。** 実材料 document の生成だけを module scope にし、改竄される `known_path`・`stats_path` は function scope で毎テスト複製する。単一 module-scope temp を共有すると stats/known tamper が後続テストへ残るため不可。また、この fixture は「hermetic」ではなく実 repo/submodule 依存の integration fixture である。
- **P3 の件数補正:** `freeze_env` 利用者は現行 8 件ではなく 9 件。T-080 legacy-strict テストも含む。
- **P4 は fresh document 化と exact reason 化を採用し、上記 source-copy テストにも適用する。** canonical drift 自体を固定するテストは追加しない。
- **P5 は採用する。** helper は production/canonical を実行時 import・読込せず、test-local literal のみを持つ。
- **P6 は直列 2 単位を採用する。** helper API、テスト名、real-repo node の exact 集合に依存関係があるため、並列編集は避ける。

## 2. golden の構造と実値

### 新規 `orchestrator/tests/s1_expected_goldens.py:1-end`

次の test-local 定数と assertion helper を置く。

- `WORKLOADS = ("balanced", "write-heavy", "read-heavy")`
- `EXPECTED_P2`: workload ごとの `variant`・`label`・`reference_fitness_tps`・exact-int `flags`
- `EXPECTED_BACKOFF`: workload ごとの `backoff_us`・選定点 flags、および `no_backoff` / `stock_adaptive` の flags
- `EXPECTED_SORT`: workload ごとの `name`・逐語 comparator・exact-int flags
- `EXPECTED_GATES`: workload ごとの gate name・逐語 predicate
- `EXPECTED_IDENT_ALL_PREDICATE`
- `EXPECTED_STOCK_FLAGS`
- `EXPECTED_SOURCE_LAYOUT`: 18 owner、63 record の順序付き `(path, key, lines-pattern)` 表
- `PINNED_CAMPAIGN_SHA256`: `output/campaigns/**` の unique 20 path → 64hex SHA
- `assert_exact_int_flags(actual, expected, label)`: key 集合、`type(value) is int`、値を検査
- `assert_known_axes_semantic_goldens(doc)`
- `assert_known_axes_source_goldens(doc)`
- `assert_known_axes_goldens(doc)`: 上記二つを統合

固定する主な実値は以下。

| 項目 | balanced | write-heavy | read-heavy |
|---|---|---|---|
| gate | `g_rl` | `g_rt` | `g_rl` |
| P2 | `5185ee5e6094`, `B0-L-W0` | 同左 | `b971a1d9f80a`, `B0-T-W0` |
| P2 flags | `BACK_OFF=0, LOCK=1, TICTOC=0, WAL=0` | 同左 | `BACK_OFF=0, LOCK=0, TICTOC=1, WAL=0` |
| backoff | `5` | `10` | `2` |
| sort | `sp_dd` | `sk_ad` | `sk_ad` |

共通 flags:

- stock: `BACK_OFF=1, NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0, WAL=0`
- gate/ident: stock 4 flags + `BACKOFF_TRIGGER_GATING=1`
- sort: stock 4 flags + `SORT_VARIANT=1`
- backoff 選定点: `BACK_OFF=1, BACKOFF_FIXED=<5|10|2>` と no-wait/WAL 3 flags
- backoff reference: `BACKOFF_FIXED=-1`、`BACK_OFF` は no-backoff が `0`、stock-adaptive が `1`

逐語 predicate:

- `g_rl`: `izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked;`
- `g_rt`: `izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid;`
- `ident_all`: canonical [66, 292, 518 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/known_axes_freeze.json:66) の全 abort reason 列挙文字列を空白・末尾 `;` 込みで固定する。

comparator は canonical [167 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/known_axes_freeze.json:167) の `sp_dd` と [393 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/known_axes_freeze.json:393) の `sk_ad` を改行・インデント込みで固定する。read-heavy は同じ `sk_ad` literal を参照する。

source layout は次の順序を固定する。

- `system_gate`: recon → remeasure provenance → main provenance → `axis_trigger_gating.py` → `s8a_trigger_sweep.py`
- `ident_all`: remeasure provenance → main provenance →上記 2 modules
- `p2_2_flag_opt`: workload WAL → `genome.py`
- `backoff_fixed_best`: workload WAL → `backoff_sweep.py`
- balanced/write-heavy `sort_best`: main WAL → main provenance → remeasure WAL → remeasure provenance → insight → `s6_sort_sweep.py` → `p3_s4_loop_sort.py`
- read-heavy `sort_best`: phase doc → write-heavy main provenance → sort modules 2 本
- `stock_common`: `Options.cmake` の 5 行 → Silo `CMakeLists.txt` の 3 行

`lines` は全文一致ではなく、行番号を許容する正規表現で対象 flag/mapping と順序を固定する。`lines` がない record への追加も拒否する。

### 実値の採取手順

1. canonical [entries:17](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/known_axes_freeze.json:17) から各 workload/configuration の意味値と `sources[*]` を抽出する。
2. comparator は各 sort provenance の次の key と照合する。
   - balanced: `...dd25aa8c/reports/s6_sort_sweep_provenance.json → entries.sp_dd.implementation`
   - write/read-heavy: `...0484feef/reports/s6_sort_sweep_provenance.json → entries.sk_ad.implementation`
3. predicate は workload ごとの remeasure provenance の `entries.<g_rl|g_rt|ident_all>.implementation` を採り、対応する main provenance と逐語一致することを確認する。
4. flags は canonical 値を採り、現行の以下と静的照合する。
   - trigger: `axis_trigger_gating.py:31-32`
   - sort: `p3_s4_loop_sort.py:93-94` + `SORT_VARIANT=1`
   - backoff: `backoff_sweep.py:41-43`
   - P2: 選定 WAL の `build_start.payload.genome`
   - stock: `Options.cmake:20,27,28,47,63` と Silo `CMakeLists.txt:5-10`
5. `output/campaigns/**` の source SHA は canonical の 20 unique path から literal map に転記し、現ファイルの SHA と一致確認する。テスト実行時に canonical から導出してはならない。
6. canonical と現 worktree では少なくとも次の mutable SHA が異なるため、これらの SHA は helper に埋め込まない。
   - `p3_s4_loop_sort.py`: `9b64f34a…` → `0e716a6c…`
   - `s6_sort_sweep.py`: `0c7dcd30…` → `28270e90…`
   - `s8a_trigger_sweep.py`: `3e94735a…` → `8c3abd48…`
7. したがって、golden の意味値・path/key/layout は canonical を歴史的根拠にしつつ、テスト対象は常に fresh `K.build_document()` とする。canonical document 全体との比較は行わない。

## 3. ファイル別編集

### [test_s1_known_axes_freeze.py:23](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:23)

- 現行 `EXPECTED_STOCK_COMMON`、`EXPECTED_TRIGGER_FLAGS`、`_assert_exact_int_flags` を削除し、新 helper を import する。
- [65 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:65) のテストを `test_build_document_matches_registered_expected_goldens` に改名する。
  - `_require_submodule_sources()`
  - `doc = M.build_document()`
  - `assert_known_axes_goldens(doc)`
  - 既存の variant/fitness/backoff/sort-name 検査も helper の独立 literal に移し、`M.EXPECTED_*` 依存を除く。
  - comparator の exact equality により、`name == "sp_dd"` を保った実装差替えを赤にする。
- [90 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:90) の self-consistency positive control は残す。
- [113 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:113) を fresh document 化する。
  - `K.build_document()` を JSON 化して tmp へ書く。
  - 最初の quoted `"sp_dd"` を `"xp_dd"` に一 byte 置換し、bytes 長不変を確認。
  - `M.verify(path)` の例外文字列を `freeze JSON の内容が現行 generator による機械再構成と不一致` と完全一致させる。
- [124 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:124) も fresh document 化する。
  - 最初に検査される `balanced.system_gate.sources[0]` を tmp へコピーして一 byte 追記する。
  - resolver でその path だけ差し替える。
  - error が当該 `target_rel` の `source sha256 不一致` であることを確認し、先行 drift による false-green を除く。
- pairing、submodule predicate、plain `_run()` は維持する。

### [test_s1_measurement_freeze.py:23](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:23)

- `skiputil.skip` と `assert_known_axes_goldens` を import する。
- module-scope fixture `real_known_axes_doc` を新設する。
  - `.git` の有無だけで submodule init を判定し、不在時は理由付き skip。
  - `K.build_document()` を一度呼ぶ。
  - `assert_known_axes_goldens(doc)` で外部固定値と比較。
  - `K.verify_document(doc)` で source・HEAD・ccbench pin・再構成の self-consistency を一度確認。
- 現行 [24-140 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:24) の `freeze_env` は function scope のまま、`real_known_axes_doc` を受け取る形にする。
  - synthetic `material_source`、手製 entries/pairings/selection_rules を全削除。
  - `K.build_document` の monkeypatch echo を全削除。
  - fresh `tmp_path` に実 document の JSON bytes を複製。
  - dummy `s1_stats.py` は維持。
  - resolver は known tmp、dummy stats、実 measurement generator の 3 path だけを解決。
  - known source は既定 `K.ROOT / rel` で足りるため、synthetic `known_resolver` は削除。
- [143-165 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:143) の wrappers は `known_source_resolver` 引数を外し、既存の正規 seam のみ渡す。
- 一 byte freeze tamper は broad `FreezeError` ではなく最終の「機械再構成と不一致」を exact 検査する。
- T-080 テスト固有の monkeypatch は目的が別なので残す。

### [conftest.py:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:47)

`REAL_REPO_SERIAL_NODES` を更新する。

- known-axes の旧テスト名を新名へ置換。
- `test_build_document_is_self_consistent_and_detects_tamper` を追加。
- measurement の fixture 利用 9 node を追加。
- [92 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:92) の「全8 node は mutable worktree を読まない」という除外コメントを削除し、fixture 非利用の静的 import テストだけが group 外であることを明記する。

### [test_real_repo_serialization.py:30](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_real_repo_serialization.py:30)

- `_REAL_REPO_SERIAL_NODES_GOLDEN` に conftest と同じ node を独立 literal として追加する。
- conftest から導出しない原則は維持する。
- これにより、fixture 初期化が external/ccbench を patch する既存 writer と並走しないこと、module fixture が xdist 上も同一 worker で一度だけ生成されることを保証する。

### 変更しないファイル

- `orchestrator/campaign/**`
- `output/s1-freeze/*.json`
- `output/s8b-freeze/*.json`
- [test_frozen_artifacts.py:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:33) の 8 pin

## 4. measurement 既存テストへの影響

| テスト | 新 fixture 下の挙動 | 実 `K.build_document()` 回数 |
|---|---|---:|
| `test_generate_builds_registered_cells_comparisons_and_schedule` | real known doc の 18 cells を検査。構造 assertion は維持し、cell variant が元 entry の deepcopy と一致することも確認 | 1 |
| `test_generate_refuses_existing_freeze` | 初回だけ実材料検証、2 回目は existing guard で build 前に拒否 | 1 |
| `test_verify_rejects_one_byte_freeze_tamper` | valid real freeze を改竄し、最終再構成不一致だけで拒否 | 3 |
| `test_verify_rejects_one_byte_workload_flag_tamper` | generate 後、schema の `workload_flags` 検査で早期拒否 | 1 |
| `test_verify_rejects_stats_implementation_tamper` | function-local dummy stats の SHA 不一致で拒否 | 1 |
| `test_verify_rejects_known_axes_material_tamper` | function-local known JSON bytes の SHA 不一致で拒否 | 1 |
| `test_schedule_is_balanced_and_reproducible` | 2 回の実 build で schedule/hash の再現性を維持 | 2 |
| `test_s1b_pairing_rejects_mismatched_flags` | real cell の ident flags 改竄を pairing 検査で拒否 | 2 |
| `test_receipt_exists_but_measurement_verify_stays_legacy_strict` | real known doc を使いつつ、T-080 adapter 非呼出し契約を維持 | 3 |
| `test_measurement_production_module_does_not_import_t080_adapter` | fixture 非利用、変更なし | 0 |

module fixture 自身の生成と self-verify でさらに 2 回。ファイル全体を一度に走らせた場合、measurement 側は合計 17 回の実 `K.build_document()` となる。

削除するのは synthetic fixture と `K.build_document` echo monkeypatch だけで、既存テスト関数は削除しない。

## 5. 実装単位

1. **単位1 — helper + known-axes A/C**
   - `s1_expected_goldens.py` 新設
   - known-axes の comprehensive golden 化
   - one-byte/source-copy false-green 2 件修正
   - known-axes node 名・不足 node の serialization 正本二面を更新
   - known-axes plain runner、serialization meta-test、frozen manifest test を通す

2. **単位2 — measurement B**
   - module/function 二層 fixture へ移行
   - echo monkeypatch と synthetic material を削除
   - 9 fixture consumer を serialization 正本二面へ追加
   - measurement、known-axes、serialization をまとめて通す

helper と serialization exact 集合を共有するため直列とする。並列化する場合でも、先に helper API を固定し、最後に serialization 二面だけを単一 integration 単位で更新する必要がある。

## 6. 検証計画

- 対象テスト:
  - `python3 orchestrator/tests/test_s1_known_axes_freeze.py`
  - `python3 tools/run_tests.py -q orchestrator/tests/test_s1_known_axes_freeze.py orchestrator/tests/test_s1_measurement_freeze.py orchestrator/tests/test_real_repo_serialization.py orchestrator/tests/test_frozen_artifacts.py`
- sort comparator 受入変異:
  - disposable worktree で `_sort_entry()` の balanced name を `sp_dd` のまま保ち comparator だけ差し替える。
  - `test_build_document_matches_registered_expected_goldens` が comparator mismatch 単一理由で赤になることを確認して破棄する。
- source/key、predicate、P2/backoff/sort flags も同様に一時変異し、helper assertion が該当 owner/field を名指しして赤になることを確認する。
- 全テスト:
  - `python3 tools/run_tests.py`
  - `python3 tools/check_codex_agents.py`
  - `python3 tools/check_docs.py`
  - commit 後 `python3 tools/check_ai_provenance.py`
- `test_frozen_artifacts.py` で 8 pin 不変を再確認し、特に S-1 2 本が現行 `354f4b87…` / `203de36b…` のままであることを確認する。

## 7. 偽赤リスクと時間見積り

- submodule 未 init 環境では measurement の 9 テストが module fixture 由来で明示 skip になる。synthetic fixture 時代より依存性が強くなる点をテスト結果に可視化する。
- external/ccbench や generator source が別 process から編集中だと、生成時と後続 verify 時の SHA がずれて偽赤になり得る。xdist 内は `real-repo` group で防ぐが、外部編集とは同時実行しない。
- `output/campaigns/**` の正当な再発行でも exact SHA golden は赤になる。これは防護ツリーの変更レビューを要求する意図した停止である。
- comparator/predicate は逐語 pin のため、意味同値な空白変更も赤になる。受入基準が逐語保証なので許容する。
- mutable source の SHA は pin しないため、comment-only 編集では赤にならない。一方、path/key/list 順序・lines mapping・抽出された flags/comparator/predicate は固定される。
- function-scope temp 複製により、stats/known tamper のテスト順依存は除去する。
- 計測なしの静的見積りでは、measurement で実 build 17 回、known-axes false-green 修正で従来比 3 回、合計約 20 回増える。対象 WAL/provenance は約 0.23 MiB・479 WAL 行なので、warm local filesystem では概ね **+1〜3 秒**、cold/network filesystem や git subprocess が遅い環境では **+3〜10 秒**を見込む。実装後に pytest `--durations` で fixture setup と各テストを実測し、想定を超える場合も echo monkeypatch へ戻さず正規 seam 内で呼出し回数を再評価する。
---

## 段3 敵対相談 1 — 正しさ境界レンズ (逐語)

判定: **NO-GO**。pytest は実行せず、静的読解のみ。nit はなく real 10 件です。

[1] real | 対象: plan §3/§6 / brief P1 | 主張: comparator golden が守るのは freeze に記録された文字列までで、実行境界を守らない。計画の変異点は `_sort_entry()` に限定されているが、実際の comparator は `prepare_cell()` が `variant["comparator"]` を取り出し quarantine へ渡す（[s1_direct_comparison.py:517](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:517)、[同:534](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:534)）。計画対象テストはこの境界を呼ばず、受入変異も recorder 側だけである（[plan_out.md:97](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:97)、[同:196](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:196)）。  
放置した場合の影響: freeze と golden は正しい comparator を示したまま、実測だけが別 comparator を走らせられる。  
推奨対処: `prepare_cell()` の quarantine 引数が cell の comparator と逐語一致するテストを balanced/write-heavy/read-heavy 全件に追加し、consumer 側差替えも受入変異にする。

[2] real | 対象: plan §2 / brief P2 | 主張: mutable source の SHA を形だけ検査するため、source が主張する意味を一行変異で偽装できる。例えば `SWEEP_US` から `100` を削除しても（[backoff_sweep.py:43](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/backoff_sweep.py:43)）、reader は候補集合を変更後の同じ `SWEEP_US` と比較するだけで（[s1_known_axes_freeze.py:290](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:290)、[同:300](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:300)）、勝者 5/10/2 と flags は不変である。plan は当該 module SHA を 64hex としか固定しない（[plan_out.md:7](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:7)、[同:213](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:213)）。  
放置した場合の影響: 測定済み競合点を事後的に候補集合から除外しても、「全 grid の argmax」という選定証明が緑のままになる。  
推奨対処: full-file SHA ではなく、少なくとも `SWEEP_US == (2,5,10,25,50,100)` など source key が主張する semantic slice を独立 golden にする。

[3] real | 対象: plan §3 / brief P3 | 主張: pre-validated な valid known doc しか M に渡さないため、M→K verifier の結線を検査していない。production の結線は [s1_measurement_freeze.py:156](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:156) と [同:249](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:249) だが、plan は fixture setup で先に K を通す（[plan_out.md:117](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:117)）。既存 known material tamper は bytes 追記だけで（[test_s1_measurement_freeze.py:228](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:228)）、M の implementation hash 検査が K 呼出しより先に落とす（[s1_measurement_freeze.py:400](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:400)、[同:407](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:407)）。  
放置した場合の影響: `_verify_known_axes()` を単なる `_load_json()` に弱体化しても measurement テストは緑になり、無効な known doc が cells へ流入する。  
推奨対処: fresh known doc の `what` 等を改竄して `M.build_document()` に直接渡し、wrapped K refusal の exact reason を要求する単一理由テストを追加する。

[4] real | 対象: plan §3 / brief P3 | 主張: generator hash・ancestry・ccbench pin の live 検査は fresh doc に対して恒真である。K は同じ live repo から三値を生成し（[s1_known_axes_freeze.py:632](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:632)）、同じ repo と照合した後、記録値を override して再構成する（[同:724](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:724)、[同:747](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:747)、[同:759](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:759)）。helper の固定対象にも三値はない（[plan_out.md:20](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:20)）。一方、途中で source が編集された場合だけ偽赤になり得ることを plan 自身が認めている（[plan_out.md:210](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:210)）。  
放置した場合の影響: 三検査を削除する変異は検出できず、並行する正当編集だけが source SHA の TOCTOU で赤になる。  
推奨対処: generator SHA 改竄、非 ancestor SHA、異なる ccbench pin の三つを独立した exact-reason negative control にし、live repo 読みは immutable snapshot または実効ロック下に置く。

[5] real | 対象: plan §3 / brief P3 | 主張: known と measurement の ccbench pin が同じ commit であることを検査していない。K は submodule の実 HEAD を full SHA で取得する（[s1_known_axes_freeze.py:633](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:633)）一方、M は独立に `pin.CURRENT_PIN` を記録する（[s1_measurement_freeze.py:262](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:262)）。両者の equality はなく、実行時には M 側 pin が checkout される（[s1_direct_comparison.py:503](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:503)）。設計上は同一 40 桁が契約である（[freeze-permanent-design.md:132](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:132)）。  
放置した場合の影響: `pin.CURRENT_PIN` だけを誤更新しても fixture は通り、known axes と異なる、または不存在の commit を measurement が実体化する。  
推奨対処: short/full を `git rev-parse` で正規化して `known_doc["ccbench_pin"]` と M pin の一致を build/verify の双方で検査し、pin-only 変異を登録する。

[6] real | 対象: plan §6 | 主張: 受入変異が「新テストだけの検出」を証明しない。`_sort_entry()` を disposable worktree で編集すると generator file SHA も変わり、旧 source-copy テストは canonical generator SHA 検査（[s1_known_axes_freeze.py:724](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:724)）で、期待していた source mismatch より先に赤になる（[test_s1_known_axes_freeze.py:124](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:124)）。plan は新テストが赤になることしか要求していない（[plan_out.md:196](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:196)）。  
放置した場合の影響: 既存の自己 hash／false-red による kill を新 golden の検出力として誤計上する。  
推奨対処: K の bytes を変えない runtime monkeypatch で戻り comparator だけを変え、HEAD assertion 群は緑・新 assertion だけ赤を明示的に要求する。

[7] real | 対象: plan §7 / brief P3 | 主張: submodule 不在時に measurement の behavioral tests 9 件すべてを skip へ落とす（[plan_out.md:209](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:209)）。このリポジトリの skip は可視化されるだけで失敗にはならず（[orchestrator/tests/README.md:92](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/README.md:92)）、static import テストしか残らない。  
放置した場合の影響: submodule を初期化しない CI/fresh clone が measurement regression を一件も実行せず exit 0 になる。  
推奨対処: 必須 CI profile では submodule 不在を hard-fail にするか、K echo を使わない hermetic M-only laneを残し、real integration lane を別途必須化する。

[8] real | 対象: brief P1 | 主張: brief は二件目の false-green を scope から落としている。source-copy テストは canonical の p2 source を改竄対象にする（[test_s1_known_axes_freeze.py:124](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:124)）が、canonical traversal では drift 済み `s8a_trigger_sweep.py` source が先に現れ（[known_axes_freeze.json:51](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/known_axes_freeze.json:51)）、target p2 source は後段である（[同:102](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/known_axes_freeze.json:102)）。しかも期待 regex は path を固定しない broad `"source sha256 不一致"` である（[test_s1_known_axes_freeze.py:134](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:134)）。  
放置した場合の影響: 改竄した copy が一度も検査されなくても、別 source の既知 drift だけで positive control が緑になる。  
推奨対処: plan §1 の fresh-doc＋最初の source＋target path exact 化を optional correction ではなく scope C の必須項目にする。

[9] real | 対象: brief P3 | 主張: module-scope fixture 全体を一回生成する案は mutable temp を共有し、テスト間汚染を起こす。既存テストは `stats_path` を破壊し（[test_s1_measurement_freeze.py:219](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:219)）、別テストは `known_path` を破壊する（[同:228](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:228)）。  
放置した場合の影響: 後続テストが自身の検査点へ到達せず、前テストの残留改竄で順序依存の偽赤になる。  
推奨対処: module scope は immutable document object だけ、known/stats の temp file は function scope で毎回複製する。

[10] real | 対象: brief P1 | 主張: test body＋helper だけという scope では xdist の競合を閉じられない。K は実 `Options.cmake` を読む（[s1_known_axes_freeze.py:539](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:539)）一方、既存 writer が適用する sort patch は同ファイルを書き換える（[silo-sort-variant.patch:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/patches/silo-sort-variant.patch:1)）。writer 群は現在 real-repo group に列挙されている（[conftest.py:54](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:54)）。  
放置した場合の影響: 新 measurement reader と既存 patch writer が並走し、transient source hash を記録する偽緑または apply/revert 間の偽赤になる。  
推奨対処: `conftest.py` と独立 serialization golden を P1 scope に明記し、全 fixture consumer を同一 group に登録する。

### P1〜P6 裁定

| P | 裁定 | 理由 |
|---|---|---|
| P1 | 否認 | source-copy false-green、runtime comparator consumer、xdist serialization の三面が scope 外。 |
| P2 | 否認 | SHA 形状だけでは `SWEEP_US` 等、source key が主張する mutable semantics を守れない。 |
| P3 | 否認 | 共有 temp 汚染、M→K 結線未検査、live metadata 恒真、cross-pin、9件 skip が残る。 |
| P4 | 採用 | fresh doc の `sp_dd` 改竄は schema/source/pairingを変えず最終再構成不一致へ到達する。 |
| P5 | 採用 | test-local literal を production から導出しない配置自体に実害はない。 |
| P6 | 採用 | 実装単位は直列でよい。ただし plan §6 の変異受入方法は否認。 |
---

## 段3 敵対相談 2 — 整合・実効性レンズ (逐語)

結論は **NO-GO**。件数の棚卸しは概ね正しいが、P3 の構成・source schema・変異検証手順に実害のある穴がある。

[1] real | 対象: brief P1 | P3 を採るなら `conftest.py` と serialization golden は scope 外にできない。現行は measurement を明示的に group 外としており、known-axes の self-consistency node も未登録である（[conftest.py:70](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:70), [conftest.py:91](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:91), [test_s1_known_axes_freeze.py:90](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:90)）。  
放置した場合の影響: xdist 中に ccbench writer と競合して一過性 SHA 不一致が発生し、改名後の旧 node は収集監査も落とす。  
推奨対処: plan の補正どおり両 serialization 面を scope に入れる。measurement は fixture consumer 9 node、fixture 非利用 1 nodeという数え方で正しい。

[2] real | 対象: plan §3 | known-axes テストの実装指示が未定義の `K.build_document()` を呼んでいるが、このファイルが import する alias は `M` だけである（[plan_out.md:105](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:105), [test_s1_known_axes_freeze.py:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:20)）。  
放置した場合の影響: 計画どおり実装すると tamper テストが `NameError` で落ち、目的の検査へ到達しない。  
推奨対処: `M.build_document()` に訂正し、例外理由は捕捉後に `str(exc.value) == ...` で完全一致させる。

[3] real | 対象: brief P3 | 「tmp 書き出しも module scope で一度」は成立しない。既存テストは stats と known JSON をその場で破壊する（[test_s1_measurement_freeze.py:219](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:219), [test_s1_measurement_freeze.py:228](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:228)）。  
放置した場合の影響: module temp を共有すると改竄が後続テストへ残り、順序依存の連鎖赤になる。  
推奨対処: module scope は immutable document のみに限定し、known/stats の bytes は function scope で複製する。

[4] real | 対象: plan §3・§7 / brief P3 | 全9テストを real-repo integration 化する設計は、現行 fixture の独立性を削除している。現行コメントは「並行タスクの正当な変更で B1 テストまで腐る」ことを明示的に防いでいる一方、plan は submodule 不在時に9件すべてを skip する（[test_s1_measurement_freeze.py:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:25), [plan_out.md:209](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:209)）。  
放置した場合の影響: fresh clone では schedule、workload schema、T-080 非呼出しなど measurement 固有の回帰検出まで一括消失する。  
推奨対処: D68 を閉じる real integration node を1件設け、schedule/schema/T-080 等は synthetic data を使う明示的 unit seam に分離する。`K.build_document` echo は使わない。

[5] real | 対象: plan §4・§7 / brief P3 | 17回という回数は正しいが、「module scope で一度生成」と時間見積りは誤誘導的である。`M.build_document()` は毎回 known verify を行い、`K.verify_document()` は63 sourceを hash 後に再構成し、validな `M.verify_document()` はさらに `M.build_document()` を呼ぶ（[s1_measurement_freeze.py:249](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:249), [s1_known_axes_freeze.py:729](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:729), [s1_known_axes_freeze.py:759](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:759), [s1_measurement_freeze.py:430](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:430)）。  
放置した場合の影響: WAL 0.23 MiB だけを根拠にした +1〜3秒予算を超え、17回すべてが `real-repo` worker の直列 critical pathになる。  
推奨対処: real integration を最小化し、実装前に「許容 wall time」を決める。`--durations` は事後確認でなく採否 gate にする。

[6] real | 対象: plan §2 / brief P2 | `EXPECTED_SOURCE_LAYOUT` は `(path,key,lines-pattern)` と SHA 形式しか規定せず、source record の exact key-set を固定していない（[plan_out.md:27](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:27), [plan_out.md:70](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:70)）。production verifier も source の `path/sha256` 以外を無視する（[s1_known_axes_freeze.py:731](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:731)）。  
放置した場合の影響: `_source()` が任意の余分な field を追加しても self-consistency と新 helper の双方を通り、「source record 構造」golden が恒真化する。  
推奨対処: 各 occurrence で key-set を `{"path","sha256","key"}` またはそれに `lines` を加えた集合へ完全一致させる。

[7] real | 対象: plan §6 | disposable worktree の submodule 初期化、baseline PASS、SKIP/HALT 拒否、変更前テストとの差分実走がない。対象テストは `.git` 不在なら即 skip する（[test_s1_known_axes_freeze.py:55](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:55), [plan_out.md:197](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:197)）。テスト強化 wave は新旧双方での変異実走が必須である（[dev-wave.md:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/.claude/commands/dev-wave.md:22)）。  
放置した場合の影響: submodule 未初期化による SKIPや既存の別理由の赤を comparator kill と誤認し、追加検出力を証明できない。  
推奨対処: submodule init → baseline green → 単一変異 → exact failing node/reason → HEAD版では生存・新テストのみkill、を機械化する。

[8] real | 対象: plan §6 | 「worktree を破棄」だけでは mutation harness の復元契約を満たさない。単一走行 guard と、元 bytes との復元後完全一致が計画にない（[plan_out.md:196](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:196), [dev-wave.md:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/.claude/commands/dev-wave.md:22)）。  
放置した場合の影響: 二重走行や異常終了で変異 production copy が残り、後続の受入結果や patch 採取を汚染する。  
推奨対処: `flock`、親側 `finally`、元 bytes 保存、復元後 byte equality、残存 process 確認後の worktree 削除を必須化する。隔離下の一時変異自体は no-touch 不変条件との矛盾ではない。

[9] real | 対象: plan §5 / brief P6 | 全直列化の根拠は成立しない。plan 自身が serialization 二面を単一 integration 単位へ後置できると認めており、既定手順も依存成果物を先に展開後、所有素集合を並列化する（[plan_out.md:176](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:176), [plan_out.md:189](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/plan_out.md:189), [dev-wave.md:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/.claude/commands/dev-wave.md:21)）。  
放置した場合の影響: known/measurement の独立編集まで直列化し、serialization literal を二度編集するため工期と転記漏れリスクが増える。  
推奨対処: helper API固定 → known側とmeasurement側を並列 → conftest/serializationを最後の単一integration単位、の3段にする。

| P | 裁定 | 理由 |
|---|---|---|
| P1 | 否認 | real-repo 化するなら conftest と独立 serialization golden が必要。 |
| P2 | 採用 | SHA境界と 18 owner / 63 record / campaign 20 unique path は整合。ただし exact source key-set を追加すること。 |
| P3 | 否認 | module temp共有は破壊的で、「build一度」も実際には17回再構成される。unit/integration分離が必要。 |
| P4 | 採用 | known側は sort name、measurement側は top-level `what` の改竄なので pairing/schema先行拒否を受けず、最終再構成不一致に到達する。 |
| P5 | 採用 | production/canonical非依存の literal helper を共有する方向は妥当。 |
| P6 | 否認 | helper-first と serialization-last の間で2テスト本体は並列化できる。 |

pytest は指示どおり実行していない。回数・node・source件数は静的に検算した。
---

## 段4 裁定 v2 + 変異事前登録 (親、逐語)

# 段4 裁定: プラン v2 ([T-066] 継続 wave)

## 所見の裁定 (C=正しさ境界レンズ、E=整合・実効性レンズ)

| 所見 | real/refuted | scope | 対処 |
|---|---|---|---|
| C1 consumer 境界 (prepare_cell→quarantine の verbatim passthrough 未検査) | real (親 grep で確認: quarantine 引数検査ゼロ) | **in** | 新 unit3: test_s1_direct_comparison.py へ sort_best/system_gate/ident_all の passthrough 検査。G5 影響: freeze/golden が正しくても実測 cells が別実装で走り certified 選択の来歴が偽になる |
| C2 SWEEP_US semantic slice | real | **in** | helper へ EXPECTED_SWEEP_US golden (backoff_sweep.SWEEP_US と照合)。G5: 測定済み競合点の事後除外で「全 grid argmax」証明が偽緑 |
| C3 M→K 結線未検査 | real | **in** | unit2: fresh known doc の what 改竄 → M.build_document が wrapped 拒否 (exact reason) |
| C4 live 検査の恒真性 | real (negative control 不在) | **in** (3 検査) / snapshot・lock 化は **out** (xdist group で足りる、外部並行編集は既知限界として記録) | unit1: generator sha 改竄・非 ancestor head・ccbench_pin 改竄の 3 negative control (exact reason) |
| C5 cross-pin 相互一致 | **refuted** | - | test_s8b_approved.py:53-64 が CURRENT_PIN の prefix 一致を gitlink/full SHA へ既に検査 — 攻撃 (pin-only 誤更新) は既存検出。M 内 production 検査追加は backlog 記載のみ |
| C6 変異方法論 (K.py 編集の bytes 波及) | real | **in** (手順) | control mutation (comment-only) で bytes 感度赤と意味検出赤を分離。monkeypatch 変異は不採用 |
| C7 submodule 不在で 9 件 skip | real (トレードオフ) | 部分 **in** | unit2: hermetic unit seam (build_schedule 決定性・_build_comparisons 構造) を追加し fresh clone でも M 固有検査を残す。CI hard-fail 化は**裁定パッケージ**でユーザーへ |
| C8 tampered_source_copy も false-green | real (E1 で論理確定) | **in** | unit1: fresh doc 化 + target path exact (scope C 必須項目へ昇格) |
| C9/E3 module temp 共有汚染 | real | **in** | module scope = immutable doc object のみ。file 複製は function scope |
| C10/E1 conftest+serialization 両面更新 | real | **in** | 親 integration ハンク (レビューで名指し)。既存欠落 (self-consistency node 未登録) も同時に閉じる |
| E2 alias 誤り (K.build_document→M) | real | in | unit プロンプトへ正確な alias を明記 |
| E4 hermetic 独立性の喪失 | 部分 real | 部分 in | C7 と同処置。9 integration node の最小化 (1 node 化) は**否認** — C3 結線検査と tamper exact reason は実経路が必要で、echo は禁止裁定 |
| E5 実行時間見積り | **refuted (実測)** | - | K.build 0.08s / K.verify 0.08s / M.build 0.08s → 17 回 ≈ 1.4s。受入時 --durations で確認のみ |
| E6 source record の exact key-set | real | **in** | helper: 各 source occurrence の key 集合を {path,sha256,key}(+lines) へ完全一致 |
| E7/E8 変異ハーネス規律 | real | **in** (手順) | submodule init・baseline green 先行・SKIP≠kill・flock・subprocess timeout・復元 byte 等価・赤 node 名記録 |
| E9 並列化 | real | **in** | 3 段: 親 helper 先行 → unit1∥unit2∥unit3 → 親 integration |

## P1〜P6 v2

- P1 修正採用: scope = (A)+C2/C4/E6、(B)+C3/C7-seam、(C)+C8、(D)、C1 (unit3)、親 integration (conftest+serialization)。production/凍結成果物 no-touch 不変
- P2 修正採用: + SWEEP_US semantic golden + exact key-set
- P3 修正採用: module=immutable doc、function=file 複製。echo 禁止は不変
- P4 採用 (両相談一致)
- P5 採用: helper は親ハンク。canonical 記録値との一致を生成時に機械照合してから凍結 (現行コード恒真化の回避)
- P6 修正採用: 親 helper commit → 3 unit 並列 (worktree 分離、所有素集合: unit1=test_s1_known_axes_freeze.py / unit2=test_s1_measurement_freeze.py / unit3=test_s1_direct_comparison.py) → 親 integration

## 変異事前登録 (B-057。各変異の単一理由性はコード読解で確認済み)

前提: 全変異は disposable worktree (submodule init 済み・baseline green 確認済み) で production を実編集し、
「新テスト (本 wave 後)」と「HEAD テスト (本 wave 前)」の両方に対して同一変異を走らせ、差分で検出力を示す。
K.py 編集は canonical generator sha 経由で HEAD の tampered_source_copy を false-reason 赤にするため、
MU-CTRL でベースライン化する。

- **MU-CTRL** (K.py へ comment 1 行追加): 期待 = NEW 全緑 / HEAD は tampered_source_copy のみ赤 (match 不成立、bytes 感度)。意味検出ではないことの対照
- **MU-A** (K.py `_sort_entry` 本走 return の `"comparator": comparator,` → `comparator + " "`): NEW = comparator golden 赤 (balanced/write-heavy、単一理由: comparator は build 経路で他に検査されない)。HEAD = MU-CTRL と同一の赤のみ
- **MU-B** (K.py `_trigger_entries` の gate dict `"gate_predicate": gate_predicate,` → `+ " "`): NEW = gate predicate golden 赤 (s1b_pairing は gate≠ident のみ検査で素通り)。HEAD = 同上
- **MU-C** (K.py `_source` の return dict へ `"extra": 1` 追加): NEW = exact key-set golden 赤 (verify は path/sha256 しか見ない)。HEAD = 同上
- **MU-D** (backoff_sweep.py `SWEEP_US` から 100 を削除): NEW = EXPECTED_SWEEP_US golden 赤 (production の set 等価検査は両側同時に縮み素通り — C2 の実証)。HEAD = **全緑** (canonical 検査は既存 drift で同じ理由のまま)
- **MU-E** (M.py `_build_cells` の `"variant": copy.deepcopy(variant),` → comparator key を落とす dict 内包): NEW = cells 射影 golden 赤 (schema は variant の中身を見ない)。HEAD = 全緑 (echo fixture は K 実値を見ない)
- **MU-F** (M.py `_verify_known_axes` の `known_axes.verify_document(...)` 呼出し除去): NEW = C3 結線テスト赤 (単一理由: 他に known doc の意味検証経路なし)。HEAD = 全緑
- **MU-H** (K.py `verify_document` の generator sha 検査 (724-727) 除去): NEW = C4 generator-sha negative control 赤。HEAD = 全緑 (canonical 検査は sources drift で同理由継続)
- **MU-I** (s1_direct_comparison.py `variant.get("comparator")` → `.strip()` 付加): NEW = unit3 passthrough 検査赤 (quarantine 受領値 ≠ 逐語)。HEAD = 全緑 (既存テストは quarantine 引数を検査しない)

kill 判定 = 受理集合/fail-closed 挙動の期待方向変化。診断文字列のみの変化は diagnostic sensitivity pin 枠へ。

## 裁定パッケージ (scope 外 real、ユーザーへ)

1. **CI/fresh-clone での submodule 必須化** (C7 残余): 現行方針は「未 init は可視 skip」。hard-fail profile を作るかは infra 裁定。推奨 = 現状維持 (hermetic unit seam で部分緩和済み、skip は受入で可視)
2. (backlog 記載のみ) M freeze 内 ccbench_pin と known freeze の相互一致を production で検査するか — 既存 test_s8b_approved の transitive 検査で攻撃経路は閉じており急がない

---

## 段5 実装単位 完了報告 u1 (known-axes)

実装完了しました。変更は [test_s1_known_axes_freeze.py](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/wt-u1/orchestrator/tests/test_s1_known_axes_freeze.py) のみで、commit は作成していません。

検証結果:

- `python3 tools/run_tests.py orchestrator/tests/test_s1_known_axes_freeze.py`
  - 11 passed
- `python3 orchestrator/tests/test_s1_known_axes_freeze.py`
  - 11 passed, 0 failed, 0 skipped
- `python3 tools/check_codex_agents.py`
  - OK
- `python3 tools/check_docs.py`
  - 違反なし
- 期待赤: 0

所有外への波及可能性:

- 既存テスト名の変更: なし
- 既存登録済み node のうち、fresh doc 化した2件も名前は維持:
  - `test_verify_rejects_one_byte_freeze_tamper`
  - `test_verify_rejects_tampered_source_copy`
- 新規テストのうち submodule を読むため、親側で `conftest.py` の `REAL_REPO_SERIAL_NODES` と `test_real_repo_serialization.py` の独立 golden への登録が必要:
  - `test_verify_rejects_generator_sha_tamper`
  - `test_verify_rejects_non_ancestor_head`
  - `test_verify_rejects_foreign_ccbench_pin`
- `test_backoff_sweep_grid_matches_registered_golden` は submodule を読まないため登録不要。

`s1_expected_goldens.py` に不足・誤りは見つかりませんでした。fresh document に対する全 golden 検査も通過しています。
---

## 段5 実装単位 完了報告 u2 (measurement)

実装完了しました。変更は [test_s1_measurement_freeze.py](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/wt-u2/orchestrator/tests/test_s1_measurement_freeze.py) のみで、commit は作成していません。

検証結果:

- 対象単体: 13 passed / 期待赤ゼロ / 2.25s
- known-axes 併走: 20 passed / 期待赤ゼロ / 2.29s
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- `git diff --check`: OK
- echo、動的 generator hash 注入、`known_source_resolver` は残っていません

`--durations=10` の対象単体上位:

| 時間 | phase | node |
|---:|---|---|
| 0.34s | call | `test_receipt_exists_but_measurement_verify_stays_legacy_strict` |
| 0.33s | call | `test_verify_rejects_one_byte_freeze_tamper` |
| 0.24s | call | `test_schedule_is_balanced_and_reproducible` |
| 0.23s | call | `test_s1b_pairing_rejects_mismatched_flags` |
| 0.21s | setup | `test_s1b_pairing_rejects_mismatched_flags` |
| 0.21s | setup | `test_generate_refuses_existing_freeze` |
| 0.21s | setup | `test_schedule_is_balanced_and_reproducible` |
| 0.21s | setup | `test_verify_rejects_one_byte_freeze_tamper` |
| 0.21s | setup | `test_verify_rejects_known_axes_material_tamper` |
| 0.21s | setup | `test_verify_rejects_stats_implementation_tamper` |

所有外への波及として、以下の10 nodeを `conftest.py` の `REAL_REPO_SERIAL_NODES` と `test_real_repo_serialization.py` の goldenへ登録する必要があります。全て module fixtureまたはM→K検査を通じて実 known-axes材料・共有 submodule sourceを読みます。

- `test_generate_builds_registered_cells_comparisons_and_schedule`
- `test_generate_refuses_existing_freeze`
- `test_verify_rejects_one_byte_freeze_tamper`
- `test_verify_rejects_one_byte_workload_flag_tamper`
- `test_verify_rejects_stats_implementation_tamper`
- `test_verify_rejects_known_axes_material_tamper`
- `test_schedule_is_balanced_and_reproducible`
- `test_s1b_pairing_rejects_mismatched_flags`
- `test_receipt_exists_but_measurement_verify_stays_legacy_strict`
- `test_build_document_rejects_tampered_known_axes_semantics`

登録不要:

- `test_measurement_production_module_does_not_import_t080_adapter`: shared ccbench patch面を読まない既存AST検査
- `test_build_schedule_is_deterministic_and_balanced_without_submodule`: filesystem非依存
- `test_build_comparisons_structure_without_submodule`: filesystem非依存

現状は未登録のため、xdist実行では module fixtureがworkerごとに構築され得ます。親側で上記10 nodeを同じ `real-repo` groupへ登録すると、実材料生成が単一workerへ集約されます。

`s1_expected_goldens` helperの不足・誤りは今回の実走では検出されませんでした。fresh `K.build_document()` に対する外部golden照合も通過しています。
---

## 段5 実装単位 完了報告 u3 (direct_comparison)

実装完了です。[test_s1_direct_comparison.py](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/wt-u3/orchestrator/tests/test_s1_direct_comparison.py:221) に3テストを追加しました。

- comparator / system_gate / ident_all の逐語受け渡しを `==` で検査
- 前後空白・改行・インデントを含む入力を使用
- `marker_id` / `source_rel` も軸定数と照合
- checkout・patch apply・quarantine・source digest を monkeypatch し、実 CCBench repoには非接触
- fake quarantine は `.passed=True` の結果を含む4-tupleを返却

検証結果:

- `python3 tools/run_tests.py orchestrator/tests/test_s1_direct_comparison.py`
  - `27 passed`
  - 期待赤ゼロ
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `git diff --check`: OK

xdist real-repo group への登録は不要です。全I/O境界を monkeypatch し、`tmp_path` 以外の実 repository treeを読み書きしないためです。

逐語性以外の新たな欠陥は確認していません。変更は所有テストファイルへの追加のみで、production・docs は未変更、commit も行っていません。
---

## 段6 敵対レビュー 1 — 正しさ境界 (逐語、NO-GO)

must-fix 7 件。canonical との転記値自体、および real-repo node 登録には誤りはありません。問題は独立検出の穴です。

[1] must-fix | 対象 [test_s1_measurement_freeze.py:275](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:275) | `comparisons` は件数・family 数・`alternative` しか検査しない。任意の有効セルへ `right_cell` を差し替えても、production schema と両テストを通る。 | **放置すると S-1a/S-1b の対象・対照標本、p 値、family judgment が別の比較へすり替わり、certified 選択が変わる。** | canonical 12 レコードの全フィールドを test-local literal で順序込み完全一致し、cross-workload/right-cell 差替え変異を追加する。

[2] must-fix | 対象 [test_s1_measurement_freeze.py:262](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:262) | schedule 検査は「決定的・18セル・総数288」だけで、事前登録した seed/order を固定しない。`MASTER_SEED` や `derive_seed` の domain を変更しても緑になる。canonical は seed `20260715`、schedule hash `b76333da5db1945908641679773bf7ef307ac2dc2bb3462a171b15be235ae150`。 | **放置すると ledger の実行順・schedule_hash・campaign identity が変わり、時間ドリフトを受ける測定値と最終選択が変わる。** | seed と canonical schedule hash、できれば全 schedule を独立 literal で固定し、seed/domain 変異を matrix に加える。

[3] must-fix | 対象 [s1_expected_goldens.py:423](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/s1_expected_goldens.py:423), [test_s1_measurement_freeze.py:105](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:105) | Python の `==` を「完全一致」と誤認している。`backoff_us: 5→5.0`、fitness の float→int、M 射影で flag `1→True` が通る。さらに `.get(...)=None` は key 不在と明示 `null` を同一視し、configuration 内 key-set と `sort_best.note` も未固定。 | **放置すると golden を通った measurement freeze が bool flag／float backoff を持ち、`prepare_cell` に拒否されて登録セルが実行不能になるほか、variant/report の schema も無審査で変わる。** | 型・dict key-set・list 順を再帰的に検査する JSON exact helperへ置換し、M の cell 射影にも同じ型厳密比較を使う。

[4] must-fix | 対象 [s1_expected_goldens.py:463](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/s1_expected_goldens.py:463) | source の `lines` は存在有無しか見ていない。canonical の Options.cmake 5 行／Silo CMakeLists 3 行を任意文字列へ差し替えても golden を通り、K の再構成も同じ producer を使うため恒真化する。 | **放置すると known-axes と measurement の proof chain が、実際とは異なる行を根拠としてレポートする。** | 固定 ccbench pin に対する `lines` の文字列・順序を literal 固定する。pin bump 時だけ裁定付きで更新する。

[5] must-fix | 対象 [test_s1_measurement_freeze.py:43](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:43) | fixture は K 文書の full `ccbench_pin`（実 submodule HEAD）と M の `pin.CURRENT_PIN` を結び付けない。`test_s8b_approved` が固定するのは superproject gitlink であり、K が読む初期化済み worktree の実 HEAD ではない。 | **放置すると commit A から抽出した cells/source references を、direct comparison が commit B でビルドし、レポートの材料参照と実行対象が分離する。** | M production verifier で両 pin を full SHA に解決して一致必須とし、fixtureにも canonical full pin と foreign-HEAD negative controlを置く。

[6] must-fix | 対象 [test_s1_measurement_freeze.py:43](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:43) | 旧 synthetic fixture を全削除した結果、submodule 未初期化時は M の build/generate/verify・hash tamper・pairing・M→K 結線を含む10 nodeが一括 skip する。新しい hermetic seam 2件は schedule/comparison の純関数しか覆わない。 | **放置すると fresh-clone runner では measurement freeze の tamper 受理や implementation hash 結線回帰が検出されず、誤った freeze/report を受理できる。** | real integration fixtureは残しつつ、M-local 契約用の独立 hermetic fixtureを復活させるか、受入環境で submodule 未初期化を hard-fail にする。

[7] must-fix | 対象 [test_s1_known_axes_freeze.py:123](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:123), [test_s1_measurement_freeze.py:220](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:220) | source/generator/pin は `startswith`、head は包含、M→K wrapper は prefix＋包含だけで、名指しされた exact reason 契約を満たさない。MU-H は検査削除を殺すだけで、誤分類・偽 detail は通す。 | **放置すると oracle の `refusals` と拒否レポートに誤った原因・hash/detail が記録され、同じ reject でも証拠参照が変わる。** | fresh doc の改竄前値から期待メッセージ全文を組み立て、`str(excinfo.value) == expected` にする。

[8] nit | 対象 [test_s1_direct_comparison.py:228](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_direct_comparison.py:228) | fake `quarantine` は production と違って `marker_id/source_rel/write` を keyword-only・必須にしている。production では positional 可かつ default 有りなので、`write=True` を省く等の等価 refactorが偽赤になる。戻り値4要素と現在の呼出し境界は一致しており、monkeypatch自体は `prepare_cell→quarantine` の検査を迂回していない。 | **成果物・受理集合は変わらないが、正当な呼出し変更をテストだけが拒否する。** | 実 signature と同じ default を持たせるか `autospec` を使う。

[9] nit | 対象 [s1_expected_goldens.py:432](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/s1_expected_goldens.py:432), [s1_expected_goldens.py:464](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/s1_expected_goldens.py:464) | `ident_all` predicate と source list 順序は静的には exact assert があり落ちるが、提示 matrix には対応変異がない。 | **現時点で成果物が変わる穴は確認できないが、両 assert の load-bearing 性は実測されていない。** | ident_all predicate 差替えと source record swap を matrix に追加する。

確認できた点:

- golden の全登録 semantic 値・source layout・campaign 20 path/hash は canonical と一致し、転記ミスなし。
- fresh doc 化した2改竄と generator/head/pin の3 negative controlは、検査順上それぞれ意図した単一理由まで到達する。
- `conftest.py` と独立 node golden は、追加4 known-axes node＋fixture利用10 measurement nodeで過不足なし。除外3 nodeのコメントも正確。
- function fixtureの現行テスト間では、fresh JSON fileと明示 deepcopyにより cross-test汚染は起きない。

判定: **NO-GO**
---

## 段6 敵対レビュー 2 — 整合・保守性 (逐語、NO-GO)

静的監査結果は **NO-GO**。受入全走が緑でも、外部固定 golden 自体に恒真化できる穴が残っている。

[1] must-fix | [s1_expected_goldens.py:376](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/s1_expected_goldens.py:376) | source record は完全な外部固定ではない。63 record 中、campaign 由来27箇所だけが hash pin され、残る36箇所・11 source path は64hex形状しか見ない。さらに `lines` 6箇所は「存在」しか検査しない。これは D81/worklog が要求した `(path/sha256/key/lines)` exact 化を満たさない。 | **放置すると: 11 source の変更に追随して36個の `sha256` と6個の `lines` が変わっても、live build→自己再構成→golden が緑のまま受理する。** | 推奨対処: 残る11 path の hash と全 `lines` literal を固定し、source record 全体を exact 比較する。pin 集合と layout 参照集合の完全一致も検査する。

[2] must-fix | [s1_expected_goldens.py:416](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/s1_expected_goldens.py:416) | 「完全一致」という docstring に反し、configuration record の exact key-set がない。特に `EXPECTED_SORT` は canonical に存在しない `reference_fitness_tps=None` と read-heavy の `remeasure_reference=None` を持ち、453–454行の `.get()` が absent と explicit null を同一視する。また通常の `==` は14個の `.0` fitness 値について `float` と `int` を区別しない。 | **放置すると: sort への明示 `null`・任意の追加キー・fitness の float→int が18 measurement cellへ伝播しても受理集合は変わらず緑になる。** | 推奨対処: workload/configuration 別の exact key-set、ABSENT の明示表現、数値の `type(...) is float` 検査を追加する。

[3] must-fix | [s1_expected_goldens.py:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/s1_expected_goldens.py:26) / [同:161](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/s1_expected_goldens.py:161) | `EXPECTED_TRIGGER_FLAGS` と `EXPECTED_GATES[*].flags` が同値を重複保持する一方、実検査は429行で前者しか使わない。後者の `flags` は dead literal である。 | **放置すると: `EXPECTED_GATES` が WAL=1、実際の受理値が WAL=0という矛盾した参照台帳を作っても全テストが通る。** | 推奨対処: `EXPECTED_GATES` から `flags` を削除して単一正本化するか、各 workload の flags を直接消費し、共通値との一致も検査する。

[4] must-fix | [s1_expected_goldens.py:2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/s1_expected_goldens.py:2) | docstring が引用する `D82` は現 HEAD に存在しない。`docs/decisions.md` の最新は D81で、対応する継続-wave insight/変異台帳もこの差分にはない。更新契約が初回導入時点から履行不能である。 | **放置すると: `D82` と変異台帳が dangling reference となり、現在値の採択根拠も将来の正当な rebaseline も追跡できない。** | 推奨対処: D82・逐語/変異台帳・worklog 索引を同じ受入単位へ追加するか、実在する裁定正本へ参照を訂正する。

[5] must-fix | [s1_expected_goldens.py:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/s1_expected_goldens.py:4) | 「production から import 禁止」はコメントだけで、production import を拒否する検査がない。外部 oracle の独立性という中核契約が宣言止まりである。 | **放置すると: producer がこの台帳を importして18構成を組み立てても検出されず、producerと期待値の同時変更を全受理する恒真 oracleへ戻る。** | 推奨対処: production tree の AST import guard と、この helper 自身が production/canonical JSONを import・読込しないことの guard を追加する。

[6] must-fix | [test_s1_direct_comparison.py:254](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_direct_comparison.py:254) | 3つの「verbatim」テストは、SUT実行後に同じ可変 `cell` から期待値を読み直す。producer が `variant["comparator"]` や `gate_predicate` をin-place正規化すれば、captured値と期待値が一緒に変わり偽緑になる。加えて comparator は synthetic、system gate は g_rl 相当だけで、sp_dd/sk_ad/g_rt literalとの結線もない。 | **放置すると: freeze記録値と実際に quarantine へ渡すコードが異なっても、入力dictを書き換える実装なら3テストすべて通る。** | 推奨対処: 呼出し前の immutable literal/deepcopy と比較し、入力不変もassertする。現在の空白sentinelに加え、全 canonical comparator/predicateをparameterizeする。

[7] must-fix | [test_s1_known_axes_freeze.py:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:14) / [同:214](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:214) | `_run()` を「pytest非依存」と説明するが、module import時にpytestを無条件importし、negative testsも `pytest.raises` に依存する。また local helper import前に `_HERE` を明示追加しておらず、measurement側のbootstrapと不一致である。 | **放置すると: pytest不在環境では11テストが `_run()` 到達前に0件実行で落ち、tests dirをprependしないimportlib loaderではcollection自体が失敗する。** | 推奨対処: stdlib fallbackのraises helperを用意し、`_HERE` bootstrapまたは統一したpackage importへ揃える。

[8] nit | [test_s1_known_axes_freeze.py:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:33) / [test_s1_measurement_freeze.py:29](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:29) | submodule init/skip判定が逐語複製され、positive controlはknown-axes側のコピーしか攻撃しない。 | **放置すると: measurement側だけfile-based skipへ退行した場合、対象ファイル単独実行では本来FAILすべき10 nodeがSKIPへ変わる。** | 推奨対処: test-local共通helperへ集約し、その一つのguardをpositive controlで固定する。

静的に反証できなかった点は以下。

- `conftest` と独立 golden は42 nodeで完全一致し、全関数名も実在する。S-1は19 nodeだが、今回の純増は19ではなく14（既存known-axes 5 + 追加4 + measurement 10）。
- measurement fixture消費10 nodeはすべて `real-repo` group、非消費3 nodeは除外されている。`--dist loadgroup` なら同一workerへ集約され、既存oracle/writerとも直列になる。
- 同名テスト関数は `module::function` 形式なので衝突しない。
- `measurement` と `direct_comparison` はREADME上のpytest専用allowlistで、素のrunner対象ではない。`direct_comparison._run(...)` はsuite runnerではなくテスト用helperである。
- 62.21s対64.04sは「この1回では退行を観測しなかった」とは言えるが、同等性の証拠ではない。しかもmodule fixture共有後も各 `M.build_document/verify` がknown-axesを再検証する。性能主張には反復値またはreal-repo groupのdurationが要る。

**NO-GO**
---

## 段6 fix 単位 完了報告 f1

実装完了しました。[test_s1_known_axes_freeze.py](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/wt-f1/orchestrator/tests/test_s1_known_axes_freeze.py) のみ変更しています。

- 3つの negative control に改竄値の message assert を追加
- `test_goldens_helper_is_independent_of_production` を新設
- `_HERE` の `sys.path` bootstrap を追加
- 独立性 guard は submodule 非依存のため real-repo group 追加不要
- 所有外ファイルへの変更なし、commit なし

実走結果:

- `tools/run_tests.py ...`: 12 passed
- 素の runner: 12 passed, 0 failed, 0 skipped
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- 期待赤: ゼロ
---

## 段6 fix 単位 完了報告 f2

must-fix 3件を [test_s1_measurement_freeze.py](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/wt-f2/orchestrator/tests/test_s1_measurement_freeze.py:44) に反映しました。

- comparisons、master seed、schedule hash を外部 golden で固定
- cells variant 射影を型厳密な再帰比較へ変更
- 実 ccbench HEAD の40桁 SHAと `pin.CURRENT_PIN` を結線
- 所有外ファイルへの変更なし
- テスト node 名の変更なし
- git commit なし

実走結果:

- 指定テスト2本: `24 passed`
- skip / xfail / failure（期待赤）: 0
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- `git diff --check`: 通過
---

## 段6 fix 単位 完了報告 f3

実装完了しました。変更は [test_s1_direct_comparison.py](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t066w2/wt-f3/orchestrator/tests/test_s1_direct_comparison.py) のみです。

- SUT 実行前に `copy.deepcopy(cell)` で期待値を固定
- captured implementation を snapshot 側と逐語比較
- 実行後に `cell == expected` で入力非破壊を検査
- synthetic sentinel に加え、golden 台帳から canonical 5ケースを追加
- 実 ccbench 関連処理は引き続き全て monkeypatch で遮断

検証結果:

- 指定テスト全体: `32 passed`、失敗・skip・xfail（期待赤）すべてゼロ
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `git diff --check`: 問題なし

real-repo group 登録は不要です。新しい parameterize node も `tmp_path` の隔離領域だけを使い、checkout・patch apply・source digest・quarantine はすべて fake 化され、実 repo／共有 submoduleを読み書きしないためです。commit は作成していません。
---

## 段6 焦点再レビュー (逐語、GO)

pytest は実行せず、指定差分・production consumer・canonical JSON を静的照合した。golden は canonical と一致し、xdist 台帳も 42 対 42 で一致している。主要な根拠は [golden helper](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/s1_expected_goldens.py:478)、[measurement consumer](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:111)、[known-axes tests](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:52)、[direct consumer tests](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_direct_comparison.py:229)。

## 1. 所見ごとの対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| RC1 | `closed` | 12 comparisons の全 field・key-set・list 順序を外部 literal と `assert_json_exact` で完全照合しており、旧件数検査だけの偽緑は閉じた。 |
| RC2 | `closed` | `EXPECTED_MASTER_SEED` と full schedule を束縛する `EXPECTED_SCHEDULE_HASH` が literal 固定され、生成結果へ直接 assert される。 |
| RC3 | `closed` | 再帰比較は `type(...) is type(...)`、18 entry の exact key-set、`_ABSENT` による欠落検査を備え、bool/int/float と None/欠落の混同を排除した。 |
| RC4 | `closed` | external 2 path の `lines` が行番号・内容・順序込み literal となり、layout の `has_lines` 集合とも相互一致する。 |
| RC5 | `partial` | fixture は full 40-hex pin と `pin.CURRENT_PIN` prefix を結線したが、K の production verifier 自体は依然「現在の submodule HEAD」としか比較しない。 |
| RC6 | `disputed` | 未 init 時の10 node skip は残存するが、可視 skip を許す既存方針として親が blocking 性を否認し、裁定パッケージへ送っている。 |
| RC7 | `closed` | 3負例とも拒否分岐固有の文言と注入値を同時検査するため、別理由による偽赤は閉じた；揮発する actual hash の固定は不要。 |
| RC8 | `disputed` | fake quarantine の厳密 signature は未変更だが、正しさ穴ではなく refactor 感度の nit という裁定で、新規回帰もない。 |
| RC9 | `closed` | ident predicate は literal 完全一致、source は `(path,key,lines有無)` の順序付き tuple と一致し、MU-J/MU-K の kill 帰属もコードと整合する。 |
| RN1 | `partial` | campaign 成果物20 path と source lines は pin 済みだが、裁定どおり編集可能11 path の hash は64hex形状検査に留まる。 |
| RN2 | `closed` | RC3 と同じ型厳密・exact key-set・欠落検査が全 workload×configuration に適用される。 |
| RN3 | `closed` | `EXPECTED_GATES[wl]["flags"]` は実 consumer に使われ、trigger flags・campaign pin集合・lines集合にも import 時の閉包検査がある。 |
| RN4 | `partial` | 現 HEAD の `docs/decisions.md` は D81 が末尾で D82 は不存在；[handoff](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-23-t066-golden-continuation.md:53) どおり段7記録待ち。 |
| RN5 | `closed` | helper の import は `__future__` のみに制限され、`campaign/*.py` から test-local 台帳への参照も走査・拒否する。 |
| RN6 | `closed` | 呼出前 deepcopy、quarantine 受領値との比較、入力非破壊検査に加え、canonical comparator/predicate 5対応を通し、in-place 正規化の偽緑を閉じた。 |
| RN7 | `partial` | tests directory の bootstrap は追加されたが、standalone runner の pytest import 依存は既存どおり残る。 |
| RN8 | `disputed` | skip 判定の逐語複製は未変更だが、既存 nit として据え置かれ、今回の変更による悪化はない。 |

`regressed` は0件。11変異全 kill の解釈も妥当だが、これは initialized-submodule 経路の証拠であり、RC6 の fresh-clone 残余まで閉じた証拠ではない。

## 2. 新規 must-fix

なし。RN4 は新規所見ではなく、既知の段7完了条件である。

## 3. 判定

fix ラウンドから段7記録へ進む判定として **GO**。ただし wave 完了を宣言できるのは、D82・insight/worklog・変異台帳を記録 commit で実在化し、予定された repo-scan invariant を再確認した後。