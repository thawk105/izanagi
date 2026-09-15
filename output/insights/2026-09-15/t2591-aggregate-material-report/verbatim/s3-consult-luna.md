## file:line 照合表

**結論：プランは修正が必要です。** 主な問題は、撤回済みの Markdown 要件が残っていること、evaluator への床値到達を投影値だけで証明しようとしていること、登録・所要時間の間接影響の説明不足です。以下はすべて静的読解であり、pytest・変異実走はしていません。

参照の基点は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2591-aggregate-material-report`。略号はプランと同じです。

- `T`：`orchestrator/tests/test_p3_b4_material_report.py`
- `IT`：`orchestrator/tests/test_p3_b4_floor_artifact_issuer.py`
- `S`：`orchestrator/tests/test_real_repo_serialization.py`
- `R`：`orchestrator/campaign/p3_b4_material_report.py`
- `I`：`orchestrator/campaign/p3_b4_floor_artifact_issuer.py`
- `D`：`orchestrator/tests/test_floor_pair_driver.py`
- `C`：`orchestrator/tests/conftest.py`
- `L`：`orchestrator/tests/acceptance_duration_ledger.json`

**照合所見**

- **所見：** 指定行はすべて実在する。`D:53`・`D:73` は想定する helper の参照ではない。一部の関数参照は定義行ではなく本体を指す。
- **根拠：** 下表。
- **real か推測か：** real、現物の行番号と内容を読解。
- **放置時の影響：** 誤った編集先・説明根拠になる。関数本体への参照は意味自体を変えない。
- **推奨：** 不一致と定義位置だけ訂正する。

| 参照 | 現物・照合結果 |
|---|---|
| `T:98` | authority 手書き dict。一致 |
| `T:101` | `floor_exact: [0, 1]`。一致 |
| `T:116` | summary hash の `"1" * 64`。一致 |
| `T:122` | spec hash の `"2" * 64`。一致 |
| `T:131` | artifact bytes の直接書込み。一致 |
| `T:132` | 実 bytes の SHA-256 計算。一致 |
| `IT:1187` | `_aggregate_public_sources` 定義。一致 |
| `IT:19` | `test_floor_pair_driver` の module import。一致 |
| `IT:53` | `_synthetic_source` 定義。一致 |
| `IT:73` | `driver_tests._install_git` 呼出し。一致 |
| `IT:188` | `_preregistration` 定義。一致 |
| `S:362` | 材料レポート canonical node golden。一致 |
| `S:426` | real-repo fixture access golden。一致 |
| `S:998` | fixture consumer 集約開始。一致 |
| `S:1263` | xdist group 契約定義。一致 |
| `S:1338` | group 別 canonical node 集合の完全一致。一致 |
| `S:1585` | 全 collection 契約テスト定義。一致 |
| `S:1589` | xdist group 契約呼出し。一致 |
| `S:1615` | long-lived fixture group 契約呼出し。一致 |
| `R:54` | path 文字列の `GENERATOR_IDENTITY`。一致 |
| `R:955` | source dict の return。意味は一致、関数定義は952行 |
| `R:958` | schema 転記。一致 |
| `R:973` | exact ratio の構築。意味は一致、投影関数定義は963行 |
| `R:990` | `not_guaranteed` への追加。一致 |
| `R:1046` | 比較用 floor dict。意味は一致、検査関数定義は1034行 |
| `R:1097` | `_render_markdown` 定義。一致 |
| `R:1214` | Markdown の floor/path/hash 置換。一致 |
| `R:1230` | 公開 builder 内のロード。意味は一致、builder 定義は1222行 |
| `I:55` | path 文字列の `GENERATOR_IDENTITY`。一致 |
| `I:1202` | 非保証列の構築。一致 |
| `I:1270` | 全 source から authority 再構成。一致 |
| `I:1274` | `B4AuthoritativeFloor` 構築。一致 |
| `I:1324` | v2 分岐。一致 |
| `I:1340` | v1 schema 検査。一致 |
| **`D:53`** | **空行。`_synthetic_source` は `IT:53`。** |
| **`D:73`** | **portable build record の `variant_id` 計算。Git helper 呼出しは `IT:73`、定義は `D:335`。** |
| `D:370` | `F.subprocess.run` の差替え。一致 |
| `D:405` | `_real_git` 定義。一致 |
| `D:417` | 実 Git repo 初期化 helper。一致 |
| `conftest.py:1538` | 台帳件数不一致の判定。一致 |
| `test_acceptance_schedule_order.py:660` | 実 collection の台帳 coverage テスト。一致 |
| 同`:712` | coverage ≥ 90% の assertion。一致 |
| `floor_pair_driver.py:1212` | 実 HEAD 解決。一致 |
| 同`:1237` | HEAD tracked blob 取得、1238行で bytes 比較。一致 |
| 同`:1285` | source commit と HEAD の同一性拒否、1290行で祖先検査。一致 |
| `L:1931` | m9 `[False-False]`、11.0秒。一致 |
| `L:1932` | m9 `[False-True]`、11.0秒。一致 |
| `L:1933` | m9 `[True-False]`、11.0秒。一致 |
| `L:1934` | m9 `[True-True]`、11.0秒。一致 |
| `L:1935` | 既存 present-floor 非保証テスト、0.002秒。挿入位置の目安として一致 |
| `L:23113` | `nodeid_count: 23109`。実項目数も23109 |
| `p3_b4_producer_auth_experiment.py:439` | 既存 normal-path node の定数。一致 |

なお、段2本文は「`_synthetic_source`（53行）」「`D._install_git`（73行）」という曖昧な書き方です。攻撃対象一覧の `D:53`・`D:73` と混同しないよう、`IT:53 → IT:73 → D:335 → D:370` と明記すべきです。

追加参照の `T:30/41/56/59/77/190/226/248/257/842/958`、`IT:1189`、`R:267/1195`、`S:1295` も記載された意味と一致します。

## 登録先閉包の漏れ

### 1. 手動登録先は増えないが、契約の列挙が不足している

- **所見：** 現物から追加の必須登録先は見つからない。ただしプランは、自走 harness、共有 fixture 閉包検査、実 collection を使う shard テストを省略している。
- **根拠：**
  - `S:362 → S:398 → S:1338 ← S:1615`：新 canonical node の登録漏れで集合一致が赤。
  - `S:1588 → S:998 → S:1295 → S:1345`：fixture consumer 集約を実 collection から導出。
  - **`S:1619 → S:1431 → S:1435/1459`**：共有 fixture を介した real-repo resource consumer 閉包の検査。`immutable_publication` は今回の resource seed に入らず、追加登録は不要。
  - **`S:1734 → S:1739 → S:1748/1749`**：実 collection を allocator と shard 閉包検査へ渡す。
  - **`T:1480 → T:1481`**：自走 harness は `pytest.main([__file__])`。関数名リストへの手動追加は不要。
  - `p3_b4_producer_auth_experiment.py:439 → :445/:450`：固定 normal-path node を返すだけ。新テストの網羅契約ではない。
- **real か推測か：** real、参照を二段以上追った静的確認。ASTでは現状31関数対31 golden、欠落・余剰ゼロ。
- **放置時の影響：** 登録不足というより、変更後に確認すべき既存契約が説明から落ちる。
- **推奨：** この参照閉包を既存検証項目へ補足する。新しい gate・登録表は不要。

### 2. 台帳未登録は「赤になる」と限らず、群全体のスケジュールを変える

- **所見：** 新 node の欠落と `nodeid_count` 不一致は別の故障である。
- **根拠：**
  - `C:1538 → C:1540`：件数不一致は台帳全体を空として扱う。
  - `C:1675 → C:1719 → C:1741`：一つでも duration 不明なら、その実行単位全体を未知コスト扱いにする。
  - `tools/acceptance_shards.py:895 → :902 → :397/:404`：shard allocator は未登録 node に1秒を与える。
  - `test_acceptance_schedule_order.py:704/712`：coverage はJSONのキー集合を直接数える。`nodeid_count` 不一致をこの assertion だけでは検出しない。
- **real か推測か：** real、コード読解。
- **放置時の影響：** テストの受理集合を保ったまま、材料群の実行順・shard の推定負荷が変わる。coverage が緑でも台帳 consumer が空になりうる。
- **推奨：** 新 node と count を整合させる現案を維持し、「登録漏れなら必ず赤」と説明しない。

## 既存期待値への波及

### 1. cache 汚染の経路はあるが、計画どおりなら踏まない

- **所見：** cache は authority root をキーに含めない。しかし新テストが直接 builder を呼ぶ限り、既存 cache を汚染しない。
- **根拠：** `T:53/54/248/257` は publication root だけをキーにする。`R:1230/1238` は新しい inputs/report を構築する。`T:858` のm9は別 publication を作る。fixture 内の patch は `T:190` の context を抜け、`T:221` の return 前に復元される。
- **real か推測か：** cache の不足したキーは real。新テストによる汚染発生は未実装なので条件付き。
- **放置時の影響：** 新テストで `_inputs`・`_document` を使えば、先行 cache により集約経路を通らない、または集約 document を後続 absent テストへ返す経路になる。
- **推奨：** 直接 builder 呼出しを維持する。共有 publication 配下を変更しない。既存 golden やm9期待値の変更理由は見つからない。

### 2. shard の移動と fixture の再構築を、期待値変更と混同してはいけない

- **所見：** node追加で群の負荷・担当 shard は変わりうるが、現行割当は材料群を分割しない。
- **根拠：** `T:41` の module mark、`tools/acceptance_shards.py:325/332/481/484/486` の file/group 閉包。`C:1733/1766` は単位内の順序を保持する。
- **real か推測か：** 閉包と順序保持は real。変更後の担当 shard・時間は未測定。
- **放置時の影響：** cache・module fixture は別プロセスでは作り直され、時間帰属が変わる。ただし、これだけから既存 bytes の変化は導けない。
- **推奨：** 群内の順序違い・単独実行での非干渉は**親が測れ**。既存値が変わると先取りして golden を更新しない。

### 3. `analysis.floor_argument` は evaluator 到達の観測値ではない

- **所見：** プランの assertion 群では「最大床値で解析した」という主張が強すぎる。
- **根拠：** 実引数は `R:267/269`。一方、`R:995–997` は evaluated なら report の `floor_argument` を authority の ratio で上書きする。`R:1071` の検査もその投影値との比較。既存m9は `T:871–878/901–907` で別途実引数を観測している。
- **real か推測か：** 観測の欠落は real、静的読解。具体的変異の生存は非実走。
- **放置時の影響：** evaluator へ別の有効床値を渡しても、レポートの床値・引数表示だけは最大値になり、新正例が誤った解析参照を見逃しうる。
- **推奨：** 親の要求済み変異 matrix で、実引数を非最大値へ変えた場合を**親が測れ**。殺せなければ「集約値のレポート投影を検証」と証拠範囲を記し、解析引数まで検証したと報告しない。新しい防御機構は不要。

## scope と並行衝突

### 1. 実 Git fixture は、現在の許可 seam を守るために必要

- **所見：** 最小限の Git seam 条件化は scope 逸脱とは判定しない。ただし、集約投影それ自体が実 Git を必要とするわけではない。
- **根拠：** `IT:1189 → IT:73 → D:370` は標準 `subprocess` module の `run` を差し替える。偽 Git は `D:363` で作業木を tracked blob の代用にし、`D:368` で祖先判定を指定戻り値にする。patch を外すと `floor_pair_driver.py:1212/1237/1285/1290` が実 Git を要求する。
- **real か推測か：** real、読解。
- **放置時の影響：** seam の無変更再利用は親 brief の許可集合違反。patchだけ除去すると、仮のHEAD・source commitを持つ既存合成入力を実 issuer が受理できない。
- **推奨：** keyword の既定動作を維持し、新正例だけ無効化する最小変更に限る。実 Git 化では spec bytes・pin・summary の `loaded_head` を揃える。共有 support module への移設や Git 用の一般基盤は不要。

### 2. 衝突しやすさは、未観測 wave の名前より編集箇所で評価すべき

- **所見：** 5 wave の具体的差分は未観測であり、特定 wave との衝突を断定できない。共有編集面の局所性には差がある。
- **根拠：** `IT:53/73/1187`、`S:362`、`L:23113`。
- **real か推測か：** 本 wave の編集位置は real。他 wave との重複は推測。
- **放置時の影響：** helper既定の競合は既存 issuer テストへ波及し、台帳countの競合は台帳全体の無効化につながる。
- **推奨：**

| 編集面 | 衝突の性質・減らし方 |
|---|---|
| `IT` の共通 helper | 同じhelperを触る変更とは意味上の衝突が大きい。引数・条件分岐・転送だけに限定 |
| `S` の材料群 golden | 材料群の同じ集合への追加とだけ行競合しやすい。集合全体の並べ替えをしない |
| `L` の node項目 | 同じ近傍への挿入は行競合しうる。新node一件に限定 |
| `L` の `nodeid_count` | 他waveも件数更新すれば同じ行に集中する。統合後の実項目数から確定し、片方の数値を採らない |

## 親 brief への反証

### 1. 「所有を素集合に割れない」は根拠不足

- **所見：** 実装子1本は合理的だが、分割不能ではない。
- **根拠：** 編集所有は `T` の正例、`IT` の helper、`S/L` の登録に分けられる。結合点は helper 引数と新 node 名。
- **real か推測か：** 分割可能な編集面は real。単独実装が効率的という判断は推測。
- **放置時の影響：** 成果物の値・受理集合は変わらないが、並列化方針の説明が事実以上になる。
- **推奨：** 「分割不能」ではなく「一つの正例のため、調整費用を避け実装子1本」とする。

### 2. path identity から「編集してもpinは壊れない」は導けない

- **所見：** 定数の型に関する主張は正しい。pin全般への一般化は誤り。
- **根拠：** `R:54`・`I:55` はpath。しかし `I:1315–1321` は成果物bytesのhashを検査し、`I:1270–1272` は再構成結果とも比較する。
- **real か推測か：** real、読解。
- **放置時の影響：** 将来 production を変更して出力bytesが変われば、同じpath identityでも既存 artifact pin と不一致になる。
- **推奨：** 「今回のテスト限定変更では生成器・既存成果物を変更しない」と限定する。

### 3. 事前登録は材料レポートbytesをpinしていないが、floor成果物にはhashを要求する

- **所見：** 親の(c)は対象を区別すれば成立する。
- **根拠：** `docs/phase3-b4-reflux-ablation-preregistration.md:161/259–266` がpinするのは分析source閉包5 member。材料レポート生成器・issuerは含まれない。一方、`:162` のfloor欄は未記入で、`:282–304` は集約成果物のpath/hashを要求する。
- **real か推測か：** real、文書の現物確認。
- **放置時の影響：** 「生成器の出力bytesをpinしない」をfloor成果物にまで広げると、必要な出典hashの拘束を誤解する。
- **推奨：** 「材料レポートJSON/Markdownの固定hashはない。floor artifactのhash pinは要求されるが現状未記入」と書く。

### 4. Markdown非保証要件の撤回は正しい

- **所見：** 撤回後も段2に残る「解消不能」「非保証assertionを削らない」は失効している。
- **根拠：** `R:1097–1192` は非保証列を描画せず、`R:1195–1219` はfloor・path・hashだけを追加する。v1/v2分岐はない。ただし `R:1141` の一般的な非認証説明は存在する。
- **real か推測か：** real、読解。
- **放置時の影響：** 不要な赤を作るか、本来不要なproduction変更を誘発する。
- **推奨：** JSONの逐語非保証とMarkdownのfloor/path/hashを検証する。撤回済み条件による停止は不要。

### 5. 実測到達と研究上の発効を混同している

- **所見：** 「レポートは certification 成果物」「テストで届くと示せない限り引用できない」は現物より強い。
- **根拠：** `R:1057–1062` は `evidence-only`・`not_in_effect`。事前登録`:303–305` は測定・記入・発効を別条件として残す。
- **real か推測か：** 表示・規範は real。「一度も実測されていない」という過去全体の主張は今回の静的調査では未確認。
- **放置時の影響：** 合成入力の正例緑を、実測床値の採用資格や実験発効の証拠として過大評価する。
- **推奨：** 成果を「実issuerの集約bytesがevidence-only材料レポートへ投影される正例」と限定する。

## 総括

### 所要時間と受入判断

- **所見：** warm 10–20秒／cold 60–90秒は未測定の仮説としては使えるが、台帳だけから裏付けられない。warmは高めの可能性もある。
- **根拠：** m9の11秒には `T:858` のpublication再発行がある。新案はそれを省く。normal-pathの58秒は `T:269/275` で入力ロードとdocument生成の双方を行い、fixture構築費の内訳も台帳から分離できない。新案には集約発行・明示resolver・builder内部resolverによる再検証が増える。既存材料テストの台帳49項目合計は **166.276秒**。
- **real か推測か：** 台帳値・処理経路はreal。新テスト時間は推測。
- **放置時の影響：** 仮にwarm見積りどおりなら群の推定占有は約176–186秒になる。群は分割されないため直列負荷が増えるが、これを全体wallの増分や5分以内の保証には換算できない。5分対象の最遅shardは `docs/decisions.md:57129` に明記されている。
- **推奨：** **親が測れ。** 新nodeのcold/warm、既存材料群、受入の最遅shardを区別して記録する。15秒を実測値として台帳に書かない。

**実装前に直すべき点は、参照表記、撤回済みMarkdown条件、evaluator到達の証拠範囲です。** 実Git fixtureの最小変更と既存2登録先の更新は妥当です。既存golden・m9期待値・productionを変更する必要は、今回の静的調査では見つかりませんでした。