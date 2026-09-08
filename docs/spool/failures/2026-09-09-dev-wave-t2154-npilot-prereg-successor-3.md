---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2154-npilot-prereg-successor
seq: 3
---

## 新規

### {{F:closure-injected-path-blind-to-swallowed-rejection}}. 閉包検査の injected 特殊経路は、拒否を握り潰した実装を被覆済みと数える [恒真ゲート] [テスト代表性]

- 事象: 条件関門の返却物検査を `except: pass` で握り潰す変異を入れたところ、負例テスト 2 件は
  赤になったが、**閉包検査 (`test_define_sink_cross_product_has_no_unreviewed_ungated_member`) は
  緑のままだった。** 同じ変異で繰延べ台帳の entry を外した状態を維持できてしまう。
  段 3 の敵対相談が読解で指摘し、本 wave の変異 m04 が実測で確認した。
- 根本原因: `injected-*` kind の sink に対する被覆判定は、sink の直後から次の injected sink までの
  行範囲に「名前の suffix が `require_returned_condition_evidence` に一致し、第 1 引数が sink の
  代入名である call」が 1 つでもあれば、patch macro 全件を被覆済みと数える。
  campaign 経路が行う import の真正性・shadow・支配関係の確認をこの経路は使わず、
  例外の握り潰し・branch 局所・必須 keyword の欠落も検査しない。
  **call の位置と第 1 引数の名前だけが被覆の根拠になっている。**
- 恒久対応: 本 wave では検査そのものを変えていない (族全体に効く共有機構の変更であり scope 外)。
  代わりに配線側へ署名として義務を課した — 呼出しは module scope で import した実体を指し、
  無条件の文として置き、送出される例外を握り潰さず変換して再送出する。
  この義務は変異 m04 が発火を確認している。検査本体の強化はユーザー裁定へ返した
  ({{D:condition-gate-live-coverage-must-be-stated-per-cell}} と同 wave の次の一手を参照)。
- 再発検知: 同経路で被覆を主張する新しい member は、拒否を握り潰す変異を必ず登録する。
  負例だけが赤で閉包検査が緑なら、閉包検査は当該 member について何も保証していない。

### {{F:frozen-prereg-records-a-commit-that-does-not-exist}}. 事前登録が記録した commit が repository に存在しないまま発行され、誰も踏まなかった [手順漏れ]

- 事象: n-pilot の事前登録が `source.commit` として記録している 40 桁 SHA は、この repository の
  到達可能な commit ではない (`git cat-file -e` が非 0、到達可能 commit 9591)。
  2026-08-16 の発行から約 3 週間、後続の複数 wave がこの事前登録を読んだが誰も気づかなかった。
- 根本原因: この欄は実行時に照合されない。driver が照合するのは job script が観測した repo HEAD と
  `git rev-parse HEAD` の一致であって `source.commit` ではない。
  発行時にも「40 桁 hex か」の形だけを見て実在を確かめていなかった。
  発行 wave の branch が着地しなかったか書き換えられたため、記録された SHA が宙に浮いた。
- 恒久対応: {{D:successor-prereg-commit-binding}} — 事前登録が記録する commit について、
  実在・HEAD 祖先性・その時点の driver blob と記録 digest の一致をテストで固定する。
  本 wave の後継事前登録に実装済みで、変異 m05 が発火を確認している。
- 再発検知: 事前登録を発行する wave は、記録した commit を `git cat-file -e` で確かめてから発行する。
  記録済みの digest を歴史 blob から再導出できるかどうかは、記録の直後にしか確かめられない。

### {{F:mutation-expected-nodes-missed-a-bytes-pinning-redundant-gate}}. 事前登録した成果物が driver bytes を pin していると、その driver への全変異が同じ node を赤にする [テスト代表性] [手順漏れ]

- 事象: 変異 matrix の初回が MISMATCH 4 件で止まった。期待した node は 6 変異すべてで漏れなく
  発火しており、不一致は**余分に赤くなった側**だけだった。余分の 1 つは後継事前登録の
  driver bytes 検査で、driver をどう変異させても必ず赤くなる。もう 1 つは親の登録漏れ
  (閉包の分類件数を固定する別テスト) だった。
- 根本原因: 成果物側に「現行 driver bytes の digest」を pin するテストを置くと、その driver に
  触る変異すべてに対して発火する冗長 gate になる。親は期待 node を「その変異が壊す論理」から
  導出し、bytes pin の存在を勘定に入れていなかった。行番号 pin が同型の振る舞いをする件は
  既に記録があるが、digest pin でも同じことが起きる。
- 恒久対応: 初回を probe として保存し (`mutation-probe1-out.json`)、観測した完全集合で再登録して
  2 巡目で 6/6 KILLED・期待 node 完全一致とした。台帳には
  **どの node が冗長 gate かを明記し、単独変異の帰属証拠から外す**。
- 再発検知: 変異を登録する前に、変更する production file の bytes / 行番号を pin している
  テストを `git grep` で引き、その全件を期待 node へ含めるか冗長 gate として宣言する。
  probe 台帳を読むときは変異ごとに冗長 gate の node を引き、残りが空なら帰属不成立とみなす。
