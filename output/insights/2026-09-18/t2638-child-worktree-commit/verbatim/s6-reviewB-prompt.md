単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s6-integrated-v1.diff` — レビュー対象の実装差分 (Codex author が子 worktree で書き、親が所有 path 限定 patch として展開し commit d8e512556 にしたもの。親は内容を変えていない)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s6-docs.diff` — 親が編集・commit 済みの docs 差分 (`docs/dev-wave/workers.md` DW-S05-A/B/C、commit 1978fe640、L1.5 予算 9,696/9,696 のため同節内で縮約相殺)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s4-adjudication.md` — 段 4 裁定 (実装の正本)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s5-author-1.md` — 実装子の最終報告。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s5-focus-run.log` — 親が計算ノードで実走した焦点走 (461 passed / 1 failed) の log。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/docs/dev-wave/core.md` の `## DW-G05` 節。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/docs/dev-wave/workers.md` の `## DW-S05-A`〜`## DW-S05-C` 節 (改訂後の実体)。読めなければ即停止。

## 目的

これは自分たちのコード ([T-2638]、D2044 項 16 の実装) の設計レビューである。依頼文は「本題の終端契約だけ。仮想リスク向けの
gate・検査・台帳・一般化の追加は scope 外。新しい保存 framework は作らない」。段 4 裁定で削るべきものは削った (done 判定・
check-only 書込み・rc 再解釈・index.lock 特別扱い・rebase 等の個別分岐)。実装がその裁定どおり最小か、逆に依頼の本体を欠いていないかを点検する。

## 依頼 (レンズ B: 過剰・削除と本体の充足)

`DW-G05` の基準で次を指摘せよ。各所見に「削ると何が失われるか / 残すと何が増えるか」と、放置時の成果物影響 (示せなければ nit) を添える。

1. **裁定 §2 を超える追加**: helper の引数・分岐・出力、`GIT_COMMANDS` の追加、待ち手の配線、テストのうち裁定に無いもの。汎用化・将来拡張の匂い。
2. **裁定 §2 に足りないもの**: 本体 (残差 commit・不発火・rc・provenance・待ち手 opt-in) のうち実装されていない/弱い箇所。
3. **テストの重複と過不足**: 同じ理由で落ちる冗長テスト、逆に本体の正例が実体を名指ししていないもの。焦点走の赤 1 件
   (`test_producer_commit_worktree_after_death` が待ち手の既存 stderr 診断「/proc/<pid>/stat を読めないため pid-only へ縮退」を `err == ""` で拒んだ)
   の最小の是正案 (期待値の弱体化にならず、`NG:` 不在と `producer-commit` 不在を固定する形) を書け。
4. **docs 縮約の意味保存**: DW-S05-A/B/C の縮約 (`s6-docs.diff`) で安全義務が落ちていないか。`<base>` の定義、`--commit-worktree` の名指し、
   D2044 項 16 の参照が最小 bytes で残っているか。
5. **commit message / stdout の形**: 固定件名・本文・trailer が「記録であり採用ではない」ことを読み手に誤解させないか。過剰な本文行は無いか。
6. **scope 外の忍び込み**: cleanup (撤去) や祖先保持への変更、submodule 再帰、排他など、裁定 §4 で scope 外としたものが入っていないか。

制約: read-only sandbox。pytest は走らせない。静的検査でよい。実装しない。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
出力は最終メッセージ本文に全文を書け。

## 出力形式

見出しはすべて `##` (H2)。最後の節は必ず `## 総括` (`#` を 2 個)。`### 総括` と書いてはならない。

## 削除候補 (番号、対象、根拠、失うもの)
## 不足 (本体に足りないもの)
## テスト所見 (赤 1 件の最小是正案を含む)
## docs 所見
## 総括
