単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor

必読事項の射影 (読めなければ即停止):
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/rulings-stage4.md (**親の段 4 裁定。実装契約の正本**)
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/parent-measurements.md (親の実測)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis_b5_search/ の全 file
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/test_axis_b5_search_parsers.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/test_axis_b5_search_executor.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/fixtures/axis_b5_search/ の全 file
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/schemas/axis_b5_search_*.schema.json
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/acceptance_duration_ledger.json
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/README.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/tools/mutation_harness.py

## 役割

あなたは dev-wave 段 6 の敵対レビュー子 (レンズ B = **実効性と整合**) である。read-only sandbox なので
書込み可能な tmp は無く、pytest は走らせなくてよい (静的検査でよい)。
**実際に走らせたら破れる箇所と、受入・変異で赤になる箇所を探す**のが役目である。

## 親が既に見つけている欠陥 (再報告しなくてよい)

- `preflight.verify_registration` の directory exact set 検査が `__pycache__/*.pyc` を「余分な path」と
  数えるため、一度でも import した環境では必ず落ちる。親が実 repo で実走して確認した。**別の穴を探せ。**

## 親が実走した結果 (事実)

- `orchestrator/tests/test_axis_b5_search_parsers.py` 20 node、`test_axis_b5_search_executor.py` 34 node、
  `test_plain_runner_coverage.py` 3 node、`test_axis_b5_search_catalog.py` 17 node、
  `test_mutation_fanout_contract.py` 28 node は、いずれも login node の自走 harness で緑。
- `__pycache__` を消した状態で `verify_registration` は `passed=True` を返し、37 file を seal した。

## 攻撃の観点

1. **受入で赤になる構成。** 新規 file の追加が既存の検査へどう当たるかを、**現物を読んで**書け。
   - `orchestrator/tests/acceptance_duration_ledger.json` に新規 test の nodeid 行が無い。
     **不足している nodeid を全部列挙せよ** (parametrize の ID を含む正確な形で)。
   - `orchestrator/tests/README.md` の allowlist、repo scan invariant、その他の meta-test。
2. **変異で帰属が壊れる箇所。** 親は次を変異候補にしている。それぞれについて、
   `tools/mutation_harness.py` の判定 (失敗 node 集合と期待 node 集合の完全一致だけを KILLED とする) に
   照らして**赤になる node 集合が一意に決まるか**を、test を読んで判定せよ。
   一意でないものは理由を書き、単一理由へ差し替える具体案を出せ。
   1. OpenAlex の初回 cursor を literal `*` から `%2A` へ
   2. OpenAlex 期待 AST の children を set 化 (多重度を落とす)
   3. live preflight の `all(収録)` を `any` へ
   4. 総件数 drift を最終 page の値で受理
   5. 条件 3 の実要素数を `capacity_echo` に差し替え
   6. 本走発行の fail-closed を外す
   7. seal の directory exact set を部分集合検査へ緩める
   8. DBLP の cutoff 判定 (`year <= 2026`) を落とす
   9. 3 値に入らない応答を `収録` へ丸める
   10. OpenAlex の判定順序を content type 先行へ入れ替える
   11. `G2-08` の主キーを arXiv ID にする
   12. retry delay の `6.0` を `7.0` へ
3. **test の実効性。** 各 test が**実装のどの行**を守っているかを追え。
   実装を壊しても赤にならない test、production の経路を通らない test (stub 同士の比較で閉じている test) を
   名指しで挙げよ。
4. **凍結文との照合。** 定数・request 形・member 集合・anchor 主キーを凍結文の現物と 1 文字ずつ比べよ。
5. **schema と実際の出力の食い違い。** schema が要求する field を production が出しているか、
   production が出す field が schema に無いことがないか。
6. **所要時間。** 新規 test の実走時間が受入の予算に与える影響を見積もれ。

## 出し方

各所見に次を付けよ。**根拠は必ず file:line で示す。**

- `real` / `refuted` の自己判定と理由。
- 放置したときに成果物または受入結果がどう変わるかを 1 行。書けない所見は `nit` と自己申告せよ。
- 是正案 (最小の変更)。**依拠する裁定の逐語より強い断定をしない。**

## 禁止

- ファイルを 1 つも書かない・変更しない。git 操作をしない。外部 network を使わない。
- 凍結済み文書・`catalog.py`・catalog JSON の変更を提案しない。
- 新しい gate・検査・台帳・一般化を、依頼された実行器の外へ足す提案をしない。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式

見出しは全部 H2 (`## `) で書く。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
予算が尽きそうなら途中結論をこの形式で書いて終われ (無出力が最悪)。

## 受入で赤になる構成
## 不足している台帳 nodeid
## 変異の帰属
## test の実効性
## 凍結文との照合
## schema と出力
## 総括
