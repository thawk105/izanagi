単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/s5-diff.patch (レビュー対象の commit de7cc6424 の差分。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/s4-ruling.md (段 4 裁定と plan v2。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/brief.md (親 brief。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/out-consult-B.md (段 3 レンズ B の所見。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/D1893.md (ユーザー裁定の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/origin-insight-excerpt.md (P2/P6 の原典と「なぜ止まらないか」。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/dw-s03-after.md (改訂後の DW-S03 = 本レンズの定義元。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/workers.md (改訂後、commit 済み。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/core.md (改訂後、commit 済み。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/operations.md (改訂後、commit 済み。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/.claude/commands/dev-wave.md (入口、不変。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/skill-self-improvement.md (routing の正本、不変。読めなければ即停止)

## 目的
これは自分たちの開発手順書 (dev-wave の docs) の docs-only 変更のレビューである。ユーザー裁定 D1893 の P2 / P6 を `docs/dev-wave/` へ収容した commit de7cc6424 (3 file、+8/−8 行、実装面 0 byte) を、**レンズ B = 過剰・削除** (改訂後 DW-S03 が定めるレンズ: 追加が研究前進・実測欠陥に対応するか、削除・局所修正で済まないか) で点検する。欠陥を指摘するのが役目で、差分を追認するものではない。

## 親が実行済みの分担 (差分は commit 後のもの)
- 親が段 4 裁定 (s4-ruling.md) に従い 7 編集 (E1〜E7) を当てて commit した。`git diff --check` rc=0、`python3 tools/check_docs.py` 違反なし、層予算の実測 L1 10,616 / 10,625、L1.5 9,660 / 9,696、full provenance 監査 rc=0。
- consumer test 3 file の焦点走: 855 passed、3 skipped (docs_bytes の growth hold、親が check_docs.py を直接走らせて rc=0 で代替)、rc=0。
- 実装面差分ゼロのため変異 matrix は DW-S04 により免除、受入全走は免除しない。

## レンズ B の問い
1. **各編集の必要性**: E1〜E7 のそれぞれが D1893 / 原典 insight の実測欠陥 (所見→T 起票の出口が無い、段 3/6 に削除方向のレンズが無い) に対応しているか、予算のためだけかを分類せよ。予算のためだけの編集 (E3/E4/E6/E7) は最小か。段 3 レンズ B が提案した「E1 を短縮して E3 を不要にする」案を親が「明記する義務が落ちる」として退けた判断は正しいか。
2. **削除で済んだか**: 収容が「既存の語の置換・削除」で完結しているか。新しい義務・gate・検査・台帳・一般化を持ち込んでいないか (ユーザー引数「本題の 2 項反映だけ」)。
3. **恒真化・空回り**: 改訂後の DW-S04「研究前進か実測欠陥を資料/実測で示せる場合だけ」は判定可能か。親が毎回「資料あり」と書けば通る穴が残るなら、それを最小の語で塞ぐ案を bytes 付きで示せ (L1 の残は 9 bytes)。逆に厳しすぎて正当な所見 (静的に確認した正しさ欠陥) が記録止まりになる穴があれば挙げよ。
4. **後段への到達**: 段 4 裁定は「段を問わず同じ基準」「routing を迂回路にしない」を文言に入れず解釈として記録した。これで足りるか、足りないなら最小の是正 (bytes 付き、L1 残 9 の中で) を示せ。docs を変えずに済むなら「変えない」と答えてよい。
5. **親自身への P2 適用**: 本 wave の段 6 を 2 本にした判断・段 3 の 2 本・plan 1 本は過剰でなかったか (docs-only の軽量版で子ゼロも可能だった)。DW-C00 の「受理集合が変わる段では省かない」に照らして評価せよ。
6. **fixture と実物の 1 文字照合**: s4-ruling.md の plan v2 表の置換後文言と、commit 後の実 file の逐語が 1 文字も違わないか照合せよ (改行位置を含む)。

## 制約
- 静的検査のみ。pytest を要求しない (書込可能 tmp が無い)。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 見出しは全部 H2 (`## `) で書く。`###` を使わない。
- 所見は 1 件ずつ「RB-n / 対象 / 主張 / 根拠 (file:line) / 放置時に成果物 (手順書の義務・受理集合) がどう変わるか / 分類 (must-fix・nit・記録) 」の形で書く。must-fix は放置時の影響を 1 行で書けるものだけにする (DW-G05)。

## 出力形式
## 所見 (RB-1 …)
## 編集ごとの必要性分類
## 逐語照合 (plan v2 と実 file)
## 総括
