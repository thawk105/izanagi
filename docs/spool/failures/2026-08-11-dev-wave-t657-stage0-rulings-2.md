---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t657-stage0-rulings
seq: 2
---

## 新規

### {{F:design-literal-hidden-in-html-comment}}. 設計文書の literal を検査値と束縛する gate が、HTML comment に隠した旧 literal を権威として読んだ [恒真ゲート]

- 事象: 設計正本の表から literal を抽出して検査側 enum と exact 照合する gate を新設した直後、
  段 6 の敵対レビューが「旧行を HTML comment の中へ移し、可視部分だけ書き換えると素通りする」
  構成を作った。抽出器は raw text を読むため、可視の設計と機械が読む値が分離する。
- 根本原因: **文書を「人が読む可視部分」と同一視したが、抽出器は可視性を判定していなかった。**
  さらに 1 巡目の fix (comment を除去して可視部分だけ読む) は、Markdown の文脈を見ないため
  code fence 内の `<!--` と fence 外の `-->` が対になり、その間の可視 drift 行ごと消えた。
  **fix 前に拒否された文書が受理される**新しい抜け道を作っており、焦点再レビューが構成した。
- 恒久対応: `orchestrator/tests/calibration_freeze_authority_contract.py` の `_read_design` が、
  設計正本に `<!--` または `-->` が 1 つでもあれば `ContractError` にする (除去はしない)。
  除去は「どこまでが comment か」の判定自体が攻撃面になるため、存在の拒否で 1 述語に閉じる。
- 再発検知: `test_design_literals_hidden_in_html_comment_are_not_authoritative`
  (comment にだけ canonical literal を残し、可視側を Markdown 表として一致しない形式にした文書を
  拒否する)。同検査の無効化を変異 M7 が KILLED で裏取り済み。

### {{F:mutation-spec-renumbered-after-preregistration}}. 段 4 で事前登録した変異 ID 体系を、親が実行直前に組み替えた [手順漏れ]

- 事象: 段 4 の裁定で M1〜M6 を事前登録したのに、親が実行用 spec を書く段で 1 件を落とし、
  残りを M1〜M5 へ改番した。段 6 の敵対レビューが「spec と事前登録が別物である」と検出した。
  母数が 6 から 5 へ変わり、wave 前の実コード形を一度も検査せずに「全登録変異を処理済み」と
  受理できる状態だった。
- 根本原因: 実測で期待 (SURVIVED) が誤りと分かった変異を、**erratum を書かずに差し替えた。**
  事前登録は「後から都合よく変えない」ためにあるという目的を、親自身が手段として扱った。
- 恒久対応: `DW-M02` の erratum 規律を親の手順にも適用する — 期待が実測と食い違ったときは
  ID を保ったまま期待を改め、初回の登録内容と実測の差を worklog エントリに残す。
  本 wave では M1〜M6 の番号を復元し、M3 の `SURVIVED` → `KILLED` を worklog へ erratum として
  記録した (`docs/spool/worklog/2026-08-11-dev-wave-t657-stage0-rulings-1.md`)。
- 再発検知: 段 6 の敵対レビューへ「事前登録と実 spec の一致」を観点として渡す
  (本 wave はこれで検出した)。
