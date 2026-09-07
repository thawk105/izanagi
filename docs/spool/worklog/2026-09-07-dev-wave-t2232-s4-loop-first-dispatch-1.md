---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2232-s4-loop-first-dispatch
seq: 1
title: 段 4 loop の Pegasus job body を初めて実際に投入した — 未実測だった reservation 束縛と claim root は通り、gflags 不在で止まった (実装面の差分ゼロ、branch worktree-dev-wave-t2232-s4-loop-first-dispatch)
---

## 本文

- 軽量版 dev-wave。一次資料は `output/insights/2026-09-07_t2232-s4-loop-first-dispatch/README.md`。
  実装面の差分ゼロのため変異 matrix は `DW-S04` により免除。受入全走は実施した。
- **依頼は着地済みの再実装だった。** 依頼本文「[T-2199] の残件 [T-2232] を実装する」に対し、
  [T-2232] は 2026-09-07 03:19 に main へ着地済み (entry (1286)、`main_after=1a820a913`、
  ancestry 実測)。依頼本文は land 自身の fold が書いた持ち越しである。再実装せず、
  同 entry が名指しする残件「初回投入と reservation / attestation の実効確認は後続 wave」へ
  `DW-S01` / F35 に従って繰り上げた。
- 投入した job は `981655.nqsv` (host `bnode116`、Elapse 9S、`driver_rc=1`)。
  投入形は `tools/pegasus/README.md` §7 の tagged qsub command のまま。
- **依頼本文が「未実測の障害として出うる」と名指ししていた 2 件は通った。**
  reservation 束縛は `qstat -f` から 8 変数すべてを組めた (`REQUESTED_S=10800`、
  `DEADLINE_EPOCH=1788798606`)。claim root の provisioning も通った。
  計算ノードの `python3.10` 実在、`/scr` の scratch、CCBench pin の exact 照合も通った。
- 止まったのは masstree の FetchContent 事前構築で、`Could NOT find gflags`。
  attestation の exact 照合には到達していない (driver 未起動)。
- 設計判断は {{D:s4-job-body-lacks-gflags-supply}}。gflags 不在は **F580 の再発**であり
  新規 F を採らない — F580 の再発検知「同種の既存 job body を 1 本名指しして、そこが行っていて
  自分が行っていない手順を段 1 brief で列挙する」が [T-2232] の wave で実行されていれば
  段 2 の時点で見えていた。手順書側の欠落は
  {{F:pegasus-submit-recipe-omits-submodule-pin}} として新規に採る。
- ユーザー裁定待ちを 2 件返す ({{T:s4-job-body-gflags-prologue}}、{{T:pegasus-readme-submodule-pin-step}})。
  いずれも段 1 brief で scope 外と凍結した「job body の機能追加」「本題の実装以外」に当たるため、
  本 wave では実装していない。
- 段 8 スキル自己改善: 新規候補なし。着地済みタスクの持ち越しを一次資料で照合する作法は
  既存の記憶と `DW-S01` に含まれており、今回それが実際に効いた。

## 次の一手差分

### 新規

- {{T:s4-job-body-gflags-prologue}} **P1・新規・ユーザー裁定待ち**: `p3_s4_loop_pegasus.sh` へ
  gflags/glog の供給経路を足す。計算ノードに gflags が無いため、現状の job body は masstree の
  FetchContent 事前構築で必ず止まる (2026-09-07 実測、job `981655.nqsv`)。
  兄弟 job body `tools/pegasus/floor_scoping.sh` の gflags/glog prologue が移植元で、
  policy の pin から `$TMPDIR` へ build / install し `CMAKE_PREFIX_PATH` を通す形である。
  供給元の 2 source は実在し pin と exact 一致し clean であることを実測済み。
  **純粋な移植ではなく設計択一が残るため裁定が要る** — policy 依存を新設してよいか、
  provenance file を記録するか、契約テスト 44 node と admission registry をどう同時更新するか、
  `CMAKE_PREFIX_PATH` を driver 本走まで持たせるか。
- {{T:pegasus-readme-submodule-pin-step}} **P2・新規・ユーザー裁定待ち**: `tools/pegasus/README.md`
  §7 の投入手順に「submodule を `p3_s4_loop.PIN` へ checkout する」を足す。
  現状の手順どおりに投入すると job body が rc=2 で必ず落ちる (main の gitlink `511c9538e` と
  PIN `028f34d` が不一致、後者は前者の祖先)。修正自体は数行だが、本題の実装外なので裁定へ送る。
