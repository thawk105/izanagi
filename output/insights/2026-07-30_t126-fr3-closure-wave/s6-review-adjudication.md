<!-- parent-owned dev-wave artifact; 2026-07-30 13:04 JST -->

# T-126 FR3 closure — 段6 review 裁定

対象は `s4-adjudication-plan-v2.md` の FR3-1〜4 と、その実効性を担保する
M8a〜M11bである。2本のread-only reviewはともにvalidator green / NO-GO、
計算ノードの関連testは `7 failed, 306 passed, 9 skipped` だった。

## 修正単位

所見は `collector.py`、artifact/schema、submit/job shell、共有fixture、mutation nodeを
横断し、分割すると同じreceipt lifecycleとproduction scriptを別workerが同時編集する。
この相互依存のため、段6 fixは1個のCodex実装単位に寄せる。親は実装面を編集しない。

## 採用所見

| ID | 裁定 | 最小fix条件 | 放置時の成果物影響 |
|---|---|---|---|
| S6-A1 / S6-C6a | real / BLOCKER | legacy import assertionを現契約へ更新し、submit scriptのpersistent importとjob scriptのstdlib-only `-I -S -B`を別々に固定する | baselineが自己矛盾し、mutation/acceptanceを証拠にできない |
| S6-A2 / S6-C1 | real / BLOCKER | normal missing/invalidを削除してrecoveredへ書き換えてもretryへ上がらない単調なorigin gateを実装する。現行artifactでnormal/recovered originを独立に固定できないなら、recovered missing/invalidを保守的にnonretryへ閉じる | failure receipt / attempt ledgerを書き換えて2回目qsub authorityを得る |
| S6-C2 | real / BLOCKER | public verifierのWmax・series timing・identity semantic検査をreceipt publish前の共通分類へ移し、semantic-invalid canonicalをnonretry failureへ閉じる | create-only final receiptと`outcome_pending`が永久に残りattemptが閉じない |
| S6-C3 | real / BLOCKER | embedded publisherは既存stageをglobal preflightしてから一括処理し、multiple / suffix / uid / mode / nlink / symlink / nonregular / external hardlink異常では一件も削除しない | 攻撃・crash evidenceを消してclean final receiptを作れる |
| S6-C4 | real / HIGH | job-result targetは検証済みsubmitted attempt IDへ束縛し、stdout/pointerはexact identity一致の補助証拠に限定する |別attemptのcanonicalを汚染し、正しいattemptのclosureからruntime resultが脱落する |
| S6-C5 | real / HIGH | early targetはvalid時だけattempt canonicalへ採用し、invalid evidenceはcanonicalと別namespaceで非破壊に閉じる | invalid bytesをcanonicalと偽り、元path/inode evidenceを失う |
| S6-A4 | real / HIGH | failure schemaで2つの新classと`retry_eligible=false`の関係をDraft-07条件として固定し、schema負例を追加する | producer defectがpoisoned create-only receiptを発行しrerun closureを妨げる |
| S6-A5 | real / HIGH | invocation claimをfull-write + fsync + exact canonical readbackし、claim hashをbinding/series proof chainへ結ぶ | sole qsub invocation proofがshort-writeで機械検証不能になる |
| S6-A6 / S6-C6b | real / HIGH | M8a/M8d/M10d/M11bを期待点まで到達する単一理由nodeへ直し、M1〜M11のold anchor / mutant / exact node registryを固定する。`_canonical` fixture side effectをpure化し、production shell→crash/signal→accounting→collector rerunを結ぶ | mutation ledgerが権限、consumer同義性、nonretry四層、publisher isolationを検出した証拠にならない |
| CT-1 | real / BLOCKER | `remaining_job_s`の正値pathで`raise None`にならないよう直す | production job scriptが開始前にTypeErrorで落ちる |
| CT-2 | real / BLOCKER | authorized retry fixtureに意味論上必要なregular series ledgerをproduction helper経由で用意する | 許可済みretry正例がpublic verifierへ到達しない |

## 不採用または境界を限定する所見

| ID | 裁定 | 根拠 |
|---|---|---|
| S6-A3 | partial / 今回のmust-fix外 | invalid/accounting-mismatch canonicalそのもの、source snapshot、closure、receipt、attempt ledgerをすべて別のsemantically-valid job resultへ置換する攻撃は、今回のprocess-death / scheduler-signal / accidental artifact corruption境界を越え、同一UIDが全create-only成果物を任意改変する攻撃である。現行の外部authorityはaccountingのjob/RC/Wmaxであり、runtime JSON全bytesを署名する独立rootはFR3計画に存在しない。現在bytesのcanonicalを削除してorigin/retryを昇格するS6-A2は明示scopeなので修正するが、任意のvalid result捏造耐性は別のtrust-root裁定なしに主張しない。 |
| S6-C6c | partial | M10cをfull shell実行へ置換する要求は採用するが、一般power-loss、同一UIDのpath race、`LD_PRELOAD`等system interpreter provenanceまでは既裁定どおりscope外とする。保証claimはprocess death/scheduler signalとrepo package/PYTHONPATH isolationに限定する。 |

## 計算ノードで観測した期待赤

- `test_submitter_has_exact_opt_in_and_no_live_command_in_dry_run_branch`: 旧persistent import期待。
- `test_m11b_exact_spooled_script_uses_embedded_isolated_publisher` の5 parameter:
  `remaining_job_s`が正値でも`raise None`を評価してrc=1。
- `test_one_authorized_retry_submit_collector_chain_is_accepted_once`:
  retry fixtureの`series-ledger.jsonl`が欠落。

fix workerはlogin nodeでbuild/test/check/qsubを実走しない。親がfix後の関連test、静的check、
焦点再review、mutation、受入を計算ノードで行う。
