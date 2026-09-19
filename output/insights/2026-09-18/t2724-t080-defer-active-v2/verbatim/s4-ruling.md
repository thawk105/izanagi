# 段 4 裁定 — dev-wave-t2724-t080-defer-active-v2 (2026-09-18 11:25 JST 起草)

裁定 inbox の再走査 (11:19 JST): T-2724 の控えは 09:24 のまま更新なし。新規 1 件 (受入門番の正本、11:16 起票) は本 wave と無関係。
local main は `99fcf2323` へ前進 (本 wave 基点 `24ede1d11` から t2290 / t2613 の docs・production を含む)。対象 file との直接交差は
consult B が「見つからず」。統合時に固定 SHA で取り込んで再受入する (段 9)。

## 所見の裁定 (real / refuted、採否、scope)

| 所見 | 判定 | 採否 | 対応 |
|---|---|---|---|
| A-1 保持 report の鮮度 (must-fix) | real | 採用 | 委譲は「直前の full validation の token」に限る。campaign-start 前の receipt 再解決では `launch_validate(ratified, root)` を**再実行**して新鮮な token を得て、それで委譲付き再解決する。gate 時 token と `ratified.sha256` / `activation_head` / `search_digest` が一致しなければ `v2-execution:` 系 refusal。predicate 自体は鮮度を検証できないので、呼出側の義務として D と docstring に書く |
| A-2 変異の単一理由性 (must-fix) | real | 採用 | 下の事前登録表を A-2 の帰属表どおりに照準 (m3 は helper の「token なしでも zero-hit を省く」変異、m6/m7 は outer field / namespace 外 file の fixture、m8 は `clean_scan_digest` と draft の `_assert_search_pass` 呼出し除去) |
| A-3 adapter への委譲追加は到達不能 (should) | real | 一部採用 | 裁定文 (G wave fragment 項 1) が adapter を名指すので **同じ helper を受ける任意引数 `launch_validated=None` を adapter に足す**が、driver からの転送は入れない (v1 発火時に token は無い = 到達不能)。委譲正例 test は adapter に作らない。helper 経由で束縛違反を拒否する負例 1 本は helper 側で担う |
| A-4 draft 側の実 hit 負例 (should) | real | 採用 | 切り離し後の stub-free fixture に S 外の走査対象 path へ合成 hit を置き、実 draft (`_draft_reconstruct_holdout`) が層 2 で拒否する対照を足す |
| A-5 / B-4 / P3' 解決 1 回化 | real | 採用 | receipt 解決は launch 判定の後ろで 1 回 (v2 成功 = token 付き、loader / launch 失敗 = token なし、公開 gate の v1 経路 = 従来どおり token なし) + campaign-start 前 1 回。早期 return で解決を省かない。`call_count == 2` と drift の 2 要素列を維持 |
| A-6 走査範囲の差は除外拡大でない (nit) | real | 記録 | D に「v2 の exact 免除は v1 の prefix 除外内に収まる」を根拠付きで書く |
| A-7 brief の一般化 (nit) | real | 記録 | insight で「G は v1 prefix 除外の走査で hit しない」「未発効 + hit は委譲されず拒否」に限定して書く |
| B-1 統合 fixture の障害 (must-fix) | real | 採用 | 接続正例の fixture は S を広げず、**初期 commit 前に材料を確定**: (a) 実 root の g1 世代文書・budget 入力・selector 証拠 (predictions / journal) はこの正例 fixture の base に複製しない (chain 有り木で history-mutated / selector 祖先不成立になるため。45 node 用の S は不変)、(b) selector 材料は fixture repo 自身の commit に束縛して合成、(c) 順序 `basis → R → … → C (certificate) → G → A → X`、`G^ == frozen_at_head`。emitter の `_prepare_emitter_base` / `_make_fixed_ccbench` は再実行せず既存 ccbench pin を protocol に渡す (hold 下)。接続できなければ「実装済み・未達」と報告し、分離 test で示せた範囲を明記 (着地条件未達 = 段 6 で停止判定) |
| B-2 serialization の literal consumer 2 本 (must-fix) | real | 採用 | `test_receipt_memo_prewarm_wiring_is_controller_only_and_lazy` (4963 付近) と `test_receipt_memo_real_xdist_order_has_no_worker_payer` (5485 付近) を残存 consumer の名前へ追随 |
| B-3 prewarm 費用は残る (should) | real | 記録 | 5 分達成の予測に使わない |
| B-5 T-2776 完了条件 (should) | real | 採用 | T-2776 は「floor 2 経路・宣言 S の独立差分検査・既存対照・3 負例・search 拒否除去変異・両木焦点走」で完了判定。chain 有り木の全走は本 wave の必須条件にしない |
| B-6 opt-out は 2 関数 / 3 node (nit) | real | 記録 | |
| B-7 runbook に可変状態を置かない (nit) | real | 採用 | runbook は判定規則だけ (「A / X 後は世代 file を指定、同一 root / HEAD / 世代の full validation 成功時に限り層 2 委譲、v1 指定では委譲しない」)。「未実測」は worklog / insight に書く |

## plan v2 (author への確定指示の骨格)

1. production (3 file): `s8b_ratified_freeze.py` の `LaunchValidatedFreeze` / `ReverifiedFreeze` に `validation_root: Path` と `search_report: Mapping` (deep-freeze) を追加し `_launch_validate` の完全一致・陽性対照・artifact 再捕捉の後に埋める。`t080_freeze_migration.py` に `_holdout_layer2_delegation(*, root, validation_head, launch_validated) -> Optional[Mapping]` を追加 (7 条件: exact 型 / `validation_root == Path(root).resolve()` / `activation_head == validation_head == _capture_head(root)` / `ratified.activation_head` 一致 / `resolve_active_generation(root)` の HEAD・generation_sha256・number・commit 一致 / `search_digest == _enumeration_digest(root)` / 凍結 doc 束縛)。`_verify_holdout_live_scan(root, holdout_doc, *, delegate_to=None, validation_head=None)`、`verify_receipt(..., launch_validated=None)`、`static_gate_adapter(..., launch_validated=None)`。`s8b_oracle_driver.py`: `_resolve_t080_receipt(*, root, launch_validated=None)`、`gate_check` / `run_block` は P3' の順序、campaign-start 前は `launch_validate` 再実行 + 一致検査 + 委譲付き再解決 + `_t080_epoch_identity` 比較。refusal prefix / reason 不変。新しい refusal return を増やさない (15 return pin)。
2. test (境界): plan の表の test 名を使う。正例は接続 fixture (B-1 の材料確定)。負例 (a)〜(f) + 束縛違反 + campaign-start の再検査 (受理→拒否の向き) + 鮮度 (gate 後に namespace 外の合成 hit を置くと campaign-start で拒否) + v1 経路は委譲しない。
3. test (切り離し): S = official namespace 全体 ∪ 候補 exact file (`V2_CANDIDATE_REL`)。(i) `_copy_git_visible_output` の除外に S を足し、copy 契約 test に差分集合検査を足す。(ii) floor 2 経路の clone から S を `git rm` + commit (S 空なら commit しない)、履歴 assertion を 3 段に分離、新負例 `test_clean_scan_rejects_synthetic_chain_artifacts[official|candidate|both]` は `output/env/pegasus/calibration/s8b-floor-official/synthetic-chain/result.json` と `V2_CANDIDATE_REL` に `_holdout_hit_text` を置き、report の `conjunction_hits` に投入 path が載ることを確認したうえで `clean_scan_digest` の拒否を要求、無害 bytes の対照は正しい allowlist で通す。(iii) `_run` と直接 memo 3 関数を `_never_issued_resolution()` へ、登録簿 (conftest / serialization golden / B-2 の 2 本 / `:2853` 導出 / 34→8 pin) を追随、opt-out 2 関数 3 node は維持。(iv) g7 の exact 集合は不変。A-4 の draft 負例。
4. 行番号 pin: `test_ccbench_spawn_sites.py:3382` の driver evaluate sink 1788 を同じ sink であることを確認して追随。
5. docs (親): runbook §1.1 / §2 P3 の段階別判定規則 (B-7 の形)、decisions fragment (slug `t080-layer2-delegation-bound-to-live-validation`)、worklog fragment、insight。

## 変異事前登録 (DW-M01、位置は実装後に一意性を確認して確定)

| id | category | 位置 (実装後に anchor 確定) | 期待 kill (完全集合は probe で確定) |
|---|---|---|---|
| m0-comment | positive / SURVIVED | `t080_freeze_migration.py` helper 内の comment 1 行 | なし (harness の SURVIVED 正例) |
| m1-subset | negative | `_launch_validate` C2-4 `current != expected` → `not expected <= current` | 既存 `test_undeclared_hit_outside_closure_rejected` 系 + 新 `test_t080_failed_launch_preserves_receipt_refusal` |
| m2a-ignore-receipt | negative | `_make_gate_decision` `allowed=not merged` → `allowed=not list(refusals)` | 新 `test_t080_active_v2_preserves_nonlayer2_receipt_refusal` (公開 gate、launch 成功 + R trailer 不正) + 既存 gate 集約 test |
| m2b-accept-invalid | negative | `_campaign_t080_value` で invalid を epoch record に変える | run_block 境界 test (gate 通過後の拒否) |
| m3-skip-zero-hit-without-token | negative | `_verify_holdout_live_scan` の `delegate_to is None` 分岐で `_assert_search_pass` を省く | 新 `test_t080_unactivated_chain_hit_is_invalid` + 既存 `…single_defects…[unknownness-layer2…]` |
| m4a-drop-expressions | negative | helper / live scan の `expressions` 比較除去 | 新 `test_delegated_scan_keeps_frozen_document_bindings[expressions]` + 既存 g1 束縛 test |
| m4b-drop-match-convention | negative | 同 `match_convention` 比較除去 | 同 `[match_convention]` |
| m5-drop-campaign-start-recheck | negative | `run_block` campaign-start 前の再解決 + epoch 比較除去 | 既存 `test_run_block_rejects_receipt_epoch_drift_before_campaign_start_g4` + 新 delegated 版 |
| m6-drop-activation-head | negative | helper の outer `activation_head == validation_head` 比較除去 (後段に重複比較を置かない) | 新 `test_layer2_delegation_rejects_wrong_activation_head` (outer field だけ replace) |
| m7-drop-enumeration-digest | negative | helper の `search_digest == _enumeration_digest(root)` 比較除去 | 新 `test_layer2_delegation_rejects_enumeration_drift` (namespace 外・非 ignored の file 追加) |
| m8a-clean-scan-no-assert | negative | `clean_scan_digest` 内の `_assert_search_pass(report)` 呼出し除去 | 新 `test_clean_scan_rejects_synthetic_chain_artifacts[official/candidate/both]` + 既存 clean scan 負例 |
| m8b-draft-no-assert | negative | `_draft_reconstruct_holdout` 経路の `_assert_search_pass` 除去 | A-4 の draft 負例 + 既存 `…[unknownness-layer2…]` |
| m9-drop-root-binding | negative | helper の `validation_root` 比較除去 | 新 `test_layer2_delegation_rejects_foreign_root` (同 HEAD・同名集合の clone) |
| m10-drop-generation-recheck | negative | helper の `resolve_active_generation` 再照合除去 | 新 `test_layer2_delegation_rejects_stale_generation_token` (HEAD field だけ現行値にした旧世代 token、または namespace dirty) |
| m11-stale-token-at-campaign-start | negative | `run_block` campaign-start 前の `launch_validate` 再実行を gate 時 token の再利用に置換 | 新 `test_t080_delegated_campaign_start_rejects_late_hit` (gate 後に namespace 外の合成 hit を追加) |

走らせ方: probe (全件 SURVIVED 期待で観測 node 収集) → final (完全集合)。runner argv は焦点 3〜4 file (`test_t080_freeze_migration.py`、`test_s8b_ratified_freeze.py`、`test_s8b_oracle_driver.py`、`test_s8b_floor_campaign.py -k clean_scan`)、`--force-dispatch`、`-rf`。所要は baseline 実測から決める。

## 実装分割

Codex author 1 本 (workspace-write、本 wave worktree、wall-clock 5400 秒)。所有 = production 3 file + test 6 file (test_t080_freeze_migration / test_s8b_ratified_freeze / test_s8b_oracle_driver / test_s8b_floor_campaign / conftest / test_real_repo_serialization) + `test_ccbench_spawn_sites.py` の行番号 pin + 直接 constructor 7 箇所の追随。未完なら同 worktree で継続 author を 1 本。親は docs・commit・変異・受入。
