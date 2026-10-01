**A-01、B-01〜B-05 はすべて closed。新所見はありません。** 対象2ファイルは `e9a21bef5` と一致し、指定差分を静的に確認しました。

| 所見 | 判定 | 修正後の根拠 |
|---|---|---|
| A-01 | **closed** | [README §4](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/README.md:113) に「F718 除外後の 0〜900 µs の 28 点の中で」を追加。§5.1 の単調性にも同じ範囲を明記。 |
| B-01 | **closed** | [README §6.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/README.md:166) と [failures](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/docs/spool/failures/2026-10-01-t2853-r2-fig2c-1.md:15) に優先順位・相談免除を記載。追加手順は「当時の明文の規則ではない」と明示し、過去の義務との混同を解消。 |
| B-02 | **closed** | [README §5.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/README.md:133) に依存ハッシュ、基準 commit、provenance の具体的な欄を追加。wrapper は「この測り直し専用、repo 外の出力親に保管」に変更。 |
| B-03 | **closed** | [README §5.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/README.md:137) を「R2 で観測した傾向の記述」「形が同じかの判定はしていない」に変更。形状の再現成功という断定は残っていない。 |
| B-04 | **closed** | [README §6.1 項5](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/README.md:175) に「見落とした論点」「原 source commit を使うこと自体は依頼の直接指定」と追記。元の brief は変更差分に含まれない。 |
| B-05 | **closed** | [README §6](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/README.md:159) に「受入全走 1 回を予定（この版の時点で未実施）」と明記。 |

追記された事実の照合結果は次のとおりです。

| 対象 | 一次資料との照合 |
|---|---|
| 当時の規則 | [共通指示](/work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/request-common.txt:3) の優先順位、20行の分割規則、21–22行の相談条件・免除と整合。引用符内は短縮した要約です。[md_4 の原 source commit 指定](/work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/request-md_4.txt:13) とも一致。 |
| 依存 `aa168498…`・基準 `5f9e8c549` | `git show 5f9e8c549:tools/plotting/plot_backoff.py` の SHA-256 は `aa1684986accec98348139c724337e899eafb3493a5e75ee9b112a5a3dbde5be`。[R2 provenance の `dependencies[0].sha256`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/figures/fig2c_r2_b10_extended_backoff.provenance.json:8) と完全一致。同 commit の生成器も `04db851a4a6bb502852fecdd53d9b64f56c0b7b7c3fb94e0526de651cc14216a` で `generator.sha256` と完全一致。 |
| 「0〜900 µs の28点」 | [comparison.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/comparison.md:17) を数え、各 workload とも全29点、1000 µs 除外後28点を確認。最大点6セルと、範囲内の単調性も整合。 |
| 原 read-heavy の1000 µs＝10.275 | [該当行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/comparison.md:113) は **10.274779 M tps**。小数第3位への丸めは **10.275** で、全29点では最大。 |

§10のレビュー要約は前回所見と整合し、保存されたレビュー2本も指定された原本とハッシュが一致しました。旧表現はレビュー履歴として残されており、削除漏れとは判断しません。

## 総括

**GO。6件すべて closed。新たな must-fix / should-fix / nit はありません。**

今回の判定は修正文書と指定一次資料の静的照合に限ります。描画・受入検査の再実行、memory 更新実体の確認は行っていません。書き込み・委任は行っていません。