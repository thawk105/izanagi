---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2761-handshake-check
seq: 3
---

## 再発

### F50

- **再発: 2026-09-17** — [T-2761] wave (背景 job + worktree 隔離) で、段 1 の条件 dispatch 判定を「既存 assert の置換だから
  `DW-O13` (gate・検証の新設) は非成立」と参照節の本文を読まずに行った。`DW-O13` の 2 文目「既存 exact 述語の改訂で受理形を
  増やす場合も新設に当たる」に該当していた (path に `release` を含む script を新たに受理する) ことに、段 3 の敵対相談 2 本を
  終えてから気づいた。最遅読了段 (段 2 プラン前) を過ぎていたので読み込み契約どおり段 2 の成果物を invalidate し、brief を
  DW-O13 の要求 (入力 field の所在・実環境の値域・到達可能性) で改訂して plan / consult を再実行した (codex 3 本分の再投入、
  実害なし。v1 の所見は v2 brief の provisional 裁定へ取り込んだ)。2026-08-21 の再発と同じ `DW-O13` の判定漏れで、
  前回は巻き戻さなかったが今回は契約どおり巻き戻した。根本原因は同じ — 条件表の「可能性が生じた時点」を、参照節の
  冒頭 2 文を読んで判定していない。

## supersede 追記

- F1022 **supersede: 2026-09-17** — 恒久対応の test 側是正は [T-2761] (commit 6dcbf6113、{{D:path-independent-word-absence-check}}) で着地した。6 つの環境依存の埋込み値を位置限定で token 化し、正規化後の本文の release 候補行を全件拒否する形にしたので、暫定防壁 (wave の slug / branch / worktree 名に `release` を含めない) は不要になった。`"while" not in script` の同型偽赤は scope 外で残る (release 専用の防壁だけが不要)。
