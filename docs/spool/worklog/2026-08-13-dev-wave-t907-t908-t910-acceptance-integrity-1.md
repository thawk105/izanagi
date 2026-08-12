---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t907-t908-t910-acceptance-integrity
seq: 1
title: 受入 integrity 3 件を実装した — 待ち手 receipt を land の必須入力にし、走行後 fingerprint と untracked 検査を足し、floor staging の追跡境界を裁定どおりに引いた (コード + docs、branch worktree-dev-wave-t907-t908-t910-acceptance-integrity)
---

## 本文

- **裁定の脅威モデルを段 4 で確定した。** [T-908] の起票理由は「2026-08-12 に待ち手を迂回して
  直接走した実例」であり、防ぐ対象は**事故**であって同一 Unix user による意図的偽造ではない。
  段 2 プラン自身も「receipt は同一 user に対する暗号学的 attest ではない」と認めた。
  この線引きを基準に敵対レビューの所見を裁き、**偽造対策にしか効かない機構は scope 外**として
  裁定パッケージへ返した (実装済みと書かない)。詳細は {{D:acceptance-authority-threat-model}}。
- **親裁定 1 件で段 2 プランを覆した。** プランは receipt 検証を `_locked_preflight` の前に
  置けと書いたが、既存の provenance 期待値 (rc 29) と両立しなかった。fix 子は規律どおり
  実装を変えず報告して停止した。親は「守るべきは receipt 無しに main を進めず成功も返さない
  ことだけで、provenance との前後関係は要求ではない」と裁定し、順序だけを緩めた。
  安全性はコードで確認した — `_verify_acceptance_receipt` は `tools/dev_wave_land.py:2525`、
  成功を返す全経路 (already-landed 2 箇所、ff-only merge、`_postcondition` の landed) は
  すべてその後で、`_locked_preflight` は拒否用 `LandResult` しか返さない。
- **敵対レビュー 2 本が blocker 5 件・must-fix 6 件を出し、real 分をすべて処理した。**
  採用したのは orphan temp receipt の land 拒否、`held-self → acquired` の ownership 遷移漏れ
  による lease 漏れ、submodule 未初期化の claim 前 fail-closed、TTL 再確認後の publish 窓の閉鎖、
  `PYTEST_ADDOPTS` 等による無実走 receipt の封鎖、`assume-unchanged` / `skip-worktree` への
  盲目の解消。refuted は 1 件 (receipt 検証順序、上記)。
- **変異が実在の検出力の穴を 1 件実証した。** 1 巡目 (baseline PASSED) で
  `--acceptance-receipt` を `required=False` にする変異が **SURVIVED** した。
  CLI テストが新 2 引数を両方省いており、`--acceptance-wave` の argparse rc=2 が先取りしていた。
  これはレビュー B が所見 RB5 で予告した穴そのもので、fix 3 巡目の再照準後もまだ開いていた。
  1 引数ずつ欠落させる形へ直して 2 巡目で KILLED になった。
- **変異 2 巡目 = baseline PASSED、10/10 KILLED、SURVIVED 0 / MISMATCH 0** (anchor `bb4767d3`)。
  ただし **M02 / M03 / M05 の失敗集合は 112 / 28 / 97 件と大きく、fake の event 列不一致が
  支配している。** これらは「その定数・呼び出しが load-bearing である」ことは示すが、
  「受理集合が期待方向へ変わった」ことの単一理由の証拠にはならない (`DW-M03` の冗長 gate 扱い)。
  **単一理由で検証できたのは M01 / M04 / M06 / M07 / M08 / M09 / M10 の 7 件。**
- **1 巡目の baseline は [T-892] の既知赤で FAILED になり、harness が production write を
  開始しなかった。** [T-892] の起票文が予告した事象そのものである。10 変異のいずれとも
  無関係な環境由来の赤なので、その 1 nodeid だけを `--deselect` して再走した
  (除外は 1 件のみ・期待 node と重複なし)。
- **`docs/dev-wave/**` は land の receipt 契約を収容できなかった。** 実測: `DW-O23` (L1) へ
  最小 3 行を足すと予算を 229 bytes 超過、`DW-O25` (L2) は exact 契約で pin 済み・単節上限
  1,000 に対し 1,462 bytes、新規 L2 節は entry の条件表に参照が要るが
  `.claude/commands/dev-wave.md` は 9,500 bytes ちょうどで**余白 0**。
  ユーザーの既裁定に従い上限は上げず、運用の正本である `docs/pegasus-runbook.md` §7.3 だけを
  更新した。`DW-O23` 側の欠落で起きるのは rc=2 の明示的な失敗であって静かな誤結果ではない。
  収容先は {{T:dev-wave-docs-land-receipt-contract}} へ起票した。
- **`tools/dev_wave_wait.py producer` の fail-open を 4 回実測した。** 投入直後に張った
  待ち手が、`.done` も成果物も無く producer が生存しているのに出力ゼロ・rc=0 で即座に返る
  (02:44 / 03:12 / 03:55 / 03:58 JST)。毎回「成果物実在 + `.done` + producer 死」の 3 点照合で
  検知して張り直したため進行には影響しなかったが、これは本 wave の主題 (受入 gate の
  fail-closed 化) と同型の欠陥である。{{T:waiter-producer-completion-fail-open}} へ起票した。
- **段 5 の子が 1 本 model call 上限 (既定 100) で SIGTERM され、完了報告を残さず落ちた。**
  単位 2 は待ち手 +503 / land +259 / テスト +1,189 行の規模だった。単位 1 を commit せずに
  単位 2 を積んだため、同じ未 commit 差分に両者が混ざって切り分け不能になった。
  snapshot patch (110,577 bytes) で保全し、継続 fix 子で完遂した。
- **検査結果。** 焦点走 269 passed / 1 failed (`test_exploration_external_root_keeps_wave_clean`
  = [T-892]、焦点走限定・本差分と無関係)。provenance 全史監査 3,074 件・新規違反なし。
  `check_docs` 違反なし。

## 次の一手差分

### 完了

- [T-907] 受入 command の走行後に `postrun-clean` / index flag 検査 / 走行前後の tree
  fingerprint 比較を足した。child rc が非 0 でも必ず走り、木が変わっていれば rc=70 が
  child rc に優先する。fingerprint は HEAD SHA / clean status / binary diff / recursive
  submodule status を label と byte 長つきで SHA-256 に入れた自己完結実装。
  remaining: none
  base: 7ba4fc1d1aa5a91a7e70e6d2ce8c1ea7bbb1861bd1c1fb7c5002aa07a711fb90
- [T-908] 待ち手経由だけを権威ある dev-wave 受入と定義した。待ち手が repo 外へ closed JSON の
  receipt を発行し、`tools/dev_wave_land.py` が必須 consumer として検証する。欠落・不正・
  予約 temp 名前空間・束縛不一致は rc=23 で main を 1 bit も変えず拒否し、`already-landed` も
  通さない。逃がし道は作っていない。`run_tests.py` 側への同等 gate は裁定どおり不実装。
  remaining: none
  base: 2669abec60592af887e3f817cc40a267349f1a2c3b81b86dddb64a063679e8f2
- [T-910] `output/env/pegasus/floor/job-staging/` を ignore し 88 file を index から外した
  (disk bytes は全 file sha256 一致で保持)。`attempts/submissions/` の 51 file は tracked のまま
  (index は byte 単位で不変)。受入の clean 述語を `--untracked-files=all` へ強めた。
  remaining: none
  base: ad682e9c86434ff627c7b8085c31098a7f5a5526d3b033efda35492bdf7b7e76

### 更新

- [T-892] **P3・優先度を上げる (2026-08-13 実測)**: 本 wave の変異 1 巡目で、
  この赤が **baseline を FAILED にして harness の production write を止めた**。
  起票文が予告した「変異 harness の baseline が緑にならず部分集合の変異検査が原理的に
  回せない」が実際に発火した。回避には当該 nodeid の `--deselect` が要る。
  base: 36552692c4d9ef25f8d79a7510a198fa85ae8ffafa8e72bea5739b12b1bad8f5

### 新規

- {{T:waiter-producer-completion-fail-open}} **P2・新規**: `tools/dev_wave_wait.py producer` が、
  `.done` も成果物も存在せず producer が生存している状態で、出力ゼロ・rc=0 で即座に返る
  ことがある。2026-08-13 に 4 回実測 (02:44 / 03:12 / 03:55 / 03:58 JST)。
  親が 3 点照合 (成果物実在 + `.done` + producer 死) で検知して張り直したため実害は出ていないが、
  待ち手を信じる呼び手は「子が成功した」と誤認する。成果物影響 = 子の成果物なしで次段へ進み、
  context 無しの出力をレビュー結果と数える経路が開く。
- {{T:dev-wave-docs-land-receipt-contract}} **P3・新規**: [T-908] の land 契約
  (必須 2 引数・rc=23・`already-landed` も通さない・逃がし道なし) を `docs/dev-wave/**` へ
  収容できなかった。実測は本文のとおりで、L1 は 229 bytes 超過、L2 の `DW-O25` は exact pin +
  単節上限、新規 L2 節は command の余白 0 で参照を足せない。予算は上げない方針なので、
  収容先の設計 (どの節を縮約するか / L2 の節分割をどう変えるか) を別途裁定する。
  成果物影響 = 未収容のままだと、runbook を読まない land 呼び手が rc=2 の理由を辿れない。
- {{T:mutation-fake-event-overdetermination}} **P3・新規**: `test_dev_wave_wait.py` の
  fake effects は期待 event 列を固定するため、共有定数や共通呼び出しを変異させると
  失敗集合が 100 件級に膨張し、変異の帰属が単一理由にならない (本 wave の M02 / M03 / M05 で
  112 / 28 / 97 件を実測)。実 Git を使う negative test へ再照準する形が要る。
  成果物影響 = 変異 matrix が KILLED を報告しても、その gate の実効検出力を証明できない。
