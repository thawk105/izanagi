---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-28
wave: worktree-dev-wave-t1943-mocc-g2-discriminator
seq: 2
---

## 新規

### {{F:compute-path-stat-keyword}}. login側Pythonでしか試していないembedded validatorが計算ノードでreceipt公開を止めた [テスト代表性] [手順漏れ]

- 事象: T-1943の唯一の計算ノードcellはverifier/discriminatorまで完了したが、artifact classificationの`Path.stat(follow_symlinks=False)`が計算ノードPythonで`TypeError`となり、completed pilot receiptとjob-resultを公開できなかった。
- 根本原因: unit testはlogin側Pythonでproduction fragmentを実行し、API keywordの版差を表現していなかった。pilotのchecker/verifierにはinterpreter選定がある一方、このembedded blockはPATHの`python3`を使う非対称も見落とした。
- 恒久対応: `tools/pegasus/mocc_trace_pilot.sh`は`os.lstat`でno-follow directory判定を行い、`orchestrator/tests/test_mocc_trace_job_contract.py::test_t1943_artifact_manifest_requires_real_witness_directory`が禁止API不在、real directory正例、directory symlink/regular-file負例をproduction fragmentで固定する。
- 再発検知: compute jobのfinalizationで`TypeError: stat() got an unexpected keyword argument 'follow_symlinks'`、または上記回帰nodeの赤を検出する。
