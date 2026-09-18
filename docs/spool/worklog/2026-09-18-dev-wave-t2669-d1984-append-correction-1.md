---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2669-d1984-append-correction
seq: 1
title: [T-2669] D1984 の却下欄「二読 fallback の択一は未裁定」を D1872 裁定済み (実装 entry 1594) の追記で訂正する D を起草した — 決定の効力は維持、新たな択一は起こさない (docs のみ、branch worktree-dev-wave-t2669-d1984-append-correction、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2669] (P2、entry 1596、D2104 項 18 で裁定済み) docs/decisions.md D1984 の却下欄にある『二読 fallback
  の択一は未裁定』を、D1872 で裁定済み (実装は entry 1594 で着地) である旨の追記で訂正する。canonical は直接編集せず
  docs/spool/README.md の形式で decisions fragment (追補)
  を書く。既存裁定の訂正記録に限り、新たな択一の再審議へ広げない。docs のみ、実装面差分ゼロ。着手直前の local main から fresh
  worktree。本題の追記だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。」(折返しは依頼原文のまま)。
- **閉じた (D 1 本 = {{D:d1984-rejection-reason-superseded-by-d1872}})。** canonical 3 台帳は 1 byte も触っていない
  (fold が末尾へ追記する)。実装面ゼロ、insight は作らず (実測値なし)。
- 一次資料の鎖を親が現物で確認した: D1872 (2026-09-09、択 (ii) = v2 fallback 廃止・exact 必須) → D1984 (2026-09-14、
  却下欄 3 項目目「二読 fallback の択一は未裁定」) → entry 1594 (2026-09-17、T-2067 実装着地、D2102 が同じ不整合を認識し
  D1872 を裁定済みとして扱った) → entry 1596 (第 20 回 /rulings、起点) → D2104 項 18 (a)。訂正対象は却下欄の逐語 1 項目に
  限り、D1984 の決定文 (「未配線 2 群の扱いも変えない」は事実認識の誤りではない) と D1872 の決定内容には触れない。
  D2102 と同じく caller 閉包メタテストの不採用を維持し、却下欄の事実認識だけを訂正する、と D に明記した。
- 軽量版 (docs-only)。段 2・3 省略 (択は D2104 項 18 で尽き、残るのは既裁定の転記)。実装子なし。段 6 相当として
  read-only codex レビュー 1 本 (`gpt-6-astra` / medium、一次資料照合 + 過剰・削除の 2 レンズを 1 本で担う、4 call、
  171 秒) を回した — **初回 NO-GO**: must-fix 4 (親の (P2) 「却下欄の結論は主決定に含意される」は D1984 の主決定が
  名指すメタテスト 1 種を超える一般化 → 「メタテスト不採用を D2102 と同じく維持し、事実認識だけを訂正、期待値の固定に
  新判断を加えない」へ置換 / D1984・D1872 の引用が文末「。」を落としていた / レビュー結果の placeholder が本文に残って
  いた / ユーザー依頼の逐語の出所が射影に無かった → job dir `verbatim/request.md` に逐語を出した)、should 0、nit 0。
  写し 10 件・D 番号 9 種・項番号 3 件・日付 3 件と「5 日」・entry 1594 と archive path・先例 2 件・「推奨通りで」は
  全件一致。(P1) (新 D として末尾着地) は妥当と判定。fix 後の焦点再レビュー (同 model / medium、1 本) は **NO-GO**:
  所見 1 は closed、所見 2・3・4 は partial (D1984 引用の改行・字下げが原文と違う / 依頼引用の末尾「。」欠落 / worklog が
  「fix 後 GO 相当」と先取り)。2 巡目 fix で D1984 引用を blockquote の list 形にして原文の改行・2 空白字下げまで
  再現し、句点を復元し、本行を経過どおりに改めた。残件は文字列一致だけなので 3 巡目の codex は投げず、親が
  canonical bytes との機械照合 (引用 2 箇所 = D1984 却下欄 3 項目目・D1872 決定文、依頼引用 = `verbatim/request.md`。
  正規化は入れ子括弧『』→「」と折返しの除去だけ、script は job dir の `verify_quotes.py`、結果 ALL-MATCH) で一致を確かめて
  閉じた。dev-wave 改善候補 1 (`tools/dev_wave_submodule_init.py` が高負荷時に内側 30 秒 deadline で rc=1
  `runtime-io-failure kind=update-no-fetch` を返し、同じ argv の再走で入れ子 googletest まで揃った) → 不採用: 実害なし
  (再走 1 回) で、収容先の `DW-C01` は exact pin 節のため Codex author + fixture placeholder を要し費用対効果が合わない。
  本行の記録に留める。
- 検査: `tools/check_docs.py`、`spool_fold.py --dry-run`、`git diff --check`、provenance 監査。受入全走は land 前に 1 回
  (結果は land の受領証)。

## 次の一手差分

### 完了

- [T-2669] D1984 の却下欄の誤記を {{D:d1984-rejection-reason-superseded-by-d1872}} の追記で訂正した (決定の効力は維持)。
  remaining: none
  base: e3cdc52d04f331c0a42d6b3d91b7e92b7d6237835e50313b03025db05e5b99e2
