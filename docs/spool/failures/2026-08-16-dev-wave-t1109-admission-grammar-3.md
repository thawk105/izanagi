---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1109-admission-grammar
seq: 3
---

## 新規

### {{F:completeness-gate-blocks-its-own-report}}. 完全性検査が report を書く**前**の関門だったため、admission 失敗の試行は診断 report を 1 件も残せなかった [誤前提] [手順漏れ]

- 事象: 8c live pilot の実走 (2026-08-15 07:53 JST) が 23 秒で `rc=1` に終わり、
  run dir には `attempts.jsonl` (3 event) だけが残った。journal の `run-finish` は
  `{"status": "partial", "report": ".../report.json"}` と**書いてある**のに、
  その `report.json` はディスク上に**存在しない**。
- 根本原因: `p3_autonomous_workload_trial._finish_trial` の順序が
  (1) `journal.append(run-finish)` → (2) `report["attempt_journal_sha256"] = ...` →
  (3) `assert_autonomous_trial_completeness(...)` → (4) `_write_json_atomic(report.json)`
  である。transport admission が失敗すると journal 先頭に `transport-admission-error` が入るが、
  この event 名が `autonomous_trial_completeness._EVENTS` の閉集合に無いため (3) が
  `closed-event-set` で例外を上げ、**(4) に到達しない**。
  完全性検査は「書かれた report を後から検証するもの」ではなく
  **report を書くこと自体の関門**だったが、その位置づけが誰にも意識されていなかった。
  結果として「失敗の理由を還流させるための partial report」が、
  失敗したときにだけ書かれないという逆転が起きていた (規律 3 の還流断絶)。
- 波及の広さ: `_EVENTS` へ event 名を足すだけでは足りず、
  `_check_run_envelope` の `first_run_event` (先頭 event を success admission としか
  数えない)、`_check_terminal_projection` の配置要件 (terminal は `events[-2]` 固定)、
  `_check_workload_coverage` の zero-cell 説明、`verify_autonomous_trial_files` の
  campaign root 要求まで、**5 面**が同時に塞いでいた。
- 恒久対応: {{D:pbs-jobid-env-grammar}} と同 wave の実装で、
  `_EVENTS` / `_TERMINAL_EVENTS` への追加、`_check_transport_admission` の error 専用 gate、
  `first_run_event` の 2 種集合判定、terminal projection の先頭配置分岐、
  workload coverage の zero-cell 拡張、campaign root 要求の限定免除を入れた。
  検出は `orchestrator/tests/test_p3_autonomous_workload_trial.py` の
  producer 統合テスト (admission 失敗後に verified partial `report.json` が
  実際に永続化されることを固定する) が担う。
- 副次的所見 (本 wave では直さない): 記録された journal の `run-start` は
  現行 producer が無条件に書く `generation_driver` / `gating_spec_sha256` /
  `honest_accounting_authority` を持たないのに、`SCHEMA_VERSION` は双方とも
  `p3-autonomous-workload-trial/v3` である。**schema_version を上げずに field を足している。**
  このため記録済み artifact の bytes を fixture にすると stale な形を固定してしまう。
  本 wave の fixture は現行 producer から導出した。
- 再発検知: 上記 producer 統合テスト。**「report が書かれない」を
  「検査が赤い」と区別する**ため、検査の緑ではなく `report.json` の実在を固定する。

## 再発

### F97

- **再発の解決: 2026-08-15** — F97 の 2 例目として記録された
  「実機 `PBS_JOBID` が transport 述語を通らない」は、ユーザー裁定 (択 (a)) に従い
  {{D:pbs-jobid-env-grammar}} で解決した。受理文法を
  `(?:0:)?[A-Za-z0-9][A-Za-z0-9._-]*` へ拡げ、qsub authority は不変に保った。
  **新たに拒否される値は 0 件**であり、防護側の主張は減っていない。
- **F97 が提案した自己整合 positive control は、族の義務として制度化した**
  ({{D:fail-closed-admission-positive-control}})。本 wave では member 8 件のうち
  1 / 3 / 4 / 5 / 6 / 7 の 6 件に実在 production 値の control を置いた。
  **member 2 (runtime attestation) は D143 のユーザー裁定待ちのため `unmet` のままである** —
  真正面に control を書けば現在は赤になる。skip・xfail・期待反転で緑に見せることはしていない。
  member 8 (provider live env / receipt 一致) も入力未取得で `unmet`。
- **F97 の型が repo 内で可視だった証拠:** `output/env/pegasus/calibration/job-staging/` には
  `0:` 付き実機 job ID を directory 名に持つ tracked artifact が **526 file** あった。
  述語が「colon を含まない」と主張し続ける間、repo は同じ値を tracked で保持していた。
  **実在値が自分の述語を通らない型は、多くの場合 repo 内に既に反証が置かれている。**
