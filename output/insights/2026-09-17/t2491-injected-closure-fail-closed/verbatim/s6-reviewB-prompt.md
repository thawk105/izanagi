単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s4-ruling.md (親の段 4 裁定 = plan v2 (R0〜R4) と変異事前登録の正本。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s5-author.md (実装子の最終報告。「変異 matrix の anchor」節を含む。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-diff.patch (実装差分 = 統合 commit の `git show`。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-focus1.log (親の焦点走 log: test file 全 node の実走結果。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s3-lensB.md (段 3 レンズ B の所見。裁定表で採否済み。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/D1882.md (裁定 D1882 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/D1869.md (裁定 D1869 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/t2154-mutation-ledger.md (F918 を実測した T-2154 の変異台帳。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_ccbench_spawn_sites.py (実装後の対象 test。1218〜1232、1577〜1620、1728〜1812、1835〜1845、1981〜2020、2300〜2320、2693〜2800 (閉包検査・繰延べ台帳)、2960〜3040 (既存 production pin)、3043〜3280 (新 test)。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_s8b_oracle_n_pilot.py (M1 の consumer。307〜330、781〜830 行。読むだけ)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_n_pilot.py (production。996〜1030 行。読むだけ)

## 依頼

あなたは dev-wave [T-2491] の段 6 敵対レビュー **レンズ B (scope / 最小形 / 変異の帰属 / 報告と実体の一致)**。実装を守らず攻撃せよ。
pytest は走らせられない (書込可能 tmp が無い)。静的検査だけでよく、緑を主張するな。親の焦点走 log が実走の証拠である。

## 答えるべきこと

1. **報告と実体の一致:** 実装子の最終報告 (s5-author.md) の各主張 (変更 file:line、R0〜R4 の対応、test の nodeid と期待値、production 4 check の当て直し、波及列挙、変異 anchor の一意性) を
   差分と実 file で照合し、食い違いを列挙せよ。焦点走 log の passed / failed / skipped 件数と報告の「67 node (追加 20)」を照合せよ。
2. **scope / 最小形 (D1882 / D1869):** 差分が名指しの判定 (injected 分岐 + それが依存する記録) と、その正例・負例・production pin の外へ出ていないか。campaign 経路・繰延べ台帳・既存 test 群・production に
   触れていないか。定数 `_RETURNED_EVIDENCE_ERROR` / `_RETURNED_EVIDENCE_CATCHERS` と comment が「前提」として書かれ、gate 化 (assert) されていないか。alias chain を引いていないか。
   production pin が裁定どおり 4 sink 限定 (全 injected 集合固定・floor deferred 固定・`failures == []` 再 assert をしていない) か。
3. **変異の帰属 (DW-M01 / M03 / M08):** 実装子の M0〜M7 anchor について、(a) 各 old が file 内で 1 箇所か、(b) 各変異の専属 killer (新負例の nodeid) が 1 つ以上あり、既存 test では落ちないか、
   (c) M2 の期待集合「n8 以外」と M4 の「n4 のみ (n5 は has_escape が先に拒否)」が正しいか、(d) M1 の期待 7 node (裁定) に漏れ・過剰がないか (`failures == []` を assert する他の production node、
   繰延べ台帳 exact test、sink inventory test)、(e) 追加で登録すべき変異 (例: NONE 分類を外す → n7 が生きるか、局所再束縛の検査を外す → n12、外側追跡を止める → n11、R2 の TryStar 検査) があれば anchor 案を書け。
   Python 3.10 環境では n10 (`except*`) が skip される事実を踏まえ、TryStar 規則の検出力をどう扱うか (登録しない・保証限界に書く) を推奨せよ。
4. **新 test の形式:** parametrize id が ASCII 英小文字・数字・ハイフンだけか。relative path `orchestrator/campaign/synthetic_t2491_*.py` が実在 file と衝突しないか。行番号 (sink 8 行目 / 6 行目) が source 文字列と一致するか。
   `test_define_sink_cross_product_t2491_injected_production_sinks_stay_covered` が `_BuildSink` の lineno を production の現行行に pin する (production が動くと赤になる) 既存の T2155 pin と同型で、それ以上の義務を作らないか。
5. **must-fix / nit の判定:** 各所見に DW-G05 (放置時に閉包検査の受理集合・変異の証拠がどう変わるか) を 1 行で添え、示せないものは nit にせよ。must-fix には修正案 (file:line、差分の形) を書け。
   既存テストの期待値を変える提案は禁止。

## 制約

- 出力は file に書かず、最終メッセージの本文に全文を書け。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式 (見出しは全部 `##`)

## 報告と実体の一致 (食い違い表)
## scope / 最小形の判定
## 変異の帰属 (anchor 一意性、専属 killer、期待集合、追加登録案)
## 新 test の形式
## must-fix と nit (DW-G05 の 1 行付き、修正案)
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
