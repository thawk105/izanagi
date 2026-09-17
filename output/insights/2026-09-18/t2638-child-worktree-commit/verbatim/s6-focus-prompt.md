単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s6-reviewA-1.md` — 段 6 レビュー A (所見 1〜8)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s6-reviewB-1.md` — 段 6 レビュー B。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s6-fix-v2.diff` — fix 後の差分 (commit d8e512556 → c5403437c: docs v2 fe1e6662e + fix c5403437c)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s6-fix-1.md` — fix 子の最終報告 (反実仮想の結果と検出限界の申告を含む)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s6-inspect-child-commit.txt` — 親が実測した実データ検証: fix 子は新機構を含む HEAD から起動され、起動器が終端で残差を子 branch へ commit した (5a99d99d0) — その commit の message・trailer・stat・作業木状態・message file 残置の実測。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/tools/dev_waves/git_state.py` の 229〜330 行 (fix 適用後の実体)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/docs/dev-wave/workers.md` の `## DW-S05-A` 節 (docs v2 適用後の実体)。読めなければ即停止。

## 目的

これは自分たちのコード ([T-2638]、D2044 項 16 の実装) の fix 後の焦点再レビューである。段 6 レビュー A/B の所見が fix (c5403437c) と docs v2 (fe1e6662e) で閉じたかを、
所見ごとに `closed` / `partial` / `regressed` で判定する。

## 依頼

1. **所見ごとの対応表** (レビュー A の 1〜8、レビュー B の削除候補 1〜2・不足・テスト所見・docs 所見) を作り、各行に `closed` / `partial` / `regressed` と根拠 (差分の hunk、file:line) を書く。
   表のない所見は closed と判定しない。
2. **fix の副作用**: message file を `<git-dir>/izanagi-worker-commit.msg` に置く変更が、linked worktree (`.git/worktrees/<name>/`) と主 checkout 以外の git-dir 形 (例: `GIT_DIR` 分離、bare) で
   問題を起こすか。既存 git-dir 内 file と衝突しないか。同名 file が残っていた場合の挙動 (上書き)。
3. **fix 子が申告した検出限界**: 「`dir=None` へ戻しても新 assert は赤化しない (使用中の配置先は検出できない)」— これを受け入れてよいか、それとも配置を直接固定する assert (例: 実装が `git_dir /` を使うことの静的検査、または `TMPDIR` を作業木内に向けた subprocess 走で作業木に untracked が出ないこと) を足すべきか。DW-G05 の基準 (成果物影響を 1 行で示せなければ nit) で裁け。
4. **実データ検証の読み**: `s6-inspect-child-commit.txt` の commit が裁定 §2.1 の message 形式・trailer・stdout 行・clean・message file 不在を満たしているか。満たさない点があれば real 所見。
5. **DW-S05-A v2 の文**: 「起動器は author/fix の投入先全残差を終端 commit、待ち手は呼出側指定 `--commit-worktree <abs>`。記録のみ (D2044 項 16)。」がレビュー A 所見 2 / B docs 所見の 3 点 (保存範囲・呼出側指定・記録のみ) を最小 bytes で満たすか。

制約: read-only sandbox。pytest は走らせない。静的検査でよい。実装しない。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
出力は最終メッセージ本文に全文を書け。

## 出力形式

見出しはすべて `##` (H2)。最後の節は必ず `## 総括` (`#` を 2 個)。`### 総括` と書いてはならない。

## 所見対応表 (所見 ID、closed/partial/regressed、根拠)
## 新規所見 (あれば。real/refuted/unverified、must-fix/nit、成果物影響)
## 総括
