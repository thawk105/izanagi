単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 裁定 (採用所見 B1〜B4 と fix2 の制約): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s6-ruling.md
- fix2 の差分 (788657426 → d1dd82f81、再レビュー対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/fix2.diff
- wave 全体の最終差分 (eef04f5a7 → d1dd82f81): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/integrated-final.diff
- fix2 子の報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s6-fix2.md
- 段 6 レビュー A / B (元の所見): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s6-review-A.md、同 dir の s6-review-B.md
- 段 4 裁定 (R8 の試験要件、R9 の規模上限): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s4-ruling.md
- 親の単独走 (fix2 後、d1dd82f81) の実測 log: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/solo-2.log
- repo 内コード (read-only、wave worktree = d1dd82f81): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/orchestrator/tests/test_verifier.py、
  同 worktree の orchestrator/verifier/{parse,dsg,core}.py

## 前置き — これは自分たちのコードの fix 後の焦点再レビューである

trace verifier に TPC-C 用 trace v3 の読み取りを足した wave の、段 6 レビュー所見 B1〜B4 (試験の実効) を直した fix2 を再レビューしてもらう。
あなたは read-only のレビュー役で、実装・テスト実行はしない (静的読解でよい。実測は親の solo-2.log を使え)。**fix を守らせず攻撃せよ。**
予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## 点検すること

1. **所見ごとの closed / partial / regressed 対応表** (B1〜B4 の各行に判定・根拠 file:line・残る穴)。表なしで閉じたと判定しない。
   - B1: pool 障害の注入が実際に parse / edge の子を落とし、その呼出しの**直後**に逐次への fallback を観測しているか。観測が恒真
     (障害なしでも通る) でないか。fallback 後の表・取引種別・結果の比較が実体を通っているか。
   - B2: legacy 1 回・compact は workers=1 / 2 の比較で、legacy と各 compact 経路の一致の網羅が落ちていないか。
   - B3: table 拒否 fixture が単一の拒否理由になっているか (宣言件数の不一致など別の違反が残っていないか)。
   - B4: packed / tuple 経路の肯定 assertion が実体を確かめているか (型名の文字列比較などで恒真になっていないか)。
2. **回帰**: fix2 が production・既存試験の行を変えていないこと (fix2.diff の hunk がすべて段 5 で足した新規 v3 試験・helper の範囲内か)、
   他の新規 v3 試験の検出力を落としていないこと (比較の削除・assertion の弱体化)。
3. **規模**: wave 起点からの test_verifier.py の差分行数を integrated-final.diff から数え、R9 (800 行) との関係を書け。親・子が書いた
   行数 (「追加 486 行」など) は再計算して照合せよ。

## 出力形式

Markdown。対応表 (所見・判定 closed/partial/regressed・根拠 file:line・残る穴)、回帰と規模の所見、判定 GO / NO-GO、最後に `## 総括` (5〜10 行)。
推測は推測と明記せよ。
