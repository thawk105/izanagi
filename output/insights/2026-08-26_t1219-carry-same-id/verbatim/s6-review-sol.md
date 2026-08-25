## 所見

### R-1 台帳 digest が list marker を含まず、別の raw occurrence を既知扱いする
対象: `tools/check_docs.py:2001`  
攻撃: 登録行 `- [T-208] 変わらず ((73) 参照)` を `1. [T-208] 変わらず ((73) 参照)` に変更する。  
なぜ通ってしまうか: digest は `_top_level_items` が marker を除いた `item_text` から作るため同値になり、`observed_known=1` のまま受理される。  
直し方: section の元文字列から list marker を含む論理行 raw text を切り出し、その digest を台帳 key にする。marker 変更の負例も追加する。  
成果物影響: 既知違反台帳の受理集合が、裁定済み raw 行から任意の ordered/unordered marker 書換えへ拡大する。  
重大度: must-fix

### R-2 candidate が正当な非 carry 項目まで包含する
対象: `tools/check_docs.py:1936`  
攻撃: 正当な次の一手として `- [T-500] (D837)` または `- [T-500] (Python 3)` を置く。  
なぜ通ってしまうか: task ID 後が「括弧で終わり数字を含む」だけで candidate になり、両 strict regex は不一致なので正常入力を赤にする。strict parser の受理集合自体は candidate に包含されている。  
直し方: 短縮形候補を空白と数字だけの target 風括弧へ絞り、legacy 風候補は `変わらず` と `参照` で検出する。非 carry の括弧付き正例を追加する。  
成果物影響: 必須 lint の拒否集合が carry 以外の正当な番号付き括弧項目まで拡大する。  
重大度: must-fix

### R-3 sample 上限後の総数が occurrence 数ではなく一意 target 数になる
対象: `tools/check_docs.py:2236`  
攻撃: 25 個の異なる carry occurrence を、同じ不在 target または同じ索引異常 target へ向ける。  
なぜ通ってしまうか: `missing_by_target` と三つの index map が `target` を key に `setdefault` するため、25 件が1件へ縮退し「他 0 件を抑止」と表示される。  
直し方: category ごとに occurrence counter を必ず加算し、sample list だけを20件で止める。target 単位の重複排除を数え上げへ使わない。  
成果物影響: 参照先不在と索引三分類の件数および抑止数が過少計上され、最悪赤経路の成果物値が不正になる。  
重大度: must-fix

## 既存テストの弱体化

なし

## 恒真なテスト

- `orchestrator/tests/test_check_docs.py:11068` の `test_backlog_guard_carry_target_index_states_are_distinct` の `kind="missing"` は、carry 固有の key 不在分岐を削除しても、universe/index 集合不一致 finding の同じ「索引 key 不在」を拾って通る。source path、task ID、target を含む carry 固有 finding を assert すべきである。
- `orchestrator/tests/test_check_docs.py:11108` の `test_backlog_guard_carry_references_are_streamed` は直ちに `list(references)` で全消費するため、関数内で全 occurrence を事前 materialize してから yield する実装でも通る。最初の `next()` 後に `scan.parsed_count == 1` を確認すべきである。

## 総括

既知の4失敗は所見から除外した。  
fail-closed の早期 return は finding を追加するため緑化せず、duplicate skip も先行 finding で赤が保証される。generator は production 経路では最後まで消費され、H2 offset と fixture 定数置換にも追加の破れは見つからなかった。  
追加で、台帳の raw 行束縛、candidate の過包含、occurrence 総数の縮退という3件を確認した。  
pytest は指示どおり実走しておらず、静的レビュー結果である。