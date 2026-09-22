**判定：GO（本段の静的レビュー）。成立する must-fix は見つかりませんでした。** 受入全走・変異 KILLED の確認まで済んだという判定ではありません。コード変更・テスト実行はしていません。

以下、`parse.py` 等は `orchestrator/verifier/`、`test_verifier.py` は `orchestrator/tests/` 配下です。不成立項目の重大度は、攻撃が成立した場合の重大度を示します。

| 番号 | レンズ項目 | 所見 | real/refuted の見込み | 重大度 | 根拠 file:line | 成果物への影響 |
|---|---|---|---|---|---|---|
| A1 | 1：偽の認定 | **不成立**。compact は全 file の schema、legacy は混在検査済みの先頭 TxnV3 から判定し、非空 v3 に必ず印を立てる。空 run は別条件で非認定。 | refuted | must-fix（不成立） | core.py:42、:50、:63／model.py:545、:560 | v3 の certified=True に至る経路を確認できない。 |
| A2 | 1：counter・capability | **不成立**。expected_commits の `replace` は印を保持し、capability 発行も同じ verify 結果の certified を採用する。 | refuted | must-fix（不成立） | core.py:72、:289、:399／test_verifier.py:3702、:3711 | counter 一致・source evidence 成立でも v3 非認定を解除しない。 |
| A3 | 2：identity | **不成立**。object helper、intern、packed の writer/read-only 解決、tuple builder/worker が同じ `(table, hex)` を使用する。table=0 も辞書の真偽で失われない。 | refuted | must-fix（不成立） | model.py:361／parse.py:351、:625／dsg.py:260、:411、:426、:517 | 異表同 hex の誤結合、同表同 hex の分裂による辺・orphan・version_dups の変化は見つからない。 |
| A4 | 2：fallback・重複 | **不成立**。overflow は同じ scanner で再読し、pool 障害は部分結果を捨てて再計算する。勝者 row から表・取引種別を復元する。 | refuted | must-fix（不成立） | parse.py:575、:665、:814、:884、:898／dsg.py:610、:774 | fallback や last-wins による metadata の取り違えは見つからない。 |
| A5 | 3：v2 不変 | **不成立**。変更 helper の v2 分岐は従前と同じ文字列・型・token 順を返す。辺追加、SCC、BFS、旧 serializer は不変。 | refuted | must-fix（不成立） | parse.py:570、:580、:625／dsg.py:627、:780／report.py:96 | v2 の既存値・notes・JSON bytes・witness 順を変える差分を確認できない。具体入力の追跡は下記。 |
| A6 | 4：schema 混在 | **不成立**。同一 file はその C 行で拒否。file 間は failure を先に処理し、NeedsLegacy を含めて照合する。中立 file・重複 txid で混在を隠せない。 | refuted | must-fix（不成立） | parse.py:366、:855、:894／test_verifier.py:3619、:3626、:3637 | 混在受理は見つからない。後方 file の構文エラーが前方の file 間混在より優先するのは R2 の明示契約。 |
| A7 | 4：厳格検査 | **不成立**。新整数の正規形・値域、v3 行長、U/I/D、nS/nQ、S/Q を検査する。並走返信の正常形式と整合する。 | refuted | must-fix（不成立） | parse.py:262、:347、:371、:503／test_verifier.py:3647、:3657 | 指定された不正入力の受理、正常 v3 の拒否は見つからない。件数・終端・key・版不一致は従来の integrity 経路を保つ。 |
| A8 | 5：構造化 anomaly | **不成立**。理由の table と勝者の tx_type を復元する。旧射影のリスト内包表記は要素を省略しないため、新関数の zip は正常結果を切り捨てない。節点/type 数不一致と基底 reason 混入も拒否する。 | refuted | must-fix（不成立） | dsg.py:777、:853／core.py:201／report.py:26、:35、:136 | 新出力点での表・取引種別の欠落、取り違えは見つからない。旧 serializer の metadata 省略は R6 の既知の対象外。 |
| A9 | 6：試験の実体 | **不成立**。経路切替は実 parser/builder を呼ぶ。辺集合への正規化後も versions 順・result・anomaly の比較が残り、実並列は子 PID を検査する。 | refuted | must-fix（不成立） | test_verifier.py:3399、:3424、:3771 | stub や恒真による見せかけの成功は確認できない。固定 PID・一時 path の焼き込みもない。 |
| A10 | 6：既存試験 | **不成立**。統合 diff は既存行の変更 **0**、削除 **0**、追加 **436**。単一の追加 hunk のみ。 | refuted | must-fix（不成立） | integrated.diff:5／test_verifier.py:3376、:3812 | 既存期待値・runner の緩和はない。production の追加＋削除も 266 行で R9 内。 |
| A11 | 6：変異の帰属 | KILLED と単一理由は未実証。特に M1 は予定された個別の legacy 辺 assertion より先に、共通 helper の経路比較で失敗する見込み。 | real（検証残件） | should | s5-author-u4r.md:97、:101、:126／test_verifier.py:3424、:3468 | 現行成果物の誤値は示さないが、「予定した assertion で殺した」という証拠にはまだ使えない。 |
| A12 | 6：焦点走の解釈 | ログで確認できるのは child rc=0、3532 passed / 3 skipped。実行対象 nodeid・skip 内訳・統合 commit の束縛は、このログ本文だけでは確認できない。 | real（証拠の限界） | should | focus-1.log:1、:10、:11、:62 | 受入全走成功、全 consumer 成功、変異 KILLED への読み替えはできない。 |

**v2 の変更行を具体入力で追跡した結果**

実行結果ではなく、統合 diff と現コードの静的な代入・分岐追跡です。

| 具体入力 | 変更行を通った結果 |
|---|---|
| `C 0 0 2 1 0 1` → `W 0 aa U 2 1` → `E 0` | schema=2、`extra={}`。従来の `Txn`・`Write` を生成し、intern は `"aa"`、`"U"` の順。追加配列は空、復元型も従来どおり。 |
| 上記 writer に `C 1 0 2 2 1 0` → `R 1 aa 2 1` → `E 1` を追加 | object/packed/tuple の検索キーはいずれも文字列 `"aa"`。従来と同じ `0→1` の wr 辺と基底 `EdgeReason` を生成する。 |
| 同じ `"aa"`・commit `(2,1)` の writer を txid 0、1 に置く | 最初の producer は 0、version_dups=1。変更後も notes は `version dup: key=aa ver=(2, 1) by txid 0 and 1`。 |
| v2 frame 内に `X 0 aa reason` または `I 0 aa reason` | issue は従来の `(0, "aa", "reason")`。sample は両方とも従来の `txn0 key=aa (reason)`。 |
| v2 の W op を `Z`、整数を `+0`・`01` にする | v3 専用検査を通らず、従来の op 無検査・`int()` 変換を維持する。 |
| C が5 token／8 token、または R の余剰 token | 既存の専用 C エラー／`expected exactly 7 fields`／unpack 由来の malformed line を維持する。 |
| v2 の writer epoch を `2**32`／`2**63` にする | 従来どおり tuple／legacy へ落ちる。schema 照合は全て 2 で通過し、v3 の印は立たない。 |

v2 では helper が同じ値を返し、反復・登録順を変えていないため、変更による witness 順の差は導けません。既存の bytes golden（test_verifier.py:1404）、辺・witness 順と repr（:2576）、fixture 結果 hash（:2893）も保持されています。ただし、静的追跡を全入力の実測証明とは扱いません。

**M1〜M15 の検出位置の照合**

以下はすべて**静的予測であり、KILLED の実測ではありません**。T 番号は author 報告のものです。

| 変異 | production の位置 | kill 候補と最初の検出点の見込み | 単一理由の評価 |
|---|---|---|---|
| M1 | model.py:361 | T01 → test_verifier.py:3424 の辺集合不一致 | 表消失による誤辺。ただし予定の :3468 より先に失敗する。 |
| M2 | parse.py:625 | T01 → :3464 の read/write token ID 一致 | 異表 token の衝突を直接検出。 |
| M3 | dsg.py:426 | T05 → :3424 の辺集合不一致 | read-only token を table 9 に誤解決。両表の writer があるため欠落 writer だけの検査にならない。 |
| M4a / M4b | dsg.py:517 / :260 | T01 → :3424 の辺集合不一致 | tuple writer/read の identity 不一致による辺消失。別々の変異が必要。 |
| M5 | parse.py:273 | T10 → :3450 の「不正入力を受理」 | 共通 helper を外すので legacy 側の同じ検査も代替防壁にならない。 |
| M6 | parse.py:366 | T09 → :3450 | legacy を先に試すため、compact 化の型不整合より先に混在受理を検出する。 |
| M7 | parse.py:375 | T12 → :3450、tx_type=`0` | 字句正常で、値域だけが拒否理由。 |
| M8 | parse.py:351 | T12 → :3450、table=`11` | 件数不一致は integrity に留まり、別の ParseError が代替しない。 |
| M9 | parse.py:373 | T13 → :3450、nS=`1` | S/Q 行がなく、未知 tag による代替拒否はない。 |
| M10 | parse.py:263 | T12 → :3450、table=`01` | 値域内の非正規表記なので字句検査に帰属する。 |
| M11 | dsg.py:780 | T04 → :3535 の exact reason 比較 | ww/wr 理由の欠落を直接検出する。 |
| M12 | parse.py:582 | T03 → :3427 の result 不一致 | compact の tx_type 固定化。個別 metadata assertion より前の検出。 |
| M13 | core.py:217 | T03 → :3515 の `r["table"]` | table 欠落による KeyError の見込み。 |
| M14 | core.py:64 | T15 → :3704 の verdict/certified | source・counter・他 integrity 条件が揃い、非認定の印だけに帰属する。 |
| M15a / M15b | parse.py:439 / :448 | T14 → :3683 の issue tuple 不一致 | R1 が残るため verdict では殺せない。収集値で直接検出する。 |

## 総括

統合差分に、成立する must-fix の正しさ欠陥は見つからず、本段は GO とします。
v3 非空 run の非認定は、legacy・compact・counter・capability の各経路で保持されます。
表込み identity と勝者の取引種別は、fallback と anomaly 復元まで一貫しています。
v2 の変更分岐を具体入力で追跡し、既存値・文言・順序を変える経路は確認できませんでした。
既存試験の変更・削除は各 0 行で、追加 436 行です。
親の焦点走は 3532 passed / 3 skipped ですが、受入全走としては扱えません。
M1〜M15 は検出可能と静的に見込めるものの、KILLED と失敗理由の実測確認は残ります。
存在履歴の検査と旧出力経路への v3 metadata 配線は、引き続き未完了です。