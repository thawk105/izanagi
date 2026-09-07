---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2353-terminal-stage
seq: 1
title: [T-2353] 8c formal consumer の terminal 検査を production の stage 形状へ直した — accepted 側は FC07 を通り、rejected 側は producer 不在で止まったまま (コード + docs + insight、branch worktree-dev-wave-t2353-terminal-stage、変異 4/4 KILLED + 登録 SURVIVED 1)
---

## 本文

- **依頼は D1665 が別 carry として残した terminal 側の食い違いの修理で、読み手だけを直す。**
  ユーザーは「規律 2 を緩めない。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は
  scope 外」と scope を固定した。設計判断は {{D:formal-consumer-terminal-stage-shape}}、
  成果物は `output/insights/2026-09-07_t2353-formal-consumer-terminal-stage/`。
- **親の初回 pin 閉包が漏れており、段 2 と段 3 の 2 レンズが独立に検出した。** 親は対象 3 file 自身への
  path 参照と hex literal を引いて「pin なし」と結論したが、fixture 生成器の**出力**を固定する
  凍結 snapshot と golden literal 7 個が実在した。親はこれを scope に入れて裁定し、pin 値は
  段 2 / 段 3 が提示した値をコピーさせず、実装子に変更後の実物から再計算させた。
  near miss は {{F:generator-output-pin-closure}}。
- **段 6 の敵対レビュー 2 本は must-fix 0 件。** 両レンズとも、新しい負例が手前の判定で落ちていないこと、
  新しい正例が commit 枝を通過してから終端へ至ることを、判定順を辿って個別に否定した。
- **両段が real と認めた scope 外の所見 1 件は裁定パッケージへ送る (下記 新規)。** terminal record の
  外枠・重複・root shadow は閉じておらず production 形状でない flat record も通るが、
  **本 wave が新たに広げた受理集合ではない** — 同じ緩さは修理前の形にも同じだけあった。
- **変異の probe 段が静的予測の漏れを暴いた。** 段 6 レンズ B は M2 の kill 集合を 14 node と予測したが
  実測は 15 node だった。予測だけで期待 node を登録していたら本走が完全一致に届かなかった。
  登録 SURVIVED の M5 は、terminal の外枠が pin されていないことを実測で示す。
- **段 5 の実装子は sandbox から pytest を起動できず (dispatch rc=16、child 未起動)、
  自分の実装を「実装済み・未実走」と正しく申告した。** 実走はすべて親が行った。
- 子は codex 6 本 (plan 1、consult 2、author 1、review 2)。いずれも同一構成で、
  親は Claude で管理と統合を担った。

## 次の一手差分

### 完了

- [T-2353] consumer の FC07 terminal 検査を production の `stage` 形状へ直し、fixture と既存 pin を
  同期した。焦点走 11 file が緑、変異は登録どおり。
  remaining: none
  base: eaa7e6f4cf7a57f5964b2aa580aa65fdbb7e33007b871758b932dcb17e7814ed

### 新規

- {{T:formal-consumer-terminal-outer-shape}} **P2・ユーザー裁定待ち**: 8c formal consumer の
  terminal record の外枠 key 集合・値の型・重複・root shadow を、D1665 が trigger 側へ入れたのと同じ
  exact gate で閉じるか。段 3 と段 6 の 4 レンズすべてが real と認め、段 3 の両レンズは拡張を推奨した。
  変異 B-057-M5 が生存したことで、外枠が pin されていないことは実測済み。**本 wave が広げた緩さではなく、
  修理前から同じだけあった**ので、放置は現状維持である。閉じる場合は FC07 の受理集合が変わるため
  ユーザー裁定が要る。
- {{T:formal-consumer-abort-witness-producer}} **P2・新規**: 8c formal consumer が rejected 側で
  要求する `candidate_attributable` / `truncated` / `witness_class_sha256s` には production producer が
  無く、terminal 修理の後も rejected の本番 projection は FC07 で止まる。`reflux_source_closure.py` の
  token 表は `wal.abort.payload.witnesses` という別名を挙げており、consumer が読む名前とも一致しない。
  producer 側を書くのか、consumer の要求を実在の field へ合わせるのかを決める。
