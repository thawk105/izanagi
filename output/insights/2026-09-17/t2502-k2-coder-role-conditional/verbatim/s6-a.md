## 受理集合の照合

**静的レビューは GO、must-fix は 0 件です。** driver と test の作業ツリー内容が commit `c79437d24` と一致することを確認しました。pytest・変異は実走していません。

以下、`L` = `orchestrator/campaign/p3_s4_loop.py`、`T` = `orchestrator/tests/test_p3_s4_loop.py`、`KM` = `orchestrator/campaign/knowledge_manifest.py`。報告資料は射影された同名ファイルを指します。

既存の前段検査を通過する入力について、経路は次のとおりです。

| 経路 | manifest | role | 今回の変更 |
|---|---|---|---|
| emit（run 併記を含む） | 任意 | 任意の有効値／省略 | 変更なし。guard 前に return |
| fixture | 非空を含む | 省略 | 変更なし |
| run、emit なし | 非空 | 省略 | **新たに ValueError** |
| run、emit なし | 非空 | K2 | 変更なし。実 K2 consumer へ |
| run、emit なし | 空 | 省略／K2 | 変更なし |
| run、emit なし | なし | 省略 | 変更なし |
| run、emit なし | なし | K2 | 既存 loader の相互必須検査で拒否 |

- **所見:** D1878 が対象とする run 経路に、過剰拒否・過少拒否は見つからない。`--coder-role ""` は argparse の `choices` で拒否される。manifest は一度読み取った typed object を guard・prepare・projection が共有し、guard 後のファイル差し替えで判定対象だけが変わる再読込経路はない。
- **仮判定:** refuted（受理集合の逸脱）。
- **根拠 file:line:** `verbatim-d1878.txt:3`、`L:2574`、`L:2667`、`L:2689`、`L:2713`、`L:2714`、`L:2739`、`L:2785`、`KM:380`、`KM:461`、`KM:487`。
- **推奨:** 修正不要。「あり／なし」は既存の経路選択に即して読む。厳密には `--run-iteration ""` は既存同様 fixture 経路、`--emit-planner-context ""` は emit 分岐に入らない。flag の字面的な存在まで保証する表現は避ける（nit）。

## 所見

**1. K2 consumer の迂回・緩和**

- **所見:** 追加 block は早期拒否だけで、受理時の loader 引数・schema 検査・K2 consumer 呼び出しを変更していない。非空＋role 省略は build context 作成・prepare・drive より前に止まり、message は `sources_count` と必要な `--coder-role` を示す。
- **仮判定:** refuted（規律 2/3 の後退）。
- **根拠 file:line:** `L:2714`、`L:2720`、`L:2725`、`L:2739`、`L:2779`、`L:2309`、`L:2318`、`L:2348`。
- **推奨:** 修正不要。「全副作用より前」とは広げない。manifest 解決・環境検査などは先行する。

**2. ValueError が成功扱いになる懸念**

- **所見:** CLI は未捕捉例外として非ゼロ終了する。Pegasus job body は `set -Eeuo pipefail` 下で直接起動している。B-4 launcher の base 登録からの呼出しにも、この例外を成功へ変換する処理はなく、`activate_context` は `finally` で状態を戻すだけ。
- **仮判定:** refuted。
- **根拠 file:line:** `L:2901`、`tools/pegasus/p3_s4_loop_pegasus.sh:9`、同 `:581`、`orchestrator/campaign/p3_b4_launcher.py:141`、同 `:475`、同 `:580`、同 `:635`。
- **推奨:** 修正不要。

**3. F649：テストが検査対象を代役へ置換していないか**

- **所見:** N の manifest は fixture 内で実 parser/resolver を通る。main の resolver 接続だけを既存 seam で差し替え、proposal loader は実物のまま。`Mock(wraps=...)` は実 prepare に委譲し、独自の拒否や戻り値を設定していない。正常時には guard が先に止めるため、N が loader を実行するのは guard を無効化した場合である。
- **仮判定:** refuted（検査対象の代役化）。
- **根拠 file:line:** `T:1047`、`T:7214`、`T:7220`、`T:7227`、`T:7230`、`T:7234`、`T:7241`。
- **推奨:** 修正不要。「N が実 loader を通る」は反実仮想時の説明に限定する。

**4. 正例の検証範囲と既存期待値**

- **所見:** P は実 loader／K2 consumer を通し、drive の入口で coder を観測する。F は fixture 実行本体を代役にして main の経路受理を検証する。I は従来から loader と drive を代役にした identity 検証であり、今回もその範囲に留まる。差分は N/P/F 追加と I 後半の role 指定だけで、既存 assert 削除・期待値緩和・skip・xfail はない。
- **仮判定:** refuted（テストを甘くして緑にした懸念）。
- **根拠 file:line:** `T:7159`、`T:7179`、`T:7246`、`T:7285`、`T:6567`、`T:6585`、`T:6587`、`T:7296`、`T:7332`。提供された統合差分とも一致。
- **推奨:** 修正不要。I/F を K2 consumer 自体の実証として数えない。

## 変異の帰属

- **所見:** M0/M1 の前後付き anchor、M2/M3 の条件行、M4 の raise block、M5 の条件先頭 anchor は、実ファイル中で各 1 出現。対象 6 node も各 1 定義。静的な期待赤集合は段 4 と一致する。
- **仮判定:** refuted（anchor の非一意性・期待集合の誤り）。
- **根拠 file:line:** `L:2713`、`L:2717`、`L:2718`、`L:2720`、`T:6521`、`T:7206`、`T:7246`、`T:7269`、`T:7296`、`T:7332`、`s4-ruling.md:75`。
- **推奨:** 以下を親の実測 matrix と照合する。これは実走結果ではない。

| 変異 | 期待 status | 赤 node 完全集合 | 緑のままの node | 帰属 |
|---|---|---|---|---|
| M0 | SURVIVED | なし | N/E/K/P/I/F | comment のみ。意図した等価対照 |
| M1 | KILLED | N | E/K/P/I/F | 実 legacy loader 後、drive spy 到達 |
| M2 | KILLED | N/E | K/P/I/F | N は拒否消失、E は空取得を過剰拒否 |
| M3 | KILLED | N/P/I | E/K/F | N は拒否消失、P/I は role 付き run を過剰拒否 |
| M4 | KILLED | N | E/K/P/I/F | `pytest.raises` 不成立 |
| M5 | KILLED | F | N/E/K/P/I | fixture を過剰拒否 |

N の flattened proposal では、role 省略時に main が loader へ渡す `knowledge_input` も `None` となるため、相互必須検査は先回りしません。manifest は実 resolver 済み、role は省略なので、parser・argparse による別原因の拒否もありません。

**M5 の置換表現**

- **所見:** 「`a.run_iteration` の行を除去」を文字どおり行削除すると、先頭に `and` が残り構文エラーになる。上表は run 条件だけを論理的に除く、構文的に有効な変異の予測である。
- **仮判定:** real（登録文の曖昧さ）。
- **根拠 file:line:** `s4-ruling.md:82`、`s5-author-out.md:164`、`L:2714`。
- **推奨:** nit。harness の置換後を `if (` の次行が `resolved_knowledge is not None` となる形で明記する。構文エラーによる collection 失敗は M5 の帰属証拠に数えない。

## 記述の食い違い

**1. K が緑に留まる理由**

- **所見:** 段 4 の「K は sources 空で短絡するためどの変異にも現れない」は M2 には当てはまらない。M2 では反転した sources 条件が真となり、role ありにより最後の条件が偽になる。期待集合自体は正しい。
- **仮判定:** real。
- **根拠 file:line:** `s4-ruling.md:79`、同 `:84`、`L:2717`、`L:2718`、`T:7336`、`T:7347`。
- **推奨:** nit。M2 だけ短絡理由を訂正する。受理集合・matrix の期待値変更は不要。

**2. brief の仮説と確定仕様**

- **所見:** brief の M3→K、M5→I、無条件の bytes 不変という記述は、確定仕様には使えない。段 4 はそれぞれ M3→N/P/I、M5→F、同一外部結果を前提とする構築ロジックの不変へ修正済み。実装は確定仕様に従う。
- **仮判定:** real（旧記述との相違、裁定済み）。
- **根拠 file:line:** `s1-brief.md:18`、同 `:26`、`s4-ruling.md:17`、同 `:18`、同 `:20`、`s5-author-out.md:113`。
- **推奨:** nit。最終報告・台帳には段 4 の修正版を使い、brief の仮説を再転記しない。

**3. D1878 の「正例を 1 件も壊さず」と I の変更**

- **所見:** 既存テストを一切変更しないという意味では、この理由文は成り立たない。I 後半が対象の非空＋role 省略を使っていたため。ただし role を足して identity 一致の期待値を保つ対応は、D1878 の決定本文に一致する。
- **仮判定:** real（理由文の一般化、裁定済み）。
- **根拠 file:line:** `verbatim-d1878.txt:10`、`s1-brief.md:27`、`s4-ruling.md:13`、`T:6585`。
- **推奨:** nit。既存テスト無変更と、意味上の正例維持を区別して記録する。

実装子報告の production・I・N/P/F の行番号と差分量は実体に一致します。E/K の現行定義開始はそれぞれ `7296`／`7332`。段 4 の `7205`／`7241` は変更前の参照です。直接呼び出し・反実仮想の結果は実装子の報告値として扱い、独立実測とはしていません。

## 総括

**GO — must-fix 0 件。**

D1878 の対象経路を閉じ、既存 K2 consumer の検査を維持しています。残る指摘は記述上の nit です。親から提示された焦点 6 passed と本静的レビューを区別し、変異 matrix・consumer 焦点走・受入全走の成功は本レビューでは認定しません。