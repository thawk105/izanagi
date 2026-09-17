## 被覆対応表の検算

**結論：単体検査の部分重複は確認できるが、M 全体の代替被覆は成立していない。** 特に実 output の列挙・発行経路、public gate の call-edge、実 ccbench pin、正常発行済み receipt と履歴検査の結合が残る。

以下の略記を使う。行番号は検査した現物のもの。

- `PLAN`：指定の `artifacts/dev-wave-t2710-t080-series-inquiry/s2-plan.md`
- `BRIEF`、`RULINGS`：指定 job dir の `s1-brief.md`、`rulings-verbatim.md`
- `ODT`、`MT`、`HT`、`RST`：それぞれ `orchestrator/tests/test_s8b_oracle_driver.py`、`test_t080_freeze_migration.py`、`test_s8b_holdout_freeze.py`、`test_real_repo_serialization.py`
- `MIG`、`HD`：`orchestrator/campaign/t080_freeze_migration.py`、`s8b_holdout_freeze.py`

**所見 A1 — real：PLAN の「重複」は predicate 部分の重複に限定しなければならない。** 行ごとの検算は次のとおり。「同じ入口」は M の変異後の呼出し入口との比較である。

| PLAN の行 | 単体 test 本体の検算 | 自己判定 |
|---|---|---|
| 89：known artifact bytes | `MT:1275,1284` は `_load_artifact` 直接呼出しで同 reason。M2 は `verify_receipt` から単一 refusal と held/released を検査（`ODT:1898`）。入口・fixture が異なる | **refuted**：全面重複ではない。helper 部分の重複は成立 |
| 90：holdout artifact bytes | 同じ単体 test の holdout 枝（`MT:1269`）。M3 と入口は異なる | **refuted**：同上 |
| 91：current ccbench | `MT:1191` は basis helper、`:1203` は live helper。`:1388` の hold/release は HEAD 取得を stub。M4 は実 submodule の checkout-only と committed gitlink の両状態を `verify_receipt` で検査（`ODT:1862,1875,1884`） | **refuted**：reason/pin 比較の部分重複だけ |
| 92：unknownness layer2 | `MT:544` は scanner を stub し、式・候補・規約の変異を検査。conjunction hit の負例ではない。`HT:710` は明示した２ file を scanner に渡し、`generate` の `rr20: holdout hit` を検査 | **real**：「検証条件は重複」は広すぎる。同じ入力変異・入口・refusal の重複はない |
| 93：user trailer | `MT:680` は実 Git 履歴を `inspect_receipt_history` で検査。ただし reason の包含だけ。M7 は正常発行経路を土台に `verify_receipt` の単一 reason と observation 不在を検査（`ODT:2158,2173`） | **refuted**：履歴 predicate は重複、全結合は非重複 |
| 94：introduction diff | `MT:648` は history の単一 refusal。後段の `verify_receipt` は `_patch_full_gate_to_pass` 下（`:646`） | **refuted**：stub-free 全結合の代替ではない |
| 95：modify→revert | `MT:701` は実 Git で modify/revert を作るが、元 receipt は `{}`（`:310`）。期待 refusal は history＋schema の２件（`:707`）。M9 は有効 receipt の一項目を変え戻し、単一 reason（`ODT:2163`） | **refuted**：同じ拒否集合ではない |
| 96：post-R delete | `MT:1047` は `_capture_draft_basis` 直接呼出し。M10 は現行 runtime loader を経た subprocess の `draft_receipt`（`ODT:2277`）と reason/detail（`:2300`） | **refuted**：precondition 部分だけ重複 |
| 97：generator tamper | `ODT:4744` は `_verify_source` 直接。`HT:814` は入力 file 集合を注入した `verify`。M11 の `gate_check → HD.verify` 到達・引数 witness を代替しない（`ODT:4795,4806,4836`） | **refuted**：hash predicate 部分だけ重複 |
| 98：正常発行全経路 | `MT:632` は多数の gate を stub（`:383`）。M1 の draft→validate→finalize→commit→verify→gate（`ODT:1571`）と同値ではない | **refuted**：全面重複なし |
| 99：report 再導出 | M1 は envelope 同一性と receipt 削除後の exact issue（`ODT:1807,1813`）。PLAN 自身が重複未証明としている | **判定保留**：代替被覆に計上不可 |

M6 の helper 表も照合した。

| PLAN の行 | 検算・自己判定 |
|---|---|
| 105：known closure | **refuted**：`MT:265` は `_classify_source_closure`、M6 は `_verify_known_closure`（`ODT:1937`）。同 reason でも入口・変異が違う |
| 106–109：holdout closure／metadata／schema／pairing | **判定保留**：PLAN は重複未証明。M6 の各直接呼出しは `ODT:1943,1951,1957,1963`。代替扱い不可 |
| 110：ccbench basis | **refuted**：重複誤認という疑いは棄却。同じ `_verify_ccbench_basis` に異なる pin を渡し同 reason を assert（`MT:1193`、`ODT:1967`）。ただし fixture の同値までは示さない |
| 111：reconstruction | **refuted**：`MT:464` は別 helper。`:500` は public verifier だが holdout projected hash の変異で `receipt.derivation_mismatch`。M6 は known projected hash の変異から `receipt.reconstruction_invalid`（`ODT:1972`） |
| 112：positive control | **refuted**：`HT:694` の hit count=0 と、M6 の固定 file 改竄→`_validate_positive_control`（`ODT:1982`）は別 predicate |
| 113：ancestry object type | **refuted**：重複誤認という疑いは棄却。実 Git blob を同 helper に渡し同 reason（`MT:1227`、`ODT:1992`） |

**所見 A2 — real：g7 の実 repo 依存を被覆表の独立項目にする必要がある。** `ODT:4760` は実 `ROOT` の Git 履歴から recorded bytes を探索し、`:4780` は実 ccbench checkout の HEAD を読む。PLAN:97 は known pin の refusal を記載しているが、fixture 内 pin 検査と実 checkout の比較を明確に分離していない。

**所見 A3 — refuted：実 Git 履歴を作ること自体が e2e 専有、という主張は成立しない。** 単体側も実 commit を作る（`MT:375,379,701`）。専有部分は、production 発行済みの正常 receipt に対する履歴変異と、stub-free verifier 全体の単一原因検査である。

**所見 A4 — refuted：PLAN が M 全体を単体で代替可能と断言している、という疑いは棄却する。** PLAN:83,89–99,337 は結合差を明記している。D700 違反になるのは、その部分重複を「毎走から外しても同じ検出力」と読み替える場合である。保留中の直接 scan と CLI は代替にならない（`test_s8b_repo_scan_invariant.py:28`、`HT:1367,1381`、`conftest.py:2230`）。

## 別系列化と受理集合

**所見 B1 — real：「C を維持する」ことと「land の受理集合を維持する」ことは別である。**

現行 gate 4 は collection 全体への exact partition を要求する（`tools/acceptance_shards.py:684`）。変更後は U の緑に加え、過去の M 証跡を使う。この二つが同じ対象状態を検査した証拠にならなければ、「今回の M が赤でも過去の緑で land できる」状態が増える。24h TTL はその差を消さない。

| 束縛先 | 緩みの判定 |
|---|---|
| HEAD | **判定保留**：同一 commit の M 完走を要求すれば、commit 変更に対する取り逃しは抑えられる。ただし Git 可視 untracked output、実 submodule checkout、実行環境まで HEAD が表すわけではない。毎走観測から過去観測への変更も残る |
| closure A：orchestrator＋tools＋external | **real**：output-only 変更後も以前の緑を再利用できる。現在 M が検出する拒否経路を失う具体例がある |
| closure B：A＋output | **real／判定保留**：A の output-only 穴は縮むが、完全な関連入力閉包とは未証明。fixture は docs も読む（`ODT:1406,1433`）。Git tree 束縛なら untracked bytes・checkout 状態・履歴可用性も別途扱う必要がある |

失効回数は、7日間の126遷移で HEAD=126、A=59、B=96、24h の15遷移で15／6／11（`probe_binding_churn.7d.txt:1`、`.24h.txt:1`）。A は67遷移、B は30遷移で再利用可能になる計算だが、**これは安全に省略できる回数でも、危険率でもない。**

**所見 B2 — real：closure A の output 穴は、現行毎走 e2e と同じ穴ではない。**

`ODT:794` は tracked regular file と非 ignored untracked regular file を列挙し、`:827` は receipt/draft を除いて output を複製する。builder はこれを実行（`:1385`）し、production 発行・検証へ進む（`:1571,1600`）。production scan は file 集合を注入せず列挙する（`MIG:2201`、`HD:608`）。

したがって、**前回系列完走後、今回の base 構築前に追加された非除外の三軸 conjunction file** は現行毎走で検出する経路がある。A の古い証跡では検査されない。これは D2068 が whitelist を却下した拒否経路そのもの（`RULINGS:156`）。

一方、fixture は session 内で共有される（`ODT:969,980`）。base 構築後の変更を継続監視するものではない。既存の snapshot 限界を認めても、検査間隔を24hまで延ばす追加の欠落は正当化できない。

**所見 B3 — real：11/11 probe を closure 束縛の成立証拠に転用できない。** 判定器は exact HEAD を要求する（`probe_series_gate.py:80`）。A/B の関連性判定は実装されていない。

## D700 却下理由の現状

**(i) 起動基盤：real、未解消。** BRIEF:61 と PLAN:335 は未解消と認めている。起動主体・頻度・queue 停止時の回収・監視責任が未定のまま移すと、実行されない期間が再発する。

ただし、**起動判断が必ず repo 内になければならない、という要求は refuted**。D2002 は外部 scheduler を認め、外部停止時にも repo 内の利用拒否を要求している（`RULINGS:105`）。必要なのは、実在する起動契約、独立期限検知、停止時の利用拒否である。

**(ii) opt-in の改名：条件付き主張は refuted、成立済みという主張は不可。** ４条件が実効化され、未起動・失敗・関連変更後未完走が利用を止めれば、旧 opt-in と挙動は異なる。しかし現在の probe は `judge()` を呼ぶ模擬試験だけ（`probe_series_gate.py:168`）。

さらに PLAN:158,168 が求める node 別 terminal に対し、probe は集計件数だけを受け取る（`probe_series_gate.py:92`）。最新失敗と過去成功の優先関係も入力にない。**所見 real：11/11 は提示された11負例の判定成功であり、D2002 条件1〜3全体の成立ではない。**

**(iii) D701：refuted、実行分割を阻止する保証ではない。** module collect-only と対象 node の setup-only を別走にする（`RST:1167,1181`）。D2003 型の実行分割は通りうる。D701 の限界節は、受入固有条件での沈黙と本体未実行を明記しており、この種類の限界を予見していた（`RULINGS:49`）。PLAN:359 にも記載がある。

## freeze hold との相互作用

**所見 C1 — real：hold 解除の追随を次回定期走へ任せると F485 を再演しうる。**

現在 `freeze_verification_hold.py:14` は `HELD=True`。３ defect は無 patch の呼出しで active-valid＋held marker を要求し、`HELD=False` の mock 下で invalid を要求する（`ODT:1898`）。実際の解除時には無 patch 側の期待値も更新が必要になる。

したがって問題は、解除後に拒否挙動を初めて試すことだけではない。**現行 test は解除挙動を既に mock で試しているが、実際の裁定変更に test 全体が追随したかを、その変更の受入で確認する必要がある。** F485 の同日追随漏れと一致する（`RULINGS:209`）。

**所見 C2 — real：PLAN の焦点走条件に解除時の扱いが明示されていない。** PLAN:361 の列挙を、hold 実装・marker 契約・関連期待値の変更まで含むものとして確定し、解除版の有効化前に M の完走を必須にする必要がある。A/B に orchestrator が含まれていても、「焦点走へ追加」だけで完走前の有効化を許せば不足する。

## 親 brief の実測値と一般化

| 主張 | 現物検算・自己判定 |
|---|---|
| M=11 node | **refuted：誤りなし。** `ODT:1293,1361`、`RST:1207` が一致。MT も AST の parameter 展開で60 node |
| 台帳2,302秒、最大240秒 | **refuted：数値は一致。** `acceptance_duration_ledger.json:17781,17829,17854` など11 entry を読み取り集計。全台帳24,379 entry |
| M は timed real-repo lock を持たない | **refuted：登録に基づく timed lock という限定では一致。** M の６関数は conftest の登録文字列にない。`conftest.py:2284` は未登録なら access=None、`:1478` は lock を取らない |
| そこから「M は実 repo に依存しない」 | **real：誤った一般化。** g7 は実履歴と実 checkout を読む（`ODT:4760,4780`）。output copy も実 repo 依存 |
| CI/cron/timer 不在 | **判定保留：repo 内候補の filename 検索では反証なし。** 外部 scheduler・host 設定の不存在までは本検査で証明していない。PLAN:27 の限定が必要 |
| SANCTIONED_EXCLUSIONS 空 | **refuted：一致。** `orchestrator/test_selection_contract.py:61` |
| 2,302秒を除けば同量の wall/CPU が減る | **real：不可。** cache 待ち・I/O・並行実行を含み、残存 shared-base node も実 builder を呼ぶ（`ODT:1047`）。PLAN:366 の限定を維持すべき |
| １ session から300秒未満を保証 | **real：不可。** PLAN:327 は統計的区間・上下限ではないと明記。BRIEF:11 の「ほぼ等しい」も、critical path の因果証明にはならない |

共有 base 検査が毎走に残ることも、M の代替理由にはならない。`ODT:1057` は `issue_receipt=False` であり、builder は発行・検証前に return する（`:1460`）。

本段では既存記録とコードを読み、静的集計だけを行った。pytest、probe 再実行、変更後 wall の測定は行っていない。

## 裁定パッケージと規律 2

**所見 D1 — real：「別系列化する」の成立条件に受理集合の同値性が不足している。** PLAN:346 は４条件を列挙するが、束縛対象と関連変更分類は後続設計に残す（`:361,372`）。このまま実装承認へ使うと、最も重要な正しさ条件が未確定のままになる。

弱めうる gate と必要条件は次のとおり。

| 弱めうる箇所 | 弱めない実装条件 |
|---|---|
| gate 4 の partition | 親が C と版付き系列定義から U/M を独立導出し、U の exact partition と M の適格証跡を land 前に両方要求する |
| gate 2/3・閉包・finished | C 全体の独立比較を維持し、U の閉包と finished=selected を省略しない |
| D701 | 既存 probe を維持し、M 本体の完走保証は別の terminal 証跡で担保する |
| output の拒否経路 | 現行 e2e が読む Git 可視入力の関連変更後は、旧証跡で land を通さない |
| g7 の実 repo 依存 | 実 ccbench checkout・必要履歴を含め、HEAD/tree だけでは表せない検査入力を確定する |
| hold 追随 | hold 変更版の有効化前に、その期待値を伴う M を完走させる |
| TTL・失敗・迂回路 | 利用時に期限と最新失敗を再評価し、未完走の検証済み利用を全対象入口で拒否する |

**所見 D2 — refuted：PLAN が実装済みを装っている、という疑いは棄却する。** PLAN:175,208,374 は未実装・未設計を明記している。ただし成果物の結論も、その限界を引き継がなければならない。模擬11/11を「利用時拒否の実効性成立」と要約してはならない。

## 総括

**現材料では M の移動を承認できるだけの、受理集合不変の証明はない。**

主要な real 所見は、closure A の output 変更取り逃し、g7 の実 repo 入力の束縛不足、hold 解除時の完走条件未確定、模擬 probe と production 実効性の隔たりである。closure B も完全閉包とは未証明。

単体 helper の部分重複、D701 通過、collection 維持、24h TTL のいずれも、この不足を埋めない。裁定パッケージは「毎走維持」または「不足条件を検証する設計調査の継続」までとし、移動は条件成立前に行わない。