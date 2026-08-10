# 段 4 裁定 — [T-657] R3 恒久機構合流の設計 wave

両レンズの結論は「段 2 プランのまま**実装 wave** へ進めてはならない」で一致した。
本 wave は**設計の起票**であり実装ではないため、この結論は wave の停止条件ではなく、
**設計文書が記録すべき制約そのもの**である。以下、所見ごとに裁定する。

## 0. 文書の性格 (親裁定 J1)

設計文書は **第 1 設計段パッケージ** として書く。「実装可能な exact 仕様」を名乗らない。
両レンズが独立に構成した破れ方が残っている以上、settled と書けば虚偽になる。
`docs/freeze-permanent-design.md` が R1..R16 の裁定待ちで起票された前例と同じ扱いにする。

## 1. 採用 (real、設計文書へ不変条件として書く)

| # | 出典 | 裁定 | 設計への反映 |
|---|---|---|---|
| J2 | A-R1 | **採用** — 下位 freeze の世代導入 G と承認 A は別 commit でしか構成できない。プランの `F` 1 commit は機械的に不成立 | topology を `G_f` / `A_f` に分解して書く |
| J3 | A-R3 | **採用** — 上位 bundle が下位 generation record を直接参照できると `no-active` を迂回する | **上位 bundle は下位 active pointer だけを参照できる**を不変条件にする。generation 直参照を禁止 |
| J4 | A-R5 | **採用** — 完了判定が negative mutation だけだと reject-all 実装で緑になる | **全段の完了判定に陽性条件 (正常入力の受理) を必須**にする設計規則を明文化 |
| J5 | A-R4 / A-R10 | **採用** — policy 実装前に X を置く段階分割は成立しない | **X (発効) は先送り 3 件の裁定後にしか置けない**を段階分割の不変条件にする |
| J6 | A-R8 / B-6 | **採用** — Q receipt が digest にも approval にも束縛されていない | Q を **digest の preimage に入れる**。E/F/B/Q の導入形状 (parent・exact diff・非 merge) も規定対象と明記 |
| J7 | B-1 / B-9 | **採用** — 封印の分離が名ばかりで、prediction binding が digest に無い | digest preimage に **`seal_binding` slot** を置き、その**中身**を S1/S2 の裁定入力とする。slot 自体は両分岐で必須 |
| J8 | B-2 | **採用** — `ruling_profile_sha256` だけでは unknown を検査できない | profile は **bytes・path・namespace・canonical schema** を持つ実体とする |
| J9 | B-3 | **採用** — 投入 receipt に bundle が無いため受理集合が黙って G-a に固定される | **保証境界の裁定前に投入 receipt schema を凍結してはならない**を制約として書く |
| J10 | B-4 / B-7 | **採用** — 候補型が validator の途中で消え、出口 (claim / marker / budget / verdict / report / submit receipt) に届かない | 「新権限型は出口まで型を保つ」を不変条件にし、consumer 閉包を **19 件 + 環境側 + shell** で列挙 |
| J11 | B-10 | **採用** — 可変状態 (現 serial・現 hash・record 件数) の再掲は腐る | 設計文書に現在値を書かない。台帳 (worklog 末尾) を正本として参照する |
| J12 | A-R7 | **採用 (親 P2 の過剰一般化を訂正)** — literal 除去は必要条件ではない。literal を残す恒久 topology の反例が構成された | literal 除去を前提にせず、**環境権限の解決方式を未裁定の択一**として書く |
| J13 | A-R9 / B-8 | **採用 (親 P1 を修正)** — 旧 freeze 文書を完全無改訂にすると authority 正本が二重化する。**独立 2 レンズが再現**したため `DW-G03` を満たす | 新設ファイルを正本にしつつ、`docs/freeze-permanent-design.md` へ **適用範囲と precedence の短い注記のみ**を追記する。R1..R16 本文は変えない |

## 2. ユーザー裁定へ返す (scope 外 real。親が決めない)

先送り 3 件 (封印 S1/S2 / 保証境界 G-a・G-b・G-c / 副作用境界) はユーザー確定済みの先送りのまま
据え置く。**それとは別に、本 wave で新たに判明した裁定漏れ**を返す。

| # | 出典 | 問い | なぜ親が決めないか |
|---|---|---|---|
| Q1 | A-R2 / B-5 | 環境の**候補 record をどこへ置くか**。(i) 権威 directory の外の候補 namespace / (ii) terminal-head 検査を bundle 参照検査へ置換 / (iii) literal を残し候補は bundle 側だけで束縛 | 受理集合が変わる。(ii) は `restore-floor-protocol.md` §6 の「record 2 あり・head 1 なら拒否」を消す |
| Q2 | B-A | 上位 bundle の **A / X の実行主体と A の意味**。既存 R13 / R14 は freeze family 側の裁定であり上位への適用は未確認 | 信頼境界が変わる |
| Q3 | B-B | 上位 bundle の **lockstep / rollback / revocation 政策**。環境だけ・凍結だけの successor を一律拒否してよいか | 既存 family の R15 lockstep を上位へ自動継承することになる |
| Q4 | B-C | **source-side pin の喪失を受け入れるか**。literal を外す分岐を採る場合、`env_contract.py` の blob 変化という review signal と loader closure 経由の間接 pin を失う | 規律 2 の交換条件であり、ユーザーが受け入れを判断する層 |

**親の推奨:** Q1 は (i)、Q2 は「A/X とも人間、A は digest + 添付レポート確認」、Q3 は lockstep 既定、
Q4 は「literal を残す分岐 (A-R7 の反例 topology) を第一候補にすれば Q4 自体が発生しない」。
いずれも推奨であって裁定ではない。

## 3. refuted (採らない)

- A-F1: M1 / M2 の**事実**は正しい。誤っていたのは親の一般化 (J12 で訂正済み)。
- A-F2: versioned な新 path 自体は履歴不変条件に抵触しない。抵触するのは旧固定 path の別 bytes 更新。
- A-F3: 結合に使う既存 field は実在する。
- A-F4: cross-pair 拒否は記述上は存在する (実装は未確認)。
- B-refuted-1: 先送り 3 件を暗黙に裁定してはいない (ただし分離契約が不十分な点は J7/J8 で採用)。
- B-refuted-2/3: 本 wave は R3 を破っておらず、旧 branch の merge / cherry-pick もしていない。

## 4. 変異事前登録 (DW-M01)

**該当なし。** 本 wave は実装差分ゼロの docs-only であり、`DW-S04` の免除
「実装差分ゼロの『実装しない』裁定の変異 matrix」に当たる。

## 5. 受入

`DW-S04` は受入全走を免除しない。docs 変更が `check_docs` 系と実 repo を読むテストへ影響するため、
段 7 の記録前に受入全走を実走し、結果を worklog へ書く。

## 6. プラン v2 (確定した設計文書の骨格)

1. 位置づけと状態 / 2. 解く問題 / 3. 用語 / 4. 骨格 (上位 bundle。凍結側 7 成分 digest を触らない理由) /
5. commit topology (J2 訂正込み) / 6. 環境権限の解決方式の択一 (J12) / 7. 束の識別子と resolver 契約
(J3 込み) / 8. 先送り 3 件の構造的隔離 (J7 / J8) / 9. 移行が触る層 (J10) / 10. 段階分割と完了判定
(J4 / J5) / 11. 保存すべき拒否 / 12. 裁定してほしいこと (先送り 3 + Q1..Q4) / 13. 損失と限界 /
14. 旧 branch の再導出 / 15. floor 復元のユーザー手番
