---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1219-carry-same-id
seq: 3
title: [T-1219] worklog の carry 検査を参照先の同一 ID まで強め、既存違反 4 件を既知違反登録した (コード + docs、branch worktree-dev-wave-t1219-carry-same-id、受入 = Pegasus gen_S 計算ノード)
---

## 本文

- 依頼は D837 (択 c) の実装。carry stub の検査を「参照先 entry の実在」から
  「参照先 entry の次の一手に同じ ID が在ること」まで強め、実測済みの既存違反 4 件は
  既知違反として登録し、赤にするのは新規発生だけにする。
  択 (b) の実在検査に留める案は不採用と確定済みで、段 4 でも戻していない。
- **現行検査は母数の 0.24% しか見ていなかった。** carry 参照は実コーパスに 404,326 件あるが、
  収集が参照先番号ごとに `setdefault` で 1 件へ潰していたため実質 957 件しか検査していない。
  同一 ID 検査は occurrence 粒度を要求するので、この collapse を streaming へ置き換えた。
- **既存違反はちょうど 4 件で、すべて entry 77 にある。** 段 2 のプランは台帳表の
  source entry を 74 / 76 / 77 / 78 と書いていたが、これは親の probe 出力の**行番号**であり
  entry 番号ではない。当該 archive が持つ entry は 77 の 1 件だけである。
  親が実測で訂正しなければ、4 件とも `expected=1, actual=0` になった上に新規違反が 4 件出て
  実 repo が赤になっていた。
- **参照先は entry 73 で、その次の一手は T-177 から T-206 までしか持たない。**
  T-207 以降を 1 つも持たないことが 4 件すべての直接原因である。
- 設計は {{D:carry-mismatch-ledger-key}} と {{D:carry-population-completeness}} に記録した。
- **敵対相談 (段 3) の記録。** 2 レンズ並列で 16 所見。親は real 12 / refuted 2 / scope 外 4 と裁定した。
  - 採用した blocker 2 件。(i) carry 風の不正文法が母数も違反数も動かさず素通りする
    (`(073)` `(73 )` `( (73) 参照)` は 2 つの regex 双方に不一致だが `TASK_ID_AT_HEAD_RE` には
    一致するので正規項目として受理される — 親が実測で確認)。
    (ii) 実測値に固定した下限は最初の fold から部分消失を黙認する。
  - **親の実測が反証した 2 件。** 「probe と production の母集合が一致する保証がない」は
    実測で差 0 を確定した (現行 2,749 / 採番 archive 401,577)。
    「索引不能 category が実コーパスで 0 件である根拠がない」は key 不在 0 / 値 None 0 /
    空集合 0 を実測した。どちらもレンズの指摘は「示されていない」点で正しく、実測で閉じた。
  - **scope 外として裁定へ返した 4 件。** 非採番 archive の carry が構造的に検査対象外である件
    (既存テストが名前で対象外を固定しており、該当は全コーパスで 1 件)、
    台帳・固定総数・exact テストを同一 patch で書き換えれば無裁定で緑にできる件
    (既存の `KNOWN_PLACEHOLDER_DEBTS` 族が現に持つ性質で、塞ぐには承認 receipt という
    新機構が要る)、carry 文法を読む他 consumer との共通 parser 化、
    F58 型の「同じ ID で内容を差し替える」検査。
- **段 6 の敵対レビューで偽陽性を 1 件止めた。** carry 風 candidate の述語が広すぎ、
  `- [T-500] (D837)` や `- [T-500] (Python 3)` のような正当な項目まで赤にしていた
  (親が実測で確認)。括弧の中身が空白と数字だけの形へ絞り、`(073)` `(73 )` `( 73)` `(0)` は
  候補のままにした。厳密 parser の受理集合が candidate 集合に包含されることも全件で確認した。
- **段 6 のレビューが変異の「見せかけの成功」を 5 件見つけた。** 登録した変異を無効化しても
  別の理由で赤になるだけの入力が 4 件、そもそも殺せない変異が 1 件あった。
  `DW-M03` に従い、その層だけが拒否理由になる入力へ再照準させた。
- **変異 matrix は 10/10 KILLED。生存ゼロ。** baseline は 552 passed / 3 skipped / rc=0。
  登録した期待 node は 10 件すべてで実際に落ちた (`expected ⊆ failed` が全件成立)。
  内訳は **単一理由 5 件** (M4 台帳総数 pin / M5 candidate == parsed / M6 母数下限 /
  M9 universe == index / M10 fail-closed の早期 return) と、
  **冗長 gate 5 件** (M1 同一 ID 比較 10 node / M2 台帳吸収 4 node / M3 per-key 観測数 2 node /
  M7 索引三分割 2 node / M8 occurrence collapse 12 node)。
  後者は中核の層を多数のテストが同時に観測するためで、`DW-M03` に従い単独変異の証拠からは外す。
  失敗 digest の切り詰めは全件 `omitted_failures=0` で、F220 の再発はない。
- **費用の実測。** `python3 tools/check_docs.py` は 10.52 秒 / 157MB から
  14.05 秒 / 162MB になった (1.34 倍、倍化せず)。
  最悪の赤経路 (全 carry が不一致) は 12.27 秒 / 133MB / finding 22 行 4,974 bytes で、
  `他 404306 件を抑止` と総数を併記する。40 万件の finding が常駐する経路は無い。
- 段 6 の fix は一枚岩で 3 巡した。編集面が同じ 2 file なので所有を素集合に割れない。
- 事故は {{F:mutation-nodeid-nonascii}}、{{F:codex-max-attempts-sandbox-coupling}}、F217 の再発に記録した。

## 次の一手差分

### 完了

- [T-1219] carry 検査を参照先の同一 ID まで強め、既存違反 4 件を digest 台帳へ登録した。
  母集合の完全性は candidate == parsed と universe == index で担保し、実測下限は補助に降格した。
  変異 10/10 KILLED、受入全走で確定した。
  remaining: none
  base: 5cee50aa4512d89bbe207ff7c10946e76550f0f8735557feb6ea02e023beabfb

### 新規

- {{T:carry-unnumbered-archive-scope}} **P2・裁定待ち**: 非採番 archive の carry が
  構造的に検査対象外である件。既存テストが名前で対象外を固定しており、
  該当は全コーパスで 1 件。D837 は archive 全体への拡張を命じていない。
  拡張するなら既存テストの期待値を変える裁定が要る。
- {{T:known-violation-ledger-approval-gate}} **P2・裁定待ち**: 既知違反台帳・固定総数・
  exact テストを同一 patch で書き換えれば無裁定で緑にできる件。
  既存の `KNOWN_PLACEHOLDER_DEBTS` 族が現に持つ性質であり、
  塞ぐには承認 receipt か保護レビュー境界という新機構が要る。
- {{T:carry-grammar-shared-parser}} **P2・新規**: carry 文法を読む consumer
  (fold、land、rulings 収集) と checker の 2 regex が一致する保証が無い。
  共通 parser 化するか consumer ごとの契約テストを置く。
- {{T:carry-population-fold-ratchet}} **P2・新規**: 母数の粗い下限を fold と原子的に
  ratchet する。凍結 entry ごとの期待件数を固定し、現行 worklog は fold の前後で
  非減少を検査する。`tools/spool_fold.py` 側の変更が要る。
