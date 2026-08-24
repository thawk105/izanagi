---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-paper-story-a1-paired-20260824
seq: 3
title: paper-story A-1 の同一 campaign 内対測定を実施し、5 点では差を判別できないことを実測した (コード + 計測、branch worktree-dev-wave-paper-story-a1-paired-20260824)
---

## 本文

- 中断 wave の再開だった。前 handoff は段 6 fix の Codex 利用上限で凍結されており、その後に
  実行された fix 6 回と焦点走 1 回を反映していなかった。job dir の mtime と handoff の最終更新の
  乖離で気づき、6 回分の作業を捨てずに済んだ。再開時に両者を照合する運用が要る。
- 段 6 は fix 16 巡を要した。内訳は敵対レビュー由来 3 巡 ({{F:mutation-found-vacuous-guarantees}} の
  是正を含む) と、親の実機投入が見つけた blocker 由来 13 巡である。後者の大半は
  {{F:nqsv-assumed-as-pbspro}} と {{F:env-capability-assumed-present}} に整理した。
- **ユーザー裁定 (批准)**: `hooks/enforcement-source-closure-ratifications.v1.jsonl` が全 branch の
  全履歴を通じて未作成で、`run_campaign` が `enforcement-source-closure-unratified` で
  fail-closed していた (F498 が記録した 2026-08-18 以降の gap)。D526 により AI からの追記手段は
  存在しないため、親は迂回も代替経路の実装もせずユーザー裁定へ戻した。ユーザーが批准行を
  実行して開設し (digest `db511c3d...`)、親は git 操作の機械的代行だけを行って
  `AI-Agent: none` で commit した。この解消は A-1 に閉じず、以後の official 新規 campaign 全体に
  効く。批准は closure 版ごとにしか効かないため、25 path が動けば再び塞がる。
- **棄却した finding**: 焦点再レビュー第 2 巡が must-fix とした「durable path の TOCTOU」は、
  同一 UID の能動的な別 process という攻撃者モデルを要する。その権限があれば receipt も result も
  tracked 成果物も書き換えられるので、dirfd 化で閉じたとは言えない。研究プロトタイプとして
  全面的な防御実装は採らず、`st_dev` / `st_ino` の inode 束縛による取り違え検出へ縮小した。
  残る能動的 race は refuted として本項に根拠を残す。同レビューの「materializer が qstat を
  照会して終端を確認する」案も棄却した。NQSV は終了した request を qstat から落とすため、
  照会成功を必須にすると正当な走行が scheduler の応答時期に依存して invalid になる。
- **削除されたテストの裁定**: fix が `test_acquisition_receipt_rejects_scr` を削除した件は、
  後退ではないと裁定した。policy 固定の durable base 自体が `/scr` 外であり attempt はその直下しか
  通らないため、`_under_scr` は到達しない二重防護である。production 側の判定は残している。
- **子の実走不能**: codex 実装子は sandbox から scheduler へ到達できず、全 16 巡を通じて
  `tools/run_tests.py` を 1 件も実走できなかった (`qstat -Q` が `EACCTAUTH`)。全巡で子は
  「実装済み・未実走」と申告し、緑の判定はすべて親の焦点走 17 回で行った。
- **子の推測が空回りした区間**: 第 12 巡と第 13 巡は「実形へ合わせろ」とだけ指示したため、子が
  fixture を推測で作り替えて赤が 19 件から 20 件へ増え、混入 error が入れ替わっただけだった。
  親が実 producer の構造 (attempt 階層、lock の top-level 3 key、`identity_preimage` が dict では
  なく文字列、実 run argv 9 token) を実測して prompt へ一次資料として貼った第 14 巡で緑になった。
  実機の構造を親が測って渡す方が、子に探させるより速い。
- **セッション異常**: 背景 Bash の待ち手が 3 回、子の生存中に無言で rc=0 終了した。完了と誤認せず
  実態を測って気づいた。以降は detach + `.done` file 方式へ統一し、待ちは pid と `.done` の
  until ループで行った。
- 変異は probe 3 巡 (生存 6 → 2 → 0) の後、本走で 23 件全件が事前登録 node と完全一致して KILLED。
  SURVIVED と MISMATCH はいずれも 0。
- 計測は 4 回成功した。**5 点の位置対応差では両 arm の差を判別できない。** 正式値 (attempt-0010) は
  write-heavy が平均 -5698 / SD 43649、balanced が +70801 / SD 66139、read-heavy が +5611 / SD 25453。
  同一実装・同一 workload の直前 2 走で write-heavy は +11480、-4144 と符号が反転し、balanced は
  +22489、+2571 と動いた。符号すら安定しない。差が無い証拠ではなく、この試行数では語れないという
  記述である。段 4 裁定どおり因果・有意差・母平均・信頼区間・再現性は主張しない。

## 次の一手差分

### 新規

- {{T:a1-paired-more-reps}} **P2・新規**: A-1 の対測定を、差を判別できる試行数へ引き上げて再実施する。
  5 点では標本 SD が平均差と同程度以上で符号も安定しないことが実測で判明した。必要反復数を
  現行の分散から見積もり、事前登録したうえで実施する。exploratory のまま混合せず、
  D510 決定 7 に従って本 wave の結果を再解釈しない。
- {{T:enforcement-closure-ratification-runbook}} **P2・新規**: enforcement-source closure の批准を
  運用手順として整える。批准は closure 版ごとにしか効かず、25 path のいずれかが動けば再び塞がる。
  計測を伴う wave が段 1 brief で台帳の現況を確認し、必要なら人間へ 1 操作で依頼できる導線を
  用意する。AI が批准を代行しない境界は維持する。
