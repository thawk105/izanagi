## 所見

### S-1 carry 風の不正文法は母数を増やさず即座に検査を迂回する
対象: `tools/check_docs.py:1003-1009`, plan「恒真化しない根拠」
攻撃: 末尾 entry に `- [T-999] 変わらず ((073) 参照)` を追加する。ID は有効だが target の先頭ゼロで両 carry regex から外れる。
なぜ通ってしまうか: 通常の次の一手項目として受理され、既存 404,326 件も減らないため母数下限を満たす。同一 ID 検査には一度も入らない。
直し方: carry 標識を含むトップレベル項目を別の broad regex で検出し、正式文法へ parse できなければ専用 finding にする。崩した括弧、空白、先頭ゼロの positive control を加える。
重大度: blocker — 新しい壊れた carry を 1 行追加するだけで中央の gate が発火しない。

### S-2 非採番 archive の carry は明示的に恒真化されている
対象: `tools/check_docs.py:2727-2736`, `orchestrator/tests/test_check_docs.py:10856-10876`, plan「変更プラン」6
攻撃: 非採番 archive の entry に `- [T-050] (999)` を置く。既存テストはこの入力で宙吊り finding 不在と rc=0 を要求している。
なぜ通ってしまうか: carry source 登録が `classification == "numbered"` に限定され、`numbered_archive_input_complete` も偽にならない。
直し方: 読めた全 worklog archive の番号付き H2 を source と target の索引対象にする。除外を維持するなら D837 の archive 全体という scope を狭める新規裁定が必要。
重大度: blocker — 現存テストが検査対象消失を正常動作として固定している。

### S-3 固定下限は将来の部分消失を検出しない
対象: plan「既知違反台帳の設計」末尾、plan「残る危険」
攻撃: carry が 500,000 件へ増えた後、parser 退行で 50,000 件を落とす。観測 450,000 件は固定下限 404,326 以上である。
なぜ通ってしまうか: 条件は `checked_count >= 404326` だけで、候補集合に対する完全性や自動 high-water ratchet がない。
直し方: 独立に数えた carry 候補数と parse 成功数を一致させ、固定下限は補助条件に降格する。source 単位の候補数も照合する。
重大度: must-fix — brief の「母集合が部分でも緑にならない」と論理的に両立しない。

### S-4 索引 key の欠落経路が positive control にない
対象: plan「テストプラン」8、plan「変更プラン」4 手順7
攻撃: `locations` には target 73 があるが `next_action_ids_by_entry` から key 73 自体を落とす。テストは `73: None` しか試さない。
なぜ通ってしまうか: 実装が欠落を空集合扱いすると、4 件は通常 mismatch となって既知台帳に吸収される。母数も維持される。
直し方: sentinel を使い「key 不在」「値 None」「空 set」を三分する。key 不在の direct test と、索引構築からの end-to-end test を追加する。
重大度: must-fix — 最も重要な target 73 の索引構築失敗が台帳によって隠れ得る。

### S-5 母数と違反抽出が同じ parser に依存している
対象: plan「変更プラン」3、5、6
攻撃: `_top_level_items` が長い section の後半だけを返さなくなる。短い synthetic archive の既知4件と主要 positive control は前半に残す。
なぜ通ってしまうか: carry の認識、母数加算、台帳観測がすべて同じ iterator の出力なので、落ちた要素を示す独立観測がない。下限以上なら赤にならない。
直し方: 長大 section、複数 section、途中打切りの mutation test を追加する。raw の carry 風候補数を別経路で数えて yield 数と照合する。
重大度: must-fix — 小さい合成コーパスでは実コーパス固有の縮退を再現できない。

### S-6 台帳 key は凍結 entry 内の内容差替えを識別しない
対象: plan「既知違反台帳の設計」、`tools/check_docs.py:2340-2352`
攻撃: entry 74 の既知行を削り、同じ entry 内の別内容へ `[T-209]` と target 73 を再利用する。tuple と観測数は変わらない。
なぜ通ってしまうか: `(source_entry, task_id, target_entry)` だけが同一なら、行の意味や item bytes の差替えを同じ既知債務として受理する。
直し方: archive 移動で変わらない H2 digest と top-level item digest を key に加える。既存 placeholder 台帳の scope と line digest の組を踏襲できる。
重大度: must-fix — F58 型の ID 内容差替えを、既知違反台帳自身が吸収する。

### S-7 親 probe と production traversal の同値性が証明されていない
対象: `materials/parent_measurements.md:1-17`, plan「変更プラン」3、6
攻撃: probe が非採番 archive、section 抽出条件、または carry 文法の一部を production 案と異なる条件で数えていた場合、404,326 は別の母集合の値になる。
なぜ通ってしまうか: 射影された実測記録には出力しかなく、source 選別別・文法別の内訳や production iterator との parity がない。
直し方: 同一 snapshot で probe と実装 iterator の occurrence key を比較し、current・採番 archive・非採番 archive・文法別の差分をゼロ確認する。
重大度: must-fix — hard-coded floor と既知4件の根拠が実装の受理集合へ移送できていない。

### S-8 「違反4件」は新設する索引不能 finding のゼロを意味しない
対象: `materials/parent_measurements.md:3-13`, plan「変更プラン」4 手順7
攻撃: 実在する過去 entry を指す carry の target が、ID 導入前で索引不能だったとする。probe がその target を mismatch 集計から除外していれば4件という結果は保たれる。
なぜ通ってしまうか: 実測は索引済み entry 957件だけを報告し、参照された missing key・None target の件数を報告していない。
直し方: proposed tri-state index で実コーパスを事前走査し、索引不能 target と occurrence がともに0かを別集計する。非ゼロなら段4の裁定対象にする。
重大度: must-fix — 実装後の `test_real_repo_clean` を支える baseline が不足している。

## 親 brief への反証

- P3 の「単調増加する母数」は検査対象の完全性を保証しない。非採番 archive への移動は source を母集合から外し、将来の増分は部分消失を固定下限より上で隠す。
- P5 の最低3本では不足する。carry 風不正文法、索引 key 不在、長大 section の途中打切りが未被覆である。
- 「既存違反はちょうど4件」は ID mismatch の観測値に限られ、新設する索引不能カテゴリが0件である根拠にはならない。
- F58 は同一 ID の内容差替え事故であり、参照先に同じ ID があるかを見る本 gate だけでは検出できない。F79 と同じ検出力の族として一般化できない。

## scope 外だが real な所見

- `/rulings`、fold、land が carry と判定する文法と、本 checker の二つの regex が一致する保証が射影資料にない。共通 parser 化または consumer ごとの契約テストを別裁定へ返すべきである。
- `check_docs.py` が land 前の全経路で必須実行されるかは本2ファイルの変更では保証されない。dirty worktree を直接読む rulings 収集を含め、発火面の監査を別 package にする必要がある。
- F58 型の「同じ ID で内容を差し替える」検査は D837 の同一 ID carry gate とは別機構である。今回へ混入せず、内容同一性 gate の裁定候補として残すべきである。

## 総括

最も危険なのは S-1 であり、carry 風の typo を1行追加するだけで母数も違反数も動かず検査が発火しない。  
現状のプランは採用不可である。非採番 archive の明示的除外と固定下限だけの完全性主張も閉じる必要がある。  
入力不完全 finding が実際に追加された場合は `tools/check_docs.py:6327-6333` で rc=1 へ伝播するため、その早期 return 自体は恒真ではない。問題は完全性フラグが対象外 archive や parser の見落としを表さない点にある。  
段4では、全 archive を対象にする境界、carry 風不正文法の fail-closed 化、独立母数、台帳 digest、probe parity を裁定すべきである。  
静的検査のみで、pytest および checker の実走は行っていない。