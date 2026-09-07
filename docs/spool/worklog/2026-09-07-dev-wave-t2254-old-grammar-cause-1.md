---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2254-old-grammar-cause
seq: 1
title: [T-2254] 旧 grammar が受入全走の失敗原因であることを現行コードで再現した — 3 案の提示と選択は 2026-09-03 に済んでおり、main に着地しているのは却下された側の案だった (docs のみ、branch worktree-dev-wave-t2254-old-grammar-cause、実装面の差分ゼロ)
---

## 本文

- **依頼が求めた実測は済んでいた。** [T-2254] は D1550 が立てた「旧 grammar が受入全走の
  失敗原因であることを実測し、確定したら 3 案を再提示する」項だが、その実測は 2026-09-05 の
  [T-733] wave が完了させており (受入全走 `1 failed / 19869 passed / 92 skipped`)、
  **3 案の提示と選択も D1563 (2026-09-03、ユーザー裁定) で済んでいた。**
  D1563 が選んだのは「新閉包で発行し直す」で、版付き decoder は明示的に却下されている。
- **にもかかわらず、main に着地しているのは却下された側の案である。** D1653 (2026-09-05) は
  **親裁定**として歴史閲覧限定 decoder を採り、`da44dc7b1` で着地した。同 commit は
  `refs/heads/main` の祖先である。D1653 は本文中で D1563 を一度も引用していない。
  D1563 が命じた発行し直しは実施されていない。
- **本 wave は原因を現行コードで独立に再現した。** 焦点は
  `orchestrator/tests/test_plot_b10_extended_backoff.py`。baseline (現行 main) は
  `10 passed`、歴史 decoder の入口を通常 decoder へ戻した対照は `1 failed, 9 passed` で、
  赤は 2026-09-05 の全走で唯一赤だった test と同一だった。内因は
  `campaign_lock.py:337` の `authority.contract_loader_blob_sha256s の exact key 集合が不正`。
  一時変異は 1 行で、走行後ただちに復元し bytes 一致を確認した。
- **対照は 2 回作った。** 1 回目 (`if False and ...` で共有 helper の分岐を無効化) は
  段 3 のレンズ B に「seam より広い」と指摘された。焦点の呼び出し 1 箇所だけを
  `da44dc7b1^` と byte 一致させた 2 回目を追加で実測し、同じ結果を得た。
- **旧 grammar の lock は、走査した 2 root で 13 件だった。** key の個数ではなく
  並び順込みの完全一致で分類し直した (レンズ B の指摘)。B10 格子 3 件と
  paper-story A-2 認証 10 件。2026-09-07 の A-2 新規 2 件だけが現行 exact-62 である。
  D1563 が書いた 11 件は 2026-09-03 時点の数。
- **親の読みを段 3 が 1 件訂正した。** 親は「親裁定がユーザー裁定を覆したまま」とだけ書いたが、
  ユーザーは 2026-09-07 に D1669 と D1680 の 2 件で D1653 の条件を先例として使っている。
  どちらも D1563 との衝突を認識したうえでの追認ではないが、伏せてはならない事実である。
  親が一次資料で裏を取ったうえで採った。
- **技術的にはどちらが正しいかも段 3 が裁定した。** D1563 の「束縛は内容ハッシュなので
  同じ内容へ再発行できる」は不十分で、lock が WAL より前に live capture される以上、
  測定後に blob hash を計算しても「測定時に一致した」という時間付きの事実は復元できない。
  この点は D1653 が正しい。一方 D1653 の「再発行は規律 7 に反する」という表現は広すぎる。
- **carry 本文が事実と食い違っていた。** 「稼働 branch
  `worktree-dev-wave-t733-source-closure-transitive` の閉包拡張がこの件で着地できていない」は
  誤りで、同 branch は main の祖先、`git log --no-merges main..<branch>` は空である。
- **段取りを 1 つ誤った。** 段 2 の read-only 子が読んでいる worktree を、走行中に親が
  一時変異させた。結果として子の出力に汚染は無かったが運任せである。
- 工数: codex 子 3 本 (plan 1、consult 2)。実装子ゼロ。計算ノードの焦点走 3 回。
  一次資料は `output/insights/2026-09-07_t2254-old-grammar-cause/README.md`。

## 次の一手差分

### 完了

- [T-2254] 旧 grammar が原因であることを現行コードの対照で再現した。3 案の提示と選択は
  D1563 で済んでおり、本項の要求は満たされている。D1563 と D1653 の権威の衝突は
  別項へ移した。
  remaining: none
  base: deb252338cd3d5f23dceb762869320a30866fbd232d109a705808151f176dc14

### 新規

- {{T:old-grammar-ruling-conflict}} **P1・ユーザー裁定待ち**: 旧 grammar の campaign lock に
  ついて、ユーザー裁定 D1563 (新閉包で発行し直す) と、実装が着地している親裁定 D1653
  (歴史閲覧限定 decoder) が正反対を向いている。D1653 を明示的に追認して D1563 を supersede
  するか、D1653 の技術的指摘を承知のうえで D1563 を再確認するかを決める。3 案の再提示と
  各案の費用は `output/insights/2026-09-07_t2254-old-grammar-cause/README.md` §6。
  親は案を選ばない。
