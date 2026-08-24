---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t319-official-marker-allowlist
seq: 1
title: [T-319] official report の root namespace marker を allowlist 必須化する (コード + docs、branch worktree-dev-wave-t319-official-marker-allowlist)
---

## 本文

- ユーザー裁定 2026-08-23 の択 (a) に従って実装した。D65 P-A1(a) Stage 1 が個別承認を要求する
  範囲であり、設計の中身は {{D:official-root-marker-allowlist}} に置いた。
- **採用しなかった所見。** 段 3 と段 6 の敵対レンズが挙げた次は real と認めたうえで実装しなかった。
  (a) 相対 path の一般受理追加 — production の resolver が絶対 path と生の親参照の拒否を既存契約に
  持つため、canonical な相対形だけを exact 例外として絶対化し他は従来どおり拒否する。
  (b) 生の親参照に関する回帰所見 — 前 wave が採用した lexical component / symlink 拒否と
  external resolver の既存署名に必要で、同じ境界の内側にある。
  (c) 歴史的 report 52 path の保存則 baseline — real だが scope 外。本 wave の主張は root の
  namespace 資格であって report inventory の保存則ではない。
- **反証した所見。** blocklist 負例の不足は refuted (欠落・exploration・unknown・malformed・
  空白・改行欠落・遠い非 official 祖先 + 局所 official root が実在する)。canonical な symlink
  alias の扱いも refuted (root alias は lexical component 検査が明示的に拒否する既存テストがある)。
  外部 admission を通して FIFO 負例を届かせる案も refuted で、FIFO テストは production の
  scan seam を直接呼ぶ形へ再照準した。
- **変異 matrix。** 実装 tip の固定 clone で再走し、baseline 19 passed、事前登録した M1〜M12 が
  12/12 KILLED、SURVIVED / MISMATCH / TIMEOUT はいずれも 0 だった。marker leaf の
  非ブロッキング拒否を落とす変異は hang リスクがあるため timeout で隔離して数えた。
- **焦点再レビュー。** fix 後の 2 本目が GO、must-fix 0、regressed 0 (closed 12 / partial 4)。
  partial は最終受入と記録の証拠項目だけである。関連 5 file の焦点走は計算ノードで
  945 passed / 8 skipped。
- **段 6 受入の消費。** 全走を 2 本失った。1 本目は待ち手が自分で main を merge した結果、
  実行中の待ち手 bytes が merge 後の tree と食い違い `restart-required` で receipt 未発行に
  なった ({{F:acceptance-self-merge-rewrites-running-waiter}})。2 本目は親が走行中に記録
  fragment を worktree へ書いたため走行後 clean 検査が rc=70 で止めた (F106 の 9 度目)。
  2 本目の suite 自体は `1 failed / 15068 passed / 60 skipped` まで到達しており、唯一の赤は
  本 wave の所有面ではない dispatch の control lock テストだった。単独再走は 13.46 秒で緑、
  失敗は `join(10)` 後の thread 生存表明で、両 dispatch 側は receipt を rc=0 で書き終えていた。
  共有ノードの過負荷による timing 由来と読み、本 wave の差分へ帰属しない。
  最終受入は記録と段 8 を commit し終えた tip に対して投入する。
- **工数。** Codex 子の受領証は 20 本、model call 合計 424、入力 38,668,770 tokens、
  出力 330,893 tokens。非 0 終了は 1 本だけで、焦点子が出力 0 byte で戻ったもの (不採用、再投入した)。
  wave は 3 つの context にまたがった (初回 + resume 2 回) が、実装面の 8 path は
  変異と焦点レビューを通した tip から 1 byte も動いていない。

## 次の一手差分

### 完了

- [T-319] official report の root namespace 判定を allowlist 必須化し、祖先 marker の全走査、
  marker leaf の有界 nofollow read、canonical root の exact 例外、観測前後の再検査を実装した。
  canonical root へ移行 marker を 1 件だけ追加し、既存成果物の bytes は変更していない。
  producer 側の marker-first 化は本項の範囲外として未実装のまま残す。
  remaining: none
  base: 40c7963a0fab4e397cb8dce213c630f55cec53d998e7f74a691fb609388a26ee

### 新規

- {{T:acceptance-bound-executable-main-takein}} **P2・新規**: 受入投入前に `HEAD..main` が
  束縛対象の実行体 (待ち手・launcher・runner) の bytes を変えるかを検査し、変えるなら先に
  wave tip へ取り込む前提条件を `DW-O18` / `DW-O27` と subprocess test へ同期する。
  現状は待ち手が自分で main を取り込む活性経路だけがあり、その差分が待ち手自身を書き換えると
  全走 1 本が receipt 未発行で失われる。
