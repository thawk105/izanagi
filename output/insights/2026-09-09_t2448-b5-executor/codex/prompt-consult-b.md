単独段 dispatch: stage=consult; lane=luna; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor

必読事項の射影 (読めなければ即停止):
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/brief.md (親の段 1 brief。**これ自身も攻撃対象である**)
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md (段 2 のプラン。主たる攻撃対象)
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/rulings-verbatim.md (D95 と D1895 の逐語)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/ (先例。runner.py・validator.py・parsers.py・checkpoint.py)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/ (既存 test と `acceptance_duration_ledger.json`、`README.md`)

## 役割

あなたは dev-wave 段 3 の敵対検証子 (レンズ B = **整合と実効性**) である。read-only sandbox なので書込み可能な tmp は無く、
pytest は走らせなくてよい (静的検査でよい)。**プランを守らせるのではなく、実際に走らせたら破れる箇所を探すのが役目である。**
親の brief も段 2 のプランも、どちらも誤りうる。親の実測値とその一般化も疑ってよい。

## 攻撃の観点

1. **file:line の実在**。プランが指す file・関数・行が実在するか、名前が正確かを全部確かめよ。
   実在しない参照、既に別物になっている参照、軸 1 の API を誤って写した箇所を挙げよ。
2. **凍結文の逐語との一致**。プランが書いた定数 (page size、retry の秒数、host、content type、
   member 集合の件数、anchor の主キー、request 形) が、凍結 3 文書の逐語と 1 文字ずつ合うかを確かめよ。
   **プランの引用ではなく、凍結文の現物と照合すること。** 食い違いは file:line と節番号の両方で示せ。
3. **既存の検査との衝突**。新規 file の追加が `tools/check_docs.py`、`tools/check_ai_provenance.py`、
   `orchestrator/tests/test_plain_runner_coverage.py` の自走 harness 契約、
   `orchestrator/tests/acceptance_duration_ledger.json` の所要台帳、`orchestrator/tests/README.md` の
   allowlist、既存の repo scan invariant にどう当たるかを、**現物を読んで**書け。
   足りない登録があるなら、どの file の何を足すのかを具体的に書け。
4. **実装量**。プランの成果物を 1 wave の実装子 2 単位で書き切れるか。行数の見積りと、
   書き切れない場合にどこを削るべきか (削っても registration preflight が閉じる最小集合) を書け。
   **削る提案では、削ったときに成果物 (実行記録・`RW3` の主張) が何を失うかを 1 行で書け。**
5. **所有分割の重複**。段 5 の 2 単位 (A = parser + fixture、B = preflight + runner + schema) の
   編集 path が素集合になっているか。共有 file (`__init__.py`、台帳、schema) が両方から触られる形になっていないか。
6. **変異の帰属不成立**。プランの変異候補それぞれについて、同じ入力を拒否する層が前後や内側に他にあり、
   赤の理由が一つに絞れない候補を指摘せよ。絞れない候補は登録しない方がよい。
7. **親 brief の (P1)〜(P3) と DW-O13 の節**。とくに (P1) の「軸 1 の parser を import しない」判断について、
   import した場合の実際の結合の強さを軸 1 の凍結 path 一覧 (`validator.FROZEN_PREDECESSOR_PATHS`) の現物で確かめ、
   親の理由が現物と合っているかを判定せよ。合っていないなら反証を出せ。

## 出し方

各所見に次を付けよ。**根拠は必ず file:line か凍結文の節番号で示す。**

- `real` / `refuted` の自己判定と、その理由。
- 放置したときに成果物 (実行記録の値・受理集合・`RW3` の主張) または受入結果がどう変わるかを 1 行。
  これを書けない所見は `nit` と自己申告せよ。
- 是正案。ただし**依拠する裁定の逐語より強い断定をしない**こと。

## 禁止

- ファイルを 1 つも書かない・変更しない。git 操作をしない。外部 network を使わない (名前解決も request も禁止)。
- 凍結済み文書と `catalog.py`、catalog JSON の変更を提案しない。
- 依頼された実行器の外へ、新しい gate・検査・台帳・一般化を足す提案をしない。
  そういう案を出すときは「scope 外の提案」と明記し、実装案ではなく裁定パッケージ候補として書け。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式

見出しは全部 H2 (`## `) で書く。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
予算が尽きそうなら途中結論をこの形式で書いて終われ (無出力が最悪)。

## file:line の実在
## 凍結文との照合
## 既存検査との衝突
## 実装量と削り方
## 所有分割
## 変異の帰属
## 親 brief への反論
## 総括
