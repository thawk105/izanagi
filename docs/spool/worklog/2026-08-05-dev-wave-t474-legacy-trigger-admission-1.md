---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t474-legacy-trigger-admission
seq: 1
title: [T-474] 旧 trigger artifact に admitted view を名乗らせない — 歴史枝の trigger 軸 6 件を拒否し、親の provisional 方向は 3 者独立指摘で撤回した (コード + docs、branch worktree-dev-wave-t474-legacy-trigger-admission)
---

## 本文

- **ユーザー裁定 ([T-409] 択一 C = 縮小版) を実装した。** 歴史枝 (pre-policy かつ Git snapshot
  三点照合を通る artifact) の trigger 軸 campaign を `legacy-unclassified` とし、raw view を
  発行しない。設計判断と supersede の範囲は {{D:legacy-trigger-raw-view-denial}}。
- **親の provisional 裁定 2 件が誤りだった。** (P2)「方向 A ならユーザー再裁定が要る」は、
  再裁定が既に存在するため誤り。(P3)「受理集合を変えず証拠 field を掲載する方向 B」は、
  段 2 プラン・敵対レンズ A・敵対レンズ B が**独立に**「raw view を発行し続けるので裁定を
  満たさない / consumer が読まない / schema の in-place 変更になる」と指摘し、撤回した。
- **段 2 codex の「ユーザー選択の記録がない」は棄却 (refuted)。** 選択は
  `rulings-inbox/2026-08-04-rulings-session-5rulings.md` §11 と worklog (193) に記録済みで、
  段 2 は裁定控え 1 本しか読まなかったための見落としだった。実装を止める理由にはならない。
- **段 3 の所見 12 件・段 6 の所見 7 件はいずれも real (refuted 0)。** 段 6 の敵対レビュー 2 本は
  ともに NO-GO を返し、must-fix 3 件 (終端 lock 再照合の消失、変異 M8 の事前登録が誤り、
  新 D の非主張欠落) を出した。焦点再レビューは 7 所見すべて closed / regressed 0 で GO。
- **親の変異事前登録に誤りが 1 件あった。** M8 (lock の read-once を戻す変異) を
  「決定論的注入路がないため生存見込み」と登録したが、レビュー R1 が注入路を具体的に示し、
  境界テストで殺せることが実測で確認された。
- **M6 の期待 node 集合は予測が不足していた。** 初回は MISMATCH。実際の失敗 node は
  事前登録の上位集合 (不足 2 件・余分 0 件) で、拒否の消失を検査する別テスト 2 本も同時に
  赤になったためである。DW-M02 に従い初回結果を台帳に残し、訂正した期待集合で M6R を
  再走して KILLED を得た。
- **実測 (Pegasus gen_S へ同期 dispatch)。** 変異 matrix は 9 変異 + M6R = **10/10 KILLED、
  生存 0** (統合 commit へ anchor 固定)。対象 + meta テスト 113 passed。全受入は fix 前が
  5935 passed / 19 skipped / 0 failed、fix 後の最終走行を同 wave で再実施した。
- **段 6 の途中で親が harness の生死を誤判定しかけた。** `pgrep -f` の待ち手自身が
  同じパターンに一致し、終了済みの harness を「実行中」と読んでいた。判定は
  `mutation_harness.py` を含む実体で行う必要がある (DW-M05 の既知の罠)。
- 逐語・変異 spec・変異台帳は `output/insights/2026-08-05_t474-legacy-trigger-admission/` に凍結した。
- **段 8 の自己改善は 3 候補すべて統合できず裁定へ返す。** いずれも今回の実測に基づくが、
  `docs/dev-wave/**` が hard ceiling に対して余白 70 bytes 程度しかなく、最小文でも入らない
  (試行時 operations.md 8494/8400 bytes、合計 25933/25200 bytes)。契約に従い編集を戻した。
  候補 (a) 中断が残した `.done` を消さずに再投入すると前回分を完了と誤読する → `DW-O01`。
  候補 (b) `pgrep -f` の照合語に harness の実行ファイル名を含めないと、spec path を含む
  待ち手自身に一致して終了済みを実行中と読む (本 wave で実際に誤読した) → `DW-M05`。
  候補 (c) kill は期待 node と実 node の**完全一致**判定なので、期待は collection の実 nodeid
  (parametrize 接尾辞込み) で書き、同じ性質を検査する既存テストも数え上げる → `DW-M08`。

## 次の一手差分

### 完了

- [T-474] 歴史枝の trigger 軸 campaign 6 件へ raw admitted view を発行しないようにし、
  合成 lock の真理値表・corpus 反例 6 件・正例 21 件・trusted snapshot census・
  read/hash 間への決定論的注入で固定した。変異 10/10 kill。
  remaining: none
  base: 5c9e8302007fa9861ed39800c33da2f1aaba8864437949edc8a356fd7b779696

### 新規

- {{T:post-policy-machine-sweep-membership}} **P2・新規**: post-policy の機械 sweep は
  membership 証拠なしで受理される。共有 validator は機械 lock に空の束縛集合を返し、producer も
  汎用検疫へ membership 証明を渡さない。将来 sweep の述語生成器が drift すると、32 正準集合外の
  候補が admitted のまま材料へ流れる。producer 側は s1 freeze が sha を記録するため所有境界を跨ぐ
- {{T:wal-side-aba-in-admission}} **P3・新規**: admission validator の WAL 側に ABA が残る。
  record 読み出し API が bytes を返さないため、hash した bytes と parse した bytes の同一性を
  保証できない。lock 側は {{D:legacy-trigger-raw-view-denial}} で閉じた
- {{T:trigger-provenance-implementation-overload}} **P3・新規**: 旧 trigger sweep の付随レポートの
  `implementation` field は、述語 (C++ 1 行) と stock 説明文の双方を保持していて二義化しており、
  かつ build された source (`src_token`) へ束縛されていない。実述語 34 件が 32 正準集合に属することは
  実測したが、それは**レポート文字列の membership** であって build された source の membership ではない
