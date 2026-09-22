**判定：GO（レンズ B の静的レビュー。受入完了を意味しない）**

must-fix は確認できませんでした。試験の重複と、fallback の観測方法に should の所見があります。以下のコード位置は統合後 worktree 基準です。

| 番号 | レンズ項目 | 所見 | real/refuted の見込み | 重大度 | 根拠 file:line | 成果物への影響 |
|---|---|---|---|---|---|---|
| B1 | 試験の実効 | fallback 後の parse PID assertion は、helper 末尾の `parse_trace_dir(..., workers=1)` による上書きを見ている。workers=2 の対象呼出し直後に確認すべき。 | real | should | `test_verifier.py:3429,3778,3780`、`parse.py:890` | この assertion は parse fallback の成立を証明しない。ただし現実装が障害から逐次へ進むことは静的に確認できる。 |
| B2 | 削除・重複 | legacy は workers を無視するのに workers=1/2 を反復。混在試験・優先順位試験にも同じ重複がある。legacy を一度、compact だけ workers 別にすればよい。 | real | should | `test_verifier.py:3410,3413,3443,3630,3638` | 同一処理の反復が試験量を増やす。削除しても経路網羅性は落ちない。 |
| B3 | 単一理由の fixture | table 拒否試験の R/W は、0R/0W 宣言へ行を追加しており、字句を直すと件数違反が残る。宣言件数も合わせたい。 | real | should | `test_verifier.py:3378,3649,3651` | fixture は単一違反でない。ただし現 assertion は **ParseError** を要求し、件数違反は integrity なので、別理由で試験が偽陽性になる攻撃は不成立。 |
| B4 | 全経路比較 | 「packed」モードは通常 builder を呼ぶだけで、実際に packed 表現になったことを肯定 assertion していない。通常 fixture で型を確認するとよい。 | real | should | `test_verifier.py:3411,3415,3553,3598` | 現コードは packed に進むが、将来常時 tuple fallback になっても経路比較が緑になりうる。 |
| B5 | 過剰・R1 | R1 は既定 False の field、clean 条件、core の印・notes に限定。存在履歴の実装や別 gate の追加という攻撃は不成立。 | refuted | — | `model.py:486,506`、`core.py:63` | v3 の認定を保留しつつ、cycle の構造化結果は残る。 |
| B6 | 過剰・schema | per-file 混在と file 間混在は異なる性質。共通 helper は R2 どおりで、merge 再検査・failure metadata の増設はない。過剰機構という攻撃は不成立。 | refuted | — | `parse.py:271,366,859,897` | エラー優先順位を維持し、計画段階の過大な機構を避けている。 |
| B7 | v2 の局所化 | identity・表示 helper への置換は v3 対応に必要で、v2 では元の文字列を返す。並び順・SCC・旧 reporter の不要な変更という攻撃は不成立。 | refuted | — | `model.py:360,364`、`dsg.py:260,361,780`、`report.py:96` | 静的には YCSB の受理・判定・出力を変える差分を確認できない。全入力の不変を実証したとの主張はしない。 |
| B8 | R8(c) の実効 | last-wins、子 PID、pool 障害、`01/+1/-0`、同一 txn 異表同 hex、R1 と反例二つ、v2 対照は揃う。R1 は印だけを外すと clean になることも確認している。欠落という攻撃は不成立。 | refuted | — | `test_verifier.py:3526,3606,3648,3693,3709,3733,3763` | 非認定が他の違反による見せかけになることを防ぐ。fallback 観測には B1 の限定がある。 |
| B9 | 後続への実効 | table・生 hex・op・commit・tx_type は object／columns に残る。既存表現を作り直さず存在履歴を追加できると推測する。認定抑止の解除点は core の一ブロック。 | refuted（推測を含む） | — | `parse.py:575,592,625,650,662`、`core.py:63,201` | 単位5の足場になる。ただし §3.3 実装と旧出力への配線は必要。field・clean 条件まで完全撤去する清掃は model にも及ぶ。 |
| B10 | 実測の解釈 | 焦点走を受入完了・変異 KILLED の証拠に昇格できない。ログは受入形でないと明記し、実行 nodeid 一覧もない。 | real（証拠の限界） | should | `focus-1.log:1,11,62`、`s5-author-u4r.md:97` | 確認できる実測は **3532 passed / 3 skipped、child rc=0**。受入全走・変異の完了は未確認。 |

R9 は [integrated.diff](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/integrated.diff:1) の追加・削除行を直接集計しました。

| 対象 | 追加 | 削除 | 合計 | 上限 |
|---|---:|---:|---:|---:|
| model.py | 40 | 0 | 40 | — |
| parse.py | 92 | 24 | 116 | — |
| dsg.py | 43 | 35 | 78 | — |
| core.py | 30 | 2 | 32 | — |
| **production 計** | **205** | **61** | **266** | **550** |
| **test_verifier.py** | **436** | **0** | **436** | **800** |

## 総括

レンズ B では GO。production の差し戻しを要する過剰実装は確認できなかった。
R9 は production 266/550 行、試験 436/800 行で上限内。
新規 helper・派生型は使用され、段2・存在履歴・単位5の配線の先取りはない。
試験は legacy の重複反復を削れ、fallback の PID 確認位置は修正したい。
字句・値域拒否は全経路の直積になっておらず、R8(c) の追加項目も揃う。
R1 の非認定は単独理由として試験され、認定抑止の解除点も局所化されている。
存在履歴と単位5は現在のデータ表現に追加可能と推測するが、完成済みではない。
静的読解のみ実施。焦点走の成功を受入完了・変異殺傷確認とは扱わない。