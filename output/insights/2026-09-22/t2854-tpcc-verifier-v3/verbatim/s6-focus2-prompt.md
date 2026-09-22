単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 前回の焦点再レビュー (NO-GO、B4 partial の根拠): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s6-focus.md
- fix3 の差分 (d1dd82f81 → 99410ebd4、再レビュー対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/fix3.diff
- wave 全体の最終差分 (eef04f5a7 → 99410ebd4): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/integrated-final2.diff
- fix3 子の報告 (一時退行での確認を含む): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s6-fix3.md
- 段 6 裁定: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s6-ruling.md
- 親の単独走 (fix3 後、99410ebd4) の実測 log: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/solo-3.log
- repo 内コード (read-only、wave worktree = 99410ebd4): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/orchestrator/tests/test_verifier.py、
  同 worktree の orchestrator/verifier/parse.py

## 前置き — fix 後の焦点再レビュー 2 巡目

前回あなた (別 context) は B1〜B3 closed、B4 partial (packed / tuple の肯定 assertion が legacy を返さない枝の中にあり、予期しない legacy 落ちで
検査が飛ぶ) で NO-GO とした。fix3 はこれを直したと主張している。read-only・静的読解でよい (実測は親の solo-3.log と fix3 子の報告を使え)。
**fix を守らせず攻撃せよ。** 予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## 点検すること

1. **B4 の closed / partial / regressed** (根拠 file:line・残る穴)。compact を期待する全設定で `_CompactTrace` の肯定 assertion が表現検査より先に
   無条件で走るか。legacy を許す明示引数を使う試験が、意図的な overflow fixture だけか (他の試験に legacy 許可が紛れていないか)。
   前回挙げた具体的な抜け (`test_v3_packed_mapping_and_read_bounds` の入力が列化時 OverflowError で legacy へ落ちる退行) を今度は検出するか。
2. **B1〜B3 の回帰**: fix3 が前回 closed の B1〜B3 を壊していないか。
3. **回帰と規模**: fix3.diff が新規 v3 試験・helper の範囲内か、既存試験・production を変えていないか。wave 起点からの test_verifier.py の
   差分行数を integrated-final2.diff から再計算し、R9 (800 行) との関係と、子の申告「追加 490 行」を照合せよ。

## 出力形式

Markdown。B1〜B4 の対応表 (判定 closed/partial/regressed・根拠 file:line・残る穴)、回帰と規模の所見、判定 GO / NO-GO、最後に `## 総括` (5〜10 行)。
推測は推測と明記せよ。
