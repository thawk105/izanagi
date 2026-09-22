**判定：GO（今回の焦点再レビュー範囲）。B1〜B4 は closed です。** fix3 による回帰・制約違反は見つかりません。受入全走・登録済み変異の完了を意味する判定ではありません。

行番号は指定された最終 worktree のコード基準です。

| 所見 | 判定 | 根拠 file:line | 残る穴 |
|---|---|---|---|
| B1 | **closed** | [test_verifier.py:3803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/orchestrator/tests/test_verifier.py:3803)：子の task 0 を異常終了。3819〜3830 で毎回マーカーを消し、対象呼出し直後に親 PID 集合・子の終了マーカー・結果・v3 出力を確認。3832 の helper でも障害注入を維持して比較する。 | 採用所見の範囲ではなし。fix3 はこの観測順序を変更していない。 |
| B2 | **closed** | [test_verifier.py:3417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/orchestrator/tests/test_verifier.py:3417)：legacy は1設定、packed／tuple は各 workers=1／2 の計5設定。3438 以降で残る4設定を比較。3649・3657 の重複削減も維持。 | なし。設定削減・比較 assertion の弱体化はない。 |
| B3 | **closed** | [test_verifier.py:3665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/orchestrator/tests/test_verifier.py:3665)：R／W は reads／writes 引数で生成し、3381 の宣言件数と一致。W の版も commit と一致する。 | 別の構文・件数違反は見つからない。`"1 0"` は意図した余剰 token 拒否。 |
| B4 | **closed** | [test_verifier.py:3424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/orchestrator/tests/test_verifier.py:3424)：compact を期待する4設定すべてで、graph 構築・legacy 分岐・表現検査より前に `_CompactTrace` を肯定 assertion。3431 の packed 型、3433〜3434 の tuple 構築対象の同一性と `dict` 型も維持。 | 前回の legacy fallback による迂回は閉じた。採用所見の範囲ではなし。 |

**B4 の攻撃結果**

`expect_compact` の明示指定は [test_verifier.py:3615](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/orchestrator/tests/test_verifier.py:3615) の1か所だけです。`epoch == 2**63` の意図的な列 overflow fixture でのみ偽になり、`2**32` は compact 必須のままです。ほかの helper 呼出しに許可解除はありません。

前回の具体例も検出できます。[test_verifier.py:3570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/orchestrator/tests/test_verifier.py:3570) は既定値で helper を呼びます。仮に負の read tid を含む列化で `OverflowError` が発生すると、[parse.py:665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/orchestrator/verifier/parse.py:665) → 898〜899 の legacy fallback 後、3425 の assertion で失敗します。legacy 同士の比較まで進めません。これは**静的推論**であり、この特定変異を今回実行したという主張ではありません。

**回帰と規模**

[fix3.diff](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/fix3.diff:5) の全3 hunk は新規 v3 helper と overflow 試験内です。production・既存試験・自走 runner の変更はありません。追加された必須条件以外の比較処理も維持されています。

差分ヘッダーを除き、`+`／`-` 行を直接再集計しました。

| 対象 | 追加 | 削除 | 追加＋削除 |
|---|---:|---:|---:|
| fix3 の test_verifier.py | 6 | 2 | 8 |
| wave 起点からの test_verifier.py | **490** | **0** | **490** |

[integrated-final2.diff:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/integrated-final2.diff:5) は試験ファイルについて単一の追加 hunk です。子の申告「追加490行」と一致し、前回の486行とも `486 + 6 − 2 = 490` で整合します。**R9 の800行以内、余裕310行**です。

親の [solo-3.log:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/solo-3.log:9) は **132 passed in 4.10s、rc=0**。また、[fix3 子の報告](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s6-fix3.md:17) では、v3 を常に legacy へ落とす一時退行により、対象の mapping 試験を含む10件が追加 assertion で失敗しています。ただし、これは前回の入力限定変異そのものではなく、登録済み M1〜M15 の本走証拠でもありません。本レビューでは編集・試験実行を行っていません。

## 総括

B1 は対象呼出し直後の障害・逐次復帰観測を保持しており、closed。
B2 は legacy の重複削減と compact の workers 別比較を保持しており、closed。
B3 は R／W の宣言件数・版の整合を保持しており、closed。
B4 は表現検査前の compact 必須 assertion により、前回の迂回を閉じた。
legacy 許可解除は意図した `2**63` overflow fixture だけ。
fix3 は新規 v3 試験内に限定され、累計490行で R9 を満たす。
親の実測は132 passed・rc=0。受入全走・登録済み変異の確認は別途残る。
今回の焦点再レビュー判定は **GO**。