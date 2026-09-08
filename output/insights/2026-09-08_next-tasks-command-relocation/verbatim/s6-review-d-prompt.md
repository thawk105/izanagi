単独段 dispatch: stage=review; sandbox=read-only; parent=/home/SFC/tanab/.claude/jobs/1d926f28/tmp/wave/brief-stage1.md

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/1d926f28/tmp/wave/brief-stage1.md (親 brief。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1d926f28/tmp/wave/codex-artifacts/author-out.md (実装子の報告。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908 (作業 root。commit 48837186c と c12e25078 を `git show` で読む。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/docs/ai-provenance.md (provenance 契約。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/docs/failures.md の F599 (`grep -n "^### F599"` で位置を取る。読めなければ即停止)

## レンズ D — 系統 blocker の前進修正の正当性 (敵対レビュー、read-only)
書込可能 tmp は無い。pytest 緑は要求しない。静的検査と `git show` / `git ls-tree` / `grep` でよい。
予算が尽きそうなら途中結論を下の出力形式で書いて終われ (無出力が最悪)。

背景: main 先頭 c12e25078 が `.codex/worktrees/*` 110 本を gitlink (mode 160000) として誤 commit した。
commit 48837186c は (a) `git rm --cached -r .codex/worktrees` で index から除き、
(b) `tools/known_violations/c12e25078…--missing-codex-author--e71feba7….json` を登録した。
`.gitignore` への追記は F599 の既裁定に反するとして含めていない。

攻撃対象:
1. 除去の完全性: `git ls-tree -r HEAD | grep 160000` が `external/ccbench` 等の正規 submodule だけを含むか。
   `.gitmodules` と一致するか。作業 file (`.codex/worktrees/` 実体) に触れていないか。
2. 登録の正当性: file 名の digest = 内容 sha256、canonical JSON、field 順、`kind` が checker の finding 種と一致するか。
   この登録が c12e25078 の finding **だけ**を相殺し、他の finding を隠さないか。
   `orchestrator/tests/test_check_ai_provenance.py` 等に既知違反の件数・集合を pin する test があり、
   1 件追加で赤になるものはないか (あれば nodeid を挙げる)。
3. commit 48837186c 自身の provenance: `.codex/worktrees/*` の削除は実装 prefix `.codex/` の非 .md path。
   trailer に Codex role=author があるが、Codex が書いたのは JSON だけで削除は親の git 操作である。
   `docs/ai-provenance.md` の「Git 操作の機械的代行は記録しない」と整合するか、それとも
   別の記録 (scope 等) が要るか。
4. 副作用: `tools/dev_wave_land.py` の `_CONTROL_CONTAINERS`、`tools/mutation_worktree.py` の共有 checkout 観測、
   受入の preflight (`git submodule status --recursive`) が、この 2 commit の land 後に期待どおり回復するか。
   逆に、land 後も残る詰まり (例: 既に c12e25078 を取り込んだ他 wave の worktree、`.git/modules` の残骸) を列挙する。
5. `.gitignore` 追記を含めない判断が F599 の射程に照らして正しいか。含めるべきなら成果物影響を 1 行で。

各所見に、放置時に成果物 (land・受入・他 wave) の何が変わるかを 1 行で書く (書けない所見は nit)。
仮想リスクだけの gate・台帳・一般化の提案はしない。

## 出力形式
- 所見ごとに: `[must-fix|should|nit] <題>` / 根拠 (file:line または command と出力) / 成果物影響 1 行 / 推奨。
- 最後に `## 総括` 節: must-fix 件数、should 件数、確信の無い点。
