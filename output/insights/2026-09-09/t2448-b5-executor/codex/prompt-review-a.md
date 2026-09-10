単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor

必読事項の射影 (読めなければ即停止):
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/rulings-stage4.md (**親の段 4 裁定。実装契約の正本**)
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/parent-measurements.md (親の実測)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis_b5_search/parsers.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis_b5_search/preflight.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis_b5_search/runner.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis_b5_search/anchor_registry.json
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/test_axis_b5_search_parsers.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/test_axis_b5_search_executor.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/schemas/axis_b5_search_page_evidence.schema.json
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/schemas/axis_b5_search_live_preflight.schema.json
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/schemas/axis_b5_search_registration_seal.schema.json
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md

## 役割

あなたは dev-wave 段 6 の敵対レビュー子 (レンズ A = **正しさ境界**) である。read-only sandbox なので
書込み可能な tmp は無く、pytest は走らせなくてよい (静的検査でよい)。実装済みのコードを**壊しに行く**。

対象は軸 B5 文献調査実行器である。守るべき正しさは性能ではなく、**事前登録の意味が実行によって
損なわれないこと**である。

## 親が既に見つけている欠陥 (再報告しなくてよい)

- `preflight.verify_registration` の directory exact set 検査が `__pycache__/*.pyc` を「余分な path」と
  数えるため、一度でも import した環境では必ず `registered_path_set_mismatch` で落ちる。
  親が実 repo で実走して確認した (`.gitignore` の 2 行目に `__pycache__/` がある)。**別の穴を探せ。**

## 攻撃の観点

1. **受理集合を広げる経路。** 実装が部分登録 §5.1 の 6 条件より広く受理する箇所を探せ。
   とくに `capacity_echo` が判定に混ざっていないか、条件 2 が実要素数を見ていないか、
   最終ページの総数照合が省ける経路が無いか、cursor 終端の判定が甘くないか。
2. **恒真な test。** test の期待値が production の出力・fixture の `len()`・実装の定数から
   導かれていないか。**変異を入れても赤にならない test** を名指しで挙げよ。
   機構の正例が実体を名指しせず、性質だけで書かれていないか (両層 stub でも通る形になっていないか)。
3. **fail-closed の穴。** 次がすべて本当に発火するか、コードを追って確かめよ。
   - live preflight が 1 件でも `不達` / `非収録` / `unclassified` で `may_start_run=False` を返すこと
   - 本走発行が `UnregisteredRunPolicyError` で止まること。**この例外を回避して request を出せる
     公開経路が 1 本も無いか**を、public API を全部数えて確かめよ
   - production 入口が bool や注入された record で迂回できないこと
4. **seal の漏れ。** 束縛対象から漏れている「実行器の一部」が無いか。
   seal record の自己参照、束縛表と実際に読み込まれる file の食い違い、
   directory exact set が再帰していない箇所を探せ。
5. **凍結値の転記誤り。** 定数 (page size、retry、host、member 集合、anchor の主キー、lookup request 形、
   `get_rows` の値) が凍結文の逐語と 1 文字ずつ合うか。**プランや裁定の引用ではなく凍結文の現物と照合せよ。**
6. **判定順序。** OpenAlex の 404 が content type 判定より先に `非収録` になるか。
   DBLP の `不達` (200 だが `text/html`) が正しく検出されるか。
   content type の比較が media type だけで parameter を無視しているか。
7. **登録に無い gate を足していないか。** W-ID drift での阻止、`capacity_echo` の一致要求、
   control の「発火」判定など、登録されていない拒否条件が入っていないか。

## 出し方

各所見に次を付けよ。**根拠は必ず file:line で示す。**

- `real` / `refuted` の自己判定と理由。
- 放置したときに成果物 (実行記録の値・受理集合・走行開始可否) がどう変わるかを 1 行。
  書けない所見は `nit` と自己申告せよ。
- 是正案 (最小の変更)。**依拠する裁定の逐語より強い断定をしない。**

## 禁止

- ファイルを 1 つも書かない・変更しない。git 操作をしない。外部 network を使わない。
- 凍結済み文書・`catalog.py`・catalog JSON の変更を提案しない。
- 新しい gate・検査・台帳・一般化を、依頼された実行器の外へ足す提案をしない。
  出すなら「scope 外の提案」と明記し、裁定パッケージ候補として書け。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式

見出しは全部 H2 (`## `) で書く。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
予算が尽きそうなら途中結論をこの形式で書いて終われ (無出力が最悪)。

## 受理集合を広げる経路
## 恒真な test
## fail-closed の穴
## seal の漏れ
## 凍結値の転記
## 登録に無い gate
## 総括
