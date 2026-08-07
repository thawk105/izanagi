---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t618-provenance-known-ledger
seq: 1
title: [T-618] 既知違反台帳へ 3f2c43d7 を注記つきで追加し、既定監査を rc=0 にした — 手作業帰属が恒久解消 (コード + docs、branch worktree-dev-wave-t618-provenance-known-ledger)
---

## 本文

- **ユーザー裁定 (worklog 293、択 (b)) をそのまま実装した。** `3f2c43d7580b8c26724d90278589862057508965`
  を `KNOWN_PROVENANCE_VIOLATIONS` の 7 件目 (`missing-ai-agent`) として注記つきで追加した。
  履歴は書き換えていない。台帳 schema の変更は {{D:known-violation-note-field}}。
- **裁定の注記が一次資料と一致することを段 1 前に実測した。** `git log -1 --format='%(trailers)'` が
  返すのは `Co-Authored-By:` 行だけで、`AI-Agent:` 行は空行によって trailer block から切り離されている。
  一方その `AI-Agent:` 行の payload 自体は必須形式を満たす。**帰属の欠落ではなく書式の崩れ**という
  裁定の前提は成立した。段 3 レンズ 1 が独立に同じ検証を行い同じ結論を得た。
- **最も価値のあった所見は段 3 レンズ 2 の「rc=1 側だけ検証されない」だった。** 段 2 プランは注記の
  stdout を rc=0 側でしか pin しておらず、**rc=1 側の出力ループだけ旧 formatter のまま残しても
  計画どおりのテストが素通りする**穴があった。裁定で rc=1 合成テストを追加し、その穴を狙う変異 M3 を
  事前登録した。本走で M3 は新設テスト **1 本だけ**を赤にして KILLED になり、穴が実際に塞がったことを
  変異で裏取りできた。
- **改行拒否の contract とテストの食い違いも段 3 が捕らえた。** プランは「LF・CR・Unicode line
  separator を一括拒否」と書きながら LF 1 例しか pin していなかった。裁定で 5 case
  (`non-str` / LF / CR / CRLF / U+2028) の parametrize にし、変異 M5 (改行検査だけ削除) が
  改行 4 case だけを赤にし `non-str` は型検査に救われて緑のまま、という予測どおりの切れ方を実測した。
- **変異候補 2 件を事前登録から外した。** (a) 「型検査だけ削除」は `None.splitlines()` の
  `AttributeError` が `main()` の `except (OSError, RuntimeError, UnicodeError)` を素通りし、
  fail-closed のままで受理集合が変わらない (親が該当 except 節を実読して確認)。診断だけの赤は
  kill にしないため M4 へ吸収した。(b) 「stale raise 削除」は本 wave の差分でない既存層で、
  同じ層を 5 本の既存 node が要求するため本 wave の検出力を測らない。
- **段 3・段 6 の 4 本とも「entry 削除」変異の単独帰属を否定した。** 台帳 entry を消すと 4 経路が
  同時に不成立になる。単独帰属を主張せず integration 変異として期待 node 4 本を全列挙して登録し、
  本走の観測 node は 4 本ちょうどで一致した。
- **段 6 のレビュー 2 本は code の must-fix ゼロだった。** 裁定が固定した注記逐語・ruling・guard の
  predicate と位置、`_KNOWN_VIOLATION_RULING` と `_known_spec()` の未変更、既存 stdout テストの
  未変更を AST 比較で確認している。**所見ゼロは変異で裏取りするまで緑と数えない**規約に従い、
  変異 5 本を本走して 5/5 KILLED・観測 node が事前登録と完全一致を得てから閉じた。
- **scope 外に置いた real 所見 2 件はいずれも既起票だった。** [T-621] (自動 dev-wave 層が stdout を
  捨てて rc だけで pass を決めるため、既知 7 件と注記が試行台帳に残らない) と [T-619]
  (`--ancestry-path` の pre-policy branch merge 盲点)。前者があるため、**本 wave の受入証拠には
  自動 receipt を使わず、post-commit の権威 full 監査の生 stdout を採った。**
- **過去記録を supersede する。** worklog (289) の「7 件目は台帳に入れなかった / 既知 6・新規 1・rc=1
  のまま残る」と、`output/insights/2026-08-07_t614-known-violation-ledger/README.md` の同じ観測は
  **書き換えない**。worklog(293) の再裁定によって運用状態が置き換わったことを本エントリで記録する。
  以後「手で 1 件を差し引く」運用は不要である。
- **実測 (すべて本 wave の tip、計算ノード)。** 台帳追加前の既定 full 監査は 1702 件中
  新規 1 / 既知 6 / rc=1。実装 commit `2327210a` 直後は 1703 件・**新規違反なし / 既知 7 / rc=0**。
  local main `df206f4c` を取り込んだ merge commit `4fc48604` 直後も 1713 件・**新規違反なし /
  既知 7 / rc=0**。対象テストファイル単体は 238 passed。**受入全走は 7177 passed / 20 skipped /
  rc=0** (18 分 15 秒)。変異は 5 本すべて KILLED で、baseline (正例 control) は 238 passed / rc=0。
- **login ノードでの bounded local 走行が rc=16 で 2 度止まった。** 変異 harness を通さない素の
  targeted 走行でも起きる F155 の再発で、本 wave の差分とは無関係。`--force-dispatch` で計算ノードへ
  回して緑を取った。受入全走は追加 flag なしの既定形で走らせ、自動 dispatch に任せた。
- **段 8 の改善候補は 1 件で、reference へ入らなかった。** 「`DW-M01` の単一理由性が『赤くなる node が
  1 本』と誤読される」— 段 2 プランは 6 候補中 2 件を誤って単独帰属と主張し、段 3 レンズ 2 が
  訂正した。`DW-M01` の文面自体は「赤理由が一つに絞れる」と正しく書いており、誤読は子の側である。
  ただし段 3 を省く軽量版の wave では、親が同じ誤りを未検証のまま登録しうる。文面追記は
  dev-wave 4 文書の aggregate 予算が **25,134 / 25,200 bytes で余地 66 bytes** のため収まらず、
  意味等価な圧縮も安全義務の文面に当たるので行わない。裁定パッケージへ送る
  ({{T:mutation-single-reason-vs-single-node}})。予算引き上げは提案しない。
- 正本 = `output/insights/2026-08-07_t618-known-violation-ledger/README.md`
  (段 1 brief、段 2 プラン、段 3 の 2 レンズ、段 4 裁定、段 5 実装報告、段 6 のレビュー 2 本、
  変異 spec と台帳を全文凍結)。

## 次の一手差分

### 完了

- [T-618] `3f2c43d7` を既知違反台帳へ注記つきで追加し、既定 full 監査を rc=0 / 既知 7 / 新規 0 に
  した。台帳 schema への `note` field 追加は {{D:known-violation-note-field}}。手作業帰属は
  恒久解消した。残る [T-621] (自動層が stdout を捨てる) と [T-619] (範囲式の盲点) は本項の射程外で、
  独立タスクとして継続する。
  remaining: none
  base: a16cffa9ac77326863780b73d8f75bce29bf3131618dd3c99d4680f6474110a5

### 新規

- {{T:mutation-single-reason-vs-single-node}} **P3・新規**: `DW-M01` の「単一理由性」を
  「赤くなる node が 1 本」と読み違える経路がある。実測では段 2 プランが 6 候補中 2 件を誤って
  単独帰属と主張し、段 3 の敵対レンズが訂正した。段 3 を省く軽量版では親が同じ誤りを未検証のまま
  登録しうる。文面追記は dev-wave aggregate 予算 (余地 66 bytes) に収まらないため、追記するか、
  別の伝達手段 (memory 等) にするか、見送るかを決める。予算引き上げは提案しない。
