単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/s4-ruling.md`
  — 親の段 4 裁定 (確定仕様と変異事前登録)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/verbatim-d1625.md`
  — 確定済みユーザー裁定 D1625 の逐語。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/s5-impl-diff.txt`
  — 実装子が作った差分の全文。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/codex-artifacts/t2314-inert-reason-pair/s5-impl-out.md`
  — 実装子の完了報告。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py`
  — 変更後の production。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py`
  — 変更後の test。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py`
  — gate 本体 (読むだけ)。読めなければ即停止。

## 依頼 — レンズ C: 正しさ防壁と受理集合

**敵対レビュー**である。実装を守らず攻撃せよ。実装・修正はするな。書込み可能な tmp が無いので
pytest 緑は要求しない。静的検査で足りる。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。

1. **受理集合が裁定を超えていないか。** 変更後の述語が受理する `(reason_code, comparison)` の
   集合を実コードから列挙し、D1625 の 2 組と完全一致するか確かめよ。第 3 の理由コード、
   `None`、空文字、型違い (bytes、部分一致) が通る経路が無いか。
2. **exact 性の劣化。** 元の `==` 連鎖から落ちた条件が 1 つも無いか、行ごとに突き合わせよ
   (`observed == expected`、receipt summary 一致、`admitted is True`、`driver_id`、`macro`、
   `terminal_status == "green"`、meaning の 2 条件)。
3. **A-01 の回帰。** `evidence` への添字参照が **1 箇所も残っていないか**。赤 record
   (`comparison` key なし) を渡したとき `verdict_s6` が例外でなく `inconclusive` を返すか、
   コードを辿って確かめよ。
4. **追加 test が恒真でないか。** 各新 test について、**probe の述語ではなく gate の admission や
   receipt summary 比較で先に落ちていないか**を層ごとに特定せよ。特に交叉負例は、
   gate を中和した上で交叉 family 由来の receipt を渡していなければ probe の述語に到達しない。
   到達しない test は「守っていない test」として所見にせよ。
5. **正例が本物か。** root-location-only の正例が production evaluator を通っており、
   `_arm_record` 等での手書き偽造でないこと、依存先を stub していないことを確かめよ。
6. **事前登録した変異 M1〜M4 が本当に殺されるか。** 裁定の変異表を読み、各変異を当てたとき
   期待 node が**それだけ**赤くなるか (他の node が巻き添えで赤くなる、あるいは 1 つも赤くならない)
   をコードから予測せよ。ずれるなら期待 node の完全集合を訂正して示せ。
7. **既存テストの期待値が変えられていないか。** 差分中に既存 assert の反転・緩和・skip・削除・
   閾値変更が無いか、1 行ずつ確かめよ。あれば最重大の所見である。

## 禁止

- 実装・修正・commit・git 操作・ファイル書き換えをしない。
- 新しい gate・検査・台帳・互換層・一般化を提案しない。
- scope 外の real 所見は「裁定パッケージ候補」と明記して返す。

## 出力形式

```
## 所見
（所見 ID / must-fix か nit か / 対象 file:line / なぜ壊れるか / 具体的な入力例）
（must-fix には「放置すると成果物の値・受理集合・参照がどう変わるか」を 1 行で必ず書く。
  書けないものは nit にせよ）

## 受理集合の列挙
（変更後に受理される組の完全集合と、その導出根拠の file:line）

## 変異 M1〜M4 の予測
（各変異について、期待 node が正しいか。ずれるなら訂正した完全集合）

## 裁定パッケージ候補

## 総括
（3〜6 行。GO / NO-GO を明示する）
```
