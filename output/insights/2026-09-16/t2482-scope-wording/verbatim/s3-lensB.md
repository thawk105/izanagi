## 数値と定義の照合

**数値は一致。ただし、非 import 委譲の除外文言に must-fix がある。**

以下、`plan` は射影の `stage2-plan.md`、`T733`・`T2344` は各先行 insight の `README.md`、`probe` は `probe-closure.md` を指す。

| 項目 | 現行 JSON | 正例対照 JSON |
|---|---:|---:|
| 収載 | 63 | 63 |
| 発見集合 | 162 | 140 |
| 未収載 | 99 | 77 |
| 1 段展開 | 83 | 81 |
| 1 段展開の未収載 | 20 | 18 |

両 JSON の配列長・重複除去後の件数・`discovered − enrolled = unenrolled` を確認した。現行 JSON の収載配列は production tuple と順序込みで一致する。発見集合の差は追加 22、削除 0。

根拠：`closure-head-e667c8c13.json:4,70–73,95,259`、`closure-control-2143a49c0.json:4,70–73,93,235`。

発見集合の定義も整合する。probe は収載 tuple を seed とし、`orchestrator` 内で解決できる AST の import と package `__init__.py` を反復展開する（`probe:70–87,91–166,173,206`）。関数内・条件分岐内の import も含み、実行到達集合ではない。

T733 の 131 は first-party import の推移的な発見集合であり、package 初期化の見落としを訂正した値（`T733:16–18,23–48`）。T2344 は同 probe による歴史 commit の 62／131／69 再現と member 集合の一致を記録している（`T2344:45–55`）。資料上、同じ語で別の集合定義を名乗る問題はない。ただし今回は歴史 probe を再実行していない。

## 所見

**1. must-fix — 「非 import 委譲は本 map の外」の無条件な維持は実態と矛盾する。**

`plan:16–17` は旧句を維持する。しかし `verify_fanout_worker.py` は tuple 末尾に収載済みで、収載 member の `pipeline.py` が ssh 経由の `python -B -m` で起動する。JSON の全 import edge に、この worker を target とするものはない。発見集合に入る理由は seed としての明示収載である。

根拠：`orchestrator/campaign/campaign_lock.py:54,112`、`orchestrator/campaign/pipeline.py:826–839`、`closure-head-e667c8c13.json:361`、`evidence.md:58–62`。

最小修正は、除外句を「**収載 path の source bytes を除き、**data/schema、生成物、subprocess、…を含む非 import 委譲は本 map の外であり、完全性を主張しない」と限定すること。worker の source bytes の束縛を、ssh・別 interpreter・binary を含む実行全体の保証へ広げない。

成果物影響：放置すると材料レポートの `excluded_scope` が、実際に収載した非 import 委譲先の source bytes まで対象外と説明し続ける。tuple・受理集合は変わらない。

**2. should-fix — 親 brief の「E1 値不変」は条件を限定する必要がある。**

`brief.md:13`、`evidence.md:41` の無条件な不変指定は不正確。scope 文字列は preimage の独立 field ではないが、編集対象の `artifact_admission.py` 自身が収載されている。修正後の blob を記録する新規 lock では、その digest が E1 に入る。`plan:95` の訂正が正しい。

根拠：`orchestrator/campaign/campaign_lock.py:57`、`orchestrator/campaign/artifact_admission.py:1057–1065`。

「preimage 形式と、同じ記録済み map から再導出する E1 は不変」とする。

成果物影響：新規 lock を参照する材料レポート・試行台帳の E1 は変わり得る。既存 lock 由来の E1 と記録済み成果物は変更しない。

**3. nit — P1 は成立するが、現在の収載数と snapshot をさらに明確に分けられる。**

`plan:9` の `curated exact 63 path` は日付句より前にあり、63 が現在の tuple の説明であることは読める。ただし `plan:10–11,23` は収載数も測定時点に係るため、次の形がより明瞭：

> curated exact 63 path; 発見集合は収載 tuple 起点の静的 import・package 初期化の展開による。2026-09-16 (e667c8c13) の発見集合は 162 module、うち未収載 99 module。

実際の配置は既存の二定数へ分け、非推移閉包の句を残す。snapshot は将来も過去の測定事実として読めるが、tuple 変更時の収載数更新まで不要にはしない。

根拠：`plan:9–11,23,29`、`rulings-verbatim.md:48–55`。成果物影響：現時点の値・参照は変わらず、日付の係り先の明瞭化のみ。

**4. nit — P2 は scope 内だが、発行器への言及は省ける。**

発見集合の意味を限定する説明は「本題の文言整合」に収まる。最小句は：

> 発見集合は収載 tuple 起点の静的 import・package 初期化の展開に限る。

`plan:18–19` の「発行器全体を網羅する集合ではない」も現行 JSON と矛盾しないが、集合の定義だけで目的を満たせる。到達不能な module をすべて未束縛と断定する句にはしない。

根拠：`user-instruction-verbatim.md:5–7`、`probe:138–166`、`plan:18–19`。成果物影響：値・参照の変更はなく、説明の短縮のみ。

## 親 brief・実測の点検結果

**P3 の内訳削除は妥当。** 24／36／2 は T733 当時の追加根拠であり、現在の直接 import 被覆の分類ではない（`T733:16–18`、`T2344:59–67`）。63 本目は「明示 import 先」ではなく subprocess 委譲先の明示収載である。production の参照検索も tuple と launcher の二箇所だった。内訳を残すなら歴史的追加理由と明記する必要があるが、現行保証文から落とす方が誤読を減らす。ただし、削除だけでは所見 1 の矛盾は解消しない。

**D1651 の五要素は計画にすべて残っている。** path 数、非推移閉包、未収載数、非 import 委譲の除外、完全性非主張は `plan:9–19` に存在する。docstring 再掲も予定されていない。除外句は所見 1 の限定を入れて実態に合わせる必要がある。

**親の実測の一般化には限界がある。** T2344 当時に集合外だった `autonomous_trial_completeness.py` は現行 JSON では集合内になっている。一方、`s8b_oracle_report.py` は現在も集合外。したがって「発行器全体を網羅しない」は支持できるが、当時の集合外一覧や 160／165 を現行の測定値として転用してはいけない。計画はその転用をしていない。

**変異計画には、静的に見て生き残る登録変異は見つからない。**

| 変異 | 実在する検出箇所 |
|---|---|
| M1：production の 63→62 | `test_artifact_admission.py:1160` の全文一致 |
| M2：非推移閉包の句を削除 | 同 `:1160` |
| M3：production の 99→69 | 同 `:1165` の全文一致 |
| M4：完全性非主張の句を削除 | 同 `:1165` |
| M5：期待 literal の 162→161 | 同 `:1160` |
| M6：`CURRENT_E0_EPOCH` の末文を削除 | `test_s1_9pair_figure_provenance.py:828` → `:384–385` の辞書完全一致 → `:154` の例外 |

production 側の 162 の変更や他の句の削除も、独立 literal との全文一致で検出対象になる。M5・M6 は期待値側の変異であり、production 変異と区別して記録する計画も正しい。定数参照への置換、部分一致への緩和はない。

ただしこれは検出経路の静的確認であり、KILLED の実測結果ではない。import 前の変更、狙った比較までの到達、dirty closure による別原因の失敗を数えないという `plan:119` の条件を維持する。

## scope 外候補

自動再計測 gate、発行器 registry、恒久的な集合整合検査、収載拡大は今回の修正に不要。将来の drift を機械的に防ぐ目的で追加するなら別 scope とする。

計画の production 二定数・live literal 二箇所という変更範囲に、検査の緩和、台帳機構追加、被覆拡大、docstring への保証再掲は見当たらない。

## 総括

**現計画はそのまま実装せず、非 import 委譲の除外句を修正する。** 数値 63／162／99、発見集合の定義、P3 の内訳削除、独立 literal による検出方針は妥当。親 brief の E1 不変条件も計画の訂正に合わせて限定する。

必読資料はすべて読取可能だった。ファイル変更・pytest 実行・変異実走は行っていない。