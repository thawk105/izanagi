単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer

必読事項の射影: 次の 4 ファイルを読め。**どれか 1 つでも読めなければ即停止し、その旨だけを出力せよ。**

- 段 4 裁定 (正本。§2 の A-1/A-3/A-4、§4 プラン v2、§5 変異事前登録):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s4-ruling.md`
- 実装子の最終報告 (**子の主張として信じてよいものは何も無い。すべて現物で検算せよ**):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s5-author.md`
- 段 3 レンズ A (実装前の攻撃。同じ穴が実装に残っていないかを見る):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s3-A.md`
- 親 brief:
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/brief-s1.md`

# 段 6 — 敵対レビュー レンズ A (規律 2: producer が consumer より緩い形を出す隙間・受理集合)

あなたは izanagi の dev-wave 段 6 の敵対レビュー子である。cwd は worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer`。
**実装はするな。ファイルを 1 byte も編集するな。commit するな。** 書込可能 tmp が無いので pytest 緑を要求しない。静的検査でよい。走らせていないものを緑と書くな。予算が尽きそうなら途中結論を出力形式どおりに書いて終われ。

## 対象

`git diff HEAD --stat` と `git diff HEAD -- orchestrator/campaign/reflux_result_evidence.py orchestrator/campaign/reflux_formal_consumer.py orchestrator/tests/test_reflux_result_evidence.py orchestrator/tests/test_reflux_formal_consumer.py` を全文読め (未 commit 差分)。所有外 file に差分があれば名指しせよ。

## 攻撃面

1. **具体的に通る入力。** `derive_physical_result` が `outcome=rejected` + class を返すのに consumer `_validate_wal_outcomes` (`reflux_formal_consumer.py`) が FC07 で落とす入力、または逆に発行拒否すべきなのに返す入力を、**具体的な VerifyResult / terminal record の値**で示せ。特に: dirty integrity、indeterminate、切詰め、複数 anomaly、terminal `verify` と snapshot の byte 不一致、`reason` ≠ verdict、`build_attempt_id` 不一致、accepted で `verify_configs` の部分一致・順序違い・空、bool/float の exact 型 (T-2438 の穴)、`anomalies[0]` を cardinality 検査より前に触る経路。
2. **恒真条件。** 各条件が入力型に含意されて恒真になっていないか (drift assertion と防護の区別が code comment と一致するか)。恒真な条件を殺す負例が「殺した」ことになっていないか。
3. **shared 化による受理集合の変化。** consumer の wrapper 差し替えで FC07 の受理集合が 1 bit でも変わっていないか。逐語移動になっているか (整列・重複排除・prefix・float 許容の混入)。`ArtifactError → FC07` 変換が保たれているか。定数の再 export で既存 test が参照する名前が全部残っているか。
4. **テストの実効性。** 各負例が**単一理由**で落ちるか (過剰決定なら名指し)。正例が実 fixture・実 verifier を名指しし stub していないか。期待値に揮発 payload が焼き込まれていないか。既存 test の期待値が変えられていないか (反転・緩和・skip・削除)。
5. **変異事前登録 M1〜M14・M-C1 の各々**について、実装後の実位置 (file:line、old 逐語) と、殺すはずの nodeid が実在するかを表にせよ。等価変異・他層 mask の疑いがあれば名指しせよ。

## 出力形式

所見ごとに `## A-<n>: <一言>` を置き、**主張 / 根拠 (file:line と具体値) / 帰結 (放置時の成果物・受理集合への影響 1 行) / 推奨 (must-fix / nit / scope 外) / 確度** を書け。変異表は `## 変異×位置×nodeid` に置け。最後に `## 総括` (5 行以内: must-fix 件数、最重、実装を支持するか) を必ず置け。結合文字 U+0300〜U+036F を使うな。
