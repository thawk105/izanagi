単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/stage4-ruling.md — 段 4 裁定 (docs はこれと一致しなければならない)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/user-utterances.md — ユーザー発話 3 件の逐語 (docs が発話の射程を超えて「承認」を書いていないかの基準)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/docs-diff.patch — 修正 2 file (docs/phase3.md、docs/paper-story/README.md) の unified diff。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/consultA-out.md — 段 3 レンズ A (論文価値) の所見と是正案。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/consultB-out.md — 段 3 レンズ B (主経路衝突) の所見と是正案。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D2104-head-and-item13.md — D2104 冒頭と項 13。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D1603.md — pin 前進の材料 3 点。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D579.md — mocc の変異探索面の制限。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/docs/spool/decisions/2026-09-17-dev-wave-cross-protocol-scope-release-1.md — 新規 decisions fragment (レビュー対象)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/docs/spool/worklog/2026-09-17-dev-wave-cross-protocol-scope-release-1.md — 新規 worklog fragment (レビュー対象。「受入後に記入」の 1 箇所は親が受入後に埋める)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/output/insights/2026-09-17/cross-protocol-scope-release/README.md — 新規 insight (裁定の一次資料、レビュー対象)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/docs/spool/README.md — fragment 文法の正本。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/docs/spool/decisions/README.md — decisions fragment の規則 (決定本文に `[T-数字]` を書かない等)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/docs/spool/worklog/README.md — worklog fragment の規則 (`見送り追記` は 1 物理行等)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/docs/paper-story/2026-09-17.md — 凍結版 (変更されていないことと、README の stale 注記が指す箇所の実在を確認する)。読めなければ即停止。

## 依頼 (docs-only wave の敵対レビュー)

あなたは docs-only 裁定パッケージ wave の敵対レビュー役である。read-only で、pytest 実走は不要 (静的検査でよい)。親の `check_docs.py` rc=0 と `spool_fold.py --dry-run` rc=0 は取得済みだが、意味の正しさは検査されていない。次を検査し、所見を「所見 → 根拠 (file:line) → 影響 (放置時に記録・裁定・論文の何が誤るか) → 是正案 (具体的な置換文)」で書け。

1. **裁定文との一致:** 修正 2 file・fragment 2 件・insight の記述が段 4 裁定 (P1〜P4 の確定文、§0 の位置づけ) と食い違う箇所。特に (a) 「ユーザー決定」と「親の裁定」の分離が全 file で保たれているか、(b) 発話の射程を超えて「承認」「確定」「解除した」と書いた箇所、(c) 「主経路完了まで」の期限が存在するかのように書いた箇所、(d) C-1 を必須条件に上げたと読める箇所、(e) selector 据置き・D1373 関門・D1360・D579 の不変が各 file に保たれているか。
2. **過大主張 (F1 型):** 「基盤は完成」「較正は揃った」「性能比較の準備は整った」「mocc は第 2 例として成立する」のように、現況を超えて書いた箇所。数値 (較正 4 件、性能比較 0 件、G2 anomaly 5/42、diff 141 行、所見件数) の出所が逐語 (plan / レンズ) と一致するか。
3. **fragment 文法:** decisions fragment の決定本文に有効な `[T-数字]` が無いか (D70 自己汚染)。worklog fragment の `見送り追記` が 1 物理行か、`新規` item の書式、`title:` に未採番 T が無いか、H2 が `## 本文` / `## 次の一手差分` の 2 つだけか。placeholder の slug 形式。fold 後に消える fragment path を living docs (phase3.md / paper-story README / insight) が恒久参照していないか。
4. **paper-story README の stale 注記:** 凍結版 2026-09-17.md を書き換えていないこと、注記が指す §1・§7・§8 C-1 の記述が実在すること、注記が「方針は古い、事実は変わっていない」の区別を保っていること、「1 件」の件数が本文と一致すること。
5. **insight の一次資料性:** §4 の候補 OID・非祖先・diff 141 行・3 証拠は「レンズ B の静的観測」と出所を明記しているか。§5 の束縛表の各行がレンズ B / plan の記述と一致するか (勝手に増減していないか)。§6 の T 5 本が worklog fragment の `新規` と 1 対 1 で一致するか。
6. **phase3.md の改訂節:** 2026-07-27 改訂と同じ位置・同じ書式か、「(1)〜(5)」が段 4 裁定の要素を漏れなく・過不足なく写しているか、現行チェックポイント L62 付近・must 表 S1 行・後続段 7 の見出し / 追記の 3 箇所が改訂節と矛盾しないか。

予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: must-fix 件数、nit 件数、裁定文との不一致の有無、文法違反の有無)。続けて上の 1〜6 を見出しにして書く。must-fix は「放置時に記録・裁定・論文の何が誤るか」を 1 行で示せるものに限り、示せないものは nit とする。
