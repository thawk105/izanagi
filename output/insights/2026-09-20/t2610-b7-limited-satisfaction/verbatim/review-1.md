## 所見

1. **real / must-fix — 「区間推定」の除外範囲が広すぎる。**
   対象: `docs/paper-story/figures/README.md:1318–1319`。
   一次資料: 同 file:1191–1201、キャプション正文。既存説明は標本平均の t95 CI を描くことを明記し、除外対象を「効果・median・床値判定の区間推定」に限定している。追補の無限定な「区間推定…は含まない」はこの区別を落としている。
   対案: 「有意差判定・区間推定・」を「有意差判定・効果／median／床値判定の区間推定（標本平均の t95 CI は標本の記述として描く）・」へ置換する。
   **放置の影響:** 執筆者が、実際に図示されている標本平均の信頼区間まで報告対象外と読み、図と本文の説明を食い違わせる。

2. **real / nit — 一覧2行だけ supersede の対象が省略されている。**
   対象: `docs/paper-story/README.md:202`、`docs/paper-story/figures/README.md:27`。
   一次資料: `verbatim/rulings-body.md:1–10,35–44`。D2044 項3の「記述的な報告は利用してよい」は撤回されていない。詳細追補は括弧で対象を限定しており正しいが、一覧の「D2044 項3は supersede」は項全体の失効とも読める。参照先で解消できるため nit。
   対案: 両方を「D2044 項3の『要件充足へ昇格させない』を、この限定付き充足で supersede した」へ置換する。
   **放置の影響:** 一覧だけを読む執筆者に、既存の記述的報告の利用許可まで失効したとの不要な疑問を残す。

3. **real / nit — 詳細追補に既存説明の重複がある。**
   対象: `docs/paper-story/README.md:67`、`docs/paper-story/figures/README.md:1308–1324`。
   一次資料: 前者:66、後者:1186–1201、および `verbatim/rulings-body.md:35–44`。stale 新項目の測定・床値・図の説明は直前項目と重複し、fig10 追補の第2 bullet は「何を示す図か」の限定を再掲している。第4 bullet の版運用も paper-story README が正本である。
   対案: stale 新項目の根拠説明を「D2174 項3は、上項の稿・図10を根拠として、B-7を…」へ短縮する。fig10 第2 bullet は「図の統計的な解釈と採用根拠にしない制限は、上の『何を示す図か』のとおり変わらない。」へ置換、第4 bullet は stale 注記への参照1文にする。これは所見1も解消する代案となる。
   一覧行と results 行も限定4語を残した参照1文に短縮可能だが、独立した入口なので限定の再掲自体は妥当。「論文で…付く限定は上の4語」は裁定から導けるが、「**B-7の充足裁定に付く限定**は上の4語」とすれば稿・図の既存限定を尽くす意味にならない。
   **放置の影響:** 現状の重複自体で結論は変わらないが、執筆者が同じ制限の微妙に異なる要約を突き合わせる必要が生じる。

4. **refuted / nit — (P1) README側に「稿の追補」を置く判断は妥当。**
   対象: `docs/paper-story/README.md:67,202`。
   一次資料: 同 file:148–152,181–187,208–223、結果稿:1–22、provenance の `caption_source`。凍結稿への追記は append-only と SHA 束縛に反する。今回の裁定だけを新しい results file に置くことも、「1 file = 1結果」「一項目だけの差分改訂を置かない」に合わない。
   対案: 変更不要。既存の読解上の追補と同じく、README側に保持する。
   **放置の影響:** 現配置による悪影響はない。稿本文を変える対案は caption_source の SHA 照合を失敗させる。

5. **refuted / nit — (P2) T-2610の完了扱いと fragment 形式は妥当。**
   対象: `docs/spool/worklog/2026-09-20-dev-wave-t2610-b7-limited-1.md` の「完了」。
   一次資料: `verbatim/rulings-body.md:35–44`、`docs/paper-story/README.md:58–70,101–103`、`docs/spool/worklog/README.md` の完了・title規則、HANDOFF の T-2610 記録。稿の入口、図の説明、ストーリー版の地図への転記はそろっている。次版の作成は今回の要求ではなく、別の active T を残す必要はない。
   対案: 完了扱いは維持。所見1の修正と親担当の検査を済ませて最終化する。H2は指定2個、末尾の `remaining: none` と `base:` は連続し、titleの既存 T-2610 は同エントリで完了に置かれている。
   **放置の影響:** 完了扱い自体による取りこぼしはない。今回の転記を active に残すと、済んだ作業が再度持ち越される。

## 検算の記録

以下、`W` は指定 worktree、`J` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-b7-limited`。指定射影 file はすべて読めた。

**読んだ資料**

- `J/verbatim/diff-docs.patch` 全60行。出力で省略された箇所は分割して再読。
- `J/verbatim/rulings-body.md` 全44行、`J/HANDOFF.md` 全文。
- `W/output/insights/2026-09-20/t2610-b7-limited-satisfaction/README.md` 全文。
- `W/docs/spool/worklog/2026-09-20-dev-wave-t2610-b7-limited-1.md` 全文、および同ディレクトリの `README.md` 全文。
- `W/docs/paper-story/README.md`: 58–70、101–125、148–152、181–187、202、208–223。202行は指定の `sed` / `cut` でも確認。
- `W/docs/paper-story/figures/README.md`: 27、1184–1324。省略箇所は分割再読。
- `W/docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md`: 1–22、245–271。
- `W/docs/paper-story/2026-09-20.md`: 2252–2256、3156–3162。
- `W/orchestrator/tests/test_plot_b7_fixed5_regression.py`: 550–567。
- fig10 provenance の `caption_source`: 337–340。静的照合では JSON の caption も読み取った。

**実行と結果**

- `git rev-parse --short=9 HEAD` → `947fd160a`。
- `git status --short` → README 2本の変更と、指定 worklog fragment・insight ディレクトリの未追跡追加のみ。凍結稿・図・provenance・ストーリー版・claim-evidence の変更なし。
- `git diff --stat` → 2 files、22 insertions、3 deletions。
- `git status --short -- docs/paper-story/results/` → 空。
- `git diff --check` → rc=0、出力なし。
- `sha256sum` → 稿は `6585d446a07d798d87c352a1b41eb5b195ee70ba453976aa5ec0f46daef4b6f9`。provenance の `caption_source.sha256` と一致。PNG・PDF・provenance の現SHAも README の3行と一致。
- `rg -n '^## 追補|^### 追補|^## Erratum' …/figures/README.md` → 416、440、822、1308行。新追補のH2書式は既存と一致。
- 書込みなしの `python3 -B` による文字列・ハッシュ照合 → 提供 patch と現 working diff は完全一致。限定4語は指定4か所に各1回、語順を含め一致。stale bullet は2件。
- 同静的照合 → caption全文の収録あり。追補は fig10 節内にあり、SHA抽出範囲の外。SHA各行は1件ずつ。fragment のH2・末尾fieldも一致。読者向けREADMEに `F428` はない。

**意味上の照合**

- 充足は報告要件に限定され、採用・認証・性能主張・有意差・反復間安定性への昇格はない。新規測定や反復の予告もない。
- 凍結 caption と外部の後続裁定を区別する説明は成立する。fig5と共通するのは「凍結物を保持し入口で解釈を補う」方式であり、fig10を利用禁止にする規則は追加していない。
- stale 注記の引用は凍結版の該当文と一致。07:04の導出起点と、ユーザー提示の13:03の裁定時刻、裁定前文の main `4a87d566b` に照らし、後続裁定で古くなった分類は妥当。13:03自体の独立した時刻監査は行っていない。
- 新項目の「太字見出し→執筆時点→変わらないこと→一次資料」の書式は既存項目と一致。「次版の再導出で拾う」は D1858 の下で新版作成要求にならない。

pytest・build・測定・fold・check_docs は実行していない。上記は静的検算であり、親担当のテスト成功を代替しない。

## 総括

実在所見は **must-fix 1件、nit 2件**。別に (P1)(P2) の懸念を各1件 refuted とした。

レンズA: 裁定の限定4語、充足の射程、凍結物とSHAは整合している。追補の「区間推定」の除外範囲は修正が必要。

レンズB: README側の追補とT-2610の完了扱いは妥当で、scope逸脱はない。重複説明の短縮と一覧の supersede 対象明示を推奨する。