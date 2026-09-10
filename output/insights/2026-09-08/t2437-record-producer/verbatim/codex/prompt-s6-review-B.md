単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer

必読事項の射影: 次の 4 ファイルを読め。**どれか 1 つでも読めなければ即停止し、その旨だけを出力せよ。**

- 段 4 裁定 (正本。§2 の B-1/B-2/B-5/B-6/B-7、§4 プラン v2):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s4-ruling.md`
- 実装子の最終報告 (**子の主張として信じてよいものは何も無い。すべて現物で検算せよ**):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s5-author.md`
- 段 3 レンズ B (実装前の攻撃):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s3-B.md`
- 親 brief:
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/brief-s1.md`

# 段 6 — 敵対レビュー レンズ B (整合と実効性: bytes 不変・同一性・端から端の到達点・scope)

あなたは izanagi の dev-wave 段 6 の敵対レビュー子である。cwd は worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer`。
**実装はするな。ファイルを 1 byte も編集するな。commit するな。** 書込可能 tmp が無いので pytest 緑を要求しない。静的検査でよい。走らせていないものを緑と書くな。予算が尽きそうなら途中結論を出力形式どおりに書いて終われ。

## 対象

`git diff HEAD --stat` と `git diff HEAD -- orchestrator/campaign/reflux_result_evidence.py orchestrator/campaign/reflux_formal_consumer.py orchestrator/tests/test_reflux_result_evidence.py orchestrator/tests/test_reflux_formal_consumer.py` を全文読め。**所有外 file (fixture builder、baseline JSON、wal.py、pipeline.py、verifier、docs) に差分があれば必ず名指しせよ** (`git status --short` 全行)。

## 攻撃面

1. **bytes 不変。** fixture builder・`reflux_origin_fixture_baseline.json`・golden 4 個 (`test_reflux_result_evidence.py:24-27`) が不変か。producer が作る record の bytes が、同じ入力に対する fixture builder の bytes と一致するか (key 順・型・null の表現)。一致しないなら FC04/FC01 でどう落ちるかを示せ。
2. **digest の同一性。** producer の `witness_class_sha256(result_to_dict(vr)["anomalies"][0])` と、WAL 往復 (json dumps → parse) 後の anomaly に対する consumer の digest が同値になる根拠を、canonical JSON の実装 (`reflux_origin_artifacts.py` の `canonical_json_bytes`) と `wal.py` の書式で示せ。int/float、list 順、key 順、Unicode の escape で乖離する入力があれば示せ。
3. **端から端 test の到達点 (B-1/B-2)。** 新 test が fixture の既存 physical root へ追記・上書きしていないか、evidence tree を新しい tmp に作っているか、33 record すべてが producer 経由か、sealed member の写像が raw bytes からか、`P6Unavailable` に到達しているか (FC07 でなく FC01/FC04/FC05/FC09 で止まっていないか、あるいは早期の `P6Unavailable` 経路で実は FC07 を通っていないか) を現物で確かめよ。docstring が salts 不変・未行使、synthetic source 束縛限定 (B-5) を書いているか。
4. **pin 閉包 (B-7)。** `test_plain_runner_coverage`、`test_consumer_source_has_no_nonaborted_construction_or_success_variant` (15 file AST 走査)、`test_reflux_origin_fixture_builder` の独立再計算、受入所要台帳の被覆率 gate に対する影響を静的に評価せよ。新 module・新 test file・xdist group・role が増えていないか。
5. **scope (DW-G05)。** 裁定 §4 の編集面を超える追加 (S3、provenance issuer、pipeline 配線、新 gate・台帳・一般化) が紛れていないか。逆に裁定 §4 の必須要素 (A-1 の terminal 結合、A-4 の shared 化、B-1 の tmp tree、A-3 の drift comment と exact 型負例) が欠けていないか。1 対 1 で表にせよ。
6. **子の報告と実体の食い違い。** s5-author.md の「実走結果」「新規 nodeid 一覧」「変異×nodeid 表」を diff の現物と突き合わせ、存在しない nodeid・数え違い・未実走を緑と書いた箇所を名指しせよ。

## 出力形式

所見ごとに `## B-<n>: <一言>` を置き、**主張 / 根拠 (file:line) / 帰結 (放置時の成果物・受理集合・参照への影響 1 行) / 推奨 (must-fix / nit / scope 外) / 確度** を書け。§5 の対応表は `## 裁定×実装 対応表` に置け。最後に `## 総括` (5 行以内: must-fix 件数、最重、実装を支持するか) を必ず置け。結合文字 U+0300〜U+036F を使うな。
