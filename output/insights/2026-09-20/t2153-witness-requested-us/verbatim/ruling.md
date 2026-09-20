# 段 4 裁定 — [T-2153] 残件 (c): `BACKOFF_REQUESTED_US` の 4 箇所同時観測

- 日付: 2026-09-20 19:40 JST。入力 = brief (P1〜P8)、段 2 plan (12 call)、段 3 consult A (正しさ境界、9 call) / B (過剰・削除・pin、18 call)。
- wave tip は main `800178b39` へ ff 済み (docs + `tools/dev_wave_land.py` のみ、編集面は不変)。author 子木 `t2153-rus-author` は `482f19b88` base (所有 2 file は同一 bytes)。

## 1. 所見の裁定 (real / refuted、採否)

| # | 所見 | 判定 | 採否・扱い |
|---|---|---|---|
| plan-P6 / A3 / B5 | 総数一致だけでは「owner 2 箇所を外側 `#if 0` で殺し、pragma once 無しの header を 2 回展開」で (4,4)/(0,4) が相殺成立 | **real** | **採用 (must-fix)**: 複数 file macro に限り、宣言した各箇所に固有の識別 marker を足し、箇所ごとに要求 (1,1) / 対照 (0,1) を要求する。生死実験 (`probe-site-token.out.txt`、g++ 11) で `-D'…SITE_SELECTED(k)=…_OBSERVED_##k'` が展開後 token を 1 行ずつ出し、コメント・raw string 内は展開されないことを確認済み (D1490 の流儀を保つ)。単 file macro (既存 21) の計装・argv・record は変えない (.cc の TU は再展開されず、header 単 file は N=1 で重複が総数に出るので総数で足りる) |
| A1 | 個別観測が evidence に無く再検証できない | **real** | **採用 (must-fix)**: 複数 file macro の green evidence に `site_observations` (全宣言箇所 × 両腕の個別観測) を載せ、再検証は登録簿から箇所集合を導出して照合する |
| A2 / B7-変異 | m3 の帰属: 個別検査導入後は「未 include を通す欠陥」の単独検出にならない | **real** | **採用**: m3 は「正しい 4 箇所入力の過剰拒否」として登録し直す (§3) |
| A4 | 副 file の証拠は owner TU + 当該 configure の include 文脈に限る旨を明記 | **real** | **採用**: docstring と insight に 1 文 |
| A5 / A6 | 副 mapping が factory・旧経路を広げる / 2 file 計装で argv 比較・supply closure が壊れる | refuted | 記録のみ。ただし A6 の条件「全計装 file を symlink 対象から除く (元 header への書き込み禁止)」は実装条件 (§2 (c)) |
| A7 / B3 | I1「21 macro 不変」を 2 cell で実証したことにしない | **real** | **採用**: 実 TU 比較は SORT (N=1 浅い鏡像) / RUNG1 (N=2 浅い鏡像、`_declared_site_count` 経路) / NOINLINE (N=1 深い鏡像) の 3 cell に限って主張し、他 18 は key/field pin と同一 code path の回帰 test で担保と書く。全 21 の bytes 同一は主張しない |
| B1 | fixture の CMake mapping 欠落 (`condition_gate_test_support.py` の固定 `_OPTIONS` に REQUESTED_US が無い → `macro-not-supplied`) | **real** | **採用 (must-fix)**: REQUESTED_US の fixture 分岐で installer 呼出し後に `CCBENCH_BACKOFF_REQUESTED_US` の既定 0 と TU mapping を局所追加 (共通 installer は変えない) |
| B2 | NOINLINE 特例 assert は緩めない、patch 束縛は header×2 + owner×2 を独立完全列挙 | real (nit) | **採用** |
| B3-P3 | reason は既存 `compile-time-branch-site-count-mismatch` を再利用、file 名は detail、expected/observed は数値文字列のまま | real (nit) | **採用** (plan の `path:2` 形は不採用) |
| B4 | 全 21 件の serialization 固定期待 test と「shadow 後に header を戻す注入 test」は削れる | real (nit) | **採用** (DW-G05: 削っても成果物不変)。既存 field pin に `CompileTimeBranchSelectionEvidence` を足すだけ |
| B6 | brief の記録訂正: 「pin 閉包 0 件」は bytes pin に限る (契約 pin あり)、B-4 現行は 49、t316 probe は FIXED gate を実呼出し | real (nit) | **採用 (記録訂正)**。実装への影響なし |
| B7 | 研究前進は CLI の観測証拠に限定して書く | real | **採用** (worklog / insight の書き方) |
| B-変異 | m6 (登録簿 entry 削除) は最小 matrix から削れる | nit | **不採用**: 前 wave と同型の正例として残す (安価、多 node 帰属は台帳で分ける) |

## 2. plan v2 (author への確定仕様)

所有 path (単位 1、1 author): `orchestrator/campaign/condition_meaning_gate.py`、`orchestrator/tests/test_condition_meaning_gate.py`。他 file は編集しない (fixture dir・installer・patch・driver・MOCC/S1 consumer・spawn 目録・B-4 目録)。

(a) **宣言**: `_CONDITIONAL_BRANCH_WITNESSES` 末尾に `"BACKOFF_REQUESTED_US": ("cc/silo/transaction.cc", "#if BACKOFF_REQUESTED_US")`、`_CONDITIONAL_BRANCH_SITE_COUNTS` に `"BACKOFF_REQUESTED_US": 2`、新 mapping `_CONDITIONAL_BRANCH_COMPANION_SITES = {"BACKOFF_REQUESTED_US": (("include/backoff.hh", "#if BACKOFF_REQUESTED_US", 2),)}`。`_declared_site_count(macro)` = **主宣言 file の N** (意味不変)、新 `_declared_total_site_count(macro)` = 主 N + 副 N の和 (REQUESTED_US = 4)。既存 21 entry の値・順序・2-tuple・`DefineSpec`・factory 条件・旧宣言経路 (BACKOFF_FIXED 固定) は不変。副 file を `ConditionalBranchMeaningDeclaration` にしない。

(b) **計装**: 主 + 副を `_capture_compile_time_branch_source` で各々 no-follow capture し、file ごとに `_instrument_declared_owner_source` (対象 file を選ぶ keyword 追加、既存 2 引数呼出し互換) で N_i 箇所を計装。file ごとの箇所数不一致は既存 reason `compile-time-branch-site-count-mismatch` (detail に file 名、expected/observed は数値文字列)。N=1 の既存 reason 逐語は不変。**複数 file macro に限り**、各箇所に総数 marker (`SELECTED()` / `COMPLETED()`) に加えて箇所固有 marker `IZANAGI_COMPILE_TIME_BRANCH_SITE_SELECTED(<k>)` / `…_SITE_COMPLETED(<k>)` を同位置に挿入 (`<k>` = `f<file_index>s<site_index>`、file 順 = 主・副の登録順)。preprocess argv に `-D…SITE_SELECTED(k)=…SITE_SELECTED_OBSERVED_##k` / `…SITE_COMPLETED(k)=…SITE_COMPLETED_OBSERVED_##k` の 2 本を複数 file macro のときだけ足す (単 file macro の argv は不変)。source 内に site marker / output token が既に在れば既存の collision reason で拒否。

(c) **shadow**: `_write_shadow_owner_source` を `{source_rel: instrumented_text}` の mapping (keyword、既定は主 1 file) で全 file を書く形へ。浅い鏡像は「主 == owner TU かつ副なし」に限り、副があれば深い鏡像 (D1613)。**全計装 file を symlink 作成対象から除外** (symlink 越しの `write_text` で元 source を書き換えない)。返り値は owner TU の shadow path。

(d) **判定 (順序固定)**: (1) 従来どおり総数 (`_declared_total_site_count` を期待式の N に使用): 非識別 → `…-not-discriminating`、不一致 → `…-selection-mismatch`。(2) 複数 file macro だけ、箇所ごとの個別観測が要求 (1,1) / 対照 (0,1) と完全一致しなければ新 reason `compile-time-branch-site-observation-mismatch` (expected / observed に箇所 key と数)。個別観測の和が総数と一致しない場合も (2) で拒否。

(e) **evidence (複数 file macro の green だけ)**: 既存 key に加え `companion_sources` (登録順 tuple、各 row = `source_rel` / `start_directive` / `site_count` / `source_sha256` / `source_file` (`CapturedFileEvidence`、計装に使った capture そのもの)) と `site_observations` (全宣言箇所の tuple、各 row = `source_rel` / `site_index` / `requested_selected` / `requested_completed` / `default_selected` / `default_completed`) の 2 key。`_assert_compile_time_branch_selection` の返り値は (既存 evidence, 副 payload) の対にし evaluator で unpack。既存 dataclass に field を足さない、`proof_kind` 不変、単 file macro の evidence dict は 1 byte も変えない。

(f) **green 再検証** (`_validate_meaning_green_evidence`): 副宣言の有無は `record.macro` から登録簿で決める (record の key から決めない)。副宣言ありなら 2 key 必須、なしなら unexpected。row の型・key 集合・順序・登録値 (`source_rel` / `start_directive` / `site_count` は exact、bool 拒否)・`source_file` の type / relative_path / sha256 / identity 等値を現行主 source と同じ強さで検査。`site_observations` は登録簿から導いた (file, index) 集合と完全一致し、各 row が (v,1)/(0,1)、和が総数と一致、両腕 argv に site marker の 2 define が在ることを検査。総数は record の申告でなく登録簿から導出。

(g) **主張範囲** (docstring + insight): "Twenty-one" → "Twenty-two"。追記 1 文: 複数 file witness の副 file の証拠は「宣言した owner TU と当該 configure の include 文脈」に限り、同 header を include する他 TU (ycsb_silo.cc 等) の枝選択は主張しない。4 箇所の活性は configure に依存し (abort() 内は `#if BACK_OFF`)、BACK_OFF=0 では completed 3/4 で red (fail-closed)、BACK_OFF を companion にしない。

(h) **test** (`test_condition_meaning_gate.py`): 独立期待表 (主 `cc/silo/transaction.cc` / `#if BACKOFF_REQUESTED_US` / 2、副 `include/backoff.hh` / 同 / 2、対照 0) を literal で持つ。fixture は `_compile_time_source_root` の REQUESTED_US 分岐 (NOINLINE 特例 assert より前、登録簿参照より前で KeyError を避ける): owner TU (2 箇所 + 両腕に無条件本文) → 中継 `cc/silo/include/transaction.hh` → `../../../include/backoff.hh` (`#pragma once`、2 箇所 + 両腕本文)、installer 呼出し後に `CCBENCH_BACKOFF_REQUESTED_US` の cache 既定 0 と TU mapping を局所追加 (B1)。node (予定名、最小集合): 正例 `test_requested_us_multifile_supply_meaning_and_admission` ((4,4)/(0,4)、admitted、未確立 []、副証拠が header の capture と一致、site_observations 4 row)、`…include_counts[pragma-once]` (pragma once 付き 2 回 include → green)、宣言数 `…site_count_mismatch[owner]` / `[header-verbatim]` (header 1 行を `#if (BACKOFF_REQUESTED_US)` に)、観測 `…include_counts[missing]` (2/4) / `[twice]` (pragma once 無し 2 回 → 6/4)、configure `…owner_site_inactive` (owner 1 箇所を `#if 0` で殺す → 3/4)、相殺 `…rejects_compensated_missing_sites` (owner 2 箇所 `#if 0` + pragma once 無し header 2 回 include → 総数 4 でも `site-observation-mismatch`、**`_assert_compile_time_branch_selection` を直接呼ぶ独立 node**)、shadow `…shadow_instruments_all_files` (全計装 path が通常 file、中継 dir が実体、元 owner/header の bytes 不変)、schema `…green_schema[mutation]` (副 key 欠落 / 空 tuple / 重複 row / 誤 path・directive・N・digest・identity / row 余分 key / site row の数値改変 / site marker define 欠落、`require_issuer=False` で再構成)、`test_single_file_green_schema_rejects_companion_sources` (SORT の green に空の副 key → unexpected)、CLI `…cli_establishes_multifile_meaning` (`condition_gate_cli` 直接呼出し、subprocess を足さない)。patch 束縛 `_patch_added_branch_declaration` は REQUESTED_US だけ header pair×2 + owner pair×2 の独立完全列挙 (他 macro の `[pair]*count` は維持)。集合 pin (`_COMPILE_TIME_BRANCH_MACROS` 末尾追加 → 22、`test_v1_domain…` 23)、docstring pin (`Twenty-two`)、非対値 parametrize に REQUESTED_US 追加、旧 CLI 経路拒否に REQUESTED_US 追加、既存 field pin に `CompileTimeBranchSelectionEvidence` を追加。未登録例は SS2PL_LOCK_IMPL のまま。全 21 件 serialization 固定期待 test と header 戻し注入 test は作らない。

(i) **不変**: `_run_process` spawn site 1、新 module なし、`DEFINE_SPECS` 不変、D1491 の 5 箇所不変、S1 helper は主 N のまま (複数 file 対応済みとは主張しない)。

## 3. 変異事前登録 (DW-M01、実装後に単一理由性を確認して spec 化)

runner = `tools/mutation_worktree.py` (独立 clone、固定 commit、dispatch)、test 集合 = `test_condition_meaning_gate.py test_s1_direct_comparison.py` (+ consumer 3 mocc file は焦点走で別途)。probe 走 → final 走 (期待 node 完全一致)。

| id | 変異 (G の置換) | 期待 | 帰属 |
|---|---|---|---|
| m0 | 副 mapping の行末に comment | SURVIVED (等価) | — |
| m1 | 副 mapping の header N 2 → 1 | KILLED | 独立期待表 / patch 束縛 / 正例 (fixture は 2 箇所) |
| m2 | shadow の mapping 書出しで副 file を計装本文でなく**元本文**にする (file は消さない) | KILLED | 正例 (completed 2/4)、shadow 検査 |
| m3 | 期待式の `_declared_total_site_count` → `_declared_site_count` | KILLED | **正しい 4 箇所入力の過剰拒否** (期待 2 に対し観測 4)。「未 include を通す欠陥」の検出とは数えない |
| m4′ | 個別観測の等値検査 (d)(2) を無効化 | KILLED | 相殺入力の独立 node (`_assert…` 直接呼出し) = 一次防壁。公開 evaluator では schema が二次拒否しうるので成果はそこで数えない |
| m5 | 副検証 (f) の適用条件を登録簿でなく `"companion_sources" in evidence` にする | KILLED | schema test [missing] (副 key を落とした green record が通る) |
| m6 | 登録簿の REQUESTED_US 主 entry 削除 | KILLED (多 node) | factory None / unestablished、集合 pin、patch 束縛 (fixture は独立期待から作り KeyError にしない) |
| m7 | 副検証の `source_file.sha256 != row["source_sha256"]` 項だけ除去 | KILLED | schema test [digest] (形式正しい別 digest を片側だけ) |
| m8 (過剰拒否の正例) | 副 key の挿入条件を無条件にする (単 file macro にも出す) | KILLED | 単 file macro の正例が `_issue_arm_record` の schema で先に落ちる (bytes 比較到達前)。検出箇所をそのまま書く |

## 4. 実 TU 実測の完了条件 (P8、変更なし)

最終 production 登録簿の CLI を `ccbench-e9e477c-requested-us` (fixed → requested-us) で login (pegasus02) と計算ノードで実走: REQUESTED_US 1v0 = supply green / meaning green **(4,4)/(0,4)** / admitted / 未確立 []、site_observations 4 row (v,1)/(0,1)。加えて BACK_OFF=0 cell (`--configure-arg=-DCCBENCH_BACK_OFF=0`) で completed 3/4 の red を 1 cell。I1 = SORT / RUNG1 / NOINLINE の変更前後 leaf 比較 (一時 path とその派生 digest のみ差、key 集合・前処理 digest・bytes・owner TU sha・closure digest・counts・reason・proof_kind 同一)。login-pre に RUNG1 cell を追加取得する (変更前)。

## 5. 記録訂正 (brief の不正確)

- 「pin 閉包 0 件」→「bytes pin は 0 件、契約 pin (集合・順序・schema・docstring・spawn 目録) はあり」。
- B-4 static inventory の現行件数は 49 (`test_p3_b4_wiring_probe.py:329`)。
- `t316_sandbox_backend_probe.py` は FIXED の gate を実呼出しする (要求不変なので追随不要)。
