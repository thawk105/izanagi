# 段 6 裁定 1 巡目 — [T-2865] (2026-09-26 20:2x JST、親)

対象: wave commit `41b8019a9`。入力: 焦点走 1 (commit 前、149 passed / 3 failed = 未 commit 由来)、焦点走 2 (commit 後 38 file、4392 passed / 9 failed / 12 skipped、request は `focus-2.log`)、レビュー A (NO-GO、must-fix 2)・B (NO-GO、must-fix 2)、親の runbook 起草で見つけた欠落 2 件。

## 裁定

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| F1 | 性能動作点が campaign identity に入らない (A1) | real / must-fix | `default_perf()` の records・threads・workload・extime・reps を正規化して search_config に焼き、`run_one_iteration` / `drive_iteration` で渡された perf と一致しなければ `ValueError` |
| F2 | verify・liveness 失敗の構造化理由が次の coder に届かない (A2・B3、規律 3) | real / must-fix | 履歴の `outcome` を設計 §3.2 の分類 (`certified`・`rejected`・`build-error`・`trace-timeout`・`trace-run-nonzero-exit`・`trace-empty`・`trace-no-abort-counts`・`non-serializable`・`indeterminate`・`bench-no-throughput`・既存の他の閉じた理由) に、`verifier_digest` を閉じた構造 (どの verify workload で落ちたか、verdict、cycle 数・integrity の理由 code など、EvalResult / WAL の構造化 field から射影。自由文は入れない) にする。**履歴 entry の key 集合は変えない** (承認済み role 本文の入力例と一致させるため) |
| F3 | auditor 前に preview できない (B1・親 P-1) | real / must-fix | `--preview-diff` は top が `{"coder"}` だけの閉じた file を読む。`--run-iteration` は従来どおり `{coder, auditor}` |
| F4 | 初回 `--no-build` の dry-pass が admitted view を要求して例外 (B2) | real / must-fix | dry-pass では WAL 必須の読込と critic digest 書出しをせず結果を返す。dry-pass は履歴にも載せない (sort の whiteboard と同じ扱い) |
| F5 | `--emit-coder-input` に critic 診断の入口が無い (親 P-2) | real / must-fix | `--critic-output <file>` を足し、bytes を `L.k2_critic_diagnosis_from_bytes` で 6 field に変換して渡す |
| F6 | 探索 namespace の driver 登録簿・certified writer の caller inventory が新 driver を知らない (焦点走 2 の 7 件) | real / must-fix | `orchestrator/tests/test_p3_exploration_namespace.py` の `DriverContract` 表と driver 名列、`orchestrator/tests/test_campaign.py` の caller 件数表に新 driver を**追加登録**する (既存 entry は変えない)。namespace の各契約 (runtime layout・selector・AST gate・CLI authority) を driver 側が満たすように直す |
| F7 | MOCC template proof の test が auditor.md の whole-file sha256 を proof と照合し、承認済みの auditor 改訂で赤 (焦点走 2 の 2 件) | real / must-fix (設計判断) | `orchestrator/tests/test_mocc_template_proof.py` の `_consumer` の whole-file sha 一致 1 行を、「proof に記録された `auditor_definition.items` == 現行 auditor.md への `check_auditor_definition` の結果」に置き換える。項目の全真検査 (次行) は残す。proof JSON は取り直さない。理由: 規律 7 (現行 bytes との差だけで記録を無効にしない)・auditor の MOCC 項目の意味は保たれている・production の consumer (`require_proof_binding`) は auditor の sha を見ない |
| F8 | 変異 M-E1 は kill 不成立 (A3・B4)、M-E4 の期待 test が veto 呼出しを覆わない (A3・B5)、M-E7 は `validate_ir` に遮られる (A3) | real / should | M-E1 は diagnostic pin に移す。M-E4 用に型 22〜26 の verdict を実 `policy_gate` に通す test を足す。M-E7 は parser と `validate_ir` の両層変異として登録し直す |
| F9 | `load_proposal_file` の `validate_ir` 重複 (B6) | real / nit | 削る (parser 内で 1 回) |
| — | admission policy の二重 bind (B6) | refuted (冪等、`ident.py:84-98`) | 変えない |
| — | preview が auditor veto をしない (A 検証節) | 設計どおり | runbook に明記 |

## 変異の再登録 (fix 後に単一理由性と期待 node の完全集合を確定)

| ID | 変更 |
|---|---|
| M-E1 | → P-E2 (diagnostic pin、kill に数えない) |
| M-E4 | 期待 test を「型 22〜26 の verdict を `policy_gate` に通す test」に照準し直す (loader と veto の二層にまたがるなら両層変異として登録) |
| M-E7 | parser の exact 型と `validate_ir` の bool 拒否の両層変異 |
| M-E12 (新) | search_config と実行時 perf の一致検査を外す → F1 の test |
| M-E13 (新) | 履歴の `outcome` を `aborted` 一律に戻す → F2 の分類 test |
| M-E14 (新) | preview が auditor key を要求する形に戻す → F3 の test |

## 計算

焦点走と受入だけ (live 実走なし)。MOCC proof は取り直さない (F7)。
