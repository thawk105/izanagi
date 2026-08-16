## 判定

NO-GO

## 所見

### 1. D3 は並行発行で破れ、同じ contract の 2 件が両方成功しうる

- `重大度`: blocker
- `根拠`: `orchestrator/campaign/s8b_floor_campaign.py:669`、`:808`、`:824`、`:863`、`:865`、`:870`。index が拒否するのは同一 `(contract_sha256, ccbench_pin)` だけで、同一 contract の異なる pin は許す。D3 判定は書込み前 snapshot に対する一回限りで、lock がない。テストも逐次 2 回だけである (`orchestrator/tests/test_s8b_protocol_builder.py:582`、`:593`)。
- `再現の筋道`: process A/B がどちらも空の index を読む。A が pin A の再実測を終えて停止する。HEAD gitlink を pin B へ進め、B が同じ contract・pin B を発行して成功する。その後 A が pin A を書く。A の post-write scan は同一 contract・異なる 2 pair を正常 index として受理するため、A も成功する。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: D3 の「環境契約 1 世代につき最大 1 件」という受理集合が「異なる pin なら複数件」に広がる。`check-protocol-index` も両方を正常件数として返し、以後どちらが正規 protocol か一意に参照できない。

### 2. lexical path は固定だが、祖先 symlink により repo 外へ発行できる

- `重大度`: major
- `根拠`: `orchestrator/campaign/s8b_floor_campaign.py:691`、`:723`、`:724`、`:1009`、`:1010`、`:1013`、`:1022`。検査する symlink は legacy file と最終 `floor-protocols` component だけで、`output` や `output/s8b-freeze` の祖先は検査しない。writer はそのまま親を辿る。テストも最終 entry symlink しか扱わない (`orchestrator/tests/test_s8b_protocol_builder.py:697`)。
- `再現の筋道`: `output` または `output/s8b-freeze` を repo 外 directory への symlink にし、そこへ valid legacy copy を置く。scan、発行、post-write scan はすべて同じ外部 tree を辿るため、issuer は成功を返せる。scan と write の間に最終 namespace を symlink へ差し替える場合も、外部 file を作った後に post scan が失敗するだけで、自動削除されない。通常 file 判定は hard link も許すため (`:745-755`)、外部 alias から発行済み bytes を後刻変更する窓も残る。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: issuer の受理集合に「repo 外を指す祖先 symlink」が入り、返却される `path` は repo 内 artifact を参照しない。裁定 B6 の「destination を導出するので外を書けない」という前提が成立しない。

### 3. D4 の HEAD blob は単一 snapshot に束縛されていない

- `重大度`: major
- `根拠`: `orchestrator/campaign/s8b_floor_campaign.py:622`、`:632`、`:637`。`git ls-tree HEAD` で得た `_oid` を捨て、その後 `git cat-file blob HEAD:path` で HEAD を再解決している。
- `再現の筋道`: 2 subprocess の間で HEAD を切り替えると、mode・kind を検査した commit と、anchor bytes を読んだ commit が別になる。post-write scan も同じ非原子的 primitive なので、HEAD を同期して切り替える process があれば検査を通過させうる。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: successor の継承 16 field と anchor SHA-256 が、検査済みの一つの HEAD blob を参照しなくなる。D4 が要求する lineage authority の commit/blob identity が曖昧になる。

### 4. issuer 内に入力からは発火しない拒否が残っている

- `重大度`: minor
- `根拠`: `orchestrator/campaign/s8b_floor_campaign.py:809`、`:835`、`:850`。anchor は同じ scan が必ず 1 件挿入し、successor はその anchor の deep copy に可変 2 field だけを代入するため、通常入力から exact-anchor 拒否や inheritance 拒否へ到達できない。
- `再現の筋道`: `:850` の issuer 内 inheritance call を除去しても、生成 document と post-write scan の受理挙動は変わらず、既存テストも同じ経路を通る。外部 artifact に対する `scan_floor_protocol_index` 内の inheritance 検査 (`:768`) は別で、こちらは実際に発火する。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: 現行受理集合は変わらない。ただし issuer の独立防壁として数えると、検査台帳上の gate 数と実効防壁が食い違う。

## 変異 M1〜M8 の生存可能性

- **M1: 殺される。** `test_floor_protocol_index_includes_legacy_and_rejects_duplicate_pair` が legacy pair の存在を直接要求する (`orchestrator/tests/test_s8b_protocol_builder.py:662`)。ただし legacy を index から単純除去すると issuer の anchor exact-one (`s8b_floor_campaign.py:809`) が先に落とすため、「D3 が legacy contract を数える」検出力としては mask されている。
- **M2: 殺される。** 同一 pair の versioned copy は path・document・canonical bytes を満たし、`_index_protocol_record` の重複拒否だけへ到達する (`test_s8b_protocol_builder.py:670`)。
- **M3: 殺される。** 3 field 化は module-level の件数 assert (`s8b_floor_contract.py:45`) とテストの exact set/16 件 assert (`test_s8b_protocol_builder.py:485`) に先に殺される。継承 gate 自体の単一理由 kill ではない。
- **M4: 殺される。** D3 を除くと g1・新 pin が発行まで通るため、公開入口の拒否テストが赤になる (`test_s8b_protocol_builder.py:582`)。ただし所見 1 の並行経路は未検出。
- **M4p: 殺される。** 常時拒否へ倒すと未使用 g2 contract の正例が失敗する (`test_s8b_protocol_builder.py:558`)。
- **M5: 殺される。** validator-admitted dirty legacy を用いた対照が、発行 bytes は committed 値であることを確認する (`test_s8b_protocol_builder.py:640`)。
- **M6: 殺される。** short hash、nested、alias、大文字を含む負例が `.*\.json` への緩和を検出する (`test_s8b_protocol_builder.py:795`)。
- **M7: 殺される。** exact versioned path の正例が pattern 削除で未知 file 拒否になる (`test_s8b_protocol_builder.py:786`)。
- **M8: 殺される。** valid document を別の canonical-looking filename へ置く単一理由 fixture がある (`test_s8b_protocol_builder.py:677`)。

M1 と M3 はテストを赤にするが、事前登録が意図した実効 gate の kill 証拠にはならない。いずれも手前の構造検査に mask される。

## 攻撃したが破れなかった点

- D1 の小文字 `64hex--40hex.json` 文法、`.json` 拡張子、document/path 束縛は、祖先 symlink 問題を除けば閉じている。大文字、Unicode 名、nested path、`..` 相当の別名は regex または非通常 entry 拒否に当たる。
- D2 の chain-record pattern は exact で、過剰受理と欠落の正負テストがある。
- D3 の逐次経路では legacy HEAD anchor が必ず index に入り、g1・新 pin は拒否される。
- D4 で working-tree legacy は parse・validate されるが、index と successor の lineage 値は HEAD bytes から作られている。dirty working tree 値そのものの混入経路は見つからなかった。
- D5 の active contract 再照合はなく、`lookup()` は一度だけである。HEAD gitlink は二度実測される。
- D6 どおり production consumer 6 件への結線はなく、成果は dormant のままである。
- D7 の零引数 API、strict parse、create-only、16/2 field 分割は実装されている。
- `freeze_protocol`、`_freeze_protocol_parser`、`write_protocol_document` は HEAD 版と AST source SHA-256 が一致し、3 関数とも非改変だった。
- 新規 `except` は確認した範囲で成功へ握り潰しておらず、失敗は拒否または非ゼロ終了になる。

## 総括

D1〜D7 の通常・逐次経路は大半が裁定どおり実装されている。  
登録済み M1〜M8 は静的にはすべてテストに殺される。  
ただし M1 と M3 は手前の構造層に mask され、狙った gate の検出力証拠ではない。  
最大の問題は D3 が snapshot 検査に留まり、並行発行を直列化していないことである。  
同一 contract・異なる pin の二件が両方成功し、post-write index も正常扱いできる。  
さらに祖先 symlink により、導出 path の lexical 制約を保ったまま repo 外へ書ける。  
HEAD anchor loader も確認した object ID を使わず、commit/blob identity が原子的でない。  
既存 frozen writer 3 関数の非改変は独立に確認できた。  
pytest は指示どおり実行せず、結論は差分全件と関連コードの静的検査に基づく。  
D3 の原子性と path/HEAD identity を閉じるまでは land 不可である。