単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 統合 diff (wave 起点 eef04f5a7 → 統合 commit 788657426 = 実装 0b0509d6e + 試験 fix、レビュー対象の全文): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/integrated.diff
- 段 5 fix 子の報告 (新規試験の比較を辺集合へ正規化、7 行): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s5-fix1.md
- author の最終報告 (自走結果・波及の列挙・変異の位置表): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s5-author-u4r.md
- 親の焦点走の実測 log (逐語): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/focus-1.log
- 段 4 裁定 (R1〜R11、規模上限 R9、変異の事前登録): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s4-ruling.md
- 段 2 plan: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s2-plan.md
- 親 brief: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s1-brief.md
- 依頼文の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/verbatim/request-t2854.md
- repo 内コード (read-only、統合後の wave worktree): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/ 配下の
  `orchestrator/verifier/{parse,model,dsg,core,report}.py`、`orchestrator/tests/test_verifier.py`

## 前置き — これは自分たちのコードの敵対レビューである

研究用 repo の trace verifier に TPC-C 用 trace 形式 v3 の読み取りを足した差分をレビューしてもらう。依頼は「本題だけ、gate・検査・台帳の追加は
scope 外」「既存 YCSB 形式の受理と判定は変えない」と明記している。あなたは read-only のレビュー役で、実装・テスト実行はしない (書込可能 tmp が
無いので静的読解でよい。テスト実測は親の focus-1.log を使え)。**実装を守らせず攻撃せよ。親の裁定・焦点走の解釈も攻撃対象である。**
予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## レンズ B — 実効性と過剰・削除 (DW-S03 の過剰・削除レンズ)

所見ごとに real / refuted の見込み・重大度 (must-fix / should / nit)・根拠 file:line・放置時に成果物 (後続の単位 5 が使える形か、certified 判定、
YCSB の既存判定、変更量・保守) がどう変わるかを 1 行で書く。攻撃が成立しなかった項目は「不成立」と書け。

1. **過剰**: 段 4 裁定を超える実装 (新 gate・検査・台帳・汎用化・互換層・配線・段 2 の先取り・§3.3 の存在履歴の実装)、使われない helper・
   型・分岐、同じ性質を二重に検査する箇所。R1 の印が最小か (印以外の検査を足していないか)。
2. **削除・局所化**: より小さい差分で同じ性質を満たせる箇所。v2 の経路の既存行を不要に書き換えた箇所 (v2 不変の保守を難しくする)。
3. **規模 (R9)**: production 4 file の追加 + 削除行数と test_verifier.py の行数を diff から数え、上限 (550 / 800) との関係を書け。
4. **試験の重複と実効**: 既存試験と重複して何も足さない追加試験、直積の繰り返し (R8 (a) 違反)、単一理由でない fixture、恒真な assert、
   揮発 payload。R8 (c) の追加試験 (last-wins の tx_type、pool 障害 fallback、実並列の子 PID、表記 01/+1/-0、同一 txn 異表同 hex、R1 の
   非認定と A の反例 2 つ、v2 の対照) が揃っているか。
5. **後続への実効**: 単位 5 (allowlist・witness・§6.1 の正例負例) と §3.3 の存在履歴の実装が、この差分の上に作り直しなしで載るか。
   R1 の印を外す手順が 1 箇所で済むか。

## 出力形式

Markdown。所見の表 (番号・レンズ項目・所見・real/refuted の見込み・重大度・根拠 file:line・成果物への影響)、判定 GO / NO-GO、
最後に `## 総括` (5〜10 行)。推測は推測と明記せよ。
