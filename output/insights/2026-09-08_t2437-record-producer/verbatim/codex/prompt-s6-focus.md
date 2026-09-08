単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer

必読事項の射影: 次の 5 ファイルを読め。**どれか 1 つでも読めなければ即停止し、その旨だけを出力せよ。**

- fix 裁定 (F-1 / F-2 / F-3a〜c):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/prompt-s6-fix1.md`
- fix 子の最終報告 (**子の主張は信じるな。現物で検算せよ**):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s6-fix1.md`
- 段 6 レビュー A (A-1〜A-5):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s6-review-A.md`
- 段 6 レビュー B (B-1〜B-7):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s6-review-B.md`
- 段 4 裁定:
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s4-ruling.md`

# 段 6 — fix 後の焦点再レビュー (1 本、read-only)

あなたは izanagi の dev-wave 段 6 の焦点再レビュー子である。cwd は worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer`。
**実装はするな。ファイルを 1 byte も編集するな。commit するな。** 書込可能 tmp が無いので pytest 緑を要求しない。静的検査でよい。走らせていないものを緑と書くな。予算が尽きそうなら途中結論を出力形式どおりに書いて終われ。

## 対象

`git diff HEAD --stat` と 4 file の `git diff HEAD` 全文 (段 5 + fix1 の累積、未 commit)。所有外 file の差分があれば名指しせよ。

## 検査

1. **所見ごとの closed / partial / regressed 対応表** (必須、これが無ければ閉じたと判定しない): A-1、A-2/B-1、A-3、A-4、B-2、B-3 (親担当、`pending-parent` と書け)、B-4〜B-7 の各々について、fix 後の現物 (file:line) を根拠に判定せよ。
2. **新たに落ちるようになった正当な production 入力は無いか。** F-1 の projection bytes 入力・digest 照合、F-3a の外枠 exact 5 key が、production `wal.py` writer の出力形 (`{variant, stage, env_tag, ts, payload}`) と `_canonical_wal_interval` の canonical-list 経路の両方で通ることを file:line で示せ。通らない正当入力があれば regressed。
3. **通ってしまう不正入力が残っていないか。** 同 attempt 別 projection、root shadow、verify_configs の空/prefix/逆順/重複、別 run snapshot、reason 不一致、dirty、切詰め、複数 class について、fix 後の経路で具体値を辿れ。
4. **既存 test の期待値が変えられていないか** (反転・緩和・skip・削除)。段 5 で作った 24 nodeid のうち改名・削除されたものを列挙せよ。
5. **変異の位置再確認。** 親の複合変異案 (M2 = typed clean + wire clean + counter の 3 置換、M3/M4 は複合、M5 削除、M15 = `ordered_wal_ref["sha256"] == derived.ordered_wal_sha256` 照合の削除、M16 = 外枠 exact 検査の削除) について、各置換の old 逐語が fix 後の現物に**一意に**存在するか、殺すはずの nodeid が実在するか、まだ mask されるかを表にせよ。

## 出力形式

`## 所見×対応表` (closed/partial/regressed/pending-parent)、`## 新規所見` (あれば `## F-<n>: <一言>` で主張/根拠/帰結/推奨/確度)、`## 変異×位置×nodeid`、最後に `## 総括` (5 行以内: closed/partial/regressed の件数、実装を支持するか)。結合文字 U+0300〜U+036F を使うな。
