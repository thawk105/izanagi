# [T-1281] 計算ノード job の完了を待つ正本の待ち手 — 変異台帳と実測

- wave: dev-wave-t1281-qsub-waiter
- 対象 HEAD: `f9f1b0ae3ac63f788bd215f74c8dbfe86a925c06`
- 実装 commit: `7b4cea2dc`、修正 commit: `6f13f3e56`、手順書 commit: `f9f1b0ae3`
- 裁定: D1290 (判定材料は done-marker と会計 `Ended Request Time:` の論理和、`qstat` の rc は使わない)

## 敵対レビューが暴いた誤完了の 2 経路 (親が現物で再現)

修正前の `accounting_ended_result` を wave worktree で直接呼んだ結果。

| 入力 | 修正前 | 修正後 |
|---|---|---|
| 対象 ID 行 (LF) + 他 job の ID 行 (CRLF) + 他 job の `Ended` 行 (CRLF) | `ended=True, reason='ok'` | `ended=False, reason='request-id-count'` |
| `Ended` 行が対象 ID 行より前 | `ended=True, reason='ok'` | `ended=False, reason='ended-before-target-request-id'` |
| 対象 ID 行と `Ended` 行がどちらも CRLF | `ended=False, reason='request-id-count'` | `ended=True, reason='ok'` |

前 2 行が誤完了 (実行中の job を完了として受理)、3 行目が逆向きの見落とし。原因は
`Ended Request Time:` が対象 record へ束縛されていなかったことと、CRLF の扱いが ID 側 (拒否) と
Ended 側 (受理) で非対称だったことである。

## 変異 matrix

事前登録 13 件。うち 12 件を計算ノード dispatch の本走で実行し、1 件 (M11) は下記の理由で本走から
外した。**11 KILLED / 1 SURVIVED (等価変異)**、期待と完全一致 (`MISMATCH` 0、`PARSE_ERROR` 0)。

| # | 変異 | 期待 | 実測 |
|---|---|---|---|
| M01 | 完了述語の論理和を論理積へ | KILLED | KILLED |
| M02 | `Ended` 行の要求を落とす | KILLED | KILLED |
| M03 | `Ended` の探索範囲を全文へ戻す | SURVIVED | SURVIVED (等価変異) |
| M04 | 対象 ID 行より前の `Ended` を拒否しない | KILLED | KILLED |
| M05 | ID 行がちょうど 1 本という要求を緩める | KILLED | KILLED |
| M06 | ID の一致比較を落とす | KILLED | KILLED |
| M07 | ID 側 regex の CRLF 許容を落とす | KILLED | KILLED |
| M08 | done-marker の非空要求を落とす | KILLED | KILLED |
| M09 | done 証拠の短絡を落とす | KILLED | KILLED |
| M10 | deadline 超過の rc を 0 にする | KILLED | KILLED |
| M12 | 受領証の `done_mtime_ns` 記録を落とす | KILLED | KILLED |
| M13 | M03 + M04 の両層同時変異 | KILLED | KILLED |

台帳は `evidence/final-ledger.json` (M01–M10) と `evidence/tail-ledger.json` (M12, M13)。
どちらも baseline `PASSED`、`repo_head` は上記 HEAD。spec は `evidence/spec-final.json` と
`evidence/spec-tail.json`。

### M03 が生存した理由 (DW-M02 の裏取り)

M03 単独の生存は穴ではなく**冗長**である。対象 ID 行より前の `Ended` を拒否する前置検査 (M04 の対象)
と「ID 行がちょうど 1 本」の要求が同時に立っている限り、`Ended` の探索範囲を全文へ広げても受理集合は
変わらない。実効 gate は前置検査であり、M04 単独は KILLED である。

両層同時変異 M13 (M03 + M04) を別途走らせて KILLED を確認した
(`evidence/bothlayers-nodes.json`、赤 node は
`test_accounting_ended_result_binds_ended_to_target_record[ended-before-target]`)。
したがって M03 は単独変異の証拠から外し、この対は load-bearing であると記録する。

### M11 を本走から外した理由 (DW-M06、erratum)

M11 は `--request-id` の parse 時検証を落とす変異である。検証を外すと不正 ID がそのまま
`compute` の待ち loop へ入り、既定 6 時間の deadline まで実際に待つため、**テストは赤ではなく停止する**。

- login 自走 probe では 180 秒の per-mutation timeout で hang を観測した
  (`evidence/probe-nodes.json` の `M11-request-id-validation-dropped`: `hang=true`)。
- 計算ノード dispatch では job 自身の walltime (3,600 秒) まで居座り、harness が終端証拠を取れずに
  orphan-hold で中止した (request 982386.nqsv)。復旧は手順書どおり、対象の不在確認 →
  `git checkout --` での復元 → clean/HEAD 確認 → hold と sidecar の削除で行い、`qdel` は使っていない。
- DW-M06 に従い timeout は fail-open の証拠であって kill ではない。よって M11 は本走から外し、
  この観測を erratum として残す。`--request-id` の rc=2 は
  `test_dev_wave_wait_compute.py` の CLI 負例が親の実走で緑になることで確認している。

## 期待 node の集め方

計算ノードの queue 混雑を避けるため、期待 node は login 自走 probe で先に集めた
(`evidence/probe-nodes.json`)。probe は各変異を 1 件ずつ当て、焦点 test file を走らせ、
`git checkout --` で復元し、その前後で `git status --porcelain` が空であることを確かめる。
本走の実測 status は probe の観測と 12 件すべてで一致した。

## 親が実走した検査

| 検査 | 結果 |
|---|---|
| `orchestrator/tests/test_dev_wave_wait_compute.py` (自走 harness) | 37 passed |
| `orchestrator/tests/test_dev_wave_wait.py` | 378 passed |
| `orchestrator/tests/test_pegasus_dispatch_compute.py` | 334 passed (素の base・patch 適用後の双方) |
| `python3 tools/check_docs.py` | 違反なし |

## 非帰属の赤

- 実装子が報告した `test_pegasus_dispatch_compute.py` の 14 件 (`setup-failure`, `phase=outer-mount`) は
  codex sandbox 側の隔離失敗である。親が login 環境で走らせると素の base でも patch 適用後でも
  334 全緑になる。
- fix 子が報告した `test_mutation_worktree.py` の 3 件は、fix を当てる前の同じ木でも同数・同テストで
  再現した。login node の `--runner-mode local` 拒否と signal 転送 harness の制約であり、
  本 wave の変更に帰属しない。
