---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1240-perf-degrade-exploration
seq: 1
title: 探索経路の perf degrade は既に land 済みで、残っていたのは層 3 材料レポートが degrade 済み走を生成できないことだった (コード + テスト、branch worktree-dev-wave-t1240-perf-degrade-exploration)
---

## 本文

依頼は「8c / s4 の探索経路へ perf preflight を結線し、perf 不在なら degrade させる」だった。
**結線は本 wave の開始前に別 wave が済ませており、残っていたのは下流の閂だった。**

**裁定 1 の前提は現行 HEAD で偽である。** 裁定文は「探索経路は preflight を一度も呼ばない」を
前提にしていたが、`loop.run_campaign` は `do_bench=True` のとき seam の有無に関わらず既定 probe を
必ず 1 回走らせる。この結線は裁定の根拠になった実機走 (request `0:913859.nqsv`) より後の
2026-08-16 18:44:59 に land 済みだった。裁定が名指しした 4 file
(`p3_autonomous_workload_trial` / `p3_s4_loop` / `p3_s4_loop_sort` / `p3_s4_loop_trigger_gating`)
はすべて `run_campaign` 経由なので、直接結線は 1 行も要らない。8c は
`trigger.drive_iteration` へ委譲するのでこの経路に乗る。

**裁定 2 が official 側を上書きしていた。** 引数は 2026-08-16 裁定の「official は no-perf 拒否を
保つ」を条件として渡してきたが、翌 2026-08-17 の [T-1253] が「正式系列も perf 不在で進める。
正式系列だけ perf 実在を要求という推奨は却下」と裁定していた。親は最初これに気付かず official へ
拒否を新設する brief を書き、**段 2 の codex 子が台帳を辿って fail-closed で停止して初めて
判明した**。brief を作り直した。並行セッションも archive の旧エントリを読んで「未裁定」と
報告してきたので、同じ罠に 2 者が独立に落ちた。

**穴の個数も間違えた。** 親は grep で「degrade できない直接呼び手は `screening_driver` 1 本」と
brief に書いたが、`orchestrator/tests/test_campaign.py` のメタテストが `pipeline.evaluate` の
呼び手をちょうど 5 本、`loop.run_campaign` の呼び手をちょうど 15 本に pin していた。実際の穴は
4 本である。走行中の段 2 子を止めて brief を作り直した (計 2 回の巻き戻し)。

**本当の閂は層 3 だった。** `pipeline` は preflight receipt があれば **perf の有無を問わず**
`perf_observation` を bench payload へ入れる。層 3 レポートは bench_done payload をほぼ丸ごと
`runs` 行へ写す一方、`layer3_schema.json` の `runs.items` は `additionalProperties: false` で
同 property を持たない。したがって **`1ea1cbdb` 以降に build+bench へ到達した探索走は、
レポート生成そのものに失敗する**。8c は自分で render するので `AutonomousTrialError` で試行が倒れる。
親が jsonschema で実測し、並行セッションが実走 WAL
(campaign `p3-t178-ycsb-a-workload-conditioned-autonomous-a6e7f12d`) で裏を取った。

**ただし本修正だけでは 8c は解除されない。** `layer3_report` の `_git_head()` は schema 検証より
先に走り、repo 外に置かれる探索 campaign では rc=128 で必ず失敗する ([T-1279])。**2 本は直列**で
あり、[T-1279] が 1 本目、本件が 2 本目である。親は一度この順序を誤って並行セッションへ伝え、
実コードで確かめて訂正した。

**段 6 のレビューが受理集合の穴を出した。** 段 5 の schema は型と enum しか見ておらず、producer が
生成できない矛盾 receipt を通していた (親の probe で 5/5 受理)。`use_perf` と `preflight.available` の
不一致、`use_perf=true` かつ `counter_status="not_required"`、WAL へ到達しえない
`status="probe_error"` などである。裁定 2 が全 degrade へ課した受入条件
「perf 有りで測ったと読めてしまう成果物を作らない」に触れるため、`if`/`then` で相互整合を
schema 内に束縛した。fix 後は 0/5 になり、producer が実生成した receipt 2 分岐は引き続き受理する。
`layer3_report.py` へ検証コードを足す案は新しい gate の新設にあたるので採らず、backlog とした。

**変異事前登録を段 6 で訂正した。** レビューが M-1 の期待 node を「T1 単独」と記した親の登録を
崩し (実際は T1 と T2 の両方が落ちる)、M-3 (`perf_observation` を `required` へ) が既存テスト 3 件に
過剰決定されることを示した。M-3 は冗長 gate として単独変異の証拠から外した。

**発火条件の判定で裁定理由を 1 つ誤った。** `screening` key の同型 schema 穴を「発火条件なし」と
書いたが、レビューが実 WAL
(`output/campaigns/backoff-sweep-silo-read-heavy-sweep-6f169f90/runs/wal.jsonl`) に
`"screening":true` が実在することを示した。正しい理由は「実 artifact はあるが `docs/phase3.md` の
screening campaign 節が schema 再凍結まで明示除外している」である。

**環境**: bounded local の焦点走が 02:18 以降 `memory.max / memory.oom.group を attest できない` で
連続失敗した。02:16 の成功走の後に予算がピーク由来へ縮んでから再現した。本 wave の差分
(JSON schema とテストのみ) とは無関係で、`--force-dispatch` で計算ノードへ回して測った。

工数: codex 子 9 本 (plan 2・consult 2・author 1・review 2・fix 2)。うち plan 1 本は
fail-closed 停止、plan 1 本は親が前提誤りに気付いて停止させた。

## 次の一手差分

### 完了

- [T-1240] 探索経路の perf degrade を実測で確定した。裁定が名指しした 4 file への直接結線は
  不要で (`loop.run_campaign` が既定 probe を必ず走らせる)、残っていた下流の閂である
  層 3 schema の `perf_observation` 拒否を塞いだ。producer 整合の束縛も入れた。
  remaining: none
  base: 5db71adf3bec43a0fe06b249662d15c0b167f353b615734f76d5d77e5405c9d9

### 新規

- {{T:direct-evaluate-perf-holes}} **P2・新規**: `pipeline.evaluate` を `loop.run_campaign` を
  経ずに呼ぶ 4 経路 (`screening_driver.py` / `s1_direct_comparison.py` / `s8b_oracle_driver.py` /
  `qualification/t126_driver.py`) は `use_perf` を渡さず、perf 不在なら bench が落ちる。
  本 wave は DW-G04 に従い実装しなかった — 4 経路とも現時点で再走の計測 ID を書けない
  (S1 は本走完了、S6/S8a は完了、8b oracle は freeze の floor/budget が null で run gate が拒否、
  T126 は live qualification 保留)。**「永久に未発火」ではない。** 各経路が発火した時点で塞ぐ。
  既存 `evaluate_fn` seam は `s1_direct_comparison` と `s8b_oracle_driver` に実在する。
  呼び手の権威ある閉包は `orchestrator/tests/test_campaign.py` のメタテストである。
- {{T:layer3-schema-payload-holes}} **P2・新規**: `pipeline` が bench payload へ足す key のうち
  `screening` と `screening_disabled` は層 3 schema の `runs.items` に無く、`perf_observation` と
  同型の穴である。実 artifact は存在する (`backoff-sweep-silo-read-heavy-sweep-6f169f90` の WAL に
  `"screening":true`) が、`docs/phase3.md` の screening campaign 節が schema 再凍結まで
  明示除外しているため本 wave では広げなかった。再開条件 = schema 再凍結。
- {{T:backoff-report-fake-zero-ipc}} **P2・新規**: `orchestrator/campaign/backoff_sweep_report.py`
  は欠測 IPC を `.dat` と Markdown の両方で literal `0` / `0.00` へ変換し、その値を機序説明にも
  使う。no-perf 走では「perf で IPC=0 を測った」と読める偽表示になる。全件検索で同型は他に 0 件
  なので DW-G03 により族一般化はしない。producer の backoff sweep は凍結材料で再走計画が無いため
  発火条件は現在ない。`orchestrator/critic/digest.py` が `perf_observation` を落とす件も同じ項で扱う
  (こちらは欠落であって偽装ではない)。
- {{T:t1253-actual-gate-closure}} **P1・新規 (ユーザー裁定待ち)**: [T-1253] の台帳本文は official の
  no-perf 拒否を「実箇所は 2 つ」と断定するが、実コードと一致しない。`s8b_holdout_freeze` と
  `s8b_ratified_freeze` は official floor を `expected_use_perf=True` で再検証し、
  `tools/pegasus/t126_qualification.sh` は functional perf が無ければ driver の手前で exit 2 し、
  `t126_driver` の prologue consumer は perf smoke rc=0 と全 event を要求する。**2 箇所だけ外しても
  official floor・refreeze・S8b oracle・T126 は perf 不在環境で進まない。** [T-1253] を
  「2 箇所限定」と読むか「official 全経路」と読むかを裁定する必要がある。
- {{T:layer3-boundary-receipt-revalidation}} **P3・新規**: 層 3 は `perf_observation.preflight` を
  schema の相互整合だけで検査しており、production の `validate_perf_preflight_receipt` を
  再実行しない。本 wave は新しい gate の新設を避けて schema 内で閉じたが、境界で producer と
  同じ validator を通す案は残る。
