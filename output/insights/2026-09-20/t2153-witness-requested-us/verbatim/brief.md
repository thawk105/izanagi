# 段 1 brief — [T-2153] 残件 (c): `BACKOFF_REQUESTED_US` の 4 箇所同時観測 (transaction.cc 2 + backoff.hh 2)

- 日付: 2026-09-20 19:15 JST、起点 local main `482f19b88` (fresh worktree `worktree-dev-wave-t2153-witness-requested-us`、開始 gate rc=0 `startup-gate.log`)
- ccbench pin: `e9e477ca1` (前 wave t2153-witness-bc の `511c953` から T-2304 で前進)。本 wave の実 TU 実測はすべて現行 pin で取り直す

## 研究前進 (1 行)

論文の方法節 / proof chain の主張「登録 macro の define は所有 TU の宣言箇所すべてで枝選択を決める」(D1490 / D2182) を、silo backoff 診断族で最後に未確立の `BACKOFF_REQUESTED_US` (T-1941 の requested-us 計数、B-10 静的 6 点の `requested_us = realized_us` 材料が依存する診断 define) にも成立させる。完了判定 = 最終 production 登録簿の CLI を実 patch 木 + official 同形供給で login と計算ノードの実 TU に実走し **(4,4)/(0,4) green・admitted・未確立 []**、変異 matrix (正例 + 負例) の期待 node 完全一致、受入全走緑、land。数値成果物は変わらない (driver `backoff_requested_us` は gate の返り値を捨てる = D1492 により配線しない)。

## 前提実測 (段 1、覆す新事実なし)

- 静的 (`nest.out.txt`、現行 pin + fixed → requested-us の重ね順 = driver と同じ): `#if BACKOFF_REQUESTED_US` の逐語は **transaction.cc L11 (top) / L157 (`#if BACK_OFF` 内) + include/backoff.hh L109 (top) / L141 (top) = 4 箇所**、他 file に無い (Options.cmake は cache mapping のみ)。header は `cc/silo/include/transaction.hh:9` → `../../../include/backoff.hh`、`#pragma once`。
- 現行 gate (main `482f19b88`、login pegasus02、`login-pre/`): REQUESTED_US 1 vs 0 = **supply green / meaning unestablished (`meaning-witness-undeclared`) / admitted、未確立 [REQUESTED_US]**。対照 SORT 1v0 / NOINLINE 1v0 (header 宣言の既存例、D1613 の深い鏡像) = green (1,1)/(0,1)。各 cell 5〜6 s。
- `CCBENCH_BACK_OFF` の CMake 既定は 1 → 既定供給で abort() 内の箇所も活性。BACK_OFF=0 の configure では completed 3/4 で red (fail-closed、下記 P5)。
- pin 閉包 (DW-O09、識別子 = 変更前 sha256、path key、output/ 全域): gate module の bytes を pin する台帳・凍結物は **0 件**。path key の hit は `test_ccbench_spawn_sites.py` (`_run_process` の spawn site 数 = 1 の目録 pin。subprocess 呼出しを足さなければ不変) と probe 2 本 (import のみ)。集合 pin は test 側の独立列挙 `_COMPILE_TIME_BRANCH_MACROS` (21) と `test_v1_domain_and_claim_boundaries_are_exact`、docstring の "Twenty-one" 逐語 pin。B-4 static inventory は module を足さないので不変。
- 編集面重複 (byte 一致版、claude 19 + codex 20 worktree): 6 file とも非 main hash は全て main の過去 blob・dirt なし → 稼働 wave との重複なし (`overlap-scan.log`)。

## scope (確定済みユーザー裁定 + 守る裁定)

- 実装: `orchestrator/campaign/condition_meaning_gate.py` に「1 macro に複数 file の箇所群を宣言し、同じ深い鏡像 shadow に全宣言 file を計装して owner TU を前処理する」拡張を足し、`BACKOFF_REQUESTED_US` を登録 (枝選択 21 → 22、対応集合 22 → 23)。test は `orchestrator/tests/test_condition_meaning_gate.py` を主とし、consumer test の pin 追随 (件数・列挙・docstring) を同じ commit に含める。
- Codex `role=author` (D95) が実装面を書く。親は実装面を編集しない。
- 守る裁定: D1490 (主張は所有 TU の枝選択まで)、D1491 (旧宣言経路は BACKOFF_FIXED 固定)、D1492 (配線は admission が成果物へ載る driver だけ → **本 wave は driver を配線しない**)、D1613 (header は深い鏡像で所有 TU の文脈で観測)、D2161 (実 TU 実測で登録、代表 1 本にしない)、D2182 (全箇所観測・主張は DefineSpec patch の逐語箇所)、規律 2 (受理集合は狭まる向きだけ)。
- 除外 (依頼): SS2PL 系 4 件 (T-2737 §7 待ち)、探索 loop 配線、offline 供給、admission 永続化、S2 再走、仮想リスク向け gate・検査・台帳・一般化。`patches/` は触らない (stock / template の pre-image は byte 一致)。`DefineSpec` / `DEFINE_SPECS` / CLI 引数は変えない。

## 不変条件 (受入で検査するもの)

- I1: 既存 21 macro の record (supply・meaning・admission) は変更前後で同一 (一時 path とその派生 digest を除く leaf 比較。SORT 1v0 / NOINLINE 1v0 を同 driver-id・同 configure で)。
- I2: 既存 dataclass (`ConditionalBranchMeaningDeclaration`、`CompileTimeBranchSelectionObservation`、`CompileTimeBranchSelectionEvidence`) に field を足さない (既定値でも canonical JSON へ出て既存 record の bytes が変わる、D2182)。既存 21 entry の 2-tuple・順序・reason/detail 逐語・record の key 集合は不変。
- I3: `_run_process` の spawn site は 1 のまま。新 module を足さない。
- I4: 受理集合は狭まる向きだけ: REQUESTED_US 1/0 は unestablished admit → green admit / red reject。他 macro に red / unestablished → green へ転じる入力を作らない。
- I5: 4 箇所すべてで要求 (4,4) / 対照 (0,4) を要求。file ごとの箇所数不一致・未計装 file・不活性箇所 (completed < 4) はすべて red。

## 割れうる前提 = 親の provisional 裁定・攻撃対象

- (P1) 登録簿の形: 主 entry は現行 2-tuple のまま `("cc/silo/transaction.cc", "#if BACKOFF_REQUESTED_US")` + `_CONDITIONAL_BRANCH_SITE_COUNTS` に 2。**副 file は別 mapping** (例 `_CONDITIONAL_BRANCH_COMPANION_SITES = {"BACKOFF_REQUESTED_US": (("include/backoff.hh", "#if BACKOFF_REQUESTED_US", 2),)}`)。総箇所 = 4 は導出する。2-tuple consumer 3 件 (mocc test) を壊さない。
- (P2) evidence: 複数 file macro の green record にだけ副 file の証拠 (source_rel・start_directive・site_count・source_sha256・`CapturedFileEvidence`) を 1 key (例 `companion_sources`) で足す。単 file macro の evidence dict は 1 byte も変えない。green 再検証の schema は「登録簿に副 file がある macro にだけその key を必須」とする (無い macro に出れば unexpected で invalid)。`proof_kind` は変えない。対案 = 別 proof_kind (段 2/3 で比較)。
- (P3) 箇所数不一致の reason: file ごとに `compile-time-branch-site-count-mismatch` (detail に file を含める、expected/observed は当該 file の値)。N=1 の従来 reason 逐語は不変。
- (P4) `_declared_site_count(macro)` の意味: **owner TU (主 entry) の箇所数のまま** (S1 fixture helper `test_s1_direct_comparison.py:719` の consumer を壊さない)。総箇所数は新 helper (例 `_declared_total_site_count`) で導出し、期待式 (N·v, N) の N は総箇所数にする。
- (P5) `BACK_OFF` を companion に**しない**。abort() 内の箇所は `#if BACK_OFF` の内側で CMake 既定 1 なら活性、0 なら completed 3/4 で red (fail-closed)。主張範囲に「4 箇所の活性は configure に依存し、gate はその configure で観測した事実を記録する」と明記。
- (P6) shadow: `_write_shadow_owner_source` を「{source_rel: instrumented_text} の mapping を全部書く」形へ拡張。主 file == owner TU でも副 file があれば深い鏡像 (D1613 形) を使う。副 file が owner TU から include されない場合は completed < 総数 で自然に red (専用検査は足さない)。
- (P7) 変異事前登録 (草案、段 4 で確定): m0 等価 (副 mapping 行末 comment) / m1 副 file の N 2 → 1 / m2 shadow が副 file を書かない (計装 header 不在 → completed 2/4) / m3 総箇所の期待式を主 file の N に戻す (2 で通る) / m4 副 file の箇所数検査を除去 / m5 green 再検証で `companion_sources` を要求しない / m6 登録簿の REQUESTED_US entry 削除 / m7 副 file の source_sha256 束縛を除去 / m8 (過剰拒否の正例) 単 file macro の evidence に `companion_sources` を常に出す → 既存 record の bytes 不変 test で殺す。
- (P8) 実 TU 実測: 現行 pin の patched 木 (`ccbench-e9e477c-requested-us`) で login (pegasus02) + 計算ノードの 2 環境。I1 用に SORT / NOINLINE の変更前 (login-pre 取得済み) と変更後を leaf 比較。

## 成果物の形

- 実装 commit (gate module + test、Codex author + fix、統合は親)、insight `output/insights/2026-09-20/t2153-witness-requested-us/README.md` (+ `verbatim/`)、decisions fragment (slug `witness-multifile-sites`)、worklog fragment、変異台帳 (probe + final)、CLI cell の stdout.jsonl (login-pre / login-after / stage6-compute)。

## 分割方針・環境

- 段 2 plan 1 本 (read-only、file:line)、段 3 consult 2 本 (A = 正しさ境界・schema・受理集合、B = 過剰・削除・pin・fixture の実効)、段 5 author 1 本 (単位 1 = gate module + 所有 test)、段 6 review 2 本 + fix、変異 matrix、受入全走、land。
- 焦点走・consumer 走は計算ノード dispatch (`tools/run_tests.py --force-dispatch`、login の bounded local は `/tmp/.git` で S1 が偽赤)。CLI cell は login (5〜6 s) と計算ノード。変異は `tools/mutation_worktree.py` の独立 clone + dispatch。
- DW-G05: 放置時の成果物影響 = certified-selection use-class の admission で REQUESTED_US が `unestablished_meaning_macros` に残り続ける (数値は変わらない)。must-fix の基準もこれで測る。

## 条件 dispatch の判定 (段 1 時点)

- DW-O08 (freeze 族): submodule 3 段初期化済み (木の中身で確認)。凍結 manifest / oracle gate / proof chain の bytes は触らない (pin 閉包 0 件)。
- DW-O09 / O10: 成立するが hit 0 件 → producer write-path の棚卸しは不要 (凍結 producer の出力 bytes は変わらない)。
- DW-O13 (gate 入力の実在、新述語 = 複数 file の箇所観測): 入力 = owner TU の前処理出力に現れる計装 marker。到達性の実測 = header 側の directive は NOINLINE cell (`ccbench-e9e477c-fixed`、backoff.hh L106) で (1,1)/(0,1)、TU 側は SORT cell で (1,1)/(0,1) → どちらの file の marker も現行機構で TU 前処理に到達する。4 箇所合計の到達は実装後の cell で測る (段 5/6、期待 (4,4)/(0,4))。
- DW-O11 (削除): なし。DW-O14 (monkeypatch): no-touch 対象なし。
