# 段 1 brief — dev-wave-t2724-t080-defer-active-v2 (2026-09-18 10:55 JST)

## 研究前進 (1 行)
土台。止めている研究 = 8b oracle 実走 (W-5、holdout rr20 / rr80 の certified 選択の再開)。実測 = X1' を含む木で焦点走 45 failed / 967 passed (G wave、request 5001.nqsv、07:10 JST) と runbook P3 `gate-check` rc=2 refusals 4 件 (`holdout-freeze-verify: [holdout.unknownness_layer2] … holdout hit 3 件`)。最小差分 = T-080 receipt の未知性層 2 (zero-hit) を承認済み active v2 の `launch_validate` (C2-4 完全一致) へ条件付き委譲 + 45 node の test の実 root 切り離し。完了判定 = (1) 境界 test が「active v2 + 同一 root/HEAD/世代で launch_validate 成功 → 層 2 委譲、他は従来拒否」を正例・負例で固定し緑、(2) chain 無し (本 branch) と chain 有り (G branch tip `229982652` を merge した scratch) の両木で 6 file の焦点走が 0 failed、(3) 変異 matrix で負例が捕まる、(4) chain の無い main へ land。

## scope (確定済みユーザー裁定: 裁定控え末尾「裁定」節 = 択 A・A-3 + T-2776 同梱、D2120 項 2 は撤回しない)
- A (production、A-3): `orchestrator/campaign/t080_freeze_migration.py` `verify_receipt` (:2284) の checks 列にある `holdout.unknownness_layer2` → `_verify_holdout_live_scan` (:2191)、同 `static_gate_adapter` (:2424 の independent 列 :2490) と、`orchestrator/campaign/s8b_oracle_driver.py` の `_resolve_t080_receipt` (:166) / `gate_check` (:587、v2 なら :656 で `launch_validate`) / `run_block` (:1280、:1338 で `launch_validate`、:1527 campaign-start 前の再解決と `_t080_epoch_identity` 比較) に、委譲 predicate を入れる。
- B (test、T-2776、4 経路 45 node): (i) `orchestrator/tests/test_s8b_oracle_driver.py` `_build_t080_stub_free_e2e_repo` (:1364) が `_copy_git_visible_output(ROOT, …)` (:1385) で実 root の output を複製 → official namespace (`output/env/pegasus/calibration/s8b-floor-official/`) と候補 exact path (`output/s8b-freeze-candidates/`) を外す (10 node)。(ii) `orchestrator/tests/test_s8b_floor_campaign.py` `_clone_committed_head_with_ccbench` (:2291、使用 :12103 と 5 node) の実 HEAD clone から同じ集合だけを外した起動可能 base + 「chain 有り tree の `clean_scan_digest` 拒否」負例 (official だけ / 候補だけ / 両方) を同 test file に追加。(iii) `_run` (:2951) の memo 経由の実 root receipt 解決 (29 node = conftest `RECEIPT_MEMO_CONSUMER_NODES` :712 と一致) を実 checkout に依存しない合成 resolution へ移し、登録簿 (conftest、`test_real_repo_serialization.py` `_RECEIPT_MEMO_CONSUMERS_GOLDEN` :503) を追随。(iv) `test_never_issued_generator_tamper_reaches_public_driver_gate_g7` の exact refusal 集合 (1 node)。
- C (docs): 新 D (spool fragment、D96)、`docs/phase3-8b-restart-runbook.md` §1.1 / §2 P3 を段階別 preflight (chain 無し main = 拒否 2 件 exact [実測済]、chain + G 発効前 = receipt 層 2 拒否 + v1 verify + floor/budget null の 4 件 [G wave 実測]、発効後 = 設計上の期待で未実測と明記) に改める。
- 変更単位は 1 wave、Codex author (D95)、境界 test + 変異 matrix + preflight 文書を同梱 (D96)。

## 不変条件 (0 byte / 意味不変)
走査除外集合 (`EXCLUDED_PATHS`、`exempt_exact` の導出 `_active_chain_exempt_exact` / `_selector_evidence_exempt_exact`)、growth hold 登録簿 (`orchestrator/tests/growth_test_holds.py`、45 node を hold に足さない、DW-O18)、chain と G の bytes と履歴、A / X の人間手番 (AI は作らない)、`never-issued` / `active-valid` / `issued-but-missing` / `invalid` の意味、receipt の履歴・静的検証 (artifact bytes / closure / derivation / ccbench gitlink)・epoch 束縛 (`_t080_epoch_identity`)、`_make_gate_decision` の無条件集約、`_campaign_t080_value` の invalid 拒否、`clean_scan_digest` (D2077 step 7: official 成果物を持つ checkout では official 床値を起動できない)、`launch_validate` の C2-4 完全一致とその他の層、既存 test の期待値 (緩めない)、`FROZEN_MANIFEST` 等の凍結 bytes (DW-O09: 変更 source の sha256 は output/ で live pin されていない — hit は歴史記録 `output/insights/2026-09-09/t2344-closure-reachability/trace-freeze.json` のみ、test 参照 0)。

## 親の provisional 裁定 (攻撃対象)
- (P1) 委譲の発火条件は「`type(launch_validated) is s8b_ratified_freeze.LaunchValidatedFreeze` ∧ `launch_validated.activation_head == _capture_head(root)` ∧ `launch_validated.search_digest == s8b_ratified_freeze._enumeration_digest(root)` (同一 root の列挙集合) ∧ その validated が同じ root の `load_ratified_freeze(root)` 由来 (同一世代)」の全部。1 つでも欠ければ従来どおり `_assert_search_pass` (zero-hit)。委譲時も凍結 doc と live report の束縛 (rr80/rr20 集合・`match_convention`・`candidate_id`・`expressions`) は維持し、zero-hit 判定だけを C2-4 に委ねる。skip flag・env・引数による無条件免除は作らない。
- (P2) 委譲時に live report をどう得るか (自前で `search_repository(root)` を再走して束縛検査だけ行う / `LaunchValidatedFreeze` に report を載せる) は plan が費用と型の波及で決める。型 field の追加は `ReverifiedFreeze` 等の兄弟型と consumer に波及するので既定は再走。
- (P3) driver の呼出し順: receipt の静的解決は現状どおり最初に行い、v2 の `launch_validate` 成功後に委譲付きで再解決した resolution を以後 (`_gate_check_validated` / `_campaign_t080_value` / campaign-start 前の epoch 比較) に使う。`launch_validate` 失敗・未発効 (`load_ratified_freeze` 失敗) は委譲なしの resolution を集約 (従来どおり拒否)。
- (P4) (iii) は `_run_with_real_manifest_gate` (:2989) と同型に `_resolve_t080_receipt` を合成 resolution へ patch し、memo consumer 登録簿から外す。解決回数・epoch drift を検査する opt-out 2 node は現状維持。
- (P5) chain 有り木の焦点走は、本 wave branch に `229982652` を固定 SHA で merge した scratch branch (land しない、X1' + G を含む) の worktree で行う。A / X は無いので「未発効 + hit → 拒否」の負例が実木で成立し、「active v2 + 委譲」の正例は git fixture (test_s8b_ratified_freeze の A / X 合成) でだけ到達可能 (DW-O13: production では到達不能、A / X は人間手番)。

## 成果物影響 (DW-G05)
放置時: chain + G を main に載せられず (受入 45 赤で land 不能)、載せても X1' 木で oracle gate が refuse → W-5 (8b oracle 実走) と certified 選択の再開が止まる。本 wave は certified 選択・レポート・台帳の値を変えない (受理集合は「active v2 の full validation を通った木で receipt 層 2 の重複判定を委譲」の 1 形だけ広がり、他は不変)。

## 既存被覆 (純増だけ)
- D2120 項 2 (a)(b)(d)、D2077 step 7、D96、D95、G wave fragment `t080-receipt-defers-unknownness-to-active-v2` (未 land、`229982652`) が裁定・順序を持つ。本 wave の新 D は実装形 (predicate の署名・負例・到達範囲) を持ち、G wave fragment の slug は `{{D:}}` 参照しない (fold 順が逆)。
- failures: F862 (帰結の列挙漏れ) 再発済み記録。本 wave で新 F を作る予定なし。

## 成果物の形
code (production 2 file + test 4〜5 file + 登録簿) / decisions fragment 1 / runbook 差分 / insight `output/insights/2026-09-18/t2724-t080-defer-active-v2/` (README・逐語・変異台帳・焦点走 log) / worklog fragment 1。

## 並列分割方針
所有 file で分け、同一 file を 2 子で触らない。候補: author A = production 2 file + `test_t080_freeze_migration.py` + `test_s8b_ratified_freeze.py` (委譲 predicate の境界 test)、author B = `test_s8b_oracle_driver.py` + `test_s8b_floor_campaign.py` + conftest / serialization 登録簿。driver 側の境界 test を B の file に入れる場合は A→B の直列にする (plan が決める)。新規 test file は allowlist / lineno pin (`test_plain_runner_coverage`、`test_ccbench_spawn_sites`) に当たるので既定は既存 file へ追記。

## 受入・実測環境
焦点走と受入は計算ノード dispatch (`tools/run_tests.py`、`tools/dev_wave_wait.py acceptance --lease-optional`)、login では codex 子・静的検査・`check_docs.py`。所在 = worklog、機体固有 = `docs/pegasus-runbook.md`。稼働 wave との重なり: t2613 (trial_registry / s8c_acceptance_receipt) と t2627 (`docs/pegasus-runbook.md`) は本 wave の file と交差しない。

## 模擬 / 実
- 実: chain 無し木 (本 branch)、chain 有り木 (scratch merge)、P3 gate-check の両木実測 (login、v1 freeze path)。
- 模擬: active v2 の A / X (git fixture)。自己 hash・pin は模擬で裁定しない。
