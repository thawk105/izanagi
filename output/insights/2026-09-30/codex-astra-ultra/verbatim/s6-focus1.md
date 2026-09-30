## 対応表

| 所見 | 判定 | 確認結果 |
|---|---|---|
| RB-1 | **closed** | 意味を保つ縮約で L1.5 は9,692 bytes。上限・対応テストの6箇所も旧値へ復元。 |
| RA-1 | **closed** | rulings.md 58行に DW-S03 参照を追加済み。 |
| RB-2 | **closed** | RA-1と同じ修正で解消。command のサイズも上限内。 |
| RA-2（不採用 nit） | **closed（裁定上）** | 所要台帳は未更新。不採用裁定どおり既存の実測更新運用へ委ねており、実装修正による解消ではない。 |

6箇所は [check_docs.py:364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/tools/check_docs.py:364) と [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/orchestrator/tests/test_check_docs.py:2777) の2777・3481・3498・3504・4017行。対応する定数・関数内で **base `3cb51f201` の行と厳密一致**した。上限は `9_696`、超過負例は `9_697`、診断文字列は `9697 bytes`。

## 再計算

`4f7512e31` の Git blob を使用。check_docs の層分類と入口の無条件 dispatch 表に従い、重複節を除き、見出し・空行・改行込みの UTF-8 bytes を集計した。

| ファイル | L1.5 に算入した範囲 | bytes |
|---|---|---:|
| workers.md | 全8節＋preamble 26 bytes | 4,284 |
| mutation.md | DW-M02〜M06、M08 | 3,231 |
| operations.md | DW-O01、O02、O05 | 2,177 |
| **合計** | **上限9,696、余裕4 bytes** | **9,692** |

mutation.md と operations.md の preamble は L1 に属するため除外した。

`.claude/commands/rulings.md` は **5,623 bytes**。上限5,623 bytesちょうど。

縮約3箇所の本文はそれぞれ **161→143、245→204、220→183 bytes**。合計96 bytes削減で、fix前の9,788から9,692になる。

## 意味等価の検査

| 対象 | 判定・理由 |
|---|---|
| DW-O01 完了判定文 | **等価**。`.done`・exit codeだけで判定する制約、grep・通知・待ち手rcの排除、最終メッセージからの成果物読取りを維持。 |
| DW-O05 | **等価**。静的検査可と予算切迫時の途中結論・終了をpromptへ記す義務を維持。「テスト実測は親が行い、子の非実走を緑と記録しない」は独立した義務として残り、主体の移動なし。 |
| DW-S05-B | **等価**。凍結境界、land待ちの意図的な赤のxfail化禁止・既存期待値変更禁止、赤の内訳報告を維持。 |
| rulings.md 13行 | **等価**。「次の順で収集」→「順に収集」でも、直後の番号付き収集順、local mainのworklogを正本とする指定、重複計上禁止は不変。 |
| rulings.md 58行 | **fix1では参照補完のみ**。Claude側／Codex側の担当経路、consult・read-only・ultraを維持。全体差分では `--reasoning ultra` の意図した追加があり、その点まで旧版と同一という意味ではない。 |

## 新たな所見

**追加修正を要する所見なし。**

fix1 のコード2ファイルは、上記6箇所以外が `cb3d129ae` と一致。他の変更対象コード6ファイルも同commitと完全一致し、段5の **astra・ultra・委任拒否**は維持されている。文書の対応するmodel・effort・委任禁止記述にも後退はない。

変更Python 8ファイルのAST構文解析と、全体差分の `git diff --check` は成功。

## 総括

指定のfix差分・全体差分を静的に確認し、採用所見の解消、派生値、意味等価性、6箇所の厳密復元を確認した。**partial／regressedに該当する所見なし。**

テスト・check_docs本体・変異実走は行っていない。実走検証は依頼どおり親担当として残る。