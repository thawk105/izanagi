---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-22
wave: dev-wave-t1472-c02-arm-noninterference
seq: 1
---

## 新規

### {{F:consumer-test-single-module-grep}}. autonomous_trial_completeness.py変更時にp3_autonomous_workload_trialのimporterだけをconsumer test拡張対象にし本体のimporterを見落とした [手順漏れ] [テスト代表性]

- 事象: `autonomous_trial_completeness.py`と`p3_autonomous_workload_trial.py`の両方を
  変更するwaveで、DW-O26のconsumer test拡張を行う際に
  `grep -rln "p3_autonomous_workload_trial\." orchestrator/tests/`だけを実行し、
  `autonomous_trial_completeness`自体をimportする8ファイル (test_trial_registry.py含む)
  を見落とした。段5実装・段6敵対レビュー2本・親の直接テスト実走のいずれもこの穴を
  検出できず、受入全走で初めてtest_trial_registry.pyの13件が
  `[payload-validation-receipt] safe identity differs`で赤化した。
- 根本原因: 変更した2ファイルのうち1ファイル (`p3_autonomous_workload_trial.py`) の
  importerだけをgrepし、もう1ファイル (`autonomous_trial_completeness.py`) の
  importerを別途grepしなかった。複数productionファイルを同時に変更するwaveでは、
  consumer test拡張は変更した**ファイルごと**に独立してimporterを洗い出す必要がある。
- 恒久対応: `docs/dev-wave/operations.md`のDW-O26に「変更したproduction fileが複数ある
  場合は各ファイルごとにimporterをgrepする」という明示を追加する改訂候補を段8の
  dev-wave改善候補へ送る (未確定、記録のみ)。
- 再発検知: 複数productionファイル変更waveで、DW-O26のconsumer test拡張grepコマンドが
  変更ファイル数と1対1で存在するか段6レビューで確認する。
