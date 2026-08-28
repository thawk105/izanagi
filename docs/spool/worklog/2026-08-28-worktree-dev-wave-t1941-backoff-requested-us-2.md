---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: worktree-dev-wave-t1941-backoff-requested-us
seq: 2
title: [T-1941] adaptive backoff requested-us診断を実走し、診断専用境界へ固定した (code + tests + insight、branch worktree-dev-wave-t1941-backoff-requested-us、変異13/13 KILLED)
---

## 本文

- 前D95 authorの`f45_missing_output`外来差分を削除・再生成せず監査し、D95 author/fix、敵対review 2本、焦点review、実機blocker fixを経て、実装/evidence/fix commit列 `a4b877289`、`a02a66779`、`5d278c612`、`4635cb574` を作成した。新GeneratorIdがpolicy hashを全域変更する案はacceptance 79赤で棄却し、既存BACKOFF_PROFILE receiptへ戻した。
- diagnostic patchはdefault 0でinert、Siloのallowlist内3fileだけを変更する。各workerのheap-backed TLS counterをper-call更新し、共有registry同期は初回登録だけ、process exitで15 fieldを1行集約する。nested patch flock自己待ちは{{F:nested-patch-flock-self-wait}}、GNU patchとproduction git applyの乖離は{{F:fixture-executor-patch-divergence}}へ記録した。
- Pegasus最終run `957236.nqsv`（bnode047、Elapse 80S、child rc=0）はcall count 931274、requested-us sum 125899500、平均135.19060985273936us/call、unknown 0、overflow false。state 0/100/200/300/400/500/600/700/800/900/1000 callは480120/238132/57590/33173/25461/19724/17576/15756/15907/15654/12181。rep SHA `f9dc81e0...`、manifest SHA `5eb418d2...`、dispatcher receipt SHA `f319bdb2...`。
- 全値とmanifestは`certified:false`、`diagnostic_only:true`。headline TPS、formal B-10、floor、fitnessの利用資格は全falseで、formal preregの1.0% exclusive上限を変更していない。1 workload x 1 repなので安定性・3 workload一般化・実時間waitは主張しない。
- 関連走は65 passed。final tipの変異は3spec全baseline PASSED、合計13/13 KILLED、MISMATCH/SURVIVED/TIMEOUT/PARSE_ERROR 0。allowlist escape probeは4重の冗長gate検出として単一理由countから除外した。
- full acceptance 1の79赤をD95 fixで閉じ、full acceptance 2はchild-green、18727 passed / 62 skipped、tested main `6ecc6f88b`、tested tip `1aa5aa790`、log SHA-256 `6d506cbca6fe9678afd28a1b6929a5f57a038b7ddd868cac644a28f25dd6d86e`、effective scheduler `loadgroup`。
- 診断値の正本とattempt履歴は`output/insights/2026-08-28_t1941-backoff-requested-us/README.md`。raw job logはrepo外専用job dirへ逐語保全した。push・remote操作は行っていない。

## 次の一手差分

### 完了

- [T-1941] 適応backoffの要求usと呼出回数を直接計装し、balanced 1 repの診断値を用途非適格のまま記録した。
  remaining: none
  base: ced37f95d46c016068e88f4fd6bd94e684147b640bc6ef141d1d3c6502cf4620
