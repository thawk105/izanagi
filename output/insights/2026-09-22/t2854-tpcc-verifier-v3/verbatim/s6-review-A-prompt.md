単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 統合 diff (wave 起点 eef04f5a7 → 統合 commit 788657426 = 実装 0b0509d6e + 試験 fix、レビュー対象の全文): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/integrated.diff
- 段 5 fix 子の報告 (新規試験の比較を辺集合へ正規化、7 行): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s5-fix1.md
- author の最終報告 (自走結果・波及の列挙・変異の位置表): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s5-author-u4r.md
- 親の焦点走の実測 log (逐語): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/focus-1.log
- 段 4 裁定 (R1〜R11、変異の事前登録): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s4-ruling.md
- 段 2 plan: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s2-plan.md
- 親 brief: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s1-brief.md
- 依頼文と並走 wave の返信の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/verbatim/request-t2854.md
- repo 内コード (read-only、統合後の wave worktree): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/ 配下の
  `orchestrator/verifier/{parse,model,dsg,core,report}.py`、`orchestrator/tests/test_verifier.py`

## 前置き — これは自分たちのコードの敵対レビューである

研究用 repo の trace verifier (直列化可能性の検査器、合成した並行性制御を採用してよいかの唯一の正しさゲート) に、TPC-C 用 trace 形式 v3 の
読み取りを足した差分をレビューしてもらう。あなたは read-only のレビュー役で、実装・テスト実行はしない (書込可能 tmp が無いので静的読解でよい。
テスト実測は親の focus-1.log を使え)。**実装を守らせず攻撃せよ。親の裁定・焦点走の解釈も攻撃対象である。** 予算が尽きそうなら途中結論を
下の出力形式どおり書いて終われ。

## レンズ A — 正しさ境界と v2 の不変

所見ごとに real / refuted の見込み・重大度 (must-fix / should / nit)・根拠 file:line・放置時に成果物 (certified 判定・anomaly の構造化出力・
YCSB の既存判定) の値や受理集合がどう変わるかを 1 行で書く。攻撃が成立しなかった項目は「不成立」と書け。

1. **偽の認定 (規律 2)**: v3 を certified にする経路が残っていないか (R1 の印を立てる条件の抜け: n_txns、legacy / compact、capability 経路、
   expected_commits の有無)。v2 の certified 集合が広がる経路。
2. **identity**: 表の違う同一 hex が同じ object に戻る、同じ (table, hex) が別 object に割れる経路 (object / packed / tuple、workers=1 と複数、
   並列 → 逐次 fallback、overflow の legacy 落ち、read-only token の解決、`_reasons`、version-dup の判定)。
3. **v2 の不変**: v2 の受理・拒否集合、verdict、integrity 値、notes 文言、result_to_dict の bytes、witness の選択順・辺の追加順、既存
   message 文言。差分で v2 の経路の行が変わっていれば、その行が v2 で同じ結果を返すことを具体の入力で確かめよ。
4. **schema の混在 (R2)** と **厳格検査 (R3・R4)**: 受理してはならない入力の受理、並走 wave の返信どおりの正常 v3 の拒否、ParseError と
   integrity の使い分け、sorted path 順の優先順位。
5. **anomaly の構造化 (規律 3)**: 表・取引種別の取り違え (last-wins の勝者との整合)、`result_to_dict_v3` の欠落・切り捨て。
6. **試験の実効**: 追加試験が機構を実体で通っているか (stub・恒真・揮発 payload の焼き込み)、既存試験の期待値が変わっていないか
   (diff の test file で既存行の変更・削除を全部数えよ)、変異 M1〜M15 の位置と kill 試験の対応が単一理由か。

## 出力形式

Markdown。所見の表 (番号・レンズ項目・所見・real/refuted の見込み・重大度・根拠 file:line・成果物への影響)、判定 GO / NO-GO、
最後に `## 総括` (5〜10 行)。推測は推測と明記せよ。
