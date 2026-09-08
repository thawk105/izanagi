単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md (後継凍結物 1/2、commit 済み。§3 が生成器の契約。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py (レビュー対象、未 commit。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py (レビュー対象、未 commit。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/rulings-stage4.md の「変異事前登録」節 (親が登録した変異候補 13 件。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_plain_runner_coverage.py、test_campaign_import_invariant.py、test_acceptance_schedule_order.py (新規 test file が発火させうるメタテスト。該当箇所を grep で引く。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/tools/check_ai_provenance.py の実装面判定 (`grep -n "IMPLEMENTATION\|implementation" ` で引く。読めなければ即停止)

## 役割 — レンズ B: test の実効性・変異の帰属・repo への統合

あなたは dev-wave 段 6 の敵対レビュー者である。**実装を守らず攻撃する。** read-only sandbox なので pytest は走らせなくてよい (静的検査)。
**親は自走 harness で 17 test 緑、再生成 bytes 一致、`--verify` の正例・負例を実測済み**であり、再実測は求めない。

攻撃すること (所見ごとに `RB-<番号>`、real / refuted の自己判定、根拠の file:line、推奨対応、must-fix なら成果物 (catalog bytes または test の受理集合) への影響を 1 行):

1. **変異候補 13 件それぞれ**について、(a) 変異位置が実装に実在するか (関数名・行)、(b) 期待どおり**単独の test** が赤になるか、(c) 同じ入力を拒否する層が他に無く赤理由が 1 つに絞れるか (単一理由性)、を静的に判定する。赤にならない候補、複数理由になる候補、等価変異になってしまう候補を挙げ、代替の変異位置または代替 oracle を提案せよ。等価変異 (#13) の具体位置を 1 つ提案せよ。
2. test の**受理集合の穴**: 実装を壊しても緑のままになる変更を 3 つ以上具体的に挙げよ (例: `expected_cardinalities` の値だけを変える、`shares_request_with` を全部 `null` にする、`branches` の `block_ids` と `queries` の `term_groups` を不整合にする、`{CUR}` の literal を `%7BCUR%7D` にする、venue の年を文字列にする)。それぞれどの test が捕まえるべきかを書け。
3. 自走 harness (`if __name__ == "__main__": raise SystemExit(pytest.main([__file__]))`) が `test_plain_runner_coverage.py` の要求形と一致するか。`test_campaign_import_invariant.py` の namespace 規則に `orchestrator.axis_b5_search` が通るか。`test_acceptance_schedule_order.py` の被覆 gate (受入所要時間台帳) に新規 17 node が与える影響 (閾値と現行の被覆率を実際の台帳 file から読んで見積もれ。台帳 path は同 test から引く)。
4. `subprocess` を使う CLI test の cwd・`PYTHONPATH`・interpreter 解決が、`tools/run_tests.py` の dispatch 経路 (計算ノード、別 cwd) でも成立するか。`ROOT` の導出が `__file__` 基準か cwd 基準か。
5. `docs/related-work/claim-survey/*.json` (939 KB) を tracked に足すことと、`orchestrator/axis_b5_search/*.py` を足すことが、`tools/check_ai_provenance.py` の実装面判定と `tools/check_docs.py` でどう扱われるか (path・拡張子で判定)。
6. 生成器の関数分割が、将来の実行器が `blocks` / `branches` / `term_groups` から期待 AST・期待 echo を**独立に**導出する (catalog の request bytes を写さない) ために十分な構造 field を出しているか。不足があれば挙げよ (ただし catalog の field 追加は 1/2 §3.2 の閉集合に反するので、不足は「裁定パッケージ候補」として分けて書け)。

## 禁止

- ファイルを書かない・変更しない。git 操作をしない。外部 network を使わない。
- 凍結済み文書の変更を提案しない。新しい gate・検査・台帳・一般化を推奨しない。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式

見出しは全部 H2 (`## `) で書く。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。予算が尽きそうなら途中結論をこの形式で書いて終われ。

## 所見
## 変異候補の判定表
## 裁定パッケージ候補 (scope 外)
## 総括
